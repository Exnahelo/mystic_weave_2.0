"""routes/progression.py — POST /progression/scan and POST /progression/commit.

Two-stage progression validation:

- /scan returns ranked candidates with explicit/implicit/contextual fit and
  parent-cap/registry/eligibility validation. Pure validation; no state
  mutation.
- /commit applies one validated advance atomically inside a SELECT FOR
  UPDATE transaction. Reuses _apply_tag_advancement_counters from state.py
  for the counter-rollover math.

Brief 18 (Backend Authority Arc, Phase 2 step 1). The scene_id parameter
is accepted but has no effect; it becomes meaningful in Brief 19 when
scene records exist.
"""

from __future__ import annotations

import json
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from api.database import get_pool
from api.game_data import (
    list_applications,
    list_knowledge_groups,
    list_magic_fields,
    list_spells,
)
from api.models import TypedLogEntry
from api.models.progression import (
    CandidateTag,
    FitStrength,
    ProgressionCommitRequest,
    ProgressionCommitResponse,
    ProgressionScanRequest,
    ProgressionScanResponse,
    ProposedEvaluation,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Registry lookup helper
# ---------------------------------------------------------------------------

def _registry_lookup(name: str) -> tuple[str, dict[str, Any]] | None:
    """Look up a name across all registries. Returns (kind, data) or None.

    Magic fields use 'id' as their canonical key; the other three use 'index'.
    """
    for entry in list_applications():
        if entry.get("index") == name:
            return ("application", entry)
    for entry in list_knowledge_groups():
        if entry.get("index") == name:
            return ("knowledge_group", entry)
    for entry in list_magic_fields():
        if entry.get("id") == name:
            return ("magic_field", entry)
    for entry in list_spells():
        if entry.get("index") == name:
            return ("spell", entry)
    return None


# ---------------------------------------------------------------------------
# Action → candidate mapping (hardcoded fit rules)
# ---------------------------------------------------------------------------

def _candidates_from_action(
    action: dict[str, Any],
    action_index: int,
) -> list[tuple[str, str, str, FitStrength]]:
    """Map a single scene action to candidate tags.

    Returns list of (tag, kind, parent_or_field, FitStrength) tuples. The
    primary action target (spell/weapon/application) is the strongest
    candidate; its parent group/field is one strength step weaker.
    """
    candidates: list[tuple[str, str, str, FitStrength]] = []
    action_type = action["type"]
    outcome = action.get("outcome", "success")

    # success/partial = explicit; failure attenuates to implicit.
    base_strength = "explicit" if outcome in ("success", "partial") else "implicit"
    parent_strength = "implicit" if base_strength == "explicit" else "contextual"

    if action_type == "spell_cast":
        spell = action["spell"]
        lookup = _registry_lookup(spell)
        if lookup and lookup[0] == "spell":
            field = lookup[1].get("field", "")
            candidates.append((
                spell, "spell", field,
                FitStrength(
                    strength=base_strength,
                    reason=f"spell_cast action declared (outcome: {outcome})",
                    source_action_index=action_index,
                ),
            ))
            if field and _registry_lookup(field):
                candidates.append((
                    field, "magic_field", "",
                    FitStrength(
                        strength=parent_strength,
                        reason=f"parent field of cast spell '{spell}'",
                        source_action_index=action_index,
                    ),
                ))

    elif action_type == "weapon_attack":
        weapon = action["weapon"]
        lookup = _registry_lookup(weapon)
        if lookup and lookup[0] == "application":
            group = lookup[1].get("group", "")
            candidates.append((
                weapon, "application", group,
                FitStrength(
                    strength=base_strength,
                    reason=f"weapon_attack action declared (outcome: {outcome})",
                    source_action_index=action_index,
                ),
            ))
            if group and _registry_lookup(group):
                candidates.append((
                    group, "knowledge_group", "",
                    FitStrength(
                        strength=parent_strength,
                        reason=f"parent group of weapon '{weapon}'",
                        source_action_index=action_index,
                    ),
                ))

    elif action_type in (
        "social_roll", "perception_roll", "movement", "defense", "generic_roll",
    ):
        app = action["application"]
        lookup = _registry_lookup(app)
        if lookup and lookup[0] == "application":
            group = lookup[1].get("group", "")
            candidates.append((
                app, "application", group,
                FitStrength(
                    strength=base_strength,
                    reason=f"{action_type} action declared with application '{app}' (outcome: {outcome})",
                    source_action_index=action_index,
                ),
            ))
            if group and _registry_lookup(group):
                candidates.append((
                    group, "knowledge_group", "",
                    FitStrength(
                        strength=parent_strength,
                        reason=f"parent group of '{app}'",
                        source_action_index=action_index,
                    ),
                ))

    return candidates


_STRENGTH_RANK = {"explicit": 0, "implicit": 1, "contextual": 2}


def _build_candidate_tag(
    tag: str,
    kind: str,
    parent: str,
    fit: FitStrength,
    character: dict[str, Any],
) -> CandidateTag:
    """Construct a CandidateTag with held/eligibility checks against character."""
    knowledge = character.get("knowledge") or {}
    magic = character.get("magic") or {}

    held = False
    current_tier = 0
    parent_cap_ok = True

    if kind == "application":
        group_block = knowledge.get(parent) or {}
        if isinstance(group_block, dict):
            apps = group_block.get("applications") or {}
            if isinstance(apps, dict) and tag in apps:
                held = True
                current_tier = apps[tag]
            parent_tier = group_block.get("tier", 0) or 0
            parent_cap_ok = (current_tier + 1) <= parent_tier

    elif kind == "knowledge_group":
        group_block = knowledge.get(tag) or {}
        if isinstance(group_block, dict) and "tier" in group_block:
            held = True
            current_tier = group_block["tier"]
        # Knowledge groups are top-level — no parent-cap.
        parent_cap_ok = True

    elif kind == "spell":
        field_block = magic.get(parent) or {}
        if isinstance(field_block, dict):
            spells = field_block.get("spells") or {}
            if isinstance(spells, dict) and tag in spells:
                held = True
                current_tier = spells[tag]
            field_tier = field_block.get("tier", 0) or 0
            parent_cap_ok = (current_tier + 1) <= field_tier

    elif kind == "magic_field":
        field_block = magic.get(tag) or {}
        if isinstance(field_block, dict) and "tier" in field_block:
            held = True
            current_tier = field_block["tier"]
        parent_cap_ok = True

    proposed_new_tier = current_tier + 1
    at_max = current_tier >= 5
    eligible = held and not at_max and parent_cap_ok

    return CandidateTag(
        tag=tag,
        kind=kind,
        parent=parent if parent else None,
        current_tier=current_tier,
        proposed_new_tier=proposed_new_tier,
        fit=fit,
        parent_cap_ok=parent_cap_ok,
        held_by_character=held,
        at_max_tier=at_max,
        eligible=eligible,
    )


async def _load_character(pool: asyncpg.Pool, session_id: str) -> dict[str, Any]:
    """Load character JSONB from the session row. 404 if not found."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT character FROM game_states WHERE session_id = $1",
            session_id,
        )
    if row is None:
        raise HTTPException(status_code=404, detail={"error": "session_not_found"})
    raw = row["character"]
    return json.loads(raw) if isinstance(raw, str) else raw


async def _check_scene_already_advanced(
    pool: asyncpg.Pool,
    session_id: str,
    scene_id: str,
) -> str | None:
    """Return tag_advance_committed if the scene exists and was advanced, else None.

    Raises 422 when the scene_id is provided but doesn't exist for this session.
    Brief 19 wires this into /progression/scan and /progression/commit so the
    optional scene_id parameter Brief 18 added becomes meaningful.
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT tag_advance_committed FROM scene_records "
            "WHERE scene_id = $1 AND session_id = $2",
            scene_id,
            session_id,
        )
    if row is None:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "unknown_scene_id",
                "scene_id": scene_id,
                "session_id": session_id,
            },
        )
    return row["tag_advance_committed"]


# ---------------------------------------------------------------------------
# /progression/scan
# ---------------------------------------------------------------------------

@router.post(
    "/progression/scan",
    response_model=ProgressionScanResponse,
    tags=["progression"],
    description=(
        "Validate proposed advances against scene actions and character state. "
        "Returns ranked candidates with fit strength, parent-cap and registry "
        "checks, and proposed-vs-strongest comparison. No state mutation."
    ),
)
async def progression_scan(
    body: ProgressionScanRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> ProgressionScanResponse:
    """Validate proposed advances against scene actions; return ranked candidates."""
    character = await _load_character(pool, body.session_id)

    # Brief 19: if scene_id is provided, check whether the scene already
    # received a tag advance. If so, all candidates are marked ineligible
    # (one-tag-per-scene enforcement at the validation layer).
    already_advanced_tag: str | None = None
    if body.scene_id:
        already_advanced_tag = await _check_scene_already_advanced(
            pool, body.session_id, body.scene_id
        )

    seen_tags: set[str] = set()
    raw_candidates: list[tuple[str, str, str, FitStrength]] = []
    for i, action in enumerate(body.scene_actions):
        action_dict = action.model_dump()
        for cand in _candidates_from_action(action_dict, i):
            if cand[0] not in seen_tags:
                seen_tags.add(cand[0])
                raw_candidates.append(cand)

    candidates: list[CandidateTag] = [
        _build_candidate_tag(tag, kind, parent, fit, character)
        for tag, kind, parent, fit in raw_candidates
    ]
    if already_advanced_tag is not None:
        candidates = [c.model_copy(update={"eligible": False}) for c in candidates]
    candidates.sort(
        key=lambda c: (
            _STRENGTH_RANK[c.fit.strength],
            not c.held_by_character,
            c.tag,
        )
    )

    proposed_evaluations: list[ProposedEvaluation] = []
    for prop in body.proposed_advances:
        tag = prop.tag
        in_candidates = tag in seen_tags

        lookup = _registry_lookup(tag)
        if lookup is None:
            proposed_evaluations.append(ProposedEvaluation(
                tag=tag,
                in_candidates=False,
                eligible=False,
                validation="unknown_tag",
                strongest_omitted=None,
            ))
            continue

        kind, data = lookup
        parent = ""
        if kind == "application":
            parent = data.get("group", "")
        elif kind == "spell":
            parent = data.get("field", "")

        synthetic_fit = FitStrength(
            strength="contextual",
            reason="narrator-proposed; not directly produced by structured actions",
            source_action_index=None,
        )
        evaluated = _build_candidate_tag(tag, kind, parent, synthetic_fit, character)
        # Brief 19: scene already advanced -> nothing is eligible.
        if already_advanced_tag is not None:
            evaluated = evaluated.model_copy(update={"eligible": False})

        if not evaluated.eligible:
            validation = "invalid"
            strongest_omitted = None
        elif not in_candidates:
            explicit = [c for c in candidates if c.fit.strength == "explicit" and c.eligible]
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
                and strongest.tag != tag
                and strongest.fit.strength == "explicit"
                and strongest.eligible
            ):
                validation = "omits_strongest"
                strongest_omitted = [strongest.tag]
            else:
                validation = "proposed_match"
                strongest_omitted = None

        proposed_evaluations.append(ProposedEvaluation(
            tag=tag,
            in_candidates=in_candidates,
            eligible=evaluated.eligible,
            validation=validation,
            strongest_omitted=strongest_omitted,
        ))

    warnings: list[str] = []
    if not body.proposed_advances:
        warnings.append("no_proposed_advances")
    if not body.scene_actions:
        warnings.append("no_scene_actions")
    if already_advanced_tag is not None:
        warnings.append("scene_already_advanced")

    return ProgressionScanResponse(
        session_id=body.session_id,
        scene_id=body.scene_id,
        candidates_ranked=candidates,
        proposed_evaluation=proposed_evaluations,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# /progression/commit
# ---------------------------------------------------------------------------

@router.post(
    "/progression/commit",
    response_model=ProgressionCommitResponse,
    tags=["progression"],
    description=(
        "Atomically commit one tag advance. Validates registry membership, "
        "tag held, not at max tier; auto-bumps parent when needed. Applies "
        "tier increase, runs counter-rollover (every 3 advances -> +1 AP), "
        "appends a typed log entry. Returns updated advancement state."
    ),
)
async def progression_commit(
    body: ProgressionCommitRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> ProgressionCommitResponse:
    """Apply one validated advance atomically. Reuses state.py counter logic."""
    # Local import to avoid circular dependency between routes/progression and routes/state.
    from api.routes.state import _apply_tag_advancement_counters

    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT character, log FROM game_states WHERE session_id = $1 FOR UPDATE",
                body.session_id,
            )
            if row is None:
                raise HTTPException(status_code=404, detail={"error": "session_not_found"})

            raw_char = row["character"]
            character = json.loads(raw_char) if isinstance(raw_char, str) else dict(raw_char)
            raw_log = row["log"]
            log_arr = json.loads(raw_log) if isinstance(raw_log, str) else list(raw_log)

            # Brief 19: optional scene_id enforces one-tag-per-scene at the DB.
            # Lock the scene row alongside the game_state row so a concurrent
            # commit on the same scene loses cleanly.
            if body.scene_id:
                scene_row = await conn.fetchrow(
                    "SELECT tag_advance_committed FROM scene_records "
                    "WHERE scene_id = $1 AND session_id = $2 FOR UPDATE",
                    body.scene_id,
                    body.session_id,
                )
                if scene_row is None:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "error": "unknown_scene_id",
                            "scene_id": body.scene_id,
                            "session_id": body.session_id,
                        },
                    )
                if scene_row["tag_advance_committed"] is not None:
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error": "scene_already_advanced",
                            "existing_tag": scene_row["tag_advance_committed"],
                            "scene_id": body.scene_id,
                        },
                    )

            lookup = _registry_lookup(body.tag)
            if lookup is None:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "unknown_tag",
                        "message": f"Tag '{body.tag}' not found in any registry.",
                        "tag": body.tag,
                    },
                )

            kind, data = lookup
            parent_bumped = False
            parent_tag: str | None = None
            new_tier = 0

            updated_character = json.loads(json.dumps(character))  # deep copy

            if kind == "application":
                parent = data.get("group", "")
                kgroup = updated_character.setdefault("knowledge", {}).get(parent)
                if not isinstance(kgroup, dict) or "applications" not in kgroup:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "error": "parent_group_not_held",
                            "message": (
                                f"Character does not hold parent group '{parent}' "
                                f"for application '{body.tag}'."
                            ),
                        },
                    )
                apps = kgroup["applications"]
                if body.tag not in apps:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "error": "tag_not_held",
                            "message": f"Character does not hold application '{body.tag}'.",
                        },
                    )
                current = apps[body.tag]
                if current >= 5:
                    raise HTTPException(
                        status_code=422,
                        detail={"error": "at_max_tier", "current_tier": current},
                    )
                new_tier = current + 1
                parent_tier = kgroup.get("tier", 0)
                if new_tier > parent_tier:
                    kgroup["tier"] = new_tier
                    parent_bumped = True
                    parent_tag = parent
                apps[body.tag] = new_tier
                updated_character["knowledge"][parent] = kgroup

            elif kind == "knowledge_group":
                kgroup = updated_character.setdefault("knowledge", {}).get(body.tag)
                if not isinstance(kgroup, dict) or "tier" not in kgroup:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "error": "tag_not_held",
                            "message": f"Character does not hold knowledge group '{body.tag}'.",
                        },
                    )
                current = kgroup["tier"]
                if current >= 5:
                    raise HTTPException(
                        status_code=422,
                        detail={"error": "at_max_tier", "current_tier": current},
                    )
                new_tier = current + 1
                kgroup["tier"] = new_tier
                updated_character["knowledge"][body.tag] = kgroup

            elif kind == "spell":
                parent = data.get("field", "")
                fblock = updated_character.setdefault("magic", {}).get(parent)
                if not isinstance(fblock, dict) or "spells" not in fblock:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "error": "parent_field_not_held",
                            "message": (
                                f"Character does not hold parent field '{parent}' "
                                f"for spell '{body.tag}'."
                            ),
                        },
                    )
                spells = fblock["spells"]
                if body.tag not in spells:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "error": "tag_not_held",
                            "message": f"Character does not hold spell '{body.tag}'.",
                        },
                    )
                current = spells[body.tag]
                if current >= 5:
                    raise HTTPException(
                        status_code=422,
                        detail={"error": "at_max_tier", "current_tier": current},
                    )
                new_tier = current + 1
                field_tier = fblock.get("tier", 0)
                if new_tier > field_tier:
                    fblock["tier"] = new_tier
                    parent_bumped = True
                    parent_tag = parent
                spells[body.tag] = new_tier
                updated_character["magic"][parent] = fblock

            elif kind == "magic_field":
                fblock = updated_character.setdefault("magic", {}).get(body.tag)
                if not isinstance(fblock, dict) or "tier" not in fblock:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "error": "tag_not_held",
                            "message": f"Character does not hold magic field '{body.tag}'.",
                        },
                    )
                current = fblock["tier"]
                if current >= 5:
                    raise HTTPException(
                        status_code=422,
                        detail={"error": "at_max_tier", "current_tier": current},
                    )
                new_tier = current + 1
                fblock["tier"] = new_tier
                updated_character["magic"][body.tag] = fblock

            new_advancement = _apply_tag_advancement_counters(character, updated_character)
            updated_character["advancement"] = new_advancement

            log_text = f"Advancement: {body.tag} -> tier {new_tier}"
            if parent_bumped:
                log_text += f" (parent {parent_tag} bumped to {new_tier})"
            if body.rationale:
                log_text += f". Rationale: {body.rationale}"

            typed_entry = TypedLogEntry(type="progression", text=log_text)
            new_log = log_arr + [typed_entry.model_dump(exclude_none=True)]
            log_entry_index = len(new_log) - 1

            await conn.execute(
                "UPDATE game_states "
                "SET character = $1::jsonb, log = $2::jsonb, updated_at = NOW() "
                "WHERE session_id = $3",
                json.dumps(updated_character),
                json.dumps(new_log),
                body.session_id,
            )

            # Brief 19: stamp the scene record with the committed tag inside
            # the same transaction so the one-tag-per-scene guarantee is
            # atomic with the character mutation.
            if body.scene_id:
                await conn.execute(
                    "UPDATE scene_records SET tag_advance_committed = $1 "
                    "WHERE scene_id = $2",
                    body.tag,
                    body.scene_id,
                )

    return ProgressionCommitResponse(
        session_id=body.session_id,
        tag=body.tag,
        kind=kind,
        new_tier=new_tier,
        advancement_after=new_advancement,
        parent_bumped=parent_bumped,
        parent_tag=parent_tag,
        log_entry_index=log_entry_index,
    )
