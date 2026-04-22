"""
routes/options.py — GET /options

Returns all supported ancestries, cultures, focus archetypes, and backgrounds
from the local game system JSON data.

The GPT calls this once at the start of character creation to enumerate
valid options. This prevents the GPT from guessing or confabulating
unsupported choices.
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
    list_ancestries,
    list_backgrounds,
    list_creature_catalog,
    list_cultures,
    list_exceptional_catalog,
    list_focus,
    list_learned_commands,
    list_magical_items,
    list_mundane_items,
    list_natural_abilities,
    list_tactical_roles,
)
from api.models import (
    AncestryOption,
    BackgroundOption,
    CultureOption,
    FocusOption,
    ItemOption,
    OptionsResponse,
)

router = APIRouter()


def _literal_values(literal_type: Any) -> list[str]:
    return list(get_args(literal_type))


@router.get("/options", response_model=OptionsResponse, tags=["options"])
async def get_options() -> OptionsResponse:
    """
    Return all supported ancestries, cultures, focus archetypes, and backgrounds.

    Call this before asking the player to choose ancestry, culture, focus, or background.
    Only present options returned by this endpoint — do not offer any options
    not listed here. Never enumerate from memory.
    """
    ancestries = [AncestryOption(**a) for a in list_ancestries()]
    cultures = [CultureOption(**c) for c in list_cultures()]
    focus = [FocusOption(**f) for f in list_focus()]
    backgrounds = [BackgroundOption(**b) for b in list_backgrounds()]
    mundane_items = [ItemOption(**item) for item in list_mundane_items()]
    magical_items = [ItemOption(**item) for item in list_magical_items()]
    apparel_items = [ItemOption(**item) for item in list_apparel_items()]
    creature_catalog = list_creature_catalog()
    exceptional_catalog = list_exceptional_catalog()
    natural_abilities = list_natural_abilities()
    learned_commands = list_learned_commands()
    tactical_roles = list_tactical_roles()

    return OptionsResponse(
        ancestries=ancestries,
        cultures=cultures,
        focus=focus,
        backgrounds=backgrounds,
        mundane_items=mundane_items,
        magical_items=magical_items,
        apparel_items=apparel_items,
        creature_catalog=creature_catalog,
        exceptional_catalog=exceptional_catalog,
        natural_abilities=natural_abilities,
        learned_commands=learned_commands,
        tactical_roles=tactical_roles,
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
