"""
routes/npcs.py — GET /npcs

Returns NPC registry entries from data/npcs/. Filterable by tier category.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from api.game_data import list_npc_roles, list_npcs, list_npcs_named
from api.models import NpcRegistryEntry, NpcRegistryResponse

router = APIRouter()


@router.get("/npcs", response_model=NpcRegistryResponse, tags=["npcs"])
async def get_npcs(
    tier: str | None = Query(
        default=None,
        description="Filter by tier category: 'named' (tier 1-2) or 'roles' (tier 3). Omit for all.",
    ),
) -> NpcRegistryResponse:
    """Return NPC registry entries. Use `tier=named` for tier 1-2 individuals, `tier=roles` for tier 3 role templates, or omit for both."""
    if tier == "named":
        entries = list_npcs_named()
    elif tier == "roles":
        entries = list_npc_roles()
    elif tier is None:
        entries = list_npcs()
    else:
        return NpcRegistryResponse(
            entries=[],
            count=0,
            error=f"Invalid tier: {tier!r}. Expected 'named', 'roles', or omitted.",
        )
    return NpcRegistryResponse(entries=[NpcRegistryEntry(**n) for n in entries], count=len(entries))