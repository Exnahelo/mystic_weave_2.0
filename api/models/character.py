"""
character.py — Character record models for Mystic Weave 5.0.0.

Hosts the Pydantic models for character identity, equipment, advancement,
narrative state, and the v5 nested knowledge/magic record shape introduced
in Brief 13. Knowledge groups visibly contain their applications and magic
fields visibly contain their spells, with parent-tier caps enforced at
model construction.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Shared aliases
# ---------------------------------------------------------------------------

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
# Nested knowledge / magic records (v5)
# ---------------------------------------------------------------------------

class KnowledgeGroupRecord(BaseModel):
    """A knowledge group held by a character, with its applications nested.

    The group's tier acts as a structural cap on each nested application's
    tier; advancement that would push an application above its parent group
    fails at model construction.
    """
    model_config = ConfigDict(extra="forbid")

    tier: int = Field(ge=1, le=5)
    applications: dict[str, int] = Field(default_factory=dict)

    @field_validator("applications")
    @classmethod
    def application_tiers_in_range(cls, v: dict[str, int]) -> dict[str, int]:
        for app, tier in v.items():
            if not (1 <= tier <= 5):
                raise ValueError(f"application '{app}' tier {tier} out of range [1,5]")
        return v

    @model_validator(mode="after")
    def applications_capped_by_group_tier(self) -> KnowledgeGroupRecord:
        for app, app_tier in self.applications.items():
            if app_tier > self.tier:
                raise ValueError(
                    f"application '{app}' tier {app_tier} exceeds parent group tier {self.tier}"
                )
        return self


class KnowledgeGroupDelta(BaseModel):
    """Partial knowledge group update for delta payloads.

    Both fields optional: a delta can advance the parent tier alone, push
    new application tiers alone, or do both. Parent-cap enforcement runs
    at full-record validation post-merge, not on the delta itself.
    """
    model_config = ConfigDict(extra="forbid")

    tier: int | None = Field(default=None, ge=1, le=5)
    applications: dict[str, int] | None = None

    @field_validator("applications")
    @classmethod
    def application_tiers_in_range(cls, v: dict[str, int] | None) -> dict[str, int] | None:
        if v is None:
            return v
        for app, tier in v.items():
            if not (1 <= tier <= 5):
                raise ValueError(f"application '{app}' tier {tier} out of range [1,5]")
        return v


class MagicFieldRecord(BaseModel):
    """A magic field held by a character, with its known spells nested.

    The field's tier acts as a structural cap on each spell's per-character
    mastery tier; advancement that would push a spell above its parent
    field fails at model construction.
    """
    model_config = ConfigDict(extra="forbid")

    tier: int = Field(ge=1, le=5)
    spells: dict[str, int] = Field(default_factory=dict)

    @field_validator("spells")
    @classmethod
    def spell_tiers_in_range(cls, v: dict[str, int]) -> dict[str, int]:
        for spell, tier in v.items():
            if not (1 <= tier <= 5):
                raise ValueError(f"spell '{spell}' tier {tier} out of range [1,5]")
        return v

    @model_validator(mode="after")
    def spells_capped_by_field_tier(self) -> MagicFieldRecord:
        for spell, spell_tier in self.spells.items():
            if spell_tier > self.tier:
                raise ValueError(
                    f"spell '{spell}' tier {spell_tier} exceeds parent field tier {self.tier}"
                )
        return self


class MagicFieldDelta(BaseModel):
    """Partial magic field update for delta payloads.

    Both fields optional. Parent-cap enforcement runs at full-record
    validation post-merge.
    """
    model_config = ConfigDict(extra="forbid")

    tier: int | None = Field(default=None, ge=1, le=5)
    spells: dict[str, int] | None = None

    @field_validator("spells")
    @classmethod
    def spell_tiers_in_range(cls, v: dict[str, int] | None) -> dict[str, int] | None:
        if v is None:
            return v
        for spell, tier in v.items():
            if not (1 <= tier <= 5):
                raise ValueError(f"spell '{spell}' tier {tier} out of range [1,5]")
        return v


# ---------------------------------------------------------------------------
# Character model
# ---------------------------------------------------------------------------

class CharacterModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Core identity
    name:           str
    ancestry:       str   # e.g. "human", "drakari"
    culture:        str
    focus:          str   # e.g. "devoted", "stalker"
    background:     str   # e.g. "soldier", "acolyte"
    hp:             HP
    domains:        DomainScores
    # v5 nested shape: groups visibly contain their applications, fields contain their spells
    knowledge:      dict[str, KnowledgeGroupRecord] = Field(default_factory=dict)
    magic:          dict[str, MagicFieldRecord]     = Field(default_factory=dict)
    status_effects: list[str]      = Field(default_factory=list)
    notes:          str            = ""

    # v3.1.0+
    identity:       Identity       = Field(default_factory=Identity)
    equipment:      Equipment      = Field(default_factory=Equipment)
    reputation:     list[ReputationEntry] = Field(default_factory=list)
    advancement:    AdvancementState = Field(default_factory=AdvancementState)


# ---------------------------------------------------------------------------
# Character delta
# ---------------------------------------------------------------------------

class CharacterStateDelta(BaseModel):
    """
    Typed partial character update for extraction-driven turn commits.

    v5 shape: knowledge and magic deltas carry partial nested records. A
    partial knowledge update sends the full group record (or a subset of
    its fields); the merge layer deep-merges it onto the stored record.

    Note on `advancement`: the delta endpoint recomputes advancement
    authoritatively from existing state and tag-tier transitions. Any
    client-supplied `advancement` value is replaced server-side. The field
    remains on the schema for forward compatibility and round-trip safety,
    but its content has no effect on persisted state.
    """
    model_config = ConfigDict(extra="forbid")

    hp: HP | None = None
    domains: dict[str, int] | None = None
    knowledge: dict[str, KnowledgeGroupDelta] | None = None
    magic: dict[str, MagicFieldDelta] | None = None
    status_effects: list[str] | None = None
    notes: str | None = None
    equipment: EquipmentDelta | None = None
    reputation: list[ReputationEntry] | None = None
    advancement: AdvancementState | None = None

    def has_updates(self) -> bool:
        return any(v is not None for v in self.model_dump(exclude_none=False).values())
