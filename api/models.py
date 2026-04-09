"""
models.py — Pydantic v2 models for all game entities.

All models use Pydantic v2 syntax. Derived from BRIEFING.md game state spec.
Updated for 2024 D&D rules: species replaces race, backgrounds added.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Character sub-models
# ---------------------------------------------------------------------------

class HP(BaseModel):
    current: int
    max: int

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


class AbilityScores(BaseModel):
    STR: int
    DEX: int
    CON: int
    INT: int
    WIS: int
    CHA: int

    @field_validator("STR", "DEX", "CON", "INT", "WIS", "CHA")
    @classmethod
    def score_in_range(cls, v: int) -> int:
        if not (1 <= v <= 30):
            raise ValueError("ability score must be between 1 and 30")
        return v


class CharacterModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    class_: str = Field(alias="class")   # SRD index string e.g. "ranger"
    species: str                          # SRD species index e.g. "human"
    subspecies: str | None = None         # SRD subspecies index e.g. "elven-lineage-high-elf"
    subclass: str | None = None           # SRD subclass index e.g. "hunter"
    background: str | None = None         # SRD background index e.g. "soldier"
    feat: str | None = None              # Starting feat from background e.g. "alert"
    feat_choices: dict[str, Any] = {}    # Subchoices for feats that require them e.g. {"skilled": ["athletics", "arcana", "nature"]}
    biography: dict[str, Any] = {}       # Character identity: origin, house, motivation, tensions
    level: int = 1
    hp: HP
    hit_die: str                          # e.g. "d10"
    ability_scores: AbilityScores
    proficiencies: list[str]
    tool_proficiencies: list[str] = []    # e.g. ["calligraphers-supplies"]
    skills: list[str]
    languages: list[str] = []             # e.g. ["common", "elvish"]
    alignment: str | None = None          # e.g. "lawful-good"
    faith: str | None = None              # any deity, pantheon, or none
    lifestyle: str | None = None          # e.g. "modest", "poor", "comfortable"
    size: str = "Medium"                  # "Medium" or "Small" (player choice for some species)
    equipment: list[str] = []             # starting equipment item indices
    gold: int = 0                         # starting gold in GP
    weapon_masteries: list[str] = []      # chosen weapon mastery properties e.g. ["cleave", "vex"]
    known_spells: list[str] = []          # known spell indices e.g. ["fireball"]
    prepared_spells: list[str] = []       # prepared spell indices (for prepared casters)
    cantrips: list[str] = []              # known cantrip indices

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

class NewSessionRequest(BaseModel):
    """Body for POST /session/new — minimal seed data."""
    model_config = ConfigDict(populate_by_name=True)

    character_name: str
    class_: str = Field(alias="class")
    species: str
    subspecies: str | None = None
    subclass: str | None = None
    background: str | None = None
    ability_scores: AbilityScores
    ability_score_method: str = "manual"  # "manual", "point-buy", or "standard-array"
    skill_choices: list[str] = []
    # Origin choices
    primary_score: str | None = None      # Which of the 3 background scores gets +2. Requires secondary_score. If None, all three get +1.
    secondary_score: str | None = None    # Which of the remaining 2 background scores gets +1 (when primary_score is set).
    language_choices: list[str] = []      # Player-chosen languages (beyond species automatic languages)
    species_choices: dict[str, Any] = {}  # Species-specific choices: spellcasting_ability, keen_senses, origin_feat, size, etc.
    equipment_choice: str = "equipment"   # "equipment" or "gold" — which starting package to take
    alignment: str | None = None          # e.g. "lawful-good"
    faith: str | None = None              # any deity, pantheon, or none
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
    """Body for POST /character/create — seeds character from local SRD data."""
    model_config = ConfigDict(populate_by_name=True)

    session_id: str
    name: str
    class_: str = Field(alias="class")
    species: str
    subspecies: str | None = None
    subclass: str | None = None
    background: str | None = None
    ability_scores: AbilityScores
    ability_score_method: str = "manual"  # "manual", "point-buy", or "standard-array"
    skill_choices: list[str] = []  # additional player-chosen skills beyond background
    # Origin choices
    primary_score: str | None = None      # Which of the 3 background scores gets +2. Requires secondary_score. If None, all three get +1.
    secondary_score: str | None = None    # Which of the remaining 2 background scores gets +1 (when primary_score is set).
    language_choices: list[str] = []      # Player-chosen languages (beyond species automatic languages)
    species_choices: dict[str, Any] = {}  # Species-specific choices: spellcasting_ability, keen_senses, origin_feat, size, etc.
    equipment_choice: str = "equipment"   # "equipment" or "gold" — which starting package to take
    alignment: str | None = None          # e.g. "lawful-good"
    faith: str | None = None              # any deity, pantheon, or none


class CreateCharacterResponse(BaseModel):
    session_id: str
    character: dict[str, Any]
    skill_conflicts: list[str] = []  # Skills that duplicated background grants — GPT should prompt for replacements


# ---------------------------------------------------------------------------
# Dice roll models
# ---------------------------------------------------------------------------

class RollRequest(BaseModel):
    """Body for POST /roll"""
    dice: str = "1d20"
    ability: str  # e.g. "DEX"
    score: int    # the raw ability score value
    proficient: bool = False
    dc: int       # difficulty class to beat

    @field_validator("ability")
    @classmethod
    def ability_valid(cls, v: str) -> str:
        valid = {"STR", "DEX", "CON", "INT", "WIS", "CHA"}
        if v.upper() not in valid:
            raise ValueError(f"ability must be one of {valid}")
        return v.upper()

    @field_validator("score")
    @classmethod
    def score_in_range(cls, v: int) -> int:
        if not (1 <= v <= 30):
            raise ValueError("score must be between 1 and 30")
        return v


class RollResponse(BaseModel):
    roll: int
    modifier: int
    total: int
    success: bool
    margin: int   # total - dc (positive = beat by this much, negative = missed by this much)
    critical_success: bool = False
    critical_failure: bool = False


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

class SubclassRef(BaseModel):
    """Lightweight subclass reference embedded in ClassOption."""
    index: str
    name: str


class ClassOption(BaseModel):
    index: str
    name: str
    hit_die: str  # e.g. "d10"
    subclasses: list[SubclassRef] = []


class SubclassOption(BaseModel):
    index: str
    name: str
    class_index: str   # parent class index e.g. "ranger"
    description: str   # short description / summary


class SubspeciesRef(BaseModel):
    """Lightweight subspecies reference embedded in SpeciesOption."""
    index: str
    name: str


class SpeciesOption(BaseModel):
    index: str
    name: str
    speed: str   # e.g. "30"
    size: str    # e.g. "Medium"
    subspecies: list[SubspeciesRef] = []


class SubspeciesOption(BaseModel):
    index: str
    name: str
    species_index: str  # parent species index


class BackgroundOption(BaseModel):
    index: str
    name: str
    description: str = ""                   # background flavor text
    lifestyle: str = "modest"               # base lifestyle tier e.g. "poor", "modest", "comfortable", "wealthy"
    ability_scores: list[str]               # e.g. ["STR", "DEX", "CON"]
    ability_score_bonuses: str = ""         # e.g. "(+2 and +1) or (+1/+1/+1) across STR, DEX, CON"
    feat: str                               # starting feat index e.g. "alert"
    skill_proficiencies: list[str]          # e.g. ["athletics", "intimidation"]
    tool_proficiencies: list[str] = []      # fixed tool profs e.g. ["calligraphers-supplies"]
    tool_proficiency_choices: list[str] = []  # choice descriptions e.g. ["Choose one kind of Gaming Set"]


class LanguageOption(BaseModel):
    index: str
    name: str
    is_rare: bool = False
    note: str = ""


class OptionsResponse(BaseModel):
    """Response for GET /options — all supported classes, species, subspecies, backgrounds, subclasses, languages."""
    classes: list[ClassOption]
    species: list[SpeciesOption]
    subspecies: list[SubspeciesOption]
    backgrounds: list[BackgroundOption]
    subclasses: list[SubclassOption] = []
    languages: list[LanguageOption] = []
