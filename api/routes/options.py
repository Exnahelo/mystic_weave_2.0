"""
routes/options.py — GET /options

Returns character creation reference data: ancestries, cultures, focus
archetypes, and backgrounds. The GPT calls this once at the start of
character creation to enumerate valid options. Item catalogs, creature
catalogs, and enum vocabularies are served by /catalog/* endpoints.
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
    Return character creation options: ancestries, cultures, focus, backgrounds.

    Call this before asking the player to choose ancestry, culture, focus, or
    background. Only present options returned by this endpoint — never
    enumerate from memory or from prompt files.
    """
    return OptionsResponse(
        ancestries=[AncestryOption(**a) for a in list_ancestries()],
        cultures=[CultureOption(**c) for c in list_cultures()],
        focus=[FocusOption(**f) for f in list_focus()],
        backgrounds=[BackgroundOption(**b) for b in list_backgrounds()],
    )
