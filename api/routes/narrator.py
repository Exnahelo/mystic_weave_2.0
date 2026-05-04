"""routes/narrator.py — POST /narrator/scene_resolved.

The narrator-facing orchestrator that composes scene boundary recording,
progression validation, advance commit, non-advancement state changes, and
time advancement into one transactional flow.

Brief 20 (Backend Authority Arc, Phase 2 keystone). Wraps Brief 18's
scan/commit and Brief 19's declare_scene_resolution, plus inline state
mutation, inside a single SELECT FOR UPDATE transaction. All-or-nothing
semantics — partial scene resolution is structurally impossible.
"""

from __future__ import annotations

import json
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends

from api.database import get_pool
from api.models import TimeElapsed, TimeState
from api.models.progression import (
    CandidateTag,
    FitStrength,
    SceneResolvedRequest,
    SceneResolvedResponse,
)
from api.routes._helpers import session_not_found
from api.routes.progression import (
    _STRENGTH_RANK,
    _build_candidate_tag,
    _candidates_from_action,
    _registry_lookup,
    commit_advance_in_transaction,
)
from api.routes.scene_records import declare_scene_in_transaction
from api.time_advance import advance_time

router = APIRouter()


@router.post(
    "/narrator/scene_resolved",
    response_model=SceneResolvedResponse,
    tags=["narrator"],
    description=(
        "Single composable endpoint for resolving one scene. Records scene "
        "boundary, validates and commits at most one tag advance, applies "
        "non-advancement state changes, and advances time — all atomically."
    ),
)
async def scene_resolved(
    body: SceneResolvedRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> SceneResolvedResponse:
    """Compose scene resolution as one transactional flow."""
    changes_applied: list[str] = []
    advance_committed: dict[str, Any] | None = None
    proposed_evaluation: dict[str, Any] | None = None

    actions_dicts = [a.model_dump() for a in body.scene_actions]

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Step 1: Verify session exists and lock for update.
            game_row = await conn.fetchrow(
                "SELECT character, world, log FROM game_states "
                "WHERE session_id = $1 FOR UPDATE",
                body.session_id,
            )
            if game_row is None:
                raise session_not_found(body.session_id)

            character = dict(game_row["character"])

            # Step 2: Declare scene boundary (creates scene_id, validates arc IDs).
            scene_result = await declare_scene_in_transaction(
                conn,
                session_id=body.session_id,
                scene_summary=body.scene_summary,
                scene_actions=actions_dicts,
                location_id=body.location_id,
                arc_progressed_ids=body.arc_progressed_ids,
            )
            scene_id = scene_result["scene_id"]
            changes_applied.append("scene_recorded")

            # Step 3: Build ranked candidates from scene actions (in-memory scan).
            seen_tags: set[str] = set()
            raw_candidates: list[tuple[str, str, str, FitStrength]] = []
            for i, action in enumerate(actions_dicts):
                for cand in _candidates_from_action(action, i):
                    if cand[0] not in seen_tags:
                        seen_tags.add(cand[0])
                        raw_candidates.append(cand)

            candidates: list[CandidateTag] = [
                _build_candidate_tag(tag, kind, parent, fit, character)
                for tag, kind, parent, fit in raw_candidates
            ]
            candidates.sort(
                key=lambda c: (
                    _STRENGTH_RANK[c.fit.strength],
                    not c.held_by_character,
                    c.tag,
                )
            )

            # Step 4: Evaluate proposed advance (if submitted).
            if body.proposed_advance is not None:
                prop_tag = body.proposed_advance.tag
                lookup = _registry_lookup(prop_tag)

                if lookup is None:
                    proposed_evaluation = {
                        "tag": prop_tag,
                        "in_candidates": False,
                        "eligible": False,
                        "validation": "unknown_tag",
                        "strongest_omitted": None,
                    }
                else:
                    kind, data = lookup
                    if kind == "application":
                        parent_field = data.get("group", "")
                    elif kind == "spell":
                        parent_field = data.get("field", "")
                    else:
                        parent_field = ""

                    synthetic_fit = FitStrength(
                        strength="contextual",
                        reason="narrator-proposed via orchestrator",
                        source_action_index=None,
                    )
                    evaluated = _build_candidate_tag(
                        prop_tag, kind, parent_field, synthetic_fit, character
                    )

                    in_candidates = prop_tag in seen_tags
                    if not evaluated.eligible:
                        validation = "invalid"
                        strongest_omitted = None
                    elif not in_candidates:
                        explicit = [
                            c for c in candidates
                            if c.fit.strength == "explicit" and c.eligible
                        ]
                        if explicit:
                            validation = "omits_strongest"
                            strongest_omitted = [c.tag for c in explicit[:3]]
                        else:
                            validation = "proposed_match"
                            strongest_omitted = None
                    else:
                        strongest = candidates[0] if candidates else None
                        if (
                            strongest is not None
                            and strongest.tag != prop_tag
                            and strongest.fit.strength == "explicit"
                            and strongest.eligible
                        ):
                            validation = "omits_strongest"
                            strongest_omitted = [strongest.tag]
                        else:
                            validation = "proposed_match"
                            strongest_omitted = None

                    proposed_evaluation = {
                        "tag": prop_tag,
                        "in_candidates": in_candidates,
                        "eligible": evaluated.eligible,
                        "validation": validation,
                        "strongest_omitted": strongest_omitted,
                    }

                    # Step 5: Commit if eligible. The narrator's choice stands;
                    # 'omits_strongest' is informational, not blocking.
                    if evaluated.eligible:
                        advance_committed = await commit_advance_in_transaction(
                            conn,
                            session_id=body.session_id,
                            tag=prop_tag,
                            rationale=body.proposed_advance.rationale,
                            scene_id=scene_id,
                        )
                        changes_applied.append(f"advance_committed:{prop_tag}")
                        # Re-load character so subsequent steps see post-commit state.
                        char_row = await conn.fetchrow(
                            "SELECT character FROM game_states WHERE session_id = $1",
                            body.session_id,
                        )
                        character = dict(char_row["character"])

            # Step 6+7: Apply non-advancement character + world changes (in-memory).
            world: dict[str, Any] | None = None
            non_advance_changes = (
                body.character_changes is not None
                or body.world_changes is not None
                or body.time_elapsed is not None
            )

            if body.character_changes is not None:
                char_changes = body.character_changes.model_dump(exclude_none=True)
                for k, v in char_changes.items():
                    character[k] = v
                    changes_applied.append(f"character.{k}")

            if body.world_changes is not None or body.time_elapsed is not None:
                world = dict(game_row["world"])

            if body.world_changes is not None:
                world_changes = body.world_changes.model_dump(exclude_none=True)
                for k, v in world_changes.items():
                    world[k] = v  # type: ignore[index]
                    changes_applied.append(f"world.{k}")

            # Step 8: Advance time.
            if body.time_elapsed is not None:
                assert world is not None  # set above when time_elapsed present
                time_state = TimeState.model_validate(world.get("time", {}))
                time_elapsed = TimeElapsed.model_validate(body.time_elapsed)
                new_time = advance_time(time_state, time_elapsed)
                world["time"] = new_time.model_dump(mode="json")
                world["turn"] = (world.get("turn") or 0) + 1
                changes_applied.append("time_advanced")

            # Step 9: Persist character + world if any non-advance changes happened.
            # (advance_committed already wrote character; we only re-write here when
            # other mutations are layered on top.)
            if non_advance_changes:
                # Use the post-commit character if a commit happened, else the loaded one.
                final_world = world if world is not None else dict(game_row["world"])
                await conn.execute(
                    "UPDATE game_states "
                    "SET character = $1::jsonb, world = $2::jsonb, "
                    "    updated_at = NOW() WHERE session_id = $3",
                    character,
                    final_world,
                    body.session_id,
                )

            # Step 10: Final read for state_after.
            final_row = await conn.fetchrow(
                "SELECT character, world, log, updated_at "
                "FROM game_states WHERE session_id = $1",
                body.session_id,
            )
            state_after = {
                "character": dict(final_row["character"]),
                "world": dict(final_row["world"]),
                "log": list(final_row["log"]),
                "updated_at": (
                    final_row["updated_at"].isoformat()
                    if final_row["updated_at"] is not None
                    else None
                ),
            }

    return SceneResolvedResponse(
        session_id=body.session_id,
        scene_id=scene_id,
        advance_committed=advance_committed,
        proposed_evaluation=proposed_evaluation,
        candidates_ranked=candidates,
        resolved_at=scene_result["resolved_at"],
        location_id=scene_result["location_id"],
        turn_at_resolution=scene_result["turn_at_resolution"],
        arc_envelope_status=scene_result["arc_envelope_status"],
        suggestions=scene_result["suggestions"],
        state_after=state_after,
        changes_applied=changes_applied,
    )
