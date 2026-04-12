"""routes/scene.py — compact scene context endpoint for narration input."""

from __future__ import annotations

import json

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from api.database import get_pool
from api.models import CharacterModel, LocationData, SceneContext, WorldModel
from api.scene_context import build_scene_context

router = APIRouter()


@router.get(
    "/scene/{session_id}",
    response_model=SceneContext,
    description=(
        "Build and return compact scene context from persisted state and current location "
        "for narration input."
    ),
)
async def get_scene_context(
    session_id: str,
    pool: asyncpg.Pool = Depends(get_pool),
) -> SceneContext:
    async with pool.acquire() as conn:
        state_row = await conn.fetchrow(
            "SELECT session_id, character, world, log FROM game_states WHERE session_id = $1",
            session_id,
        )

        if state_row is None:
            raise HTTPException(status_code=404, detail="session not found")

        try:
            character = CharacterModel.model_validate(json.loads(state_row["character"]))
            world = WorldModel.model_validate(json.loads(state_row["world"]))
        except ValidationError as e:
            raise HTTPException(
                status_code=500,
                detail={"message": "stored game state is invalid", "errors": e.errors()},
            )

        location_row = await conn.fetchrow(
            "SELECT data FROM locations WHERE id = $1",
            world.location,
        )

    if location_row is None:
        raise HTTPException(status_code=404, detail=f"current location not found: {world.location}")

    try:
        location = LocationData.model_validate(json.loads(location_row["data"]))
    except ValidationError as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "stored location is invalid", "errors": e.errors()},
        )

    return build_scene_context(
        session_id=state_row["session_id"],
        character=character,
        world=world,
        location=location,
        log=json.loads(state_row["log"]),
    )
