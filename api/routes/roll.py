"""
routes/roll.py — POST /roll

Authoritative dice resolution. The GPT must call this endpoint for any
contested action. It may not fudge, reinterpret, or override the result.

Modifier calculation (standard 5e):
  ability modifier = floor((score - 10) / 2)
  proficiency bonus at level 1 = +2
  total modifier = ability modifier + proficiency bonus (if proficient)
"""

from __future__ import annotations

import math

from fastapi import APIRouter

from api.models import RollRequest, RollResponse
from core.dice_roller import roll as dice_roll

router = APIRouter()

_PROFICIENCY_BONUS_LEVEL_1 = 2


def _ability_modifier(score: int) -> int:
    return math.floor((score - 10) / 2)


@router.post("/roll", response_model=RollResponse)
async def roll_dice(body: RollRequest) -> RollResponse:
    """
    Roll dice with 5e modifier math and return a pass/fail result.

    Critical rules (non-negotiable):
    - A natural 1 is always a critical failure regardless of modifiers.
    - A natural 20 is always a critical success regardless of DC.
    """
    # Roll the raw dice (uses core/dice_roller.py)
    raw_roll = dice_roll(body.dice)

    # Calculate modifier
    mod = _ability_modifier(body.score)
    if body.proficient:
        mod += _PROFICIENCY_BONUS_LEVEL_1

    total = raw_roll + mod

    # Critical rules override everything
    is_d20 = body.dice.strip().lower() in ("1d20", "d20")
    critical_success = is_d20 and raw_roll == 20
    critical_failure = is_d20 and raw_roll == 1

    if critical_success:
        success = True
    elif critical_failure:
        success = False
    else:
        success = total >= body.dc

    margin = total - body.dc

    return RollResponse(
        roll=raw_roll,
        modifier=mod,
        total=total,
        success=success,
        margin=margin,
        critical_success=critical_success,
        critical_failure=critical_failure,
    )
