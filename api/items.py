"""
Item catalog schema for Mystic Weave 2.0.

Flat schema: every field at the top level. Required fields gated by category.
Vocabulary cross-references validated against registries at catalog-load time
(see scripts/validate_catalog.py).

Model serves both:
  - Narrator GPT (prose: description, narrative_effects; categorical: tags)
  - Combat backend (numeric: base_damage, armor_floor, armor_ceiling)
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------- closed vocabularies (Literal types; registries are runtime truth) ----------

ItemCategory = Literal["weapon", "armor", "shield", "ammunition", "apparel", "gear"]

Rarity = Literal["common", "uncommon", "rare", "very-rare", "legendary", "unique"]

Legality = Literal["open", "restricted", "contraband"]

WealthTierFloor = Literal["destitute", "modest", "comfortable", "wealthy", "affluent"]

ToolRole = Literal["permission", "difficulty-shift"]

AmmoClass = Literal["standard", "special"]

ItemTier = Literal["T0", "T1", "T2", "T3", "T4", "T5"]

WeaponHands = Literal["one", "two", "versatile"]


# ---------- helper sub-models ----------

class WeaponHandedness(BaseModel):
    """How a weapon is wielded. Two-handed weapons cannot be paired off-hand."""

    model_config = ConfigDict(extra="forbid")
    hands: WeaponHands


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


# ---------- top-level Item ----------

class Item(BaseModel):
    """
    Canonical item shape for Mystic Weave. Source of truth for all item data.
    """

    model_config = ConfigDict(extra="forbid")

    # ---------- identity ----------
    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    name: str
    category: ItemCategory
    subcategory: Optional[str] = None
    schema_version: Literal[1] = 1

    # ---------- prose (GPT-facing) ----------
    description: str = Field(max_length=500)
    narrative_effects: list[str] = Field(default_factory=list)

    # ---------- categorical descriptors ----------
    tags: list[str] = Field(default_factory=list)
    roll_tag: Optional[str] = None

    # ---------- worldness / economy ----------
    rarity: Rarity = "common"
    legality: Legality = "open"
    value_cd: int = Field(ge=0)
    wealth_tier_floor: Optional[WealthTierFloor] = None
    market_tags: list[str] = Field(default_factory=list)

    # ---------- state / consumption ----------
    consumable: bool = False
    charges_max: Optional[int] = Field(default=None, ge=1)

    # ---------- combat dispatch (required by category) ----------
    knowledge_tag: Optional[str] = None
    application_tag: Optional[str] = None

    # ---------- weapon-specific ----------
    base_damage: Optional[int] = Field(default=None, ge=0)
    weapon_handedness: Optional[WeaponHandedness] = None

    # ---------- armor/shield-specific ----------
    armor_floor: Optional[int] = Field(default=None, ge=0)
    armor_ceiling: Optional[int] = Field(default=None, ge=0)

    # ---------- ammunition-specific ----------
    ammo_class: Optional[AmmoClass] = None
    used_with: list[str] = Field(default_factory=list)
    bundle_size: Optional[int] = Field(default=None, ge=1)
    damage_modifier: Optional[int] = None
    recoverable: bool = True
    special_effect_tag: Optional[str] = None

    # ---------- magical-specific ----------
    tier: Optional[ItemTier] = None
    magic_field: Optional[str] = None
    mechanical_effect: Optional[MechanicalEffect] = None

    # ---------- tool-specific ----------
    tool_role: Optional[ToolRole] = None

    # ---------- validation ----------
    @model_validator(mode="after")
    def _enforce_category_requirements(self) -> "Item":
        if self.category == "weapon":
            if self.base_damage is None:
                raise ValueError("category=weapon requires base_damage")
            if self.knowledge_tag is None or self.application_tag is None:
                raise ValueError("category=weapon requires knowledge_tag and application_tag")

        if self.category in ("armor", "shield"):
            if self.armor_floor is None or self.armor_ceiling is None:
                raise ValueError(
                    f"category={self.category} requires armor_floor and armor_ceiling"
                )
            if self.armor_floor > self.armor_ceiling:
                raise ValueError("armor_floor must be <= armor_ceiling")
            if self.knowledge_tag is None or self.application_tag is None:
                raise ValueError(
                    f"category={self.category} requires knowledge_tag and application_tag"
                )

        if self.category == "ammunition":
            if self.ammo_class is None:
                raise ValueError("category=ammunition requires ammo_class")
            if not self.used_with:
                raise ValueError("category=ammunition requires non-empty used_with")
            if self.damage_modifier is None:
                raise ValueError(
                    "category=ammunition requires damage_modifier (use 0 for standard)"
                )
            if self.knowledge_tag is None or self.application_tag is None:
                raise ValueError(
                    "category=ammunition requires knowledge_tag and application_tag"
                )

        if self.category in ("apparel", "gear"):
            non_combat_violations = []
            if self.base_damage is not None:
                non_combat_violations.append("base_damage")
            if self.armor_floor is not None or self.armor_ceiling is not None:
                non_combat_violations.append("armor_floor/armor_ceiling")
            if self.ammo_class is not None:
                non_combat_violations.append("ammo_class")
            if non_combat_violations:
                raise ValueError(
                    f"category={self.category} must not have combat fields: "
                    f"{', '.join(non_combat_violations)}"
                )

        # Magical fields
        if self.tier is not None and self.tier != "T0":
            if self.magic_field is None:
                raise ValueError(f"tier={self.tier} requires magic_field (T0 may omit it)")

        if self.magic_field is not None and self.tier is None:
            raise ValueError("magic_field set without tier; declare T0-T5")

        # Charges
        if self.charges_max is not None and not self.consumable:
            raise ValueError("charges_max set requires consumable=True")

        # Magical-unarmored rule:
        # An armor-slot item with application_tag=unarmored and armor_floor > 0
        # must be magical (tier T1+ and magic_field set). Mundane unarmored
        # cannot grant armor; only magical garments can armor while preserving
        # martial_arts evasion.
        if (
            self.category in ("armor", "shield")
            and self.application_tag == "unarmored"
            and self.armor_floor is not None
            and self.armor_floor > 0
        ):
            if self.tier is None or self.tier == "T0":
                raise ValueError(
                    "application_tag=unarmored with armor_floor > 0 requires tier T1+ "
                    "(magical unarmored)"
                )
            if self.magic_field is None:
                raise ValueError(
                    "application_tag=unarmored with armor_floor > 0 requires magic_field"
                )

        return self


# ---------- derived index helpers (used by routes/loaders) ----------

def derive_indexes(item: Item) -> dict:
    """Compute boolean flags from an Item for fast filtering."""
    return {
        "is_weapon": item.category == "weapon",
        "is_armor": item.category == "armor",
        "is_shield": item.category == "shield",
        "is_ammunition": item.category == "ammunition",
        "is_apparel": item.category == "apparel",
        "is_gear": item.category == "gear",
        "is_magical": item.tier is not None and item.tier != "T0",
        "is_mundane": item.tier is None,
        "has_charges": item.charges_max is not None,
        "is_consumable": item.consumable,
    }
