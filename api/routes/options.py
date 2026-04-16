"""
routes/options.py — GET /options

Returns all supported species, focus archetypes, and backgrounds
from the local game system JSON data.

The GPT calls this once at the start of character creation to enumerate
valid options. This prevents the GPT from guessing or confabulating
unsupported choices.
"""

from __future__ import annotations

from fastapi import APIRouter

from api.game_data import (
    list_apparel_items,
    list_backgrounds,
    list_focus,
    list_magical_items,
    list_mundane_items,
    list_species,
)
from api.models import (
    BackgroundOption,
    FocusOption,
    ItemOption,
    OptionsResponse,
    SpeciesOption,
)

router = APIRouter()


@router.get("/options", response_model=OptionsResponse, tags=["options"])
async def get_options() -> OptionsResponse:
    """
    Return all supported species, focus archetypes, and backgrounds.

    Call this before asking the player to choose species, focus, or background.
    Only present options returned by this endpoint — do not offer any options
    not listed here. Never enumerate from memory.
    """
    species = [SpeciesOption(**s) for s in list_species()]
    focus = [FocusOption(**f) for f in list_focus()]
    backgrounds = [BackgroundOption(**b) for b in list_backgrounds()]
    mundane_items = [ItemOption(**item) for item in list_mundane_items()]
    magical_items = [ItemOption(**item) for item in list_magical_items()]
    apparel_items = [ItemOption(**item) for item in list_apparel_items()]

    return OptionsResponse(
        species=species,
        focus=focus,
        backgrounds=backgrounds,
        mundane_items=mundane_items,
        magical_items=magical_items,
        apparel_items=apparel_items,
    )
