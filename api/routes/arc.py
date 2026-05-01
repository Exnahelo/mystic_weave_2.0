"""routes/arc.py — create and read Arc System v1 records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from api.arc_state_machine import get_allowed_transitions, is_active, is_terminal, is_transition_allowed
from api.database import get_pool
from api.game_data import get_arc_type_default_envelope
from api.models import (
    Arc,
    ArcAPAward,
    ArcBudget,
    ArcConditionSet,
    ArcEscalationRules,
    ArcFlags,
    ArcOriginType,
    ArcPrimaryType,
    ArcRewardEnvelope,
    ArcState,
    ArcStakeScale,
    ArcTimestamps,
    ArcTransitionLogEntry,
)
from api.repositories.arc_repository import ArcRepository

router = APIRouter(prefix="/arc", tags=["arc"])


class ArcCreateRequest(BaseModel):
    """Payload for arc creation."""
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=2000)
    primary_type: ArcPrimaryType
    subtype: str
    stake_scale: ArcStakeScale
    origin_type: ArcOriginType
    parent_arc_id: str | None = None
    patron_faction: str | None = None
    patron_npc_id: str | None = None
    target_locations: list[str] = Field(default_factory=list)
    closure_conditions: ArcConditionSet = Field(default_factory=ArcConditionSet)
    failure_conditions: ArcConditionSet = Field(default_factory=ArcConditionSet)
    escalation_rules: ArcEscalationRules | None = None
    formal_contract_qualified: bool = False
    explicit_objective: str | None = None
    expected_return: str | None = None
    notes: list[str] = Field(default_factory=list)


class ArcTransitionRequest(BaseModel):
    """Payload for arc state transitions."""
    model_config = ConfigDict(extra="forbid")

    from_state: ArcState
    to_state: ArcState
    reason: str = Field(min_length=1, max_length=500)
    triggering_event: str | None = None


class ArcProgressRequest(BaseModel):
    """Payload for resolved-scene progress events."""
    model_config = ConfigDict(extra="forbid")

    resolved_scene_occurred: bool = True
    location_id: str | None = None
    discovery_logged: bool = False
    major_conflict_resolved: bool = False
    notes: str | None = None


class ArcProgressResponse(BaseModel):
    """Response from a progress call."""
    model_config = ConfigDict(extra="forbid")

    arc: Arc
    soft_cap_reached: bool
    hard_cap_reached: bool
    auto_transitioned_to_at_scope_cap: bool
    warning: str | None = None


def _plain_validation_errors(err: ValidationError) -> list[dict[str, Any]]:
    """Return JSON-serializable pydantic errors without exception objects."""
    cleaned: list[dict[str, Any]] = []
    for item in err.errors():
        clone = dict(item)
        ctx = clone.get("ctx")
        if isinstance(ctx, dict):
            clone["ctx"] = {k: str(v) for k, v in ctx.items()}
        cleaned.append(clone)
    return cleaned


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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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


def build_arc_from_request(session_id: str, req: ArcCreateRequest) -> Arc:
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
        closure_conditions=req.closure_conditions,
        failure_conditions=req.failure_conditions,
        escalation_rules=req.escalation_rules or ArcEscalationRules(),
        budget=budget,
        rewards=ArcRewardEnvelope(ap_award=ap_award),
        flags=flags,
        timestamps=ArcTimestamps(created_at=now),
        notes=req.notes,
    )


@router.post("/{session_id}/create", response_model=Arc)
async def create_arc(
    session_id: str,
    req: ArcCreateRequest,
    repo: ArcRepository = Depends(get_arc_repository),
) -> Arc:
    """Create a new arc with strict provenance validation."""
    validate_provenance(req)
    try:
        arc = build_arc_from_request(session_id, req)
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


@router.post("/{session_id}/{arc_id}/transition", response_model=Arc)
async def transition_arc(
    session_id: str,
    arc_id: str,
    req: ArcTransitionRequest,
    repo: ArcRepository = Depends(get_arc_repository),
) -> Arc:
    """
    Request an arc state transition.

    Enforces the Arc System v1 transition matrix and rejects stale
    from_state values. Closure/failure condition evaluation lands with settle.
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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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

    now = datetime.now(timezone.utc)
    new_timestamps = arc.timestamps.model_copy()
    new_timestamps.last_progressed_at = now
    if is_terminal(req.to_state):
        new_timestamps.closed_at = now

    await repo.update_state_and_consumption(
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

    updated = await repo.get_by_id(session_id, arc_id)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arc {arc_id} not found in session {session_id}",
        )
    return updated


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

    await repo.update_state_and_consumption(
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