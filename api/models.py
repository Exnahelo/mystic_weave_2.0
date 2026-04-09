"""
models.py — Pydantic v2 models for all game entities.

All models use Pydantic v2 syntax. Designed for Mystic Weave 2.0:
d100 roll-under, domain scores, knowledge/application competency tiers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    power: int
    agility: int
    perception: int
    endurance: int
    intellect: int
    will: int
    presence: int

    @field_validator("power", "agility", "perception", "endurance",
                     "intellect", "will", "presence")
    @classmethod
    def score_in_range(cls, v: int) -> int:
        if not (1 <= v <= 60):
            raise ValueError("domain score must be between 1 and 60")
        return v


class CharacterModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    species: str                              # e.g. "human", "dragonborn"
    focus: str                                # e.g. "devoted", "stalker"
    background: str                           # e.g. "soldier", "acolyte"
    level: int = 1
    hp: HP
    domains: DomainScores
    knowledge: dict[str, int] = {}            # tag name → tier (1–5)
    application: dict[str, int] = {}          # tag name → tier (1–5)
    status_effects: list[str] = []
    notes: str = ""

    @field_validator("level")
    @classmethod
    def level_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("level must be at least 1")
        return v


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

class WorldModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: str
    threat: str
    goal: str
    turn: int = 1

    @field_validator("turn")
    @classmethod
    def turn_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("turn must be at least 1")
        return v


# ---------------------------------------------------------------------------
# State request / response models
# ---------------------------------------------------------------------------

class SaveStateRequest(BaseModel):
    """Body for POST /state/{session_id}"""
    character: CharacterModel
    world: WorldModel
    log_entry: str


class GameStateResponse(BaseModel):
    """Response for GET /state/{session_id}"""
    session_id: str
    character: dict[str, Any]
    world: dict[str, Any]
    log: list[str]
    updated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Session models
# ---------------------------------------------------------------------------

class AdjustmentPoints(BaseModel):
    """Player's +5 domain adjustment pool at creation. Max +3 per domain."""
    power: int = 0
    agility: int = 0
    perception: int = 0
    endurance: int = 0
    intellect: int = 0
    will: int = 0
    presence: int = 0

    @field_validator("power", "agility", "perception", "endurance",
                     "intellect", "will", "presence")
    @classmethod
    def per_domain_cap(cls, v: int) -> int:
        if v < 0:
            raise ValueError("adjustment points cannot be negative")
        if v > 3:
            raise ValueError("max +3 adjustment per domain")
        return v

    @model_validator(mode="after")
    def total_pool_cap(self) -> AdjustmentPoints:
        total = (self.power + self.agility + self.perception +
                 self.endurance + self.intellect + self.will + self.presence)
        if total > 5:
            raise ValueError(f"Adjustment pool is 5 points max. Got {total}.")
        return self


class NewSessionRequest(BaseModel):
    """Body for POST /session/new"""
    character_name: str
    species: str
    focus: str
    background: str
    adjustment_points: AdjustmentPoints = AdjustmentPoints()
    starting_location: str = "unknown"
    goal: str = "survive"
    threat: str = "unknown"


class NewSessionResponse(BaseModel):
    session_id: str
    character: dict[str, Any]
    world: dict[str, Any]


# ---------------------------------------------------------------------------
# Character creation models
# ---------------------------------------------------------------------------

class CreateCharacterRequest(BaseModel):
    """Body for POST /character/create — seeds character from game system data."""
    session_id: str
    name: str
    species: str
    focus: str
    background: str
    adjustment_points: AdjustmentPoints = AdjustmentPoints()


class CreateCharacterResponse(BaseModel):
    session_id: str
    character: dict[str, Any]


# ---------------------------------------------------------------------------
# Dice roll models
# ---------------------------------------------------------------------------

class RollRequest(BaseModel):
    """Body for POST /roll — d100 roll-under resolution."""
    target: int  # assembled target number: domain + knowledge tier + application tier + difficulty modifier

    @field_validator("target")
    @classmethod
    def target_in_range(cls, v: int) -> int:
        if v < 1:
            return 1   # floor at 1 — always at least a crit success chance
        if v > 99:
            return 99  # cap at 99 — always at least a crit failure chance
        return v


class RollResponse(BaseModel):
    roll: int                              # raw d100 result (1–100)
    target: int                            # the target number that was sent
    success: bool                          # roll <= target
    margin: int                            # target - roll (positive = succeeded by, negative = failed by)
    degree: str                            # "critical_success", "strong_success", "success", "partial_failure", "failure", "critical_failure"
    critical_success: bool = False         # roll == 1
    critical_failure: bool = False         # roll == 100


# ---------------------------------------------------------------------------
# Location models
# ---------------------------------------------------------------------------

class LocationData(BaseModel):
    """Shape of the JSONB data column in the locations table."""
    id: str
    name: str
    type: str = "unknown"
    description: str = ""
    tags: list[str] = []
    connections: list[str] = []
    threat_level: int = 0
    known_npcs: list[str] = []
    discovered: bool = True


class LocationResponse(BaseModel):
    id: str
    name: str
    data: dict[str, Any]
    updated_at: datetime | None = None


class ConnectionInfo(BaseModel):
    to_id: str
    traversal: str | None = None
    distance: str | None = None


class ConnectionsResponse(BaseModel):
    from_id: str
    connections: list[ConnectionInfo]


# ---------------------------------------------------------------------------
# Options models
# ---------------------------------------------------------------------------

class SpeciesOption(BaseModel):
    index: str
    name: str
    primary_domain: str | None = None      # e.g. "power" for Orc, None for Human
    domains: dict[str, int]                # all 7 domain base scores


class FocusOption(BaseModel):
    index: str
    name: str
    description: str = ""
    knowledge_tags: dict[str, int] = {}    # tag name → starting tier
    application_tags: dict[str, int] = {}  # tag name → starting tier


class BackgroundOption(BaseModel):
    index: str
    name: str
    description: str = ""
    knowledge_tags: dict[str, int] = {}    # tag name → starting tier
    application_tags: dict[str, int] = {}  # tag name → starting tier


class OptionsResponse(BaseModel):
    """Response for GET /options — all supported species, focus archetypes, backgrounds."""
    species: list[SpeciesOption]
    focus: list[FocusOption]
    backgrounds: list[BackgroundOption]
