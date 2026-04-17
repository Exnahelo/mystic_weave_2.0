"""
routes/character.py — POST /character/create

Seeds a full character from game system data and saves it into an existing session.
Called when the player wants to re-create or replace a character in an existing session.
"""

from __future__ import annotations

import json

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from api.database import get_pool
from api.game_data import seed_character
from api.models import CharacterModel, CreateCharacterRequest, CreateCharacterResponse

router = APIRouter()


@router.post("/character/create", response_model=CreateCharacterResponse)
async def create_character(
    body: CreateCharacterRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> CreateCharacterResponse:
    """
    Seed a character from game system data and update the session's character record.

    The session must already exist (created via POST /session/new).
    Returns 404 if the session is not found.
    """
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT 1 FROM game_states WHERE session_id = $1",
            body.session_id,
        )
        if not exists:
            raise HTTPException(status_code=404, detail="session not found")

        # Build character from game system data
        try:
            character = seed_character(
                name=body.name,
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

        character_json = validated_character.model_dump(by_alias=True)

        # Update the character column in the existing session
        await conn.execute(
            """
            UPDATE game_states
               SET character = $1::jsonb,
                   updated_at = now()
             WHERE session_id = $2
            """,
            json.dumps(character_json),
            body.session_id,
        )

    return CreateCharacterResponse(
        session_id=body.session_id,
        character=character_json,
    )