"""
routes/session.py — POST /session/new

Creates a new game session. The character is seeded from game system data
using the provided species, focus archetype, and background.
"""

from __future__ import annotations

import json
import uuid

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from api.database import get_pool
from api.game_data import seed_character
from api.models import NewSessionRequest, NewSessionResponse

router = APIRouter()


def _short_id() -> str:
    """Generate a short 8-character hex session ID."""
    return uuid.uuid4().hex[:8]


@router.post("/session/new", response_model=NewSessionResponse, status_code=201)
async def new_session(
    body: NewSessionRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> NewSessionResponse:
    """
    Create a new game session.

    Seeds the character from local game system data using the provided
    species, focus, and background. Returns the session_id and initial
    character + world state.
    """
    session_id = _short_id()

    # Build character from game system data
    try:
        character = seed_character(
            name=body.character_name,
            species_index=body.species,
            focus_index=body.focus,
            background_index=body.background,
            adjustment_points=body.adjustment_points.model_dump(),
            identity=body.identity.model_dump() if body.identity else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Build initial world state
    world: dict = {
        "location":   body.starting_location,
        "threat":     body.threat,
        "goal":       body.goal,
        "turn":       1,
        "companions": [],
        "economy":    body.starting_economy.model_dump(),
        "politics": {
            "faction_memberships":  [],
            "active_obligations":   [],
            "legal_standing":       "unknown",
            "known_leverage":       [],
            "active_tensions":      [],
            "conclave_status":      "unknown",
        },
    }

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO game_states (session_id, character, world, log, updated_at)
            VALUES ($1, $2::jsonb, $3::jsonb, '[]'::jsonb, now())
            """,
            session_id,
            json.dumps(character),
            json.dumps(world),
        )

    return NewSessionResponse(
        session_id=session_id,
        character=character,
        world=world,
    )