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
    kind: ItemKind = Query(
        ...,
        description="Required. Which item catalog to return: mundane, magical, apparel, weapon, armor, or ammunition.",
    ),
) -> ItemCatalogResponse:
    """
    Return one runtime item catalog.

    `kind` is required so clients cannot accidentally request the full combined
    catalog and exceed response-size caps.
    """
    return ItemCatalogResponse(
        mundane_items=[ItemOption(**item) for item in list_mundane_items()] if kind == "mundane" else [],
        magical_items=[ItemOption(**item) for item in list_magical_items()] if kind == "magical" else [],
        apparel_items=[ItemOption(**item) for item in list_apparel_items()] if kind == "apparel" else [],
        weapon_items=[ItemOption(**item) for item in list_weapons()] if kind == "weapon" else [],
        armor_items=[ItemOption(**item) for item in list_armor()] if kind == "armor" else [],
        ammunition_items=[ItemOption(**item) for item in list_ammunition()] if kind == "ammunition" else [],
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