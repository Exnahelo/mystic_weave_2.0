from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

if TYPE_CHECKING:
    from api.models import Alignment, DomainScores, Equipment, HP, Identity, ReputationEntry


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

TacticalRole = Literal["mount", "pack", "scout", "guard", "hunter", "companion"]
TrainingLevel = Literal["untrained", "basic", "trained", "expert"]
BondLevel = Literal["wary", "accepting", "bonded", "devoted"]
AgeCategory = Literal["juvenile", "young_adult", "adult", "mature", "elder"]
CreatureSize = Literal["tiny", "small", "medium", "large", "huge"]
CarryingCapacity = Literal["none", "small", "medium", "large"]
MovementMode = Literal["walk", "fly", "swim", "climb", "burrow"]
NaturalWeapon = Literal["bite", "claw", "hoof", "tail_slam", "breath", "sting", "none"]

Sapience = Literal["partial", "full"]
Communication = Literal["instinctive", "symbolic", "speech"]
Autonomy = Literal["limited", "moderate", "high"]


class CreatureDomains(BaseModel):
    model_config = ConfigDict(extra="forbid")

    physical: int = Field(ge=25, le=60)
    instinct: int = Field(ge=25, le=60)
    composure: int = Field(ge=25, le=60)


class BondLinks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary: str
    secondary: Optional[str] = None

    @field_validator("primary")
    @classmethod
    def primary_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("primary must be a non-empty string")
        return value


class CreatureNarrative(BaseModel):
    """
    Optional narrative block for creatures with individual story-weight
    content. Nullable on the parent models. Catalog-templated creatures
    without individual history leave this as None.

    Used on CreatureCompanion and ExceptionalCompanion. For
    ExceptionalCompanion with sapience=full, the fields here may be
    redundant with motivations/alignment — that's a content concern,
    not a schema one.
    """

    model_config = ConfigDict(extra="forbid")

    origin: Optional[str] = None
    wound: Optional[str] = None
    quirks: list[str] = Field(default_factory=list)
    flaws: list[str] = Field(default_factory=list)
    bonds: list[str] = Field(default_factory=list)
    drives: list[str] = Field(default_factory=list)


class CompanionEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    companion: "Companion"


class ArchivedCompanionEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    companion: "Companion"
    archived_at: str


class ExceptionalProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sapience: Sapience
    communication: Communication
    autonomy: Autonomy


class CreatureCompanion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    species: str
    subtype: Optional[str] = None
    size: CreatureSize
    size_note: Optional[str] = None
    age_category: AgeCategory

    tactical_roles: list[TacticalRole] = Field(min_length=1)
    training_level: TrainingLevel
    bond_level: BondLevel

    natural_abilities: list[str] = Field(default_factory=list)
    learned_commands: list[str] = Field(default_factory=list)
    command_notes: str = ""

    movement_modes: list[MovementMode] = Field(default_factory=lambda: ["walk"])
    natural_weapons: list[NaturalWeapon] = Field(default_factory=lambda: ["none"])
    carrying_capacity: CarryingCapacity = "none"

    hp: "HP"
    domains: CreatureDomains
    temperament: str = ""

    bond_links: BondLinks
    narrative: Optional[CreatureNarrative] = None


class SapientCompanion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    ancestry: str
    culture: str
    background: str
    focus: str

    hp: "HP"
    domains: "DomainScores"
    knowledge: dict[str, int] = Field(default_factory=dict)
    application: dict[str, int] = Field(default_factory=dict)

    identity: "Identity"
    equipment: "Equipment"
    reputation: list["ReputationEntry"] = Field(default_factory=list)

    bond_links: BondLinks
    known_languages: list[str] = Field(default_factory=list)
    companions: list[CreatureCompanion] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_nesting(self) -> "SapientCompanion":
        for companion in self.companions:
            if not isinstance(companion, CreatureCompanion):
                raise ValueError(
                    "SapientCompanion.companions may contain only "
                    "CreatureCompanion instances"
                )
        return self


class ExceptionalCompanion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    species: str
    subtype: Optional[str] = None
    size: CreatureSize
    size_note: Optional[str] = None
    age_category: AgeCategory

    tactical_roles: list[TacticalRole] = Field(min_length=1)
    training_level: TrainingLevel
    bond_level: BondLevel

    natural_abilities: list[str] = Field(default_factory=list)
    learned_commands: list[str] = Field(default_factory=list)
    command_notes: str = ""

    movement_modes: list[MovementMode] = Field(default_factory=lambda: ["walk"])
    natural_weapons: list[NaturalWeapon] = Field(default_factory=lambda: ["none"])
    carrying_capacity: CarryingCapacity = "none"

    hp: "HP"
    temperament: str = ""

    bond_links: BondLinks
    narrative: Optional[CreatureNarrative] = None

    exceptional_profile: ExceptionalProfile
    motivations: list[str]
    domains: Union[CreatureDomains, "DomainScores"]
    knowledge: Optional[dict[str, int]] = None
    application: Optional[dict[str, int]] = None
    alignment: Optional["Alignment"] = None
    supernatural_traits: list[str] = Field(default_factory=list)
    known_languages: list[str] = Field(default_factory=list)
    tier_history: list[dict] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_sapience_requirements(self) -> "ExceptionalCompanion":
        sapience = self.exceptional_profile.sapience

        if sapience == "full":
            if not isinstance(self.domains, core_models.DomainScores):
                raise ValueError(
                    "ExceptionalCompanion with sapience=full requires "
                    "full DomainScores, not CreatureDomains"
                )
            if self.knowledge is None:
                raise ValueError(
                    "ExceptionalCompanion with sapience=full requires knowledge"
                )
            if self.application is None:
                raise ValueError(
                    "ExceptionalCompanion with sapience=full requires application"
                )
            if self.alignment is None:
                raise ValueError(
                    "ExceptionalCompanion with sapience=full requires alignment"
                )

        if sapience == "partial":
            if not isinstance(self.domains, CreatureDomains):
                raise ValueError(
                    "ExceptionalCompanion with sapience=partial requires "
                    "simplified CreatureDomains, not DomainScores"
                )

        if self.exceptional_profile.communication != "speech" and self.known_languages:
            raise ValueError(
                "known_languages should only be populated when communication=speech"
            )

        return self


Companion = Union[SapientCompanion, CreatureCompanion, ExceptionalCompanion]


def generate_companion_id(
    handler_id: str,
    subspecies: str,
    existing_ids: set[str],
) -> str:
    """
    Generate a readable slug ID for a new companion.

    Format: <handler_id>_<subspecies>, with _2, _3, etc. suffix on
    collision against existing_ids in the same session.
    """
    base = f"{handler_id}_{subspecies}"
    if base not in existing_ids:
        return base
    n = 2
    while f"{base}_{n}" in existing_ids:
        n += 1
    return f"{base}_{n}"


def derive_sapient_slug(name: str) -> str:
    """Derive a snake_case slug from a sapient companion name."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return slug


from api import models as core_models

_CORE_TYPES = {
    "ArchivedCompanionEnvelope": ArchivedCompanionEnvelope,
    "Alignment": core_models.Alignment,
    "CompanionEnvelope": CompanionEnvelope,
    "DomainScores": core_models.DomainScores,
    "Equipment": core_models.Equipment,
    "HP": core_models.HP,
    "Identity": core_models.Identity,
    "ReputationEntry": core_models.ReputationEntry,
    "Companion": Companion,
}

SapientCompanion.model_rebuild(_types_namespace=_CORE_TYPES)
CreatureCompanion.model_rebuild(_types_namespace=_CORE_TYPES)
ExceptionalCompanion.model_rebuild(_types_namespace=_CORE_TYPES)
CompanionEnvelope.model_rebuild(_types_namespace=_CORE_TYPES)
ArchivedCompanionEnvelope.model_rebuild(_types_namespace=_CORE_TYPES)

core_models.WorldModel.model_rebuild(
    _types_namespace={
        "ArchivedCompanionEnvelope": ArchivedCompanionEnvelope,
        "Companion": Companion,
        "CompanionEnvelope": CompanionEnvelope,
    }
)
core_models.WorldStateDelta.model_rebuild(
    _types_namespace={
        "ArchivedCompanionEnvelope": ArchivedCompanionEnvelope,
        "Companion": Companion,
        "CompanionEnvelope": CompanionEnvelope,
    }
)
core_models.NewSessionRequest.model_rebuild(
    _types_namespace={
        "ArchivedCompanionEnvelope": ArchivedCompanionEnvelope,
        "Companion": Companion,
        "CompanionEnvelope": CompanionEnvelope,
    }
)