"""
routes/catalog.py — GET /catalog/items, /catalog/creatures, /catalog/vocab

Runtime lookup endpoints split out of /options. /options is reserved for
character creation data (ancestries, cultures, focus, backgrounds). Catalog
endpoints serve everything the GPT needs at runtime: item shops, creature
references, companion vocab and enum literals.
"""

from __future__ import annotations

from typing import Any, Literal, get_args

from fastapi import APIRouter, Query

from api.companions import (
    AgeCategory,
    Autonomy,
    BondLevel,
    CarryingCapacity,
    Communication,
    CreatureSize,
    MovementMode,
    NaturalWeapon,
    Sapience,
    TrainingLevel,
)
from api.game_data import (
    list_ammunition,
    list_apparel_items,
    list_armor,
    list_creature_catalog,
    list_exceptional_catalog,
    list_learned_commands,
    list_magical_items,
    list_mundane_items,
    list_natural_abilities,
    list_tactical_roles,
    list_weapons,
)
from api.models import (
    CompanionVocabResponse,
    CreatureCatalogResponse,
    ItemCatalogResponse,
    ItemOption,
)

router = APIRouter()


ItemKind = Literal["mundane", "magical", "apparel", "weapon", "armor", "ammunition"]


def _literal_values(literal_type: Any) -> list[str]:
    return list(get_args(literal_type))


@router.get(
    "/catalog/items",
    response_model=ItemCatalogResponse,
    tags=["catalog"],
)
async def get_item_catalog(
    kind: ItemKind | None = Query(
        default=None,
        description="Filter to a single catalog: mundane, magical, apparel, weapon, armor, or ammunition. Omit to return all catalogs.",
    ),
) -> ItemCatalogResponse:
    """
    Return runtime item catalogs.

    Omit `kind` for all lists, or pass mundane, magical, apparel, weapon, armor, or ammunition.
    """
    mundane: list[ItemOption] = []
    magical: list[ItemOption] = []
    apparel: list[ItemOption] = []
    weapons: list[ItemOption] = []
    armor: list[ItemOption] = []
    ammunition: list[ItemOption] = []

    if kind in (None, "mundane"):
        mundane = [ItemOption(**item) for item in list_mundane_items()]
    if kind in (None, "magical"):
        magical = [ItemOption(**item) for item in list_magical_items()]
    if kind in (None, "apparel"):
        apparel = [ItemOption(**item) for item in list_apparel_items()]
    if kind in (None, "weapon"):
        weapons = [ItemOption(**item) for item in list_weapons()]
    if kind in (None, "armor"):
        armor = [ItemOption(**item) for item in list_armor()]
    if kind in (None, "ammunition"):
        ammunition = [ItemOption(**item) for item in list_ammunition()]

    return ItemCatalogResponse(
        mundane_items=mundane,
        magical_items=magical,
        apparel_items=apparel,
        weapon_items=weapons,
        armor_items=armor,
        ammunition_items=ammunition,
    )


@router.get(
    "/catalog/creatures",
    response_model=CreatureCatalogResponse,
    tags=["catalog"],
)
async def get_creature_catalog() -> CreatureCatalogResponse:
    """
    Return creature and exceptional companion catalogs.
    """
    return CreatureCatalogResponse(
        creature_catalog=list_creature_catalog(),
        exceptional_catalog=list_exceptional_catalog(),
    )


@router.get(
    "/catalog/vocab",
    response_model=CompanionVocabResponse,
    tags=["catalog"],
)
async def get_companion_vocab() -> CompanionVocabResponse:
    """
    Return companion vocab lists and enum literals.
    """
    return CompanionVocabResponse(
        natural_abilities=list_natural_abilities(),
        learned_commands=list_learned_commands(),
        tactical_roles=list_tactical_roles(),
        training_levels=_literal_values(TrainingLevel),
        bond_levels=_literal_values(BondLevel),
        age_categories=_literal_values(AgeCategory),
        creature_sizes=_literal_values(CreatureSize),
        carrying_capacities=_literal_values(CarryingCapacity),
        movement_modes=_literal_values(MovementMode),
        natural_weapons=_literal_values(NaturalWeapon),
        sapience_levels=_literal_values(Sapience),
        communication_levels=_literal_values(Communication),
        autonomy_levels=_literal_values(Autonomy),
    )