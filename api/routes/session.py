"""
routes/session.py — POST /session/new

Creates a new game session with a default world state. The character
is seeded from SRD data using the provided class, species, subspecies,
and background. Can also be re-seeded via POST /character/create.
"""

from __future__ import annotations

import json
import uuid

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from api.database import get_pool
from api.models import NewSessionRequest, NewSessionResponse
from api.srd5e import seed_character_from_srd, validate_ability_scores

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

    Seeds the character from local SRD data using the provided class, species,
    subspecies, and background. Returns the session_id and initial character
    + world state.
    """
    session_id = _short_id()

    # Validate ability scores against chosen method
    try:
        validate_ability_scores(body.ability_scores.model_dump(), body.ability_score_method)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Build character from SRD data
    try:
        character, _skill_conflicts = seed_character_from_srd(
            name=body.character_name,
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

    # Build initial world state
    world = {
        "location": body.starting_location,
        "threat": body.threat,
        "goal": body.goal,
        "turn": 1,
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
