"""
routes/options.py — GET /options

Returns all supported ancestries, cultures, focus archetypes, and backgrounds
from the local game system JSON data. This is the creation-scope enumeration
endpoint. Runtime catalogs (items, creatures, companion vocab) live under
/catalog/*.

The GPT calls /options once at the start of character creation to enumerate
valid choices. This prevents the GPT from guessing or confabulating
unsupported choices.
"""

from __future__ import annotations

from fastapi import APIRouter

from api.game_data import (
    list_ancestries,
    list_backgrounds,
    list_cultures,
    list_focus,
)
from api.models import (
    AncestryOption,
    BackgroundOption,
    CultureOption,
    FocusOption,
    OptionsResponse,
)

router = APIRouter()


@router.get("/options", response_model=OptionsResponse, tags=["options"])
async def get_options() -> OptionsResponse:
    """
    Return creation options only: ancestries, cultures, focus, backgrounds.

    Use this at character creation. Do not invent or enumerate choices from
    memory. Runtime catalogs live under /catalog/*.
    """
    return OptionsResponse(
        ancestries=[AncestryOption(**a) for a in list_ancestries()],
        cultures=[CultureOption(**c) for c in list_cultures()],
        focus=[FocusOption(**f) for f in list_focus()],
        backgrounds=[BackgroundOption(**b) for b in list_backgrounds()],
    )
