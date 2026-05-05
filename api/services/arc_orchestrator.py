"""Arc lifecycle orchestrator (Brief 3).

Composes the arc state machine, settlement application, and child-arc
spawning into a single declarative endpoint. The narrator submits intent
and structured data; the backend executes the state machine atomically
within one Postgres transaction.

Replaces the routine paths through /transition + /settle + /spawn for
arc lifecycle. Edge cases (replaced_by_successor, merged_into_parent
without an active spawn intent) still go through /transition directly.

The atomicity guarantee: every write a single declare call performs
(arc state, transition_log, character, world, log entries, child arc)
either lands together or rolls back together. The narrator never sees
partial state.

Per Brief 3 §Q1, the atomicity refactor here is scoped to the helpers
declare touches. The legacy /settle and /transition endpoints retain
their existing non-atomic write sequences as a known latent issue
(todo.md PENDING DESIGN).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import asyncpg
from fastapi import HTTPException, status

from api.arc_conditions import ConditionEvaluationError, evaluate_condition_set, is_empty
from api.arc_state_machine import is_terminal, is_transition_allowed
from api.game_data import get_arc_type_default_envelope
from api.models import (
    Arc,
    ArcAPAward,
    ArcBudget,
    ArcEconomyEnvelope,
    ArcFlags,
    ArcItemAccessEnvelope,
    ArcLeverageEnvelope,
    ArcReputationEnvelope,
    ArcRewardEnvelope,
    ArcSettlementResult,
    ArcTimestamps,
    ArcTransitionLogEntry,
    CharacterModel,
    TypedLogEntry,
    WorldModel,
)
from api.repositories.arc_repository import ArcRepository
from api.repositories.state_repository import TransactionalStateRepository
from api.schemas.arc_schemas import (
    ArcDeclareRequest,
    ArcDeclareResponse,
    ArcSettlementEnumeration,
    ArcSuggestion,
    ItemAward,
    ObligationChange,
    ReputationDelta,
)
from api.services.arc_settlement import apply_arc_settlement

HTTP_422 = 422


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------


async def compose_intent(
    *,
    pool: asyncpg.Pool,
    arc_repo: ArcRepository,
    session_id: str,
    arc_id: str,
    request: ArcDeclareRequest,
) -> ArcDeclareResponse:
    """Resolve a declare intent atomically.

    The orchestrator owns the connection + transaction boundary; per-intent
    helpers operate on the conn passed in. If any write fails, the entire
    declare call rolls back.
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            arc = await _fetch_arc_in_transaction(conn, session_id, arc_id)
            txn_state_repo = TransactionalStateRepository(conn)

            intent = request.intent
            if intent == "activate":
                return await _resolve_activate(conn, arc_repo, arc, request)
            if intent == "close":
                return await _resolve_close_or_fail(
                    conn, arc_repo, txn_state_repo, arc, request, outcome="complete"
                )
            if intent == "fail":
                return await _resolve_close_or_fail(
                    conn, arc_repo, txn_state_repo, arc, request, outcome="failed"
                )
            if intent == "abandon":
                return await _resolve_abandon(conn, arc_repo, arc, request)
            if intent == "spawn_child":
                return await _resolve_spawn_child(
                    conn, arc_repo, arc, session_id, request
                )
            if intent == "scope_check":
                return await _resolve_scope_check(arc, request)

            raise HTTPException(
                status_code=HTTP_422,
                detail={"error": "unknown_intent", "intent": intent},
            )


# ---------------------------------------------------------------------------
# Per-intent resolvers
# ---------------------------------------------------------------------------


async def _resolve_activate(
    conn: asyncpg.Connection,
    arc_repo: ArcRepository,
    arc: Arc,
    request: ArcDeclareRequest,
) -> ArcDeclareResponse:
    """proposed → available → in_progress, atomic."""
    if arc.state != "proposed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "activate_requires_proposed",
                "message": f"intent='activate' requires arc state 'proposed'; current state is '{arc.state}'.",
                "current_state": arc.state,
            },
        )

    now = datetime.now(timezone.utc)
    new_timestamps = arc.timestamps.model_copy()
    new_timestamps.accepted_at = now
    new_timestamps.last_progressed_at = now

    await arc_repo.update_arc_in_transaction(
        conn,
        arc_id=arc.id,
        new_state="in_progress",
        consumption=arc.consumption,
        timestamps=new_timestamps,
        full_arc=arc,
    )

    actions: list[str] = []
    for from_s, to_s in [("proposed", "available"), ("available", "in_progress")]:
        await arc_repo.append_transition_log_in_transaction(
            conn,
            ArcTransitionLogEntry(
                arc_id=arc.id,
                session_id=arc.session_id,
                from_state=from_s,
                to_state=to_s,
                reason=request.reason,
                transitioned_at=now,
                resolved_scenes_at_transition=arc.consumption.resolved_scenes_used,
                locations_visited_at_transition=list(arc.consumption.locations_visited),
                triggering_event=request.triggering_event or "declare:activate",
            ),
        )
        actions.append(f"transition:{from_s}->{to_s}")

    return ArcDeclareResponse(arc=arc, actions_taken=actions)


async def _resolve_close_or_fail(
    conn: asyncpg.Connection,
    arc_repo: ArcRepository,
    state_repo: TransactionalStateRepository,
    arc: Arc,
    request: ArcDeclareRequest,
    *,
    outcome: str,  # "complete" | "failed"
) -> ArcDeclareResponse:
    """Compose: (→ ready_to_close) → terminal, with settlement applied."""
    if request.settlement is None:
        raise HTTPException(
            status_code=HTTP_422,
            detail={
                "error": "settlement_required",
                "message": f"intent='{request.intent}' requires a settlement enumeration body.",
            },
        )

    valid_pre_states = ("in_progress", "at_scope_cap", "ready_to_close")
    if arc.state not in valid_pre_states:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "arc_not_in_closable_state",
                "message": f"intent='{request.intent}' requires arc state in {valid_pre_states}; current is '{arc.state}'.",
                "current_state": arc.state,
            },
        )

    # Settlement validation — same envelope/AP rules as legacy /settle.
    settlement = request.settlement
    _validate_settlement(arc, settlement, outcome=outcome)

    # Block parent close when AP-owning children are still active. Same as legacy /settle.
    if outcome == "complete":
        await _check_no_blocking_ap_children(arc_repo, arc)

    # Closure-condition gate. Mirrors the existing /transition→ready_to_close gate.
    if outcome == "complete" and arc.state != "ready_to_close":
        if is_empty(arc.closure_conditions):
            raise HTTPException(
                status_code=HTTP_422,
                detail={
                    "error": "no_closure_conditions",
                    "message": (
                        "Cannot transition to 'ready_to_close' without authored closure conditions. "
                        "Define closure_conditions at arc creation, use intent='abandon' to drop the arc, "
                        "or use force_close for stuck arcs."
                    ),
                },
            )
        try:
            closure_met = evaluate_condition_set(
                arc.closure_conditions,
                arc,
                world_flags=request.world_flags or {},
            )
        except ConditionEvaluationError as exc:
            raise HTTPException(
                status_code=HTTP_422,
                detail={"error": "condition_evaluation_error", "message": str(exc)},
            )
        if not closure_met:
            raise HTTPException(
                status_code=HTTP_422,
                detail={
                    "error": "closure_conditions_unmet",
                    "message": (
                        "Closure conditions not satisfied. Set the relevant world_flags in the "
                        "request, complete the conditions in fiction, or use intent='abandon'/force_close."
                    ),
                },
            )

    now = datetime.now(timezone.utc)
    actions: list[str] = []
    from_state = arc.state

    if arc.state != "ready_to_close":
        await arc_repo.append_transition_log_in_transaction(
            conn,
            ArcTransitionLogEntry(
                arc_id=arc.id,
                session_id=arc.session_id,
                from_state=arc.state,
                to_state="ready_to_close",
                reason=request.reason,
                transitioned_at=now,
                resolved_scenes_at_transition=arc.consumption.resolved_scenes_used,
                locations_visited_at_transition=list(arc.consumption.locations_visited),
                triggering_event=request.triggering_event or f"declare:{request.intent}",
            ),
        )
        actions.append(f"transition:{arc.state}->ready_to_close")

    # Build settlement record on the arc.
    arc.settlement = ArcSettlementResult(
        arc_id=arc.id,
        outcome=outcome,  # type: ignore[arg-type]
        awarded_ap=settlement.awarded_ap,
        reputation_changes=[r.model_dump() for r in settlement.reputation_changes],
        coin_cd_awarded=settlement.coin_awarded,
        coin_cd_forfeit=settlement.coin_forfeited,
        obligations_added=[o.model_dump() for o in settlement.obligations],
        items_awarded=[i.id for i in settlement.items_awarded],
        leverage_gained=list(settlement.leverage_gained),
        settled_at=now,
        notes=settlement.notes,
    )

    new_timestamps = arc.timestamps.model_copy()
    new_timestamps.last_progressed_at = now
    new_timestamps.closed_at = now

    # Apply settlement to character/world.
    character = await _fetch_character_in_transaction(state_repo, arc.session_id)
    world = await _fetch_world_in_transaction(state_repo, arc.session_id)
    updated_character, updated_world, consequence_events = await apply_arc_settlement(
        arc=arc, character=character, world=world,
    )
    arc.consequence_events_emitted = consequence_events

    await state_repo.update_character(arc.session_id, updated_character)
    await state_repo.update_world(arc.session_id, updated_world)

    await arc_repo.update_arc_in_transaction(
        conn,
        arc_id=arc.id,
        new_state=outcome,  # type: ignore[arg-type]
        consumption=arc.consumption,
        timestamps=new_timestamps,
        full_arc=arc,
    )
    actions.append(f"transition:ready_to_close->{outcome}")
    actions.append("settlement:applied")

    closure_payload: dict[str, Any] = {
        "arc_id": arc.id,
        "arc_title": arc.title,
        "outcome": outcome,
        "settled_at": now.isoformat(),
        "awarded_ap": settlement.awarded_ap,
        "reputation_changes": [r.model_dump() for r in settlement.reputation_changes],
        "coin_awarded": settlement.coin_awarded,
        "coin_forfeited": settlement.coin_forfeited,
        "items_awarded": [i.model_dump() for i in settlement.items_awarded],
        "leverage_gained": list(settlement.leverage_gained),
        "obligations": [o.model_dump() for o in settlement.obligations],
        "world_state_consequences": list(settlement.world_state_consequences),
        "consequence_events": list(consequence_events),
        "resolved_scenes_used": arc.consumption.resolved_scenes_used,
        "locations_visited": list(arc.consumption.locations_visited),
        "via": "declare",
    }
    closure_text = f"Arc '{arc.title}' settled as {outcome} via declare"
    await state_repo.append_log_entry(
        arc.session_id,
        TypedLogEntry(type="closure_summary", text=closure_text, payload=closure_payload),
    )

    await arc_repo.append_transition_log_in_transaction(
        conn,
        ArcTransitionLogEntry(
            arc_id=arc.id,
            session_id=arc.session_id,
            from_state=("ready_to_close" if from_state != "ready_to_close" else from_state),
            to_state=outcome,  # type: ignore[arg-type]
            reason=f"declare:{request.intent}: {request.reason}",
            transitioned_at=now,
            resolved_scenes_at_transition=arc.consumption.resolved_scenes_used,
            locations_visited_at_transition=list(arc.consumption.locations_visited),
            triggering_event=request.triggering_event or f"declare:{request.intent}",
        ),
    )

    return ArcDeclareResponse(arc=arc, actions_taken=actions)


async def _resolve_abandon(
    conn: asyncpg.Connection,
    arc_repo: ArcRepository,
    arc: Arc,
    request: ArcDeclareRequest,
) -> ArcDeclareResponse:
    valid_pre_states = ("proposed", "available", "in_progress", "at_scope_cap")
    if arc.state not in valid_pre_states:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "arc_not_abandonable",
                "message": f"intent='abandon' requires non-terminal arc; current state is '{arc.state}'.",
                "current_state": arc.state,
            },
        )

    if not is_transition_allowed(arc.state, "abandoned"):
        raise HTTPException(
            status_code=HTTP_422,
            detail={
                "error": "illegal_transition",
                "message": f"Transition '{arc.state}' → 'abandoned' is not permitted by the state machine.",
            },
        )

    now = datetime.now(timezone.utc)
    new_timestamps = arc.timestamps.model_copy()
    new_timestamps.last_progressed_at = now
    new_timestamps.closed_at = now

    from_state = arc.state
    await arc_repo.update_arc_in_transaction(
        conn,
        arc_id=arc.id,
        new_state="abandoned",
        consumption=arc.consumption,
        timestamps=new_timestamps,
        full_arc=arc,
    )
    await arc_repo.append_transition_log_in_transaction(
        conn,
        ArcTransitionLogEntry(
            arc_id=arc.id,
            session_id=arc.session_id,
            from_state=from_state,
            to_state="abandoned",
            reason=request.reason,
            transitioned_at=now,
            resolved_scenes_at_transition=arc.consumption.resolved_scenes_used,
            locations_visited_at_transition=list(arc.consumption.locations_visited),
            triggering_event=request.triggering_event or "declare:abandon",
        ),
    )

    return ArcDeclareResponse(arc=arc, actions_taken=[f"transition:{from_state}->abandoned"])


async def _resolve_spawn_child(
    conn: asyncpg.Connection,
    arc_repo: ArcRepository,
    parent: Arc,
    session_id: str,
    request: ArcDeclareRequest,
) -> ArcDeclareResponse:
    if request.child_arc is None:
        raise HTTPException(
            status_code=HTTP_422,
            detail={"error": "child_arc_required", "message": "intent='spawn_child' requires child_arc body."},
        )
    if parent.state not in ("available", "in_progress", "at_scope_cap"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "parent_not_spawnable",
                "message": f"Parent must be in available/in_progress/at_scope_cap; current is '{parent.state}'.",
            },
        )

    parent_action = request.parent_action_after_spawn or "continue"
    if parent_action == "transition_to" and not request.parent_target_state:
        raise HTTPException(
            status_code=HTTP_422,
            detail={
                "error": "parent_target_state_required",
                "message": "parent_action_after_spawn='transition_to' requires parent_target_state.",
            },
        )

    spawn_req = request.child_arc

    # Mirror the existing /spawn validation surface.
    if spawn_req.child_formal_contract_qualified:
        missing = []
        if not (spawn_req.child_patron_npc_id or spawn_req.child_patron_faction):
            missing.append("patron_npc_id or patron_faction")
        if not spawn_req.child_explicit_objective or not spawn_req.child_explicit_objective.strip():
            missing.append("explicit_objective")
        if not spawn_req.child_expected_return or not spawn_req.child_expected_return.strip():
            missing.append("expected_return")
        if missing:
            raise HTTPException(
                status_code=HTTP_422,
                detail={
                    "error": "insufficient_provenance",
                    "message": "child_formal_contract_qualified=true requires patron, objective, and expected return.",
                    "missing_fields": missing,
                },
            )
    if not parent.flags.formal_contract_qualified and spawn_req.ap_ownership == "parent":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "emergent_parent_no_ap_to_partition",
                "message": "Parent is emergent; set ap_ownership='child' or 'none'.",
            },
        )
    if not spawn_req.child_formal_contract_qualified and spawn_req.ap_ownership == "child":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "emergent_child_cannot_own_ap",
                "message": "Emergent child arcs cannot own AP.",
            },
        )

    envelope_defaults = get_arc_type_default_envelope(spawn_req.child_primary_type)
    budget = ArcBudget(
        resolved_scene_soft_cap=envelope_defaults["scene_soft_cap"],
        resolved_scene_hard_cap=envelope_defaults["scene_hard_cap"],
        location_soft_cap=envelope_defaults["location_soft_cap"],
        location_hard_cap=envelope_defaults["location_hard_cap"],
    )
    if spawn_req.child_formal_contract_qualified and spawn_req.ap_ownership == "child":
        ap_award = ArcAPAward(
            min=envelope_defaults["ap_award_min"],
            max=envelope_defaults["ap_award_max"],
            fixed=envelope_defaults["ap_award_fixed"],
        )
    else:
        ap_award = ArcAPAward(min=0, max=0, fixed=False)

    now = datetime.now(timezone.utc)
    child = Arc(
        id=f"arc-{uuid.uuid4().hex[:16]}",
        session_id=session_id,
        title=spawn_req.child_title,
        summary=spawn_req.child_summary,
        primary_type=spawn_req.child_primary_type,
        subtype=spawn_req.child_subtype,
        stake_scale=spawn_req.child_stake_scale,
        origin_type=spawn_req.child_origin_type,
        parent_arc_id=parent.id,
        state="proposed",
        patron_faction=spawn_req.child_patron_faction,
        patron_npc_id=spawn_req.child_patron_npc_id,
        target_locations=spawn_req.child_target_locations,
        closure_conditions=spawn_req.child_closure_conditions,
        failure_conditions=spawn_req.child_failure_conditions,
        budget=budget,
        rewards=ArcRewardEnvelope(
            ap_award=ap_award,
            reputation=ArcReputationEnvelope(),
            economy=ArcEconomyEnvelope(),
            items_access=ArcItemAccessEnvelope(),
            leverage=ArcLeverageEnvelope(),
        ),
        flags=ArcFlags(
            formal_contract_qualified=spawn_req.child_formal_contract_qualified,
            ap_ownership=spawn_req.ap_ownership,
        ),
        timestamps=ArcTimestamps(created_at=now),
    )

    await arc_repo.create_in_transaction(conn, child)

    if child.id not in parent.spawned_arc_ids:
        parent.spawned_arc_ids.append(child.id)

    actions: list[str] = [f"spawn:{child.id}"]
    parent_new_state = parent.state

    if parent_action == "merge_into_child":
        parent_new_state = "replaced_by_successor"
    elif parent_action == "transition_to":
        target = request.parent_target_state
        if not is_transition_allowed(parent.state, target):  # type: ignore[arg-type]
            raise HTTPException(
                status_code=HTTP_422,
                detail={
                    "error": "illegal_parent_transition",
                    "message": f"Transition '{parent.state}' → '{target}' is not permitted.",
                },
            )
        parent_new_state = target  # type: ignore[assignment]

    parent_timestamps = parent.timestamps.model_copy()
    parent_timestamps.last_progressed_at = now
    if is_terminal(parent_new_state):
        parent_timestamps.closed_at = now

    await arc_repo.update_arc_in_transaction(
        conn,
        arc_id=parent.id,
        new_state=parent_new_state,  # type: ignore[arg-type]
        consumption=parent.consumption,
        timestamps=parent_timestamps,
        full_arc=parent,
    )

    if parent_new_state != parent.state and parent_action != "continue":
        actions.append(f"transition:{parent.state}->{parent_new_state}")

    await arc_repo.append_transition_log_in_transaction(
        conn,
        ArcTransitionLogEntry(
            arc_id=parent.id,
            session_id=session_id,
            from_state=parent.state,
            to_state=parent_new_state,  # type: ignore[arg-type]
            reason=f"Spawned child arc {child.id}: {request.reason}",
            transitioned_at=now,
            resolved_scenes_at_transition=parent.consumption.resolved_scenes_used,
            locations_visited_at_transition=list(parent.consumption.locations_visited),
            triggering_event=request.triggering_event or "declare:spawn_child",
        ),
    )

    return ArcDeclareResponse(arc=parent, child_arc=child, actions_taken=actions)


async def _resolve_scope_check(
    arc: Arc,
    request: ArcDeclareRequest,
) -> ArcDeclareResponse:
    """Read-only. Compute envelope status + minimal recommendations."""
    if is_terminal(arc.state):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "arc_terminal",
                "message": f"intent='scope_check' requires non-terminal arc; current state is '{arc.state}'.",
            },
        )

    scene_soft = arc.budget.resolved_scene_soft_cap
    scene_hard = arc.budget.resolved_scene_hard_cap
    scenes_used = arc.consumption.resolved_scenes_used
    soft_approaching = scenes_used >= scene_soft if scene_soft > 0 else False
    hard_reached = scenes_used >= scene_hard if scene_hard > 0 else False
    phase_shift_candidate = (
        arc.origin_type == "emergent" and soft_approaching and not hard_reached
    )

    envelope_status: dict[str, Any] = {
        "arc_id": arc.id,
        "state": arc.state,
        "resolved_scenes_used": scenes_used,
        "resolved_scene_soft_cap": scene_soft,
        "resolved_scene_hard_cap": scene_hard,
        "soft_cap_approaching": soft_approaching,
        "hard_cap_reached": hard_reached,
        "phase_shift_candidate": phase_shift_candidate,
    }

    suggestions: list[ArcSuggestion] = []
    if phase_shift_candidate:
        suggested_payload = {
            "child_primary_type": arc.primary_type,
            "child_stake_scale": arc.stake_scale,
            "child_patron_faction": arc.patron_faction,
            "child_patron_npc_id": arc.patron_npc_id,
        }
        suggestions.append(ArcSuggestion(
            suggested_intent="spawn_child",
            reason=(
                "Emergent arc has crossed soft cap. If institutional phase has begun "
                "(named patron, council/court engagement, formal organization adoption, "
                "documented mandate), spawn a formal child arc to own the institutional "
                "phase. See arc-rules.md Phase Change Indicators."
            ),
            suggested_payload=suggested_payload,
        ))
    elif hard_reached:
        suggestions.append(ArcSuggestion(
            suggested_intent="close",
            reason="Hard cap reached. Decide closure outcome (complete or fail) and submit settlement.",
        ))
    elif soft_approaching:
        suggestions.append(ArcSuggestion(
            suggested_intent="close",
            reason="Soft cap approaching. Plan closure within next 1-2 scenes.",
        ))

    return ArcDeclareResponse(
        arc=arc,
        actions_taken=[],
        envelope_status=envelope_status,
        suggestions=suggestions,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _fetch_arc_in_transaction(
    conn: asyncpg.Connection,
    session_id: str,
    arc_id: str,
) -> Arc:
    row = await conn.fetchrow(
        "SELECT data FROM arcs WHERE session_id = $1 AND id = $2",
        session_id,
        arc_id,
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arc {arc_id} not found in session {session_id}",
        )
    return Arc.model_validate(row["data"])


async def _fetch_character_in_transaction(
    state_repo: TransactionalStateRepository,
    session_id: str,
) -> CharacterModel:
    raw = await state_repo.get_character(session_id)
    if raw is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session state not found for {session_id}",
        )
    # _normalize_character_state lives in state.py; reproduce minimal needs inline.
    from api.routes.state import _normalize_character_state  # local to avoid circular import
    return CharacterModel.model_validate(_normalize_character_state(raw))


async def _fetch_world_in_transaction(
    state_repo: TransactionalStateRepository,
    session_id: str,
) -> WorldModel:
    state = await state_repo.get_state_full(session_id)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session state not found for {session_id}",
        )
    return WorldModel.model_validate(state.world)


def _validate_settlement(
    arc: Arc,
    settlement: ArcSettlementEnumeration,
    *,
    outcome: str,
) -> None:
    """Mirror legacy /settle envelope validation. Raises 422 on any failure."""
    if outcome == "failed" and settlement.awarded_ap > 0:
        raise HTTPException(
            status_code=HTTP_422,
            detail={
                "error": "ap_on_failure_not_allowed",
                "message": "Failed arcs cannot award AP per the v1 locked policy.",
            },
        )
    if settlement.awarded_ap > 0:
        if not arc.flags.formal_contract_qualified:
            raise HTTPException(
                status_code=HTTP_422,
                detail={"error": "emergent_arc_no_ap", "message": "Emergent arcs cannot award AP."},
            )
        if arc.flags.ap_ownership == "none":
            raise HTTPException(
                status_code=HTTP_422,
                detail={"error": "no_ap_ownership", "message": "ap_ownership='none'."},
            )
        if arc.parent_arc_id and arc.flags.ap_ownership == "parent":
            raise HTTPException(
                status_code=HTTP_422,
                detail={
                    "error": "ap_owned_by_parent",
                    "message": "AP owned by parent arc; settle the parent.",
                },
            )
        if settlement.awarded_ap < arc.rewards.ap_award.min or settlement.awarded_ap > arc.rewards.ap_award.max:
            raise HTTPException(
                status_code=HTTP_422,
                detail={
                    "error": "ap_outside_envelope",
                    "envelope_min": arc.rewards.ap_award.min,
                    "envelope_max": arc.rewards.ap_award.max,
                    "submitted": settlement.awarded_ap,
                },
            )

    for r in settlement.reputation_changes:
        if r.delta > 0 and r.delta > arc.rewards.reputation.max_positive_delta:
            raise HTTPException(
                status_code=HTTP_422,
                detail={
                    "error": "reputation_positive_outside_envelope",
                    "faction": r.faction,
                    "delta": r.delta,
                    "envelope_max_positive": arc.rewards.reputation.max_positive_delta,
                },
            )
        if r.delta < 0 and abs(r.delta) > arc.rewards.reputation.max_negative_delta:
            raise HTTPException(
                status_code=HTTP_422,
                detail={
                    "error": "reputation_negative_outside_envelope",
                    "faction": r.faction,
                    "delta": r.delta,
                    "envelope_max_negative": arc.rewards.reputation.max_negative_delta,
                },
            )

    if (
        settlement.coin_awarded > 0
        and arc.rewards.economy.coin_cd_max is not None
        and settlement.coin_awarded > arc.rewards.economy.coin_cd_max
    ):
        raise HTTPException(
            status_code=HTTP_422,
            detail={
                "error": "coin_outside_envelope",
                "awarded": settlement.coin_awarded,
                "envelope_max": arc.rewards.economy.coin_cd_max,
            },
        )


async def _check_no_blocking_ap_children(
    arc_repo: ArcRepository,
    arc: Arc,
) -> None:
    """Block parent close while any AP-owning child arc is non-terminal."""
    children = await arc_repo.list_children(arc.session_id, arc.id)
    for child in children:
        if child.flags.ap_ownership == "child" and child.state not in (
            "complete", "failed", "abandoned", "replaced_by_successor", "merged_into_parent",
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "child_ap_unsettled",
                    "blocking_child_id": child.id,
                    "blocking_child_state": child.state,
                },
            )
