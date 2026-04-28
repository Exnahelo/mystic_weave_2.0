"""
Item catalog schema for Mystic Weave 2.0.

Architecture:
    identity   -- what it is
    inventory  -- how it occupies/carries/stacks
    worldness  -- how the world values, restricts, recognizes it
    modules    -- what it does (presence-based, no discriminator string)
    state      -- per-instance, lives on inventory records, NOT here

Decision rule:
    rules-resolving change      -> effect
    plausible improvised action -> affordance
    why an effect exists        -> source/provenance
    world reaction              -> worldness
    this copy                   -> state (inventory record)
    kind of item                -> identity or category module
    carrying/stacking/storage   -> inventory
"""

from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------- controlled vocabularies (Literal types for now; mechanics/*.json
#            holds the authoritative list, validators cross-check at load) ----

Rarity = Literal["common", "uncommon", "rare", "very-rare", "legendary", "unique"]
Legality = Literal["open", "restricted", "contraband"]
SettlementTier = Literal["hamlet", "village", "town", "city", "capital"]
EffectSource = Literal[
    "magical", "material", "mundane", "crafted", "blessed", "cursed", "innate"
]
ActivationType = Literal[
    "passive", "action", "bonus-action", "reaction", "minute", "hour", "ritual"
]
RechargeCycle = Literal["short-rest", "long-rest", "dawn", "dusk", "never"]
PricingModel = Literal["authored", "computed"]


# ---------- identity helpers ----------

class ItemMeta(BaseModel):
    """Optional sparse provenance, when justified per-record."""
    model_config = ConfigDict(extra="forbid")
    source: Optional[str] = None
    license: Optional[str] = None
    version: Optional[str] = None


# ---------- inventory ----------

class Inventory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weight_lb: Optional[float] = Field(default=None, ge=0)
    bulk: Optional[float] = Field(default=None, ge=0)  # stub-friendly
    stackable: bool = False
    max_stack: Optional[int] = Field(default=None, ge=1)


# ---------- worldness ----------

class Pricing(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: PricingModel = "authored"
    canonical_value_cp: Optional[int] = Field(default=None, ge=0)
    inputs: Optional[dict] = None

    @model_validator(mode="after")
    def _enforce_model_inputs(self) -> "Pricing":
        if self.model == "authored" and self.canonical_value_cp is None:
            raise ValueError(
                "pricing.model='authored' requires canonical_value_cp"
            )
        if self.model == "computed" and self.inputs is None:
            raise ValueError("pricing.model='computed' requires inputs")
        return self


class Availability(BaseModel):
    model_config = ConfigDict(extra="forbid")
    settlement_minimum: Optional[SettlementTier] = None
    legality: Optional[Legality] = None
    market_tags: list[str] = Field(default_factory=list)


class Notability(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notable: bool = False
    quest_bound: bool = False
    faction_significance: list[str] = Field(default_factory=list)


class Worldness(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rarity: Rarity = "common"
    pricing: Pricing = Field(default_factory=lambda: Pricing(canonical_value_cp=0))
    availability: Availability = Field(default_factory=Availability)
    notability: Notability = Field(default_factory=Notability)


# ---------- effects ----------

class Effect(BaseModel):
    """
    A rules-resolving change. `source` is provenance only; resolution looks at
    `id` against the effect registry.
    """
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    source: EffectSource
    applies_to: Optional[str] = None
    requires_activation: bool = False
    cost_charges: Optional[int] = Field(default=None, ge=0)
    params: dict = Field(default_factory=dict)


# ---------- capability modules ----------

class Range(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["melee", "ranged", "thrown"]
    normal_ft: int = Field(ge=0)
    long_ft: Optional[int] = Field(default=None, ge=0)


class Damage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dice: str  # e.g. "1d8"
    type: str  # cross-checked against mechanics/damage_types.json
    condition: Optional[str] = None  # e.g. "one-handed", "two-handed"


class WeaponModule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weapon_type: str
    training: Literal["simple", "martial", "exotic"]
    hands: Literal["one", "two", "one-or-two"]
    range: Range
    damage: list[Damage]
    properties: list[str] = Field(default_factory=list)
    attribute_scaling: list[str] = Field(default_factory=list)


class DexBonus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allowed: bool
    max: Optional[int] = Field(default=None, ge=0)


class ArmorModule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    armor_type: Literal["light", "medium", "heavy", "shield"]
    base_ac: int = Field(ge=0)
    dex_bonus: DexBonus
    strength_required: Optional[int] = Field(default=None, ge=0)
    stealth_disadvantage: bool = False


class ConsumableModule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    uses: int = Field(ge=1)
    consume_action: ActivationType = "action"


class ToolModule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proficiency_group: str
    roll_tags: list[str] = Field(default_factory=list)
    tool_role: Optional[Literal["permission", "difficulty-shift"]] = None


class ContainerModule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    capacity_lb: Optional[float] = Field(default=None, ge=0)
    capacity_items: Optional[int] = Field(default=None, ge=0)
    extradimensional: bool = False


class AmmunitionModule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weapon_compatibility: list[str]
    recoverable: bool = True


class ActivationModule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: ActivationType
    duration: Optional[str] = None
    command_word: bool = False


class ChargesModule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    maximum: int = Field(ge=1)
    recharge: Optional[RechargeCycle] = None
    recharge_dice: Optional[str] = None


class AttunementModule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    required: bool = True
    restrictions: list[str] = Field(default_factory=list)


class KnowledgeModule(BaseModel):
    """Catalog-side ID metadata; per-character knowledge state is on inventory."""
    model_config = ConfigDict(extra="forbid")
    identification_difficulty: Optional[int] = Field(default=None, ge=0)
    hidden_until_identified: list[str] = Field(default_factory=list)


# ---------- stub modules (subsystems not yet built) ----------

class DurabilityModule(BaseModel):
    """STUB: degradation/repair subsystem not implemented."""
    model_config = ConfigDict(extra="allow")


class CraftingModule(BaseModel):
    """STUB: crafting subsystem not implemented."""
    model_config = ConfigDict(extra="allow")


class EncumbranceModule(BaseModel):
    """STUB: bulk/encumbrance subsystem not implemented."""
    model_config = ConfigDict(extra="allow")


# ---------- module bag ----------

class Modules(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weapon: Optional[WeaponModule] = None
    armor: Optional[ArmorModule] = None
    consumable: Optional[ConsumableModule] = None
    tool: Optional[ToolModule] = None
    container: Optional[ContainerModule] = None
    ammunition: Optional[AmmunitionModule] = None
    activation: Optional[ActivationModule] = None
    charges: Optional[ChargesModule] = None
    attunement: Optional[AttunementModule] = None
    knowledge: Optional[KnowledgeModule] = None
    effects: list[Effect] = Field(default_factory=list)
    durability: Optional[DurabilityModule] = None
    crafting: Optional[CraftingModule] = None
    encumbrance: Optional[EncumbranceModule] = None


# ---------- top-level item ----------

class Item(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # identity
    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    affordances: list[str] = Field(default_factory=list)
    schema_version: Literal[1] = 1
    meta: Optional[ItemMeta] = None

    # composition
    inventory: Inventory = Field(default_factory=Inventory)
    worldness: Worldness = Field(default_factory=Worldness)
    modules: Modules = Field(default_factory=Modules)


# ---------- derived indexes (computed at load, not authored) ----------

def derive_indexes(item: Item) -> dict:
    m = item.modules
    return {
        "is_weapon": m.weapon is not None,
        "is_armor": m.armor is not None,
        "is_consumable": m.consumable is not None,
        "is_container": m.container is not None,
        "is_ammunition": m.ammunition is not None,
        "is_magical": any(e.source == "magical" for e in m.effects),
        "is_attuneable": m.attunement is not None,
        "has_charges": m.charges is not None,
        "is_notable": item.worldness.notability.notable,
        "is_quest_bound": item.worldness.notability.quest_bound,
    }
