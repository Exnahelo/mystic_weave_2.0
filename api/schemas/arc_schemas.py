from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from api.models import (
    Arc,
    ArcAPOwnership,
    ArcConditionSet,
    ArcEscalationRules,
    ArcOriginType,
    ArcPrimaryType,
    ArcState,
    ArcStakeScale,
)


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
    world_flags: dict[str, Any] | None = None
    force: bool = False


class ArcSpawnRequest(BaseModel):
    """Payload for spawning a child arc from a parent."""
    model_config = ConfigDict(extra="forbid")

    child_title: str = Field(min_length=1, max_length=200)
    child_summary: str = Field(min_length=1, max_length=2000)
    child_primary_type: ArcPrimaryType
    child_subtype: str
    child_stake_scale: ArcStakeScale
    child_origin_type: ArcOriginType = "derived"
    child_patron_faction: str | None = None
    child_patron_npc_id: str | None = None
    child_target_locations: list[str] = Field(default_factory=list)
    child_closure_conditions: ArcConditionSet = Field(default_factory=ArcConditionSet)
    child_failure_conditions: ArcConditionSet = Field(default_factory=ArcConditionSet)
    child_formal_contract_qualified: bool = False
    child_explicit_objective: str | None = None
    child_expected_return: str | None = None
    ap_ownership: ArcAPOwnership = "parent"
    reason: str = Field(min_length=1, max_length=500)


class ArcSettleRequest(BaseModel):
    """Payload for settling a complete or failed arc."""
    model_config = ConfigDict(extra="forbid")

    outcome: Literal["complete", "failed"]
    awarded_ap: int = Field(default=0, ge=0)
    reputation_changes: list[dict[str, Any]] = Field(default_factory=list)
    coin_cd_awarded: int = Field(default=0, ge=0)
    coin_cd_forfeit: int = Field(default=0, ge=0)
    obligations_added: list[dict[str, Any]] = Field(default_factory=list)
    items_awarded: list[str] = Field(default_factory=list)
    leverage_gained: list[str] = Field(default_factory=list)
    notes: str | None = None


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


class ArcSettleResponse(BaseModel):
    """Response from a settle call, including consequence events."""
    model_config = ConfigDict(extra="forbid")

    arc: Arc
    consequence_events: list[str]
    character_updated: bool = True
    world_updated: bool = True