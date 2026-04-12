"""
routes/roll.py — POST /roll

Authoritative d100 roll-under resolution. The GPT must call this endpoint
for any contested action. It may not fudge, reinterpret, or override the result.

Resolution:
  GPT assembles target = domain score + knowledge tier + application tier + difficulty modifier
  Server rolls 1d100
  Success if roll <= target
  Roll 1 = critical success (always)
  Roll 100 = critical failure (always)
"""

from __future__ import annotations

from fastapi import APIRouter

from api.models import RollRequest, RollResponse
from core.dice_roller import roll as dice_roll

router = APIRouter()


def _degree_of_success(raw_roll: int, target: int) -> str:
    """Determine the degree of success band from roll and target."""
    if raw_roll == 1:
        return "critical_success"
    if raw_roll == 100:
        return "critical_failure"
    if raw_roll <= target:
        margin = target - raw_roll
        if margin >= 20:
            return "strong_success"
        return "success"
    else:
        margin = raw_roll - target
        if margin <= 10:
            return "partial_failure"
        return "failure"


@router.post(
    "/roll",
    response_model=RollResponse,
    description="Roll 1d100 against a target and return success state plus degree band.",
)
async def roll_dice(body: RollRequest) -> RollResponse:
    """
    Roll 1d100 against the target number and return the result with
    degree of success.

    Critical rules (non-negotiable):
    - Roll 1 is always critical success regardless of target.
    - Roll 100 is always critical failure regardless of target.
    """
    raw_roll = dice_roll("1d100")

    # Critical rules override everything
    if raw_roll == 1:
        success = True
    elif raw_roll == 100:
        success = False
    else:
        success = raw_roll <= body.target

    margin = body.target - raw_roll  # positive = succeeded by, negative = failed by
    degree = _degree_of_success(raw_roll, body.target)

    return RollResponse(
        roll=raw_roll,
        target=body.target,
        success=success,
        margin=margin,
        degree=degree,
        critical_success=(raw_roll == 1),
        critical_failure=(raw_roll == 100),
    )
