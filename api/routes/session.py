"""
routes/session.py — POST /session/new

    Creates a new game session. The character is seeded from game system data
    using the provided ancestry, culture, focus archetype, and background.
"""

from __future__ import annotations

import json
import uuid

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from api.database import get_pool
from api.game_data import seed_character
from api.models import CharacterModel, NewSessionRequest, NewSessionResponse, WorldModel

router = APIRouter()


def _short_id() -> str:
    """Generate a short 16-character hex session ID."""
    return uuid.uuid4().hex[:16]


@router.post("/session/new", response_model=NewSessionResponse, status_code=201)
async def new_session(
    body: NewSessionRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> NewSessionResponse:
    """
    Create a new game session.

    Seeds the character from local game system data using the provided
    ancestry, culture, focus, and background. Returns the session_id and initial
    character + world state.
    """
    session_id = _short_id()

    # Build character from game system data
    try:
        character = seed_character(
            name=body.character_name,
            ancestry_index=body.ancestry,
            culture_index=body.culture,
            focus_index=body.focus,
            background_index=body.background,
            adjustment_points=body.adjustment_points.model_dump(),
            identity=body.identity.model_dump() if body.identity else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        validated_character = CharacterModel.model_validate(character)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    if body.equipment is not None:
        validated_character.equipment = body.equipment

    # Build initial world state. WorldModel supplies defaults for turn,
    # companion_archive, politics, time, survival, and pacing — only the
    # session-specific fields are passed explicitly.
    try:
        validated_world = WorldModel(
            location=body.starting_location,
            threat=body.threat,
            goal=body.goal,
            companions=list(body.companions) if body.companions else [],
            economy=body.starting_economy,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    character_json = validated_character.model_dump()
    world_json = validated_world.model_dump()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO game_states (session_id, character, world, log, updated_at)
            VALUES ($1, $2::jsonb, $3::jsonb, '[]'::jsonb, now())
            """,
            session_id,
            json.dumps(character_json),
            json.dumps(world_json),
        )

    return NewSessionResponse(
        session_id=session_id,
        character=validated_character,
        world=validated_world,
    )