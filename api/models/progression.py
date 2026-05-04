"""Progression scan / commit models.

Structured action types declared by the narrator at scene boundaries.
Each action type maps to a set of candidate tags via hardcoded fit rules
in api/routes/progression.py.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Scene action types — discriminated union on `type`
# ---------------------------------------------------------------------------

class SpellCastAction(BaseModel):
    """A character cast a spell. Maps to spell tag (explicit) and field (implicit)."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["spell_cast"] = "spell_cast"
    spell: str = Field(description="Canonical spell index (e.g., 'seedwake')")
    outcome: Literal["success", "partial", "failure"] = Field(
        description="Roll outcome; influences fit strength on failure"
    )


class WeaponAttackAction(BaseModel):
    """A character attacked with a weapon. Maps to weapon tag (explicit) and combat group (implicit)."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["weapon_attack"] = "weapon_attack"
    weapon: str = Field(description="Canonical weapon application index (e.g., 'longbow')")
    outcome: Literal["success", "partial", "failure"]


class SocialRollAction(BaseModel):
    """A character made a social roll. Maps to specific social tag (explicit)."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["social_roll"] = "social_roll"
    application: str = Field(
        description="Canonical social application index (e.g., 'persuasion', 'command')"
    )
    outcome: Literal["success", "partial", "failure"]


class PerceptionRollAction(BaseModel):
    """A character made a perception/awareness roll."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["perception_roll"] = "perception_roll"
    application: str = Field(
        description="Canonical perception application index (e.g., 'spoor_reading')"
    )
    outcome: Literal["success", "partial", "failure"]


class MovementAction(BaseModel):
    """A character moved with notable conditions. Maps to mobility/stealth tag."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["movement"] = "movement"
    application: str = Field(
        description="Canonical mobility application index (e.g., 'evasion', 'parkour')"
    )
    outcome: Literal["success", "partial", "failure"]


class DefenseAction(BaseModel):
    """A character defended (took a hit, parried, dodged)."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["defense"] = "defense"
    application: str = Field(
        description="Canonical defense application index (armor type, etc.)"
    )
    outcome: Literal["success", "partial", "failure"]


class GenericRollAction(BaseModel):
    """A roll that doesn't fit other action types. Application explicitly named."""
    model_config = ConfigDict(extra="forbid")

    type: Literal["generic_roll"] = "generic_roll"
    application: str = Field(description="Any canonical application index")
    outcome: Literal["success", "partial", "failure"]


SceneAction = Annotated[
    Union[
        SpellCastAction,
        WeaponAttackAction,
        SocialRollAction,
        PerceptionRollAction,
        MovementAction,
        DefenseAction,
        GenericRollAction,
    ],
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Scan request / response
# ---------------------------------------------------------------------------

class ProposedAdvance(BaseModel):
    """A tag the narrator proposes to advance after the scene resolved."""
    model_config = ConfigDict(extra="forbid")

    tag: str = Field(description="The canonical tag index to advance")
    rationale: str | None = Field(
        default=None,
        description="Optional narrator-side rationale; logged but not validated",
        max_length=500,
    )


class ProgressionScanRequest(BaseModel):
    """Request payload for /progression/scan."""
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(description="Active session ID")
    scene_actions: list[SceneAction] = Field(
        default_factory=list,
        description="Structured actions taken during the scene (max 20)",
        max_length=20,
    )
    proposed_advances: list[ProposedAdvance] = Field(
        default_factory=list,
        description="Tags the narrator proposes to advance (typically 0-1)",
        max_length=3,
    )
    scene_summary: str | None = Field(
        default=None,
        description="Free-text scene summary for logging/context (not parsed)",
        max_length=2000,
    )
    scene_id: str | None = Field(
        default=None,
        description=(
            "Optional scene record ID. Reserved for Brief 19's scene record "
            "subsystem; has no effect in Brief 18 except being echoed in the "
            "response. When Brief 19 lands, this enables one-tag-per-scene "
            "enforcement."
        ),
    )


class FitStrength(BaseModel):
    """Why a candidate tag matches the scene actions."""
    model_config = ConfigDict(extra="forbid")

    strength: Literal["explicit", "implicit", "contextual"]
    reason: str = Field(description="Short explanation of why this tag is a candidate")
    source_action_index: int | None = Field(
        default=None,
        description=(
            "Index in scene_actions[] that produced this candidate; None if "
            "scene-summary-derived or narrator-proposed."
        ),
    )


class CandidateTag(BaseModel):
    """A tag the backend identified as a plausible advance for this scene."""
    model_config = ConfigDict(extra="forbid")

    tag: str
    kind: Literal["application", "knowledge_group", "magic_field", "spell"]
    parent: str | None = Field(
        description="Parent group/field for applications/spells; None for top-level"
    )
    current_tier: int = Field(
        description="Character's current tier for this tag (0 if not yet held)"
    )
    proposed_new_tier: int = Field(description="Tier after advance (current + 1)")
    fit: FitStrength
    parent_cap_ok: bool = Field(description="Whether parent-cap allows this advance")
    held_by_character: bool = Field(description="Whether the character has this tag at all")
    at_max_tier: bool = Field(description="Whether tag is already at max tier (5)")
    eligible: bool = Field(
        description="True if the advance is structurally valid (held, not at max, parent-cap ok)"
    )


class ProposedEvaluation(BaseModel):
    """Result of evaluating one ProposedAdvance against the candidate set."""
    model_config = ConfigDict(extra="forbid")

    tag: str
    in_candidates: bool
    eligible: bool
    validation: Literal[
        "proposed_match",
        "omits_strongest",
        "invalid",
        "unknown_tag",
    ]
    strongest_omitted: list[str] | None = None


class ProgressionScanResponse(BaseModel):
    """Response from /progression/scan. Pure validation, no state mutation."""
    model_config = ConfigDict(extra="forbid")

    session_id: str
    scene_id: str | None
    candidates_ranked: list[CandidateTag] = Field(
        description="Candidates sorted by fit strength (explicit > implicit > contextual)"
    )
    proposed_evaluation: list[ProposedEvaluation]
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-blocking warnings (e.g., 'no_proposed_advances')",
    )


# ---------------------------------------------------------------------------
# Commit request / response
# ---------------------------------------------------------------------------

class ProgressionCommitRequest(BaseModel):
    """Request payload for /progression/commit. One advance, atomic."""
    model_config = ConfigDict(extra="forbid")

    session_id: str
    tag: str = Field(description="Canonical tag index to advance by 1 tier")
    rationale: str | None = Field(default=None, max_length=500)
    scene_id: str | None = Field(
        default=None,
        description="Optional scene record ID; reserved for Brief 19",
    )


class ProgressionCommitResponse(BaseModel):
    """Response from /progression/commit. Includes updated advancement state."""
    model_config = ConfigDict(extra="forbid")

    session_id: str
    tag: str
    kind: Literal["application", "knowledge_group", "magic_field", "spell"]
    new_tier: int
    advancement_after: dict[str, Any] = Field(
        description="The character's advancement block after the commit"
    )
    parent_bumped: bool = Field(
        description="True if parent group/field was auto-bumped to satisfy parent-cap"
    )
    parent_tag: str | None = Field(
        default=None,
        description="If parent_bumped, the parent tag that was bumped",
    )
    log_entry_index: int = Field(
        description="Index of the new log entry recording this advancement"
    )


# ---------------------------------------------------------------------------
# Scene record models (Brief 19)
# ---------------------------------------------------------------------------

class DeclareSceneResolutionRequest(BaseModel):
    """Request payload for /scene/declare_resolution."""
    model_config = ConfigDict(extra="forbid")

    session_id: str
    scene_summary: str | None = Field(default=None, max_length=2000)
    scene_actions: list[SceneAction] = Field(
        default_factory=list,
        description="Structured actions taken during the scene",
        max_length=20,
    )
    location_id: str | None = Field(
        default=None,
        description=(
            "Where the scene resolved; if omitted, server reads world.location "
            "at time of resolution."
        ),
    )
    arc_progressed_ids: list[str] = Field(
        default_factory=list,
        description="Active arc IDs this scene contributed to. Server validates each exists.",
        max_length=10,
    )


class ArcEnvelopeStatus(BaseModel):
    """One arc's envelope state at scene-resolution time."""
    model_config = ConfigDict(extra="forbid")

    arc_id: str
    title: str
    state: str
    resolved_scenes_used: int
    resolved_scene_soft_cap: int
    resolved_scene_hard_cap: int
    locations_visited: int
    location_soft_cap: int
    location_hard_cap: int
    soft_cap_approaching: bool = Field(description="True if at or beyond soft cap")
    hard_cap_reached: bool = Field(
        description="True if at hard cap; transition to ready_to_close suggested"
    )
    phase_shift_candidate: bool = Field(
        default=False,
        description=(
            "True when this arc is emergent origin AND has crossed its soft cap. "
            "Indicates the narrator should evaluate whether institutional phase "
            "has begun and whether a formal child arc should be spawned. See "
            "arc-rules.md 'Phase Change Indicators' for the structural conditions "
            "warranting spawn."
        ),
    )


class DeclareSceneResolutionResponse(BaseModel):
    """Response from /scene/declare_resolution."""
    model_config = ConfigDict(extra="forbid")

    scene_id: str
    session_id: str
    resolved_at: str = Field(description="ISO timestamp")
    location_id: str | None
    turn_at_resolution: int | None
    arc_envelope_status: list[ArcEnvelopeStatus] = Field(
        description="Status of all active arcs after this scene's contribution"
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggest-level guidance: e.g., 'arc_X soft cap approaching, consider settling'",
    )


class SceneRecord(BaseModel):
    """Full scene record returned by GET endpoints."""
    model_config = ConfigDict(extra="forbid")

    scene_id: str
    session_id: str
    resolved_at: str
    scene_summary: str | None
    scene_actions: list[dict[str, Any]] = Field(description="Raw scene actions as recorded")
    tag_advance_committed: str | None
    arc_progressed_ids: list[str]
    location_id: str | None
    turn_at_resolution: int | None
    time_at_resolution: dict[str, Any] | None


class SceneRecordsListResponse(BaseModel):
    """Paginated list of scene records for a session."""
    model_config = ConfigDict(extra="forbid")

    session_id: str
    records: list[SceneRecord]
    has_more: bool
    next_cursor: str | None = Field(
        default=None,
        description="Opaque cursor for the next page; None if no more.",
    )


# ---------------------------------------------------------------------------
# Orchestrator models (Brief 20)
# ---------------------------------------------------------------------------

class CharacterStateChanges(BaseModel):
    """Non-advancement character changes the orchestrator can apply.

    Advancement is intentionally excluded — it goes through `proposed_advance`
    and lands via the validated progression pipeline. Submitting `knowledge`,
    `magic`, or `advancement` here will be rejected by `extra="forbid"`.
    """
    model_config = ConfigDict(extra="forbid")

    hp: dict[str, Any] | None = None
    status_effects: list[str] | None = None
    equipment: dict[str, Any] | None = None
    domains: dict[str, Any] | None = None
    notes: str | None = None
    identity: dict[str, Any] | None = None
    reputation: list[dict[str, Any]] | None = None


class WorldStateChanges(BaseModel):
    """Non-time world changes the orchestrator can apply.

    Time advancement goes through `time_elapsed`; submitting `time` or `turn`
    here will be rejected. Turn auto-increments on each time advance.
    """
    model_config = ConfigDict(extra="forbid")

    location: str | None = None
    threat: str | None = None
    goal: str | None = None
    politics: dict[str, Any] | None = None
    economy: dict[str, Any] | None = None
    survival: dict[str, Any] | None = None
    pacing: dict[str, Any] | None = None
    companions: list[dict[str, Any]] | None = None
    companion_archive: list[dict[str, Any]] | None = None


class SceneResolvedRequest(BaseModel):
    """Single payload representing one resolved scene.

    The orchestrator processes this transactionally: scene boundary recorded,
    progression validated, advance committed (if proposed and eligible),
    state changes applied, time advanced — all-or-nothing.
    """
    model_config = ConfigDict(extra="forbid")

    session_id: str

    scene_summary: str | None = Field(default=None, max_length=2000)
    scene_actions: list[SceneAction] = Field(default_factory=list, max_length=20)
    location_id: str | None = Field(
        default=None,
        description="Where the scene occurred; defaults to world.location.",
    )
    arc_progressed_ids: list[str] = Field(default_factory=list, max_length=10)

    proposed_advance: ProposedAdvance | None = Field(
        default=None,
        description=(
            "If the narrator wants to advance a tag this scene; the orchestrator "
            "validates against scene_actions and commits if eligible. Eligible "
            "advances commit even when a stronger candidate is omitted; the "
            "proposed_evaluation field surfaces that for narrator awareness."
        ),
    )

    character_changes: CharacterStateChanges | None = None
    world_changes: WorldStateChanges | None = None

    time_elapsed: dict[str, Any] | None = Field(
        default=None,
        description=(
            "TimeElapsed payload to advance world.time; same shape as accepted "
            "by /state/{id}/delta time_elapsed. Turn auto-increments on advance."
        ),
    )


class SceneResolvedResponse(BaseModel):
    """Composed response: what happened, what state is now, what's pending."""
    model_config = ConfigDict(extra="forbid")

    session_id: str
    scene_id: str

    advance_committed: dict[str, Any] | None = Field(
        default=None,
        description="Same shape as ProgressionCommitResponse if a commit happened.",
    )
    proposed_evaluation: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Same shape as ProgressionScanResponse.proposed_evaluation[0]; "
            "present only if proposed_advance was submitted."
        ),
    )
    candidates_ranked: list[CandidateTag] = Field(
        default_factory=list,
        description="Strongest-fit candidates derived from scene_actions.",
    )

    resolved_at: str
    location_id: str | None
    turn_at_resolution: int | None

    arc_envelope_status: list[ArcEnvelopeStatus] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)

    state_after: dict[str, Any] = Field(
        description=(
            "Full game state: {character, world, log, updated_at}. Same shape "
            "as GET /state/{id}."
        ),
    )

    changes_applied: list[str] = Field(
        default_factory=list,
        description=(
            "Human-readable list of what landed: e.g., ['scene_recorded', "
            "'advance_committed:seedwake', 'world.location', 'time_advanced']."
        ),
    )
