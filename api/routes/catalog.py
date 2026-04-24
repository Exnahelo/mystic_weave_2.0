"""
routes/catalog.py — Bulk reference data endpoints

GET /catalog/items     — item catalogs (mundane, magical, apparel, weapons, armor)
GET /catalog/creatures — creature data and companion vocabulary
GET /catalog/enums     — literal enum vocabularies for companion profiles

These were previously bundled into /options but have been split out because
/options is called at character creation and the catalog data was pushing
the response past GPT tool-response size limits.
"""

from __future__ import annotations

from typing import Any, get_args

from fastapi import APIRouter

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
    CreatureCatalogResponse,
    EnumsResponse,
    ItemCatalogResponse,
    ItemOption,
)

router = APIRouter()


def _literal_values(literal_type: Any) -> list[str]:
    return list(get_args(literal_type))


@router.get("/catalog/items", response_model=ItemCatalogResponse, tags=["catalog"])
async def get_items_catalog() -> ItemCatalogResponse:
    """Return all item reference data grouped by category."""
    return ItemCatalogResponse(
        mundane=[ItemOption(**item) for item in list_mundane_items()],
        magical=[ItemOption(**item) for item in list_magical_items()],
        apparel=[ItemOption(**item) for item in list_apparel_items()],
        weapons=[ItemOption(**item) for item in list_weapons()],
        armor=[ItemOption(**item) for item in list_armor()],
    )


@router.get("/catalog/creatures", response_model=CreatureCatalogResponse, tags=["catalog"])
async def get_creatures_catalog() -> CreatureCatalogResponse:
    """Return creature catalog, exceptional catalog, and companion vocabulary."""
    return CreatureCatalogResponse(
        creatures=list_creature_catalog(),
        exceptional=list_exceptional_catalog(),
        natural_abilities=list_natural_abilities(),
        learned_commands=list_learned_commands(),
        tactical_roles=list_tactical_roles(),
    )


@router.get("/catalog/enums", response_model=EnumsResponse, tags=["catalog"])
async def get_enums() -> EnumsResponse:
    """Return literal enum vocabularies used in companion and creature profiles."""
    return EnumsResponse(
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