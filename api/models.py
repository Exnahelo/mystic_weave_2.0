"""
models.py — Pydantic v2 models for core game entities.

All models use Pydantic v2 syntax. Designed for Mystic Weave 4.5.0:
d100 roll-under, domain scores, knowledge/application competency tiers,
fungible advancement points, and a four-layer character system built from
ancestry, culture, background, and focus.

v3.1.0 additions:
  CharacterModel — identity, equipment, reputation blocks
  WorldModel     — economy, politics blocks

v4.5.0 additions:
  CharacterModel — ancestry/culture/fields schema
  Options models — ancestry + culture option payloads
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

if TYPE_CHECKING:
    from api.companions import ArchivedCompanionEnvelope, CompanionRecord


DOMAIN_KEYS: tuple[str, ...] = (
    "power", "agility", "perception", "endurance",
    "intellect", "will", "presence",
)

TagTier = Annotated[
    int,
    Field(
        ge=1,
        le=5,
        description="Competency tag tier. Must be an integer from 1 through 5.",
    ),
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AlignmentOrder(str, Enum):
    lawful  = "lawful"
    neutral = "neutral"
    chaotic = "chaotic"


class AlignmentIntent(str, Enum):
    good    = "good"
    neutral = "neutral"
    evil    = "evil"


class WealthTier(str, Enum):
    destitute   = "destitute"
    modest      = "modest"
    comfortable = "comfortable"
    wealthy     = "wealthy"
    affluent    = "affluent"


class EquipmentTag(str, Enum):
    utility        = "utility"
    weapon         = "weapon"
    armor          = "armor"
    consumable     = "consumable"
    arcane         = "arcane"
    sacred         = "sacred"
    trade_good     = "trade_good"
    special        = "special"


# ---------------------------------------------------------------------------
# Character sub-models
# ---------------------------------------------------------------------------

class HP(BaseModel):
    current: int
    max: int = 100

    @field_validator("current")
    @classmethod
    def current_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("current HP cannot be negative")
        return v

    @field_validator("max")
    @classmethod
    def max_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max HP must be at least 1")
        return v


class DomainScores(BaseModel):
    power:      int
    agility:    int
    perception: int
    endurance:  int
    intellect:  int
    will:       int
    presence:   int

    @field_validator("power", "agility", "perception", "endurance",
                     "intellect", "will", "presence")
    @classmethod
    def score_in_range(cls, v: int) -> int:
        if not (1 <= v <= 80):
            raise ValueError("domain score must be between 1 and 80")
        return v


class AdvancementState(BaseModel):
    """
    Fungible AP pool, lifetime totals, and a single tag advance counter.

    Tag advances increment tag_counter. Every 3 advances (counter == 3)
    resets the counter to 0 and adds 1 to points_available. Awarded AP
    grants drop directly into points_available. Spend draws from
    points_available with bracketed cost (1/2/3 by score range).
    """

    points_available: int = 0
    points_spent: int = 0
    points_earned_total: int = 0
    tag_counter: int = Field(default=0, ge=0, le=2)

    @field_validator("points_available", "points_spent", "points_earned_total")
    @classmethod
    def non_negative_int(cls, v: int) -> int:
        if v < 0:
            raise ValueError("advancement points cannot be negative")
        return v


class Alignment(BaseModel):
    order:      AlignmentOrder  = AlignmentOrder.neutral
    intent:     AlignmentIntent = AlignmentIntent.neutral
    ethos_note: str             = ""   # freeform; GPT uses for narration texture


class EquipmentItem(BaseModel):
    """Single item in any equipment slot."""
    id:          str
    name:        str
    description: str          = ""
    tags:        list[EquipmentTag] = Field(default_factory=list)
    # Optional link to application tag for roll context (e.g. "grappling")
    roll_tag:    str | None   = None


class Equipment(BaseModel):
    """Three-slot equipment inventory."""
    worn:    list[EquipmentItem] = Field(default_factory=list)   # equipped on person right now
    carried: list[EquipmentItem] = Field(default_factory=list)   # in pack / accessible this scene
    stashed: list[EquipmentItem] = Field(default_factory=list)   # at a known location, not on person


class EquipmentDelta(BaseModel):
    """Sparse equipment update; merges by slot rather than replacing all equipment."""
    model_config = ConfigDict(extra="forbid")

    worn: list[EquipmentItem] | None = None
    carried: list[EquipmentItem] | None = None
    stashed: list[EquipmentItem] | None = None


class Identity(BaseModel):
    """
    Narrative character block. Captured at creation, GPT-readable every session.
    All fields optional at creation — can be filled in as play reveals them.
    """
    origin:      str        = ""   # where they came from / formative history
    motivations: list[str]  = Field(default_factory=list)   # 1–3 driving goals
    quirks:      list[str]  = Field(default_factory=list)   # 1–3 behavioural traits or mannerisms
    bonds:       list[str]  = Field(default_factory=list)   # people, places, or things they're tied to
    flaws:       list[str]  = Field(default_factory=list)   # weaknesses, biases, or blind spots
    wound:       str        = ""   # notable formative scar or event
    alignment:   Alignment  = Field(default_factory=Alignment)

    @field_validator("motivations", "quirks", "bonds", "flaws")
    @classmethod
    def max_three(cls, v: list[str]) -> list[str]:
        if len(v) > 3:
            raise ValueError("maximum 3 entries per narrative list")
        return v


class ReputationEntry(BaseModel):
    """
    Standing with a single faction or community.
    Missing entry = unknown (faction has no opinion yet).
    Range: -100 (despised) to +100 (revered).
    """
    faction:     str   # faction ID, e.g. "draconic_council", "silver_scale_trading_company"
    standing:    int   = 0
    note:        str   = ""   # reason or last major change
    last_change: str   = ""   # brief description of the event that moved it

    @field_validator("standing")
    @classmethod
    def clamp_standing(cls, v: int) -> int:
        return max(-100, min(100, v))


# ---------------------------------------------------------------------------
# Character model
# ---------------------------------------------------------------------------

class CharacterModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Core identity
    name:           str
    ancestry:       str   # e.g. "human", "drakari"
    draconic_traits: list[str] = Field(default_factory=list)
    culture:        str
    focus:          str   # e.g. "devoted", "stalker"
    background:     str   # e.g. "soldier", "acolyte"
    hp:             HP
    domains:        DomainScores
    knowledge:      dict[str, TagTier] = Field(default_factory=dict)   # tag name → tier (1–5)
    application:    dict[str, TagTier] = Field(default_factory=dict)   # tag name → tier (1–5)
    fields:         dict[str, TagTier] = Field(default_factory=dict)   # field name → tier (1–5)
    status_effects: list[str]      = Field(default_factory=list)
    notes:          str            = ""

    # v3.1.0+
    identity:       Identity       = Field(default_factory=Identity)
    equipment:      Equipment      = Field(default_factory=Equipment)
    reputation:     list[ReputationEntry] = Field(default_factory=list)
    advancement:    AdvancementState = Field(default_factory=AdvancementState)


# ---------------------------------------------------------------------------
# World sub-models
# ---------------------------------------------------------------------------

class Economy(BaseModel):
    """
    Economic state. wealth_tier is the universal abstraction (works for barter
    and currency economies alike). coin is stored as total Copper Drakes (CD)
    as a raw integer for regions that use hard currency (e.g. outside
    Drakenvale via the SSTC). 100 CD = 1 GD.
    """
    wealth_tier:  WealthTier        = WealthTier.modest
    coin:         int               = 0          # total Copper Drakes (CD)
    trade_goods:  list[str]         = Field(default_factory=list)         # named barter items not in equipment
    obligations:  list[str]         = Field(default_factory=list)         # debts, favors owed, sworn duties

    @field_validator("coin")
    @classmethod
    def coin_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("coin cannot be negative")
        return v


class EconomyDelta(BaseModel):
    """Sparse economy update for delta application."""
    model_config = ConfigDict(extra="forbid")

    wealth_tier: WealthTier | None = None
    coin: int | None = None
    trade_goods: list[str] | None = None
    obligations: list[str] | None = None

    @field_validator("coin")
    @classmethod
    def coin_non_negative(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("coin cannot be negative")
        return v


class Politics(BaseModel):
    """
    World-level relational and political state.
    Not a subsystem — a lightweight store for the GPT to track active context.
    """
    faction_memberships:   list[str] = Field(default_factory=list)   # factions the party formally belongs to
    active_obligations:    list[str] = Field(default_factory=list)   # current political duties or oaths
    legal_standing:        str       = "unknown"   # e.g. "exile", "citizen", "wanted"
    known_leverage:        list[str] = Field(default_factory=list)   # secrets or leverage the party holds
    active_tensions:       list[str] = Field(default_factory=list)   # ongoing faction conflicts relevant to party
    conclave_status:       str       = "unknown"   # "pending" | "active" | "concluded" | "unknown"


class TimeOfDay(str, Enum):
    dawn      = "dawn"
    morning   = "morning"
    midday    = "midday"
    afternoon = "afternoon"
    dusk      = "dusk"
    night     = "night"


class WeatherState(str, Enum):
    clear      = "clear"
    mist       = "mist"
    storm      = "storm"
    ash_haze   = "ash-haze"
    unnatural  = "unnatural"


class HungerState(str, Enum):
    sated    = "sated"
    hungry   = "hungry"
    starving = "starving"


class HydrationState(str, Enum):
    hydrated   = "hydrated"
    thirsty    = "thirsty"
    dehydrated = "dehydrated"


class FatigueState(str, Enum):
    rested    = "rested"
    tired     = "tired"
    fatigued  = "fatigued"
    exhausted = "exhausted"


class LoadState(str, Enum):
    light      = "light"
    normal     = "normal"
    burdened   = "burdened"
    overloaded = "overloaded"


class ConsequenceWeight(str, Enum):
    local = "local"
    situational = "situational"
    regional = "regional"
    campaign = "campaign"


class TimeState(BaseModel):
    """In-world time, calendar, and weather state."""
    day:          int          = 1
    month:        str          = "Verdantrise"
    year:         int          = 847
    time_of_day:  TimeOfDay    = TimeOfDay.morning
    season:       str          = "spring"
    festival:     str | None   = None
    weather:      WeatherState = WeatherState.clear
    weather_note: str          = ""

    @field_validator("day")
    @classmethod
    def day_in_range(cls, v: int) -> int:
        if not (1 <= v <= 30):
            raise ValueError("day must be between 1 and 30")
        return v

    @field_validator("year")
    @classmethod
    def year_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("year must be at least 1")
        return v


class TimeElapsed(BaseModel):
    """Duration to advance world.time by on a state save.

    Three modes:
    - steps: time-of-day band advances (1 step = 1 band, 6 bands per day)
    - days: full day advances
    - until: special anchor advance ("dawn" advances to the next dawn)

    `until` is mutually exclusive with steps/days. If until is set, steps and
    days must both be 0.
    """
    model_config = ConfigDict(extra="forbid")

    steps: int = Field(0, ge=0, le=12, description="Time-of-day band advances.")
    days: int = Field(0, ge=0, le=30, description="Full day advances.")
    until: Literal["dawn"] | None = Field(None, description='If "dawn", advance to next dawn.')

    @model_validator(mode="after")
    def validate_combination(self) -> "TimeElapsed":
        if self.until is not None and (self.steps or self.days):
            raise ValueError("`until` cannot be combined with non-zero steps or days")
        return self


class SurvivalState(BaseModel):
    """Lightweight survival/load tracking using coarse state bands."""
    hunger:    HungerState    = HungerState.sated
    hydration: HydrationState = HydrationState.hydrated
    fatigue:   FatigueState   = FatigueState.rested
    load:      LoadState      = LoadState.normal


class PacingState(BaseModel):
    """Lightweight pacing guidance block for scene cadence and intensity."""
    tension: int = 3
    last_consequence_weight: ConsequenceWeight = ConsequenceWeight.local
    turns_since_social_beat: int = 0
    turns_since_discovery: int = 0
    turn_count: int = 0

    @field_validator("tension")
    @classmethod
    def clamp_tension(cls, v: int) -> int:
        return max(0, min(10, v))

    @field_validator("turns_since_social_beat", "turns_since_discovery", "turn_count")
    @classmethod
    def non_negative_counter(cls, v: int) -> int:
        if v < 0:
            raise ValueError("pacing counters must be non-negative")
        return v
    

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

class WorldModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location:   str
    threat:     str
    goal:       str
    turn:       int = 1

    # New in v3.1.0
    companions: list["CompanionRecord"] = Field(default_factory=list)
    companion_archive: list["ArchivedCompanionEnvelope"] = Field(default_factory=list)
    economy:    Economy              = Field(default_factory=Economy)
    politics:   Politics             = Field(default_factory=Politics)

    # New in v3.2.0
    time:       TimeState            = Field(default_factory=TimeState)

    # New in v3.3.0
    survival:   SurvivalState        = Field(default_factory=SurvivalState)

    # New in v3.4.0
    pacing:     PacingState          = Field(default_factory=PacingState)

    @field_validator("turn")
    @classmethod
    def turn_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("turn must be at least 1")
        return v

    @model_validator(mode="after")
    def sync_pacing_turn_count(self) -> WorldModel:
        """world.turn is authoritative; pacing.turn_count mirrors it for pacing guidance."""
        self.pacing.turn_count = self.turn
        return self


# ---------------------------------------------------------------------------
# State request / response models
# ---------------------------------------------------------------------------

class CharacterStateDelta(BaseModel):
    """
    Typed partial character update for extraction-driven turn commits.

    Note on `advancement`: the delta endpoint recomputes advancement
    authoritatively from existing state and tag-tier transitions. Any
    client-supplied `advancement` value is replaced server-side. The field
    remains on the schema for forward compatibility and round-trip safety,
    but its content has no effect on persisted state.
    """
    model_config = ConfigDict(extra="forbid")

    hp: HP | None = None
    domains: dict[str, int] | None = None
    knowledge: dict[str, TagTier] | None = None
    application: dict[str, TagTier] | None = None
    fields: dict[str, TagTier] | None = None
    status_effects: list[str] | None = None
    notes: str | None = None
    equipment: EquipmentDelta | None = None
    reputation: list[ReputationEntry] | None = None
    advancement: AdvancementState | None = None
    draconic_traits: list[str] | None = None

    def has_updates(self) -> bool:
        return any(v is not None for v in self.model_dump(exclude_none=False).values())


class WorldStateDelta(BaseModel):
    """Typed partial world update for extraction-driven turn commits."""
    model_config = ConfigDict(extra="forbid")

    location: str | None = None
    threat: str | None = None
    goal: str | None = None
    turn: int | None = None
    companions: list["CompanionRecord"] | None = None
    companion_archive: list["ArchivedCompanionEnvelope"] | None = None
    economy: EconomyDelta | None = None
    politics: Politics | None = None
    time: dict[str, object] | None = None
    survival: SurvivalState | None = None
    pacing: PacingState | None = None

    def has_updates(self) -> bool:
        return any(v is not None for v in self.model_dump(exclude_none=False).values())


class ApplyStateDeltaRequest(BaseModel):
    """Body for POST /state/{session_id}/delta"""
    model_config = ConfigDict(extra="forbid")

    character: CharacterStateDelta = Field(default_factory=CharacterStateDelta)
    world: WorldStateDelta = Field(default_factory=WorldStateDelta)
    log_entry: str
    time_elapsed: TimeElapsed = Field(default_factory=TimeElapsed)

    @model_validator(mode="after")
    def requires_any_delta(self) -> ApplyStateDeltaRequest:
        if not self.character.has_updates() and not self.world.has_updates():
            raise ValueError("state delta must include at least one character or world change")
        return self


class SaveStateRequest(BaseModel):
    """Body for POST /state/{session_id}"""
    model_config = ConfigDict(extra="forbid")

    character: CharacterModel | CharacterStateDelta = Field(default_factory=CharacterStateDelta)
    world: WorldModel | WorldStateDelta = Field(default_factory=WorldStateDelta)
    log_entry: str
    time_elapsed: TimeElapsed = Field(default_factory=TimeElapsed)


class GameStateResponse(BaseModel):
    """Response for GET /state/{session_id}"""
    session_id: str
    character:  CharacterModel
    world:      WorldModel
    log:        list[str]
    updated_at: datetime | None = None


class SpendAPRequest(BaseModel):
    """Body for POST /character/{session_id}/spend_ap"""
    model_config = ConfigDict(extra="forbid")

    target_domain: str = Field(
        description="Domain to advance. Must be one of the seven domains."
    )
    points: int = Field(
        gt=0,
        description="Number of domain points to purchase. Must be positive.",
    )

    @field_validator("target_domain")
    @classmethod
    def domain_valid(cls, v: str) -> str:
        if v not in DOMAIN_KEYS:
            raise ValueError(f"unknown domain: {v!r}")
        return v


class SpendAPResponse(BaseModel):
    session_id: str
    target_domain: str
    points_purchased: int
    ap_cost_total: int
    new_domain_score: int
    advancement: AdvancementState


# ---------------------------------------------------------------------------
# Session models
# ---------------------------------------------------------------------------

class AdjustmentPoints(BaseModel):
    """Player's +10 domain adjustment pool at creation. Max +5 per domain."""
    power:      int = 0
    agility:    int = 0
    perception: int = 0
    endurance:  int = 0
    intellect:  int = 0
    will:       int = 0
    presence:   int = 0

    @field_validator("power", "agility", "perception", "endurance",
                     "intellect", "will", "presence")
    @classmethod
    def per_domain_cap(cls, v: int) -> int:
        if v < 0:
            raise ValueError("adjustment points cannot be negative")
        if v > 5:
            raise ValueError("max +5 adjustment per domain")
        return v

    @model_validator(mode="after")
    def total_pool_cap(self) -> AdjustmentPoints:
        total = (self.power + self.agility + self.perception +
                 self.endurance + self.intellect + self.will + self.presence)
        if total > 10:
            raise ValueError(f"Adjustment pool is 10 points max. Got {total}.")
        return self


class NewSessionRequest(BaseModel):
    """Body for POST /session/new"""
    character_name:   str
    ancestry:         str
    culture:          str
    focus:            str
    background:       str
    adjustment_points: AdjustmentPoints = Field(default_factory=AdjustmentPoints)
    starting_location: str              = "unknown"
    goal:             str               = "survive"
    threat:           str               = "unknown"
    # New in v3.1.0 — all optional; GPT gathers these during character creation
    identity:         Identity          = Field(default_factory=Identity)
    starting_economy: Economy           = Field(default_factory=Economy)
    companions:       list["CompanionRecord"] | None = None
    equipment:        Equipment | None = None


class NewSessionResponse(BaseModel):
    session_id: str
    character:  CharacterModel
    world:      WorldModel


# ---------------------------------------------------------------------------
# Character creation models
# ---------------------------------------------------------------------------

class CreateCharacterRequest(BaseModel):
    """Body for POST /character/create — seeds character from game system data."""
    session_id:        str
    name:              str
    ancestry:          str
    culture:           str
    focus:             str
    background:        str
    adjustment_points: AdjustmentPoints = Field(default_factory=AdjustmentPoints)
    identity:          Identity         = Field(default_factory=Identity)


class CreateCharacterResponse(BaseModel):
    session_id: str
    character:  CharacterModel


# ---------------------------------------------------------------------------
# Health / metadata response models
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    service: str


class VersionResponse(BaseModel):
    service: str
    api_version: str
    git_sha: str
    data_fingerprint: str
    combat_rules_fingerprint: str
    ancestry_count: int
    culture_count: int
    focus_count: int
    backgrounds_count: int


# ---------------------------------------------------------------------------
# Dice roll models
# ---------------------------------------------------------------------------

class RollRequest(BaseModel):
    """Body for POST /roll — d100 roll-under resolution."""
    # Assembled target: domain score + knowledge tier + application tier + difficulty modifier.
    # Server clamps to 1–99.
    target: int
    reason: str | None = Field(
        default=None,
        description="Optional short description of the attempted action for observability/debugging.",
    )

    @field_validator("target")
    @classmethod
    def target_in_range(cls, v: int) -> int:
        if v < 1:
            return 1    # floor — always at least a crit success chance
        if v > 99:
            return 99   # cap — always at least a crit failure chance
        return v


class RollResponse(BaseModel):
    roll:             int    # raw d100 result (1–100)
    target:           int    # clamped target number
    success:          bool   # roll <= target
    margin:           int    # target - roll (positive = succeeded by, negative = failed by)
    degree:           str    # "critical_success" | "strong_success" | "success" |
                             # "partial_failure" | "failure" | "critical_failure"
    critical_success: bool = False   # roll == 1
    critical_failure: bool = False   # roll == 100


class ComputeMaxHpRequest(BaseModel):
    armor_id: str
    armor_tier: int = Field(..., ge=0, le=5)
    shield_id: str | None = None
    shield_tier: int = Field(default=0, ge=0, le=5)


class ComputeMaxHpResponse(BaseModel):
    max_hp: int
    base: int
    armor_contribution: int
    shield_contribution: int
    armor_id: str
    armor_tier: int
    shield_id: str | None
    shield_tier: int


class CombatRoll1Result(BaseModel):
    value: int
    target: int
    base_target: int


class CombatRoll2Result(BaseModel):
    attacker: int
    defender: int
    margin: int


class CombatDamageResult(BaseModel):
    weapon_base: int
    effective_base: int
    ammo_modifier: int
    margin_multiplier: float
    agility_reduction_multiplier: float
    pre_reduction: int
    final: int


class CombatReboundResult(BaseModel):
    attacker_damage: int


class ResolveAttackRequest(BaseModel):
    weapon_id: str
    weapon_tier: int = Field(..., ge=0, le=5)
    ammo_id: str | None = None
    use_off_hand: bool = False
    defender_is_unarmored: bool
    defender_unarmored_tier: int = Field(default=0, ge=0, le=5)
    defender_agility_tier: int = Field(default=0, ge=0, le=5)


class ResolveAttackResponse(BaseModel):
    hit: bool
    critical_hit: bool
    fumble: bool
    tied: bool
    roll_1: CombatRoll1Result
    roll_2: CombatRoll2Result | None
    damage: CombatDamageResult
    rebound: CombatReboundResult | None = None
    events: list[str]


# ---------------------------------------------------------------------------
# Location models
# ---------------------------------------------------------------------------

class LocationData(BaseModel):
    """Shape of the JSONB data column in the locations table."""
    id:          str
    name:        str
    type:        str        = "unknown"
    description: str        = ""
    tags:        list[str]  = Field(default_factory=list)
    connections: list[str]  = Field(default_factory=list)
    threat_level: int       = 0
    known_npcs:  list[str]  = Field(default_factory=list)
    discovered:  bool       = True


class LocationResponse(BaseModel):
    id:         str
    name:       str
    data:       LocationData
    updated_at: datetime | None = None


class ConnectionInfo(BaseModel):
    to_id:     str
    traversal: str | None = None
    distance:  str | None = None


class ConnectionsResponse(BaseModel):
    from_id:     str
    connections: list[ConnectionInfo]


# ---------------------------------------------------------------------------
# Scene context models (derived, non-persistent)
# ---------------------------------------------------------------------------

class SceneLocationSummary(BaseModel):
    """Compact location payload for turn narration."""
    id: str
    name: str
    type: str = "unknown"
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class SceneRelevantCharacterState(BaseModel):
    """Narration-relevant subset of character/world state."""
    name: str
    hp: HP
    status_effects: list[str] = Field(default_factory=list)
    survival: SurvivalState = Field(default_factory=SurvivalState)
    active_companions: list[str] = Field(default_factory=list)


class SceneContext(BaseModel):
    """Derived GPT-facing scene payload assembled from full state + location + log."""
    session_id: str
    location_summary: SceneLocationSummary
    visible_entities: list[str] = Field(default_factory=list)
    immediate_stakes: list[str] = Field(default_factory=list)
    relevant_character_state: SceneRelevantCharacterState
    recent_log: list[str] = Field(default_factory=list)
    active_threats: list[str] = Field(default_factory=list)
    available_opportunities: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Options models
# ---------------------------------------------------------------------------

class AncestryTrait(BaseModel):
    name: str
    type: str
    description: str
    mechanical_note: str | None = None
    application_tag: str | None = None
    roll_domain: str | None = None
    usage: str | None = None
    fatigue: str | None = None


class AncestryOption(BaseModel):
    index:          str
    name:           str
    description:    str = ""
    primary_domain: str | None = None   # e.g. "power" for Orc, None for Human
    domains:        dict[str, int]      # all 7 domain base scores
    traits:         list[AncestryTrait] = Field(default_factory=list)


class CultureOption(BaseModel):
    index: str
    name: str
    description: str = ""
    domain_bonuses: dict[str, int] = Field(default_factory=dict)
    knowledge_tags: dict[str, TagTier] = Field(default_factory=dict)
    application_tags: dict[str, TagTier] = Field(default_factory=dict)
    field_tags: dict[str, TagTier] = Field(default_factory=dict)


class FocusOption(BaseModel):
    index:            str
    name:             str
    description:      str             = ""
    knowledge_tags:   dict[str, TagTier] = Field(default_factory=dict)   # tag name → starting tier
    application_tags: dict[str, TagTier] = Field(default_factory=dict)   # tag name → starting tier
    field_tags:       dict[str, TagTier] = Field(default_factory=dict)
    signature_tag:    str | None      = None


class BackgroundOption(BaseModel):
    index:            str
    name:             str
    description:      str             = ""
    domain_bonuses:   dict[str, int]  = Field(default_factory=dict)
    knowledge_tags:   dict[str, TagTier] = Field(default_factory=dict)   # tag name → starting tier
    application_tags: dict[str, TagTier] = Field(default_factory=dict)   # tag name → starting tier
    field_tags:       dict[str, TagTier] = Field(default_factory=dict)


class MechanicalEffect(BaseModel):
    """
    Structured mechanical effect on a magical or special item. Distinct from
    narrative_effects (prose-only); this field is read directly by the
    narrator to compute roll modifiers and adjudicate item interactions.

    The rules system for tier-driven magical effects is not yet authored.
    Until then, this field is the canonical source for how a specific
    magical item modifies play.
    """
    model_config = ConfigDict(extra="forbid")

    trigger: str = Field(
        description="Required conditions for the effect to be active. Plain prose. Example: 'hood up, wearer still'."
    )
    modifier: str = Field(
        description="The mechanical adjustment, in target-bonus form. Example: '+10 target', '-5 target', '+1 damage step'."
    )
    applies_to: str = Field(
        description="Categories of checks or situations the effect applies to. Plain prose. Example: 'checks where magical awareness, ward-sense, or entity perception is the primary failure risk'."
    )
    does_not_apply: str = Field(
        default="",
        description="Categories of checks or situations the effect explicitly does not cover. Plain prose. Helps the narrator avoid over-application. Example: 'ordinary sight/scent/hearing; untargeted area effects that do not require registering the wearer'."
    )


class ItemOption(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    category: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    roll_tag: str | None = None
    mechanical_effect: MechanicalEffect | None = None
    consumable: bool = False
    charges: int | None = None
    rarity: str = "common"
    value_cd: int = 0
    effects: list[str] = Field(default_factory=list)


class CatalogItemDetailResponse(BaseModel):
    """Full catalog item, as authored. Shape matches api.items.Item."""
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    description: str = ""
    tier: str | None = None
    magic_field: str | None = None
    mechanical_effect: MechanicalEffect | None = None


class KnowledgeGroupEntry(BaseModel):
    index: str
    name: str
    primary_domain: str
    secondary_domain: str | None = None
    domain_note: str | None = None
    description: str
    examples: list[str] = Field(default_factory=list)
    kind: str


class MagicFieldEntry(BaseModel):
    index: str
    name: str
    primary_domain: str
    secondary_domain: str | None = None
    domain_note: str | None = None
    description: str
    examples: list[str] = Field(default_factory=list)
    kind: str


class ApplicationEntry(BaseModel):
    index: str
    name: str
    group: str
    primary_domain: str
    domain_note: str | None = None
    description: str
    examples: list[str] = Field(default_factory=list)


class NpcRegistryEntry(BaseModel):
    """A single NPC registry entry loaded from data/npcs/."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    name: str
    tier: int
    age: int | None = None
    house_affiliation: str | None = None
    current_location: str | None = None
    status: str | None = None
    disposition: str | None = None
    role_summary: str | None = None
    voice: str | None = None
    narrative_anchors: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    description: str = ""
    scene_guidance: str = ""
    role_scope: str | None = None
    typical_context: str | None = None
    register_text: str | None = Field(default=None, alias="register", serialization_alias="register")
    authority_scope: str | None = None
    common_scene_functions: list[str] = Field(default_factory=list)
    generation_guidance: str | None = None


class NpcRegistryResponse(BaseModel):
    """Response for GET /npcs."""
    model_config = ConfigDict(extra="allow")

    entries: list[NpcRegistryEntry]
    count: int = 0


class OptionsResponse(BaseModel):
    """
    Response for GET /options — creation-scope enumeration.

    Only ancestries, cultures, focus archetypes, and backgrounds live here.
    Runtime catalogs are served by /catalog/items, /catalog/creatures,
    /catalog/vocab.
    """
    ancestries:  list[AncestryOption]
    cultures:    list[CultureOption]
    focus:       list[FocusOption]
    backgrounds: list[BackgroundOption]


class ItemCatalogResponse(BaseModel):
    """Response for GET /catalog/items."""
    mundane_items: list[ItemOption] = Field(default_factory=list)
    magical_items: list[ItemOption] = Field(default_factory=list)
    apparel_items: list[ItemOption] = Field(default_factory=list)
    weapon_items: list[ItemOption] = Field(default_factory=list)
    armor_items: list[ItemOption] = Field(default_factory=list)
    ammunition_items: list[ItemOption] = Field(default_factory=list)


class CreatureCatalogResponse(BaseModel):
    """Response for GET /catalog/creatures."""
    creature_catalog: list[dict] = Field(default_factory=list)
    exceptional_catalog: list[dict] = Field(default_factory=list)
 

class CompanionVocabResponse(BaseModel):
    """Response for GET /catalog/vocab."""
    natural_abilities: list[dict] = Field(default_factory=list)
    learned_commands: list[dict] = Field(default_factory=list)
    tactical_roles: list[dict] = Field(default_factory=list)
    training_levels: list[str] = Field(default_factory=list)
    bond_levels: list[str] = Field(default_factory=list)
    age_categories: list[str] = Field(default_factory=list)
    creature_sizes: list[str] = Field(default_factory=list)
    carrying_capacities: list[str] = Field(default_factory=list)
    movement_modes: list[str] = Field(default_factory=list)
    natural_weapons: list[str] = Field(default_factory=list)
    sapience_levels: list[str] = Field(default_factory=list)
    communication_levels: list[str] = Field(default_factory=list)
    autonomy_levels: list[str] = Field(default_factory=list)


class TagsResponse(BaseModel):
    knowledge_groups: list[KnowledgeGroupEntry]
    magic_fields: list[MagicFieldEntry]
    applications: list[ApplicationEntry]


# Resolve companion forward references for modules/tests that import route
# modules directly without going through api.main.
from api import companions as _companions  # noqa: E402,F401
