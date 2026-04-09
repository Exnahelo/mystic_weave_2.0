"""
routes/spells.py — Spell lookup endpoints

GET /spells                  — list spells (filterable by class, level, school)
GET /spells/{spell_index}    — get full spell data
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

class SpellSummary(BaseModel):
    index: str
    name: str
    level: int          # 0 = cantrip
    school: str         # e.g. "Evocation"
    casting_time: str
    range: str
    duration: str
    concentration: bool
    ritual: bool
    classes: list[str]  # class index strings


class SpellListResponse(BaseModel):
    count: int
    spells: list[SpellSummary]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _spell_summary(s: dict[str, Any]) -> SpellSummary:
    return SpellSummary(
        index=s["index"],
        name=s["name"],
        level=s["level"],
        school=s.get("school", {}).get("name", ""),
        casting_time=s.get("casting_time", ""),
        range=s.get("range", ""),
        duration=s.get("duration", ""),
        concentration=s.get("concentration", False),
        ritual=s.get("ritual", False),
        classes=[c["index"] for c in s.get("classes", [])],
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/spells", response_model=SpellListResponse, tags=["spells"])
async def list_spells(
    class_index: str | None = Query(None, description="Filter by class index (e.g. 'wizard', 'ranger')"),
    level: int | None = Query(None, ge=0, le=9, description="Filter by spell level (0=cantrip)"),
    school: str | None = Query(None, description="Filter by school index (e.g. 'evocation', 'conjuration')"),
) -> SpellListResponse:
    """
    List spells from the SRD, with optional filters.

    Use class_index to get spells available to a specific class.
    Use level=0 to get cantrips only.
    Filters are combined (AND logic).
    """
    data = _load_indexed("spells.json")
    spells = list(data.values())

    if class_index is not None:
        spells = [s for s in spells if any(c["index"] == class_index for c in s.get("classes", []))]

    if level is not None:
        spells = [s for s in spells if s.get("level") == level]

    if school is not None:
        spells = [s for s in spells if s.get("school", {}).get("index", "").lower() == school.lower()]

    summaries = [_spell_summary(s) for s in spells]
    return SpellListResponse(count=len(summaries), spells=summaries)


@router.get("/spells/{spell_index}", tags=["spells"])
async def get_spell(spell_index: str) -> dict[str, Any]:
    """
    Return full spell data for the given index (e.g. 'fireball', 'hunters-mark').

    Returns 404 if the spell does not exist.
    """
    data = _load_indexed("spells.json")
    if spell_index not in data:
        raise HTTPException(status_code=404, detail=f"Spell not found: {spell_index!r}")
    return data[spell_index]
