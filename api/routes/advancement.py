"""
routes/advancement.py — POST /character/{session_id}/spend_ap

Dedicated endpoint for AP spending. Handles:
- bracket-cost math (1/2/3 per point at 25-60 / 61-70 / 71-80)
- fungible AP pool deduction and domain score increment in a single transaction
"""

from __future__ import annotations

import json

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from api.database import get_pool
from api.models import AdvancementState, SpendAPRequest, SpendAPResponse

router = APIRouter()


def _bracket_cost(score: int) -> int:
    """Return AP cost to raise the domain from `score` to `score + 1`."""
    if score < 60:
        return 1
    if score < 70:
        return 2
    if score < 80:
        return 3
    raise ValueError(f"domain score {score} is at or above the cap of 80")


def _total_cost(start_score: int, points: int) -> int:
    """Compute total AP cost to raise from start_score by `points`, point-by-point."""
    if start_score + points > 80:
        raise ValueError(
            f"would raise domain score above cap of 80 (start={start_score}, points={points})"
        )
    cost = 0
    for i in range(points):
        cost += _bracket_cost(start_score + i)
    return cost


@router.post(
    "/character/{session_id}/spend_ap",
    response_model=SpendAPResponse,
    description=(
        "Spend AP to raise a domain score. AP is drawn from the single "
        "fungible pool (points_available). Bracket costs apply point-by-point: "
        "1 AP per point at scores 25-60, 2 AP at 61-70, 3 AP at 71-80."
    ),
)
async def spend_ap(
    session_id: str,
    body: SpendAPRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> SpendAPResponse:
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT character FROM game_states WHERE session_id = $1 FOR UPDATE",
                session_id,
            )
            if row is None:
                raise HTTPException(status_code=404, detail="session not found")

            character = row["character"]
            domains = character.get("domains") or {}
            advancement_dict = character.get("advancement") or {}

            current_score = domains.get(body.target_domain)
            if current_score is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"character has no score for domain {body.target_domain!r}",
                )

            try:
                cost = _total_cost(current_score, body.points)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc))

            available = advancement_dict.get("points_available", 0)
            if cost > available:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"insufficient AP: cost {cost}, available {available}"
                    ),
                )

            domains[body.target_domain] = current_score + body.points
            advancement_dict["points_available"] = available - cost
            advancement_dict["points_spent"] = (
                advancement_dict.get("points_spent", 0) + cost
            )

            character["domains"] = domains
            character["advancement"] = advancement_dict

            await conn.execute(
                "UPDATE game_states SET character = $1::jsonb, updated_at = now() WHERE session_id = $2",
                character,
                session_id,
            )

    return SpendAPResponse(
        session_id=session_id,
        target_domain=body.target_domain,
        points_purchased=body.points,
        ap_cost_total=cost,
        new_domain_score=domains[body.target_domain],
        advancement=AdvancementState.model_validate(advancement_dict),
    )