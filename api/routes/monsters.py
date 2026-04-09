"""
routes/monsters.py — Monster encounter endpoints

GET /monsters                   — list monsters (filterable by CR, type)
GET /monsters/{monster_index}   — get full monster stat block
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.srd5e import _load_indexed

router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class MonsterSummary(BaseModel):
    index: str
    name: str
    size: str
    type: str
    alignment: str
    armor_class: int        # highest AC value from the armor_class array
    hit_points: int
    challenge_rating: float
    xp: int


class MonsterListResponse(BaseModel):
    count: int
    monsters: list[MonsterSummary]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _best_ac(armor_class_list: list[dict[str, Any]]) -> int:
    """Return the highest AC value from the armor_class array."""
    if not armor_class_list:
        return 10
    return max(entry.get("value", 10) for entry in armor_class_list)


def _monster_summary(m: dict[str, Any]) -> MonsterSummary:
    return MonsterSummary(
        index=m["index"],
        name=m["name"],
        size=m.get("size", "Medium"),
        type=m.get("type", "unknown"),
        alignment=m.get("alignment", "unaligned"),
        armor_class=_best_ac(m.get("armor_class", [])),
        hit_points=m.get("hit_points", 1),
        challenge_rating=m.get("challenge_rating", 0),
        xp=m.get("xp", 0),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/monsters", response_model=MonsterListResponse, tags=["monsters"])
async def list_monsters(
    cr_min: float | None = Query(None, ge=0, description="Minimum challenge rating (inclusive)"),
    cr_max: float | None = Query(None, ge=0, description="Maximum challenge rating (inclusive)"),
    monster_type: str | None = Query(None, description="Filter by type (e.g. 'humanoid', 'undead', 'beast')"),
) -> MonsterListResponse:
    """
    List monsters from the SRD, with optional filters.

    Use cr_min and cr_max to find monsters appropriate for the party's level.
    Use monster_type to filter by creature type.
    Filters are combined (AND logic).

    Common CR ranges by party level:
    - Level 1: CR 0–1/4
    - Level 2–3: CR 1/4–1
    - Level 4–5: CR 1–3
    - Level 6–10: CR 3–8
    """
    data = _load_indexed("monsters.json")
    monsters = list(data.values())

    if cr_min is not None:
        monsters = [m for m in monsters if m.get("challenge_rating", 0) >= cr_min]

    if cr_max is not None:
        monsters = [m for m in monsters if m.get("challenge_rating", 0) <= cr_max]

    if monster_type is not None:
        monsters = [m for m in monsters if m.get("type", "").lower() == monster_type.lower()]

    summaries = [_monster_summary(m) for m in monsters]
    return MonsterListResponse(count=len(summaries), monsters=summaries)


@router.get("/monsters/{monster_index}", tags=["monsters"])
async def get_monster(monster_index: str) -> dict[str, Any]:
    """
    Return the full stat block for a monster (e.g. 'goblin', 'bandit', 'wolf').

    Returns 404 if the monster does not exist.

    The stat block includes:
    - Ability scores, AC, HP, speed
    - Actions and special abilities
    - Challenge rating and XP
    - Damage resistances, immunities, vulnerabilities
    """
    data = _load_indexed("monsters.json")
    if monster_index not in data:
        raise HTTPException(status_code=404, detail=f"Monster not found: {monster_index!r}")
    return data[monster_index]
