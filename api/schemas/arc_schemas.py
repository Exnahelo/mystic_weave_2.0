from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


def _validate_condition_set_types(condition_set: ArcConditionSet, field_label: str) -> ArcConditionSet:
    """Reject any ArcCondition.type not in the registry's condition_types list.

    Runs at request-model boundary only (create + spawn). Stored arcs with
    retired condition labels remain loadable through the underlying Arc
    model, which intentionally does not gate on type at construction.
    """
    from api.game_data import get_arc_condition_types

    valid_types = get_arc_condition_types()
    invalid: list[str] = []
    for bucket_name in ("all_of", "any_of", "none_of"):
        bucket = getattr(condition_set, bucket_name, None) or []
        for cond in bucket:
            if cond.type not in valid_types:
                invalid.append(cond.type)
    if invalid:
        raise ValueError(
            f"Invalid arc condition type(s) in {field_label}: {sorted(set(invalid))}. "
            f"Must be one of the registry condition_types in "
            f"data/catalog/registries/arc_types.json. Valid types: {sorted(valid_types)}"
        )
    return condition_set


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

    @field_validator("closure_conditions")
    @classmethod
    def _validate_closure_conditions(cls, v: ArcConditionSet) -> ArcConditionSet:
        return _validate_condition_set_types(v, "closure_conditions")

    @field_validator("failure_conditions")
    @classmethod
    def _validate_failure_conditions(cls, v: ArcConditionSet) -> ArcConditionSet:
        return _validate_condition_set_types(v, "failure_conditions")


class ArcTransitionRequest(BaseModel):
    """Payload for arc state transitions."""
    model_config = ConfigDict(extra="forbid")

    from_state: ArcState
    to_state: ArcState
    reason: str = Field(min_length=1, max_length=500)
    triggering_event: str | None = None
    world_flags: dict[str, Any] | None = None
    force: bool = False
    beat: str | None = Field(default=None, min_length=1, max_length=2000)


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

    @field_validator("child_closure_conditions")
    @classmethod
    def _validate_child_closure(cls, v: ArcConditionSet) -> ArcConditionSet:
        return _validate_condition_set_types(v, "child_closure_conditions")

    @field_validator("child_failure_conditions")
    @classmethod
    def _validate_child_failure(cls, v: ArcConditionSet) -> ArcConditionSet:
        return _validate_condition_set_types(v, "child_failure_conditions")


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
    beat: str | None = Field(default=None, min_length=1, max_length=2000)


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


class ReputationDelta(BaseModel):
    """One reputation channel entry inside ArcSettlementEnumeration.

    Empty list (`reputation_changes: []`) is the explicit no-change marker.
    Non-empty list requires every entry to name the faction and the delta.
    """
    model_config = ConfigDict(extra="forbid")

    faction: str = Field(min_length=1)
    delta: int
    note: str = ""


class ItemAward(BaseModel):
    """One item channel entry inside ArcSettlementEnumeration.

    Empty list is the explicit no-items marker. Items go into the
    settlement audit trail; physical inventory mutation is a separate
    concern (see `world.politics.known_leverage` and the
    evidence/custody schema gap in todo.md).
    """
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = ""


class ObligationChange(BaseModel):
    """One obligation channel entry inside ArcSettlementEnumeration."""
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1)
    action: Literal["created", "cleared", "worsened"]
    note: str = ""


class ArcSettlementEnumeration(BaseModel):
    """Required body for declare intent='close' or 'fail'.

    Every channel must be present in the request. Empty list is the
    explicit no-change marker. The forcing function from arc-rules.md's
    Settlement Enumeration Template is enforced here at the schema level:
    a narrator that omits a channel from the request gets a 422 naming
    the missing field. Compare to the legacy /settle endpoint, where
    every channel had a default and silent omission was possible.

    Per-channel rules (mirrors ArcSettleRequest where existing):
      - awarded_ap must be 0 if outcome is 'fail' (enforced at the
        intent-handling layer).
      - awarded_ap must be 0 if the arc is not formal-contract-qualified
        (enforced at the intent-handling layer).
      - reputation, coin, item, obligation envelope checks are performed
        against the arc's reward envelope, same as /settle.
    """
    model_config = ConfigDict(extra="forbid")

    awarded_ap: int = Field(ge=0)
    reputation_changes: list[ReputationDelta]
    coin_awarded: int = Field(ge=0)
    coin_forfeited: int = Field(ge=0)
    items_awarded: list[ItemAward]
    leverage_gained: list[str]
    obligations: list[ObligationChange]
    world_state_consequences: list[str]
    notes: str | None = None


ArcDeclareIntent = Literal[
    "activate",        # proposed → available → in_progress
    "close",           # → ready_to_close → complete (settlement required)
    "fail",            # → ready_to_close → failed (settlement required)
    "abandon",         # → abandoned (no settlement)
    "spawn_child",     # spawn child arc; parent action configurable
    "scope_check",     # read-only; reports envelope + recommendations
]


ParentActionAfterSpawn = Literal["continue", "merge_into_child", "transition_to"]


class ArcDeclareRequest(BaseModel):
    """Single declarative arc lifecycle endpoint.

    The narrator submits intent + the data required for that intent.
    The backend executes the state machine atomically — all transitions
    and settlement writes succeed together or roll back together.

    Replaces the routine paths through /transition + /settle + (some)
    /spawn for arc lifecycle. Edge cases (e.g., replaced_by_successor,
    merged_into_parent without a parallel intent) still go through
    /transition directly.
    """
    model_config = ConfigDict(extra="forbid")

    intent: ArcDeclareIntent
    reason: str = Field(min_length=10, max_length=500)

    # Required for intent='close' or 'fail':
    settlement: ArcSettlementEnumeration | None = None

    # Required for intent='spawn_child':
    child_arc: ArcSpawnRequest | None = None
    parent_action_after_spawn: ParentActionAfterSpawn | None = None
    parent_target_state: str | None = None  # required if parent_action_after_spawn='transition_to'

    # Optional:
    notes: str | None = None
    triggering_event: str | None = None
    world_flags: dict[str, Any] | None = None


class ArcSuggestion(BaseModel):
    """A recommended next action for the narrator, from scope_check.

    Minimal — names the suggested intent and the reason it was raised.
    Heuristics over arc history are deliberately out of scope; the value
    of scope_check is the audit trail of the call itself, not the
    quality of the recommendation. See Brief 3 §Q3.
    """
    model_config = ConfigDict(extra="forbid")

    suggested_intent: ArcDeclareIntent
    reason: str
    suggested_payload: dict[str, Any] | None = None


class ArcDeclareResponse(BaseModel):
    """Response from /arc/{session_id}/{arc_id}/declare."""
    model_config = ConfigDict(extra="forbid")

    arc: Arc
    child_arc: Arc | None = None
    actions_taken: list[str]
    envelope_status: dict[str, Any] | None = None
    suggestions: list[ArcSuggestion] = Field(default_factory=list)


class ArcForceCloseRequest(BaseModel):
    """Payload for force-closing an arc that cannot transition through the
    normal closure path (e.g., authored with invalid closure conditions,
    stuck at hard cap with no escape, or otherwise in need of an admin-
    style escape hatch).

    Bypasses closure-condition evaluation and the state-machine transition
    matrix. Records an admin_correction log entry with the reason text so
    future maintainers can audit when and why force_close was used.
    """
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(
        min_length=10,
        max_length=500,
        description="Required free-text explanation of why force_close was needed. "
        "Recorded in the session log as an audit annotation.",
    )
    outcome: Literal["complete", "failed", "abandoned"]
    awarded_ap: int = Field(default=0, ge=0)
    notes: str | None = None