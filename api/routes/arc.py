"""routes/arc.py — create and read Arc System v1 records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from api.arc_conditions import ConditionEvaluationError, evaluate_condition_set, is_empty
from api.arc_state_machine import get_allowed_transitions, is_active, is_terminal, is_transition_allowed
from api.database import get_pool
from api.game_data import get_arc_type_default_envelope
from api.models import (
    Arc,
    ArcAPAward,
    ArcBeatLogEntry,
    ArcBudget,
    ArcConditionSet,
    ArcEconomyEnvelope,
    ArcEscalationRules,
    ArcFlags,
    ArcItemAccessEnvelope,
    ArcLeverageEnvelope,
    ArcReputationEnvelope,
    ArcRewardEnvelope,
    ArcSettlementResult,
    ArcTimestamps,
    ArcTransitionLogEntry,
    TypedLogEntry,
)
from api.repositories.arc_repository import ArcRepository
from api.repositories.state_repository import StateRepository
from api.schemas.arc_schemas import (
    ArcCreateRequest,
    ArcDeclareRequest,
    ArcDeclareResponse,
    ArcForceCloseRequest,
    ArcProgressRequest,
    ArcProgressResponse,
    ArcSettleRequest,
    ArcSettleResponse,
    ArcSpawnRequest,
    ArcTransitionRequest,
)
from api.services.arc_orchestrator import compose_intent
from api.services.arc_settlement import apply_arc_settlement

router = APIRouter(prefix="/arc", tags=["arc"])
HTTP_422_UNPROCESSABLE_CONTENT = 422


SUBTYPE_DEFAULT_CLOSURE_CONDITIONS: dict[str, dict[str, Any]] = {
    "investigation": {
        "any_of": [
            {"type": "report_delivered", "payload": {"flag_id": "report_delivered"}},
            {"type": "evidence_chain_complete", "payload": {"flag_id": "evidence_chain_complete"}},
            {"type": "decision_made", "payload": {"flag_id": "decision_made"}},
        ]
    },
    "recovery": {
        "any_of": [
            {"type": "target_item_recovered", "payload": {"flag_id": "target_recovered"}},
            {"type": "target_destroyed", "payload": {"flag_id": "target_destroyed"}},
            {"type": "decision_made", "payload": {"flag_id": "recovery_resolved"}},
        ]
    },
    "containment": {
        "any_of": [
            {"type": "threat_state_changed", "payload": {"flag_id": "threat_contained"}},
            {"type": "report_delivered", "payload": {"flag_id": "containment_report"}},
            {"type": "world_flag_present", "payload": {"flag": "containment_resolved"}},
        ]
    },
    "delivery": {"any_of": [{"type": "target_delivered", "payload": {"flag_id": "target_delivered"}}]},
    "escort": {"any_of": [{"type": "target_survived", "payload": {"flag_id": "escort_complete"}}]},
    "diplomatic": {
        "any_of": [
            {"type": "decision_made", "payload": {"flag_id": "diplomatic_resolution"}},
            {"type": "faction_state_changed", "payload": {"flag_id": "faction_state_changed"}},
        ]
    },
    "surveillance": {
        "any_of": [
            {"type": "report_delivered", "payload": {"flag_id": "surveillance_report"}},
            {"type": "evidence_chain_complete", "payload": {"flag_id": "surveillance_complete"}},
        ]
    },
    "seizure": {"any_of": [{"type": "target_secured", "payload": {"flag_id": "target_seized"}}]},
    "_default": {
        "any_of": [
            {"type": "decision_made", "payload": {"flag_id": "arc_resolution"}},
            {"type": "world_flag_present", "payload": {"flag": "arc_resolved"}},
        ]
    },
}


from api.routes._helpers import plain_validation_errors as _plain_validation_errors


def get_arc_repository(pool: asyncpg.Pool = Depends(get_pool)) -> ArcRepository:
    """FastAPI dependency returning an ArcRepository for the app pool."""
    return ArcRepository(pool)


def validate_provenance(req: ArcCreateRequest) -> None:
    """
    Strict provenance check for formal-contract-qualified arcs.

    Per Arc System v1 locked decision (todo.md), formal_contract_qualified=true
    requires an explicit patron, objective, and expected return/deliverable.
    Trust networks, introductions, social proximity, family connection, and
    problem discovery without explicit tasking do not confer formal status.
    """
    if not req.formal_contract_qualified:
        return

    missing: list[str] = []
    if not (req.patron_npc_id or req.patron_faction):
        missing.append("patron_npc_id or patron_faction")
    if not req.explicit_objective or not req.explicit_objective.strip():
        missing.append("explicit_objective")
    if not req.expected_return or not req.expected_return.strip():
        missing.append("expected_return")

    if missing:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "insufficient_provenance",
                "message": (
                    "formal_contract_qualified=true requires explicit patron, "
                    "objective, and expected return. Trust networks and "
                    "introductions do not confer formal status."
                ),
                "missing_fields": missing,
            },
        )


def ensure_closure_conditions(req: ArcCreateRequest) -> ArcConditionSet:
    """Return authored closure conditions, or subtype defaults when empty."""
    if not is_empty(req.closure_conditions):
        return req.closure_conditions

    default_template = SUBTYPE_DEFAULT_CLOSURE_CONDITIONS.get(
        req.subtype,
        SUBTYPE_DEFAULT_CLOSURE_CONDITIONS["_default"],
    )
    return ArcConditionSet.model_validate(default_template)


def build_arc_from_request(
    session_id: str,
    req: ArcCreateRequest,
    closure_conditions: ArcConditionSet | None = None,
) -> Arc:
    """Construct an Arc from a create request, applying registry defaults."""
    envelope_defaults = get_arc_type_default_envelope(req.primary_type)

    budget = ArcBudget(
        resolved_scene_soft_cap=envelope_defaults["scene_soft_cap"],
        resolved_scene_hard_cap=envelope_defaults["scene_hard_cap"],
        location_soft_cap=envelope_defaults["location_soft_cap"],
        location_hard_cap=envelope_defaults["location_hard_cap"],
    )
    ap_award = ArcAPAward(
        min=envelope_defaults["ap_award_min"] if req.formal_contract_qualified else 0,
        max=envelope_defaults["ap_award_max"] if req.formal_contract_qualified else 0,
        fixed=envelope_defaults["ap_award_fixed"],
    )
    reputation_envelope = ArcReputationEnvelope(
        max_positive_delta=envelope_defaults["reputation_max_positive_delta"],
        max_negative_delta=envelope_defaults["reputation_max_negative_delta"],
        affected_factions=[],
    )
    economy_envelope = ArcEconomyEnvelope(
        coin_cd_max=envelope_defaults["economy_coin_cd_max"],
        barter_allowed=True,
        obligation_allowed=True,
    )
    items_envelope = ArcItemAccessEnvelope(
        magical_item_tier_max=envelope_defaults["items_magical_tier_max"],
        mundane_item_tier_max=envelope_defaults["items_mundane_tier_max"],
    )
    leverage_envelope = ArcLeverageEnvelope(
        obligation_slots_max=envelope_defaults["leverage_obligation_slots_max"],
        secret_or_evidence_grade_max=envelope_defaults["leverage_evidence_grade_max"],
    )
    rewards = ArcRewardEnvelope(
        ap_award=ap_award,
        reputation=reputation_envelope,
        economy=economy_envelope,
        items_access=items_envelope,
        leverage=leverage_envelope,
    )
    flags = ArcFlags(
        formal_contract_qualified=req.formal_contract_qualified,
        ap_ownership="parent" if req.formal_contract_qualified else "none",
    )
    now = datetime.now(timezone.utc)

    return Arc(
        id=f"arc-{uuid.uuid4().hex[:16]}",
        session_id=session_id,
        title=req.title,
        summary=req.summary,
        primary_type=req.primary_type,
        subtype=req.subtype,
        stake_scale=req.stake_scale,
        origin_type=req.origin_type,
        parent_arc_id=req.parent_arc_id,
        state="proposed",
        patron_faction=req.patron_faction,
        patron_npc_id=req.patron_npc_id,
        target_locations=req.target_locations,
        closure_conditions=closure_conditions or req.closure_conditions,
        failure_conditions=req.failure_conditions,
        escalation_rules=req.escalation_rules or ArcEscalationRules(),
        budget=budget,
        rewards=rewards,
        flags=flags,
        timestamps=ArcTimestamps(created_at=now),
        notes=req.notes,
    )


def _raise_condition_error(exc: ConditionEvaluationError) -> None:
    raise HTTPException(
        status_code=HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"error": "condition_evaluation_error", "message": str(exc)},
    )


@router.post("/{session_id}/create", response_model=Arc)
async def create_arc(
    session_id: str,
    req: ArcCreateRequest,
    repo: ArcRepository = Depends(get_arc_repository),
) -> Arc:
    """Create a new arc with strict provenance validation."""
    validate_provenance(req)
    closure_conditions = ensure_closure_conditions(req)
    try:
        arc = build_arc_from_request(session_id, req, closure_conditions)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=_plain_validation_errors(exc))
    await repo.create(arc)
    return arc


@router.get("/{session_id}", response_model=list[Arc])
async def list_session_arcs(
    session_id: str,
    repo: ArcRepository = Depends(get_arc_repository),
) -> list[Arc]:
    """List all arcs for a session."""
    return await repo.list_by_session(session_id)


@router.get("/{session_id}/active", response_model=list[Arc])
async def list_active_arcs(
    session_id: str,
    repo: ArcRepository = Depends(get_arc_repository),
) -> list[Arc]:
    """List arcs in active states (in_progress, at_scope_cap)."""
    return await repo.list_active_by_session(session_id)


@router.get("/{session_id}/{arc_id}", response_model=Arc)
async def get_arc(
    session_id: str,
    arc_id: str,
    repo: ArcRepository = Depends(get_arc_repository),
) -> Arc:
    """Fetch a single arc by ID, scoped to session."""
    arc = await repo.get_by_id(session_id, arc_id)
    if arc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arc {arc_id} not found in session {session_id}",
        )
    return arc


@router.post("/{session_id}/{arc_id}/transition", response_model=Arc, deprecated=True)
async def transition_arc(
    session_id: str,
    arc_id: str,
    req: ArcTransitionRequest,
    repo: ArcRepository = Depends(get_arc_repository),
) -> Arc:
    """
    Request an arc state transition.

    Enforces the Arc System v1 transition matrix and rejects stale
    from_state values. Closure and authored failure conditions are evaluated
    before persistence for ready_to_close and failed transitions.
    """
    arc = await repo.get_by_id(session_id, arc_id)
    if arc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arc {arc_id} not found in session {session_id}",
        )

    if arc.state != req.from_state:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "stale_from_state",
                "message": (
                    f"Requested from_state '{req.from_state}' does not match "
                    f"actual current state '{arc.state}'."
                ),
                "actual_state": arc.state,
                "requested_from_state": req.from_state,
            },
        )

    if not is_transition_allowed(req.from_state, req.to_state):
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "illegal_transition",
                "message": (
                    f"Transition from '{req.from_state}' to '{req.to_state}' "
                    "is not permitted by the state machine."
                ),
                "from_state": req.from_state,
                "to_state": req.to_state,
                "allowed_transitions": sorted(get_allowed_transitions(req.from_state)),
            },
        )

    if req.to_state == "ready_to_close":
        if is_empty(arc.closure_conditions):
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "no_closure_conditions",
                    "message": (
                        "Cannot transition to 'ready_to_close' without authored closure conditions. "
                        "Define closure_conditions at arc creation or use 'abandoned' to drop the arc."
                    ),
                },
            )
        try:
            closure_met = evaluate_condition_set(
                arc.closure_conditions,
                arc,
                world_flags=req.world_flags or {},
            )
        except ConditionEvaluationError as exc:
            _raise_condition_error(exc)
        if not closure_met:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "closure_conditions_unmet",
                    "message": (
                        "Closure conditions not satisfied. Either complete the conditions, "
                        "set the relevant world_flags in the transition request, or transition "
                        "to 'failed' or 'abandoned' instead."
                    ),
                    "closure_conditions": arc.closure_conditions.model_dump(),
                },
            )

    if req.to_state == "failed":
        if not is_empty(arc.failure_conditions):
            try:
                failure_met = evaluate_condition_set(
                    arc.failure_conditions,
                    arc,
                    world_flags=req.world_flags or {},
                )
            except ConditionEvaluationError as exc:
                _raise_condition_error(exc)
            if not failure_met and not req.force:
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                    detail={
                        "error": "failure_conditions_unmet_no_force",
                        "message": (
                            "Authored failure conditions not satisfied. Pass 'force: true' "
                            "to override and record an unforeseen failure."
                        ),
                        "failure_conditions": arc.failure_conditions.model_dump(),
                    },
                )

    if req.to_state == "merged_into_parent" and not arc.parent_arc_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "no_parent_to_merge_into",
                "message": "Cannot transition to merged_into_parent on an arc without a parent.",
            },
        )

    now = datetime.now(timezone.utc)
    new_timestamps = arc.timestamps.model_copy()
    new_timestamps.last_progressed_at = now
    if is_terminal(req.to_state):
        new_timestamps.closed_at = now

    if req.beat is not None:
        arc.log.append(
            ArcBeatLogEntry(
                text=req.beat,
                timestamp=now,
                source="transition",
            )
        )
        arc.state = req.to_state
        arc.timestamps = new_timestamps
        await repo.update_arc(
            arc_id=arc_id,
            new_state=req.to_state,
            consumption=arc.consumption,
            timestamps=new_timestamps,
            full_arc=arc,
        )
    else:
        await repo.update_arc(
            arc_id=arc_id,
            new_state=req.to_state,
            consumption=arc.consumption,
            timestamps=new_timestamps,
        )

    await repo.append_transition_log(
        ArcTransitionLogEntry(
            arc_id=arc_id,
            session_id=session_id,
            from_state=req.from_state,
            to_state=req.to_state,
            reason=req.reason,
            transitioned_at=now,
            resolved_scenes_at_transition=arc.consumption.resolved_scenes_used,
            locations_visited_at_transition=list(arc.consumption.locations_visited),
            triggering_event=req.triggering_event or "manual_transition",
        )
    )

    if req.to_state == "merged_into_parent" and arc.parent_arc_id:
        parent = await repo.get_by_id(session_id, arc.parent_arc_id)
        if parent is not None and arc_id not in parent.merge_source_arc_ids:
            parent.merge_source_arc_ids.append(arc_id)
            await repo.update_arc(
                arc_id=arc.parent_arc_id,
                new_state=parent.state,
                consumption=parent.consumption,
                timestamps=parent.timestamps,
                full_arc=parent,
            )

    updated = await repo.get_by_id(session_id, arc_id)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arc {arc_id} not found in session {session_id}",
        )
    return updated


@router.post("/{session_id}/{arc_id}/spawn", response_model=Arc)
async def spawn_child_arc(
    session_id: str,
    arc_id: str,
    req: ArcSpawnRequest,
    repo: ArcRepository = Depends(get_arc_repository),
) -> Arc:
    """Spawn a child arc from a parent arc."""
    parent = await repo.get_by_id(session_id, arc_id)
    if parent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arc {arc_id} not found in session {session_id}",
        )

    if parent.state not in ("in_progress", "at_scope_cap"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "parent_not_in_spawnable_state",
                "message": (
                    f"Parent arc must be in 'in_progress' or 'at_scope_cap' to spawn a child. "
                    f"Current state: '{parent.state}'."
                ),
                "parent_state": parent.state,
            },
        )

    if req.child_formal_contract_qualified:
        missing = []
        if not (req.child_patron_npc_id or req.child_patron_faction):
            missing.append("patron_npc_id or patron_faction")
        if not req.child_explicit_objective or not req.child_explicit_objective.strip():
            missing.append("explicit_objective")
        if not req.child_expected_return or not req.child_expected_return.strip():
            missing.append("expected_return")
        if missing:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "insufficient_provenance",
                    "message": (
                        "child_formal_contract_qualified=true requires explicit patron, "
                        "objective, and expected return on the child."
                    ),
                    "missing_fields": missing,
                },
            )

    if not parent.flags.formal_contract_qualified and req.ap_ownership == "parent":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "emergent_parent_no_ap_to_partition",
                "message": (
                    "Parent arc is emergent (not formal_contract_qualified). It has no AP "
                    "envelope to retain. Set ap_ownership='child' if the child is formal, "
                    "or 'none' if both are emergent."
                ),
            },
        )
    if not req.child_formal_contract_qualified and req.ap_ownership == "child":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "emergent_child_cannot_own_ap",
                "message": (
                    "Child arc is emergent. Emergent arcs cannot own AP envelopes. "
                    "Set ap_ownership='parent' (if parent is formal) or 'none'."
                ),
            },
        )

    envelope_defaults = get_arc_type_default_envelope(req.child_primary_type)
    budget = ArcBudget(
        resolved_scene_soft_cap=envelope_defaults["scene_soft_cap"],
        resolved_scene_hard_cap=envelope_defaults["scene_hard_cap"],
        location_soft_cap=envelope_defaults["location_soft_cap"],
        location_hard_cap=envelope_defaults["location_hard_cap"],
    )
    if req.child_formal_contract_qualified and req.ap_ownership == "child":
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
        title=req.child_title,
        summary=req.child_summary,
        primary_type=req.child_primary_type,
        subtype=req.child_subtype,
        stake_scale=req.child_stake_scale,
        origin_type=req.child_origin_type,
        parent_arc_id=arc_id,
        state="proposed",
        patron_faction=req.child_patron_faction,
        patron_npc_id=req.child_patron_npc_id,
        target_locations=req.child_target_locations,
        closure_conditions=req.child_closure_conditions,
        failure_conditions=req.child_failure_conditions,
        budget=budget,
        rewards=ArcRewardEnvelope(ap_award=ap_award),
        flags=ArcFlags(
            formal_contract_qualified=req.child_formal_contract_qualified,
            ap_ownership=req.ap_ownership,
        ),
        timestamps=ArcTimestamps(created_at=now),
    )

    await repo.create(child)

    if child.id not in parent.spawned_arc_ids:
        parent.spawned_arc_ids.append(child.id)
    await repo.update_arc(
        arc_id=arc_id,
        new_state=parent.state,
        consumption=parent.consumption,
        timestamps=parent.timestamps,
        full_arc=parent,
    )

    await repo.append_transition_log(
        ArcTransitionLogEntry(
            arc_id=arc_id,
            session_id=session_id,
            from_state=parent.state,
            to_state=parent.state,
            reason=f"Spawned child arc {child.id}: {req.reason}",
            transitioned_at=now,
            resolved_scenes_at_transition=parent.consumption.resolved_scenes_used,
            locations_visited_at_transition=list(parent.consumption.locations_visited),
            triggering_event="spawn",
        )
    )

    return child


@router.post("/{session_id}/{arc_id}/settle", response_model=ArcSettleResponse, deprecated=True)
async def settle_arc(
    session_id: str,
    arc_id: str,
    req: ArcSettleRequest,
    repo: ArcRepository = Depends(get_arc_repository),
) -> ArcSettleResponse:
    """Settle rewards for an arc and transition it to complete or failed."""
    arc = await repo.get_by_id(session_id, arc_id)
    if arc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arc {arc_id} not found in session {session_id}",
        )

    if req.outcome == "complete" and arc.state != "ready_to_close":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "arc_not_ready_to_close",
                "message": (
                    f"Cannot settle as complete unless arc is in 'ready_to_close' state. "
                    f"Current state: '{arc.state}'. Transition to ready_to_close first."
                ),
                "current_state": arc.state,
            },
        )
    if req.outcome == "failed" and arc.state not in ("in_progress", "at_scope_cap", "ready_to_close"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "arc_not_in_failable_state",
                "message": (
                    f"Cannot settle as failed unless arc is in 'in_progress', 'at_scope_cap', "
                    f"or 'ready_to_close'. Current state: '{arc.state}'."
                ),
                "current_state": arc.state,
            },
        )

    if req.outcome == "failed" and req.awarded_ap > 0:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "ap_on_failure_not_allowed",
                "message": "Failed arcs cannot award AP per the v1 locked policy (partial_ap_on_failure: false).",
            },
        )

    children = await repo.list_children(session_id, arc_id)
    for child in children:
        if child.flags.ap_ownership == "child" and child.state not in (
            "complete",
            "failed",
            "abandoned",
            "replaced_by_successor",
            "merged_into_parent",
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "child_ap_unsettled",
                    "message": (
                        f"Cannot settle parent arc while child {child.id} owns AP and is "
                        f"not yet terminal. Settle the child first."
                    ),
                    "blocking_child_id": child.id,
                    "blocking_child_state": child.state,
                },
            )

    if req.awarded_ap > 0:
        if not arc.flags.formal_contract_qualified:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "emergent_arc_no_ap",
                    "message": "Emergent arcs (formal_contract_qualified: false) cannot award AP per the v1 locked policy.",
                },
            )
        if arc.flags.ap_ownership == "none":
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "no_ap_ownership",
                    "message": "Arc has ap_ownership='none' and cannot award AP.",
                },
            )
        if arc.parent_arc_id and arc.flags.ap_ownership == "parent":
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "ap_owned_by_parent",
                    "message": "AP for this objective branch is owned by the parent arc. Settle the parent arc to award AP.",
                },
            )
        if not arc.parent_arc_id:
            if any(child.flags.ap_ownership == "child" for child in children):
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                    detail={
                        "error": "ap_owned_by_child",
                        "message": "AP for this objective branch is owned by a child arc. Settle the child arc to award AP.",
                    },
                )
        if req.awarded_ap < arc.rewards.ap_award.min or req.awarded_ap > arc.rewards.ap_award.max:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "ap_outside_envelope",
                    "message": (
                        f"awarded_ap {req.awarded_ap} is outside envelope "
                        f"[{arc.rewards.ap_award.min}, {arc.rewards.ap_award.max}]."
                    ),
                    "envelope_min": arc.rewards.ap_award.min,
                    "envelope_max": arc.rewards.ap_award.max,
                },
            )

    for rep_change in req.reputation_changes:
        delta = rep_change.get("delta", 0)
        if delta > 0 and delta > arc.rewards.reputation.max_positive_delta:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "reputation_positive_outside_envelope",
                    "faction": rep_change.get("faction"),
                    "delta": delta,
                    "envelope_max_positive": arc.rewards.reputation.max_positive_delta,
                },
            )
        if delta < 0 and abs(delta) > arc.rewards.reputation.max_negative_delta:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "reputation_negative_outside_envelope",
                    "faction": rep_change.get("faction"),
                    "delta": delta,
                    "envelope_max_negative": arc.rewards.reputation.max_negative_delta,
                },
            )

    if (
        req.coin_cd_awarded > 0
        and arc.rewards.economy.coin_cd_max is not None
        and req.coin_cd_awarded > arc.rewards.economy.coin_cd_max
    ):
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "coin_outside_envelope",
                "awarded": req.coin_cd_awarded,
                "envelope_max": arc.rewards.economy.coin_cd_max,
            },
        )

    now = datetime.now(timezone.utc)
    settlement = ArcSettlementResult(
        arc_id=arc_id,
        outcome=req.outcome,
        awarded_ap=req.awarded_ap,
        reputation_changes=req.reputation_changes,
        coin_cd_awarded=req.coin_cd_awarded,
        coin_cd_forfeit=req.coin_cd_forfeit,
        obligations_added=req.obligations_added,
        items_awarded=req.items_awarded,
        leverage_gained=req.leverage_gained,
        settled_at=now,
        notes=req.notes,
    )

    from_state = arc.state
    arc.settlement = settlement
    new_state = "complete" if req.outcome == "complete" else "failed"
    new_timestamps = arc.timestamps.model_copy()
    new_timestamps.last_progressed_at = now
    new_timestamps.closed_at = now

    state_repo = StateRepository(repo._pool)
    character = await state_repo.get_character(session_id)
    world = await state_repo.get_world(session_id)

    if character is None or world is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session state not found for {session_id}",
        )

    updated_character, updated_world, consequence_events = await apply_arc_settlement(
        arc=arc,
        character=character,
        world=world,
    )
    await state_repo.update_character(session_id, updated_character)
    await state_repo.update_world(session_id, updated_world)

    arc.consequence_events_emitted = consequence_events

    await repo.update_arc(
        arc_id=arc_id,
        new_state=new_state,
        consumption=arc.consumption,
        timestamps=new_timestamps,
        full_arc=arc,
    )

    closure_payload: dict[str, Any] = {
        "arc_id": arc_id,
        "arc_title": arc.title,
        "outcome": req.outcome,
        "settled_at": now.isoformat(),
        "awarded_ap": req.awarded_ap,
        "reputation_changes": list(req.reputation_changes),
        "coin_cd_awarded": req.coin_cd_awarded,
        "coin_cd_forfeit": req.coin_cd_forfeit,
        "items_awarded": list(req.items_awarded),
        "leverage_gained": list(req.leverage_gained),
        "obligations_added": list(req.obligations_added),
        "consequence_events": list(consequence_events),
        "resolved_scenes_used": arc.consumption.resolved_scenes_used,
        "locations_visited": list(arc.consumption.locations_visited),
    }

    closure_text_parts = [
        f"Arc '{arc.title}' settled as {req.outcome}",
    ]
    if req.awarded_ap > 0:
        closure_text_parts.append(f"{req.awarded_ap} AP")
    if req.coin_cd_awarded > 0:
        closure_text_parts.append(f"{req.coin_cd_awarded} CD awarded")
    if req.coin_cd_forfeit > 0:
        closure_text_parts.append(f"{req.coin_cd_forfeit} CD forfeit")
    if req.items_awarded:
        closure_text_parts.append(f"{len(req.items_awarded)} item(s)")
    if req.leverage_gained:
        closure_text_parts.append(f"{len(req.leverage_gained)} leverage")
    if req.reputation_changes:
        closure_text_parts.append(f"{len(req.reputation_changes)} reputation change(s)")
    closure_text = ": ".join([closure_text_parts[0], ", ".join(closure_text_parts[1:])]) \
        if len(closure_text_parts) > 1 else closure_text_parts[0]

    closure_entry = TypedLogEntry(
        type="closure_summary",
        text=closure_text,
        payload=closure_payload,
    )
    await state_repo.append_log_entry(session_id, closure_entry)

    await repo.append_transition_log(
        ArcTransitionLogEntry(
            arc_id=arc_id,
            session_id=session_id,
            from_state=from_state,
            to_state=new_state,
            reason=f"Arc settled as {req.outcome}: AP={req.awarded_ap}, coin={req.coin_cd_awarded}",
            transitioned_at=now,
            resolved_scenes_at_transition=arc.consumption.resolved_scenes_used,
            locations_visited_at_transition=list(arc.consumption.locations_visited),
            triggering_event="settle",
        )
    )

    updated = await repo.get_by_id(session_id, arc_id)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arc {arc_id} not found in session {session_id}",
        )
    return ArcSettleResponse(
        arc=updated,
        consequence_events=consequence_events,
        character_updated=True,
        world_updated=True,
    )


@router.post("/{session_id}/{arc_id}/force_close", response_model=ArcSettleResponse)
async def force_close_arc(
    session_id: str,
    arc_id: str,
    req: ArcForceCloseRequest,
    repo: ArcRepository = Depends(get_arc_repository),
) -> ArcSettleResponse:
    """Admin escape hatch for an arc stuck in a non-terminal state. Bypasses closure-condition evaluation and the transition matrix. Settlement runs for outcome=complete|failed; abandoned skips it. Records an admin_correction log entry with the reason."""
    arc = await repo.get_by_id(session_id, arc_id)
    if arc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arc {arc_id} not found in session {session_id}",
        )

    if is_terminal(arc.state):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "arc_already_terminal",
                "message": f"Arc is already in terminal state '{arc.state}' and cannot be force-closed.",
                "current_state": arc.state,
            },
        )

    if req.outcome == "failed" and req.awarded_ap > 0:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "ap_on_failure_not_allowed",
                "message": "Failed arcs cannot award AP per the v1 locked policy.",
            },
        )
    if req.outcome == "abandoned" and req.awarded_ap > 0:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "ap_on_abandoned_not_allowed",
                "message": "Abandoned arcs cannot award AP.",
            },
        )

    if req.awarded_ap > 0:
        if not arc.flags.formal_contract_qualified:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "emergent_arc_no_ap",
                    "message": "Emergent arcs cannot award AP.",
                },
            )
        if arc.flags.ap_ownership == "none":
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"error": "no_ap_ownership", "message": "Arc has ap_ownership='none' and cannot award AP."},
            )
        if req.awarded_ap < arc.rewards.ap_award.min or req.awarded_ap > arc.rewards.ap_award.max:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "ap_outside_envelope",
                    "envelope_min": arc.rewards.ap_award.min,
                    "envelope_max": arc.rewards.ap_award.max,
                },
            )

    now = datetime.now(timezone.utc)
    from_state = arc.state
    new_state = req.outcome  # "complete" | "failed" | "abandoned" — all terminal

    new_timestamps = arc.timestamps.model_copy()
    new_timestamps.last_progressed_at = now
    new_timestamps.closed_at = now

    state_repo = StateRepository(repo._pool)

    consequence_events: list[str] = []
    character_updated = False
    world_updated = False

    if req.outcome != "abandoned":
        settlement = ArcSettlementResult(
            arc_id=arc_id,
            outcome=req.outcome,  # type: ignore[arg-type]
            awarded_ap=req.awarded_ap,
            reputation_changes=[],
            coin_cd_awarded=0,
            coin_cd_forfeit=0,
            obligations_added=[],
            items_awarded=[],
            leverage_gained=[],
            settled_at=now,
            notes=req.notes,
        )
        arc.settlement = settlement

        character = await state_repo.get_character(session_id)
        world = await state_repo.get_world(session_id)
        if character is None or world is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session state not found for {session_id}",
            )
        updated_character, updated_world, consequence_events = await apply_arc_settlement(
            arc=arc,
            character=character,
            world=world,
        )
        await state_repo.update_character(session_id, updated_character)
        await state_repo.update_world(session_id, updated_world)
        arc.consequence_events_emitted = consequence_events
        character_updated = True
        world_updated = True

    await repo.update_arc(
        arc_id=arc_id,
        new_state=new_state,
        consumption=arc.consumption,
        timestamps=new_timestamps,
        full_arc=arc,
    )

    annotation_entry = TypedLogEntry(
        type="admin_correction",
        text=f"[operational_constraint] force_close arc {arc_id} ({from_state} → {new_state}): {req.reason}",
    )
    await state_repo.append_log_entry(session_id, annotation_entry)

    if req.outcome != "abandoned":
        closure_entry = TypedLogEntry(
            type="closure_summary",
            text=f"Arc '{arc.title}' force-closed as {req.outcome}",
            payload={
                "arc_id": arc_id,
                "arc_title": arc.title,
                "outcome": req.outcome,
                "settled_at": now.isoformat(),
                "awarded_ap": req.awarded_ap,
                "force_close": True,
                "reason": req.reason,
                "resolved_scenes_used": arc.consumption.resolved_scenes_used,
                "locations_visited": list(arc.consumption.locations_visited),
            },
        )
        await state_repo.append_log_entry(session_id, closure_entry)

    await repo.append_transition_log(
        ArcTransitionLogEntry(
            arc_id=arc_id,
            session_id=session_id,
            from_state=from_state,
            to_state=new_state,
            reason=f"force_close: {req.reason}",
            transitioned_at=now,
            resolved_scenes_at_transition=arc.consumption.resolved_scenes_used,
            locations_visited_at_transition=list(arc.consumption.locations_visited),
            triggering_event="force_close",
        )
    )

    updated = await repo.get_by_id(session_id, arc_id)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arc {arc_id} not found in session {session_id}",
        )
    return ArcSettleResponse(
        arc=updated,
        consequence_events=consequence_events,
        character_updated=character_updated,
        world_updated=world_updated,
    )


@router.post("/{session_id}/{arc_id}/declare", response_model=ArcDeclareResponse)
async def declare_arc(
    session_id: str,
    arc_id: str,
    req: ArcDeclareRequest,
    pool: asyncpg.Pool = Depends(get_pool),
    repo: ArcRepository = Depends(get_arc_repository),
) -> ArcDeclareResponse:
    """Declarative arc lifecycle endpoint. Composes /transition + /settle + /spawn behind one call. The narrator submits intent and required structured data; the backend executes the state machine atomically. Replaces routine paths through the legacy endpoints; edge cases still go through /transition."""
    return await compose_intent(
        pool=pool,
        arc_repo=repo,
        session_id=session_id,
        arc_id=arc_id,
        request=req,
    )


@router.post("/{session_id}/{arc_id}/progress", response_model=ArcProgressResponse)
async def progress_arc(
    session_id: str,
    arc_id: str,
    req: ArcProgressRequest,
    repo: ArcRepository = Depends(get_arc_repository),
) -> ArcProgressResponse:
    """
    Record resolved-scene/location progress on an in-progress arc.

    Updates consumption and auto-transitions to at_scope_cap when a hard cap
    is reached. Further progress is refused while at_scope_cap.
    """
    arc = await repo.get_by_id(session_id, arc_id)
    if arc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arc {arc_id} not found in session {session_id}",
        )

    if arc.state == "at_scope_cap":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "arc_at_scope_cap",
                "message": (
                    "Arc has reached its hard scope cap. Progress is refused "
                    "until an explicit transition (ready_to_close, failed, "
                    "replaced_by_successor, or merged_into_parent) is made."
                ),
                "current_state": arc.state,
                "scenes_used": arc.consumption.resolved_scenes_used,
                "scene_hard_cap": arc.budget.resolved_scene_hard_cap,
            },
        )
    if not is_active(arc.state) or arc.state != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "arc_not_in_progress",
                "message": (
                    "Progress can only be recorded on arcs in 'in_progress' state. "
                    f"Current state: '{arc.state}'."
                ),
                "current_state": arc.state,
            },
        )

    new_consumption = arc.consumption.model_copy(deep=True)
    if req.resolved_scene_occurred:
        new_consumption.resolved_scenes_used += 1
    if req.location_id and req.location_id not in new_consumption.locations_visited:
        new_consumption.locations_visited.append(req.location_id)
    if req.discovery_logged:
        new_consumption.discoveries_logged += 1
    if req.major_conflict_resolved:
        new_consumption.major_conflicts_resolved += 1

    soft_cap_reached = (
        new_consumption.resolved_scenes_used >= arc.budget.resolved_scene_soft_cap
    )
    hard_cap_reached = (
        new_consumption.resolved_scenes_used >= arc.budget.resolved_scene_hard_cap
    )
    location_hard_cap_reached = (
        len(new_consumption.locations_visited) >= arc.budget.location_hard_cap
    )

    auto_transitioned = False
    new_state = arc.state
    if hard_cap_reached or location_hard_cap_reached:
        new_state = "at_scope_cap"
        auto_transitioned = True

    now = datetime.now(timezone.utc)
    new_timestamps = arc.timestamps.model_copy()
    new_timestamps.last_progressed_at = now

    if req.beat is not None:
        arc.log.append(
            ArcBeatLogEntry(
                text=req.beat,
                timestamp=now,
                source="progress",
            )
        )
        arc.state = new_state
        arc.consumption = new_consumption
        arc.timestamps = new_timestamps
        await repo.update_arc(
            arc_id=arc_id,
            new_state=new_state,
            consumption=new_consumption,
            timestamps=new_timestamps,
            full_arc=arc,
        )
    else:
        await repo.update_arc(
            arc_id=arc_id,
            new_state=new_state,
            consumption=new_consumption,
            timestamps=new_timestamps,
        )

    if auto_transitioned:
        await repo.append_transition_log(
            ArcTransitionLogEntry(
                arc_id=arc_id,
                session_id=session_id,
                from_state=arc.state,
                to_state=new_state,
                reason=(
                    f"Hard cap reached: {new_consumption.resolved_scenes_used} resolved scenes "
                    f"and {len(new_consumption.locations_visited)} locations visited."
                ),
                transitioned_at=now,
                resolved_scenes_at_transition=new_consumption.resolved_scenes_used,
                locations_visited_at_transition=list(new_consumption.locations_visited),
                triggering_event="progress_call",
            )
        )

    updated = await repo.get_by_id(session_id, arc_id)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arc {arc_id} not found in session {session_id}",
        )

    warning = None
    if hard_cap_reached:
        warning = (
            "Hard scope cap reached. Arc has been transitioned to at_scope_cap. "
            "Issue a /transition call (ready_to_close, failed, replaced_by_successor, "
            "or merged_into_parent) to proceed."
        )
    elif soft_cap_reached:
        warning = (
            "Soft scope cap reached. Continued progress is allowed but consider "
            "closure or escalation soon."
        )

    return ArcProgressResponse(
        arc=updated,
        soft_cap_reached=soft_cap_reached,
        hard_cap_reached=hard_cap_reached,
        auto_transitioned_to_at_scope_cap=auto_transitioned,
        warning=warning,
    )