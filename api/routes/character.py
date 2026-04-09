"""
routes/character.py — POST /character/create

Seeds a full character from local SRD data and saves it into an existing session.
Called once after POST /session/new when the player has chosen class, species,
subspecies, background, ability scores, and skill selections.
"""

from __future__ import annotations

import json

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from api.database import get_pool
from api.models import CreateCharacterRequest, CreateCharacterResponse
from api.srd5e import seed_character_from_srd, validate_ability_scores

router = APIRouter()


@router.post("/character/create", response_model=CreateCharacterResponse)
async def create_character(
    body: CreateCharacterRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> CreateCharacterResponse:
    """
    Seed a character from SRD data and update the session's character record.

    The session must already exist (created via POST /session/new).
    Returns 404 if the session is not found.
    """
    # Verify session exists
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT 1 FROM game_states WHERE session_id = $1",
            body.session_id,
        )
        if not exists:
            raise HTTPException(status_code=404, detail="session not found")

        # Validate ability scores against chosen method
        try:
            validate_ability_scores(body.ability_scores.model_dump(), body.ability_score_method)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        # Build character from SRD data
        try:
            character, skill_conflicts = seed_character_from_srd(
                name=body.name,
                class_index=body.class_,
                species_index=body.species,
                ability_scores=body.ability_scores.model_dump(),
                background_index=body.background,
                subspecies_index=body.subspecies,
                subclass_index=body.subclass,
                skill_choices=body.skill_choices,
                primary_score=body.primary_score,
                secondary_score=body.secondary_score,
                language_choices=body.language_choices,
                species_choices=body.species_choices,
                equipment_choice=body.equipment_choice,
                alignment=body.alignment,
                faith=body.faith,
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        # Update the character column in the existing session
        await conn.execute(
            """
            UPDATE game_states
               SET character = $1::jsonb,
                   updated_at = now()
             WHERE session_id = $2
            """,
            json.dumps(character),
            body.session_id,
        )

    return CreateCharacterResponse(
        session_id=body.session_id,
        character=character,
        skill_conflicts=skill_conflicts,
    )
