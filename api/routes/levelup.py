"""
routes/levelup.py — POST /character/levelup

Applies a level-up to a character in an existing session.
Calculates new HP, proficiency bonus, and features gained at the new level.
Returns the updated character dict (does NOT auto-save to game_states — the
GPT must call POST /state/{session_id} after narrating the level-up).
"""

from __future__ import annotations

import json
import math
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from api.database import get_pool
from api.srd5e import (
    _load_indexed,
    ability_modifier,
    get_class,
    get_subclass,
    proficiency_bonus,
)

router = APIRouter()

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class LevelUpRequest(BaseModel):
    """Body for POST /character/levelup"""
    model_config = ConfigDict(populate_by_name=True)

    session_id: str
    hp_roll: int | None = None  # Player's hit die roll (1–hit_die_max). If None, uses average.
    subclass_index: str | None = None  # Required when levelling to the subclass selection level


class FeatureGained(BaseModel):
    index: str
    name: str
    level: int
    description: str


class LevelUpResponse(BaseModel):
    session_id: str
    old_level: int
    new_level: int
    character: dict[str, Any]
    features_gained: list[FeatureGained]
    spell_slots: dict[str, int] | None = None  # Present for spellcasting classes
    hp_gained: int
    new_prof_bonus: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_level_data(class_index: str, level: int) -> dict[str, Any] | None:
    """Return the levels.json entry for a given class + level (class-level only, not subclass-level)."""
    data = _load_indexed("levels.json")
    key = f"{class_index}-{level}"
    entry = data.get(key)
    if entry and "subclass" not in entry:
        return entry
    return None


def _get_features_at_level(
    class_index: str,
    level: int,
    subclass_index: str | None = None,
) -> list[dict[str, Any]]:
    """Return features.json entries for a class at a given level (optionally including subclass features)."""
    features_data = _load_indexed("features.json")
    result = []
    for feat in features_data.values():
        feat_class = feat.get("class", {}).get("index", "")
        feat_subclass = feat.get("subclass", {}).get("index", "") if feat.get("subclass") else None
        feat_level = feat.get("level", 0)

        if feat_level != level:
            continue

        if feat_class != class_index:
            continue

        # Class feature (no subclass)
        if feat_subclass is None:
            result.append(feat)
        # Subclass feature — only include if subclass matches
        elif subclass_index and feat_subclass == subclass_index:
            result.append(feat)

    return result


def _average_hp_roll(hit_die_str: str) -> int:
    """Return the average roll for a hit die (rounded up), e.g. d10 → 6."""
    die_size = int(str(hit_die_str).lstrip("d"))
    return math.ceil((die_size + 1) / 2)


def _extract_spell_slots(level_data: dict[str, Any]) -> dict[str, int] | None:
    """Extract spell slot counts from a level entry, or None if not a spellcaster."""
    sc = level_data.get("spellcasting")
    if not sc:
        return None
    slots = {k: v for k, v in sc.items() if k.startswith("spell_slots_level_") and v > 0}
    if not slots:
        return None
    return slots


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/character/levelup", response_model=LevelUpResponse, tags=["character"])
async def level_up(
    body: LevelUpRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> LevelUpResponse:
    """
    Apply a level-up to the character in the given session.

    - Calculates new HP (player-rolled or average).
    - Updates proficiency bonus.
    - Returns features gained at the new level.
    - Returns spell slot table if the class is a spellcaster at this level.
    - Does NOT save to game_states — call POST /state/{session_id} after narrating.

    Subclass selection:
    - In 2024 rules, all classes choose a subclass at level 3.
    - Pass subclass_index when levelling to level 3 (or the class's subclass level).
    - If subclass_index is provided, subclass features at that level are also returned.
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT character FROM game_states WHERE session_id = $1",
            body.session_id,
        )

    if row is None:
        raise HTTPException(status_code=404, detail="session not found")

    character: dict[str, Any] = json.loads(row["character"])
    old_level: int = character.get("level", 1)
    new_level = old_level + 1

    if new_level > 20:
        raise HTTPException(status_code=422, detail="Character is already at maximum level (20).")

    class_index: str = character.get("class", "")
    hit_die_str: str = character.get("hit_die", "d8")
    current_subclass: str | None = character.get("subclass")

    # Validate class
    try:
        get_class(class_index)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Validate subclass if provided
    if body.subclass_index:
        try:
            sub = get_subclass(body.subclass_index)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        sub_class_idx = sub.get("class", {}).get("index", "")
        if sub_class_idx != class_index:
            raise HTTPException(
                status_code=422,
                detail=f"Subclass {body.subclass_index!r} belongs to {sub_class_idx!r}, not {class_index!r}.",
            )
        current_subclass = body.subclass_index

    # Determine HP gained
    die_size = int(str(hit_die_str).lstrip("d"))
    if body.hp_roll is not None:
        if not (1 <= body.hp_roll <= die_size):
            raise HTTPException(
                status_code=422,
                detail=f"hp_roll must be between 1 and {die_size} for a {hit_die_str}.",
            )
        hp_roll = body.hp_roll
    else:
        hp_roll = _average_hp_roll(hit_die_str)

    con_score = character.get("ability_scores", {}).get("CON", 10)
    con_mod = ability_modifier(con_score)
    hp_gained = max(1, hp_roll + con_mod)  # minimum 1 HP per level

    # Update HP
    old_hp = character.get("hp", {"current": 0, "max": 0})
    new_max_hp = old_hp.get("max", 0) + hp_gained
    new_current_hp = old_hp.get("current", 0) + hp_gained

    # Get level data for spell slots and prof bonus
    level_data = _get_level_data(class_index, new_level)
    new_prof_bonus = proficiency_bonus(new_level)

    # Get features gained at new level
    raw_features = _get_features_at_level(class_index, new_level, current_subclass)
    features_gained = [
        FeatureGained(
            index=f["index"],
            name=f["name"],
            level=f["level"],
            description=" ".join(f.get("desc", [])) if isinstance(f.get("desc"), list) else str(f.get("desc", "")),
        )
        for f in raw_features
    ]

    # Extract spell slots
    spell_slots = _extract_spell_slots(level_data) if level_data else None

    # Build updated character
    updated_character = dict(character)
    updated_character["level"] = new_level
    updated_character["hp"] = {"current": new_current_hp, "max": new_max_hp}
    if current_subclass:
        updated_character["subclass"] = current_subclass

    return LevelUpResponse(
        session_id=body.session_id,
        old_level=old_level,
        new_level=new_level,
        character=updated_character,
        features_gained=features_gained,
        spell_slots=spell_slots,
        hp_gained=hp_gained,
        new_prof_bonus=new_prof_bonus,
    )
