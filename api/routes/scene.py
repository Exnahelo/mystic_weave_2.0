"""routes/scene.py — compact scene context endpoint for narration input."""

from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from api.database import get_pool
from api.models import CharacterModel, LocationData, SceneContext, WorldModel
from api.repositories.state_repository import StateRepository
from api.routes._helpers import get_state_repository
from api.routes.state import _normalize_character_state
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
    repo: StateRepository = Depends(get_state_repository),
    pool: asyncpg.Pool = Depends(get_pool),
) -> SceneContext:
    state = await repo.get_state_full(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="session not found")

    try:
        character = CharacterModel.model_validate(
            _normalize_character_state(state.character)
        )
        world = WorldModel.model_validate(state.world)
    except ValidationError as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "stored game state is invalid", "errors": e.errors()},
        )

    # Locations don't yet have a repository; fetch via the pool dependency.
    async with pool.acquire() as conn:
        location_row = await conn.fetchrow(
            "SELECT data FROM locations WHERE id = $1",
            world.location,
        )

    if location_row is None:
        # Fresh sessions and any state where world.location has no matching
        # locations row return a degraded context rather than 404 — the
        # narrator can detect the synthetic name and prompt for a starting
        # location in prose.
        location = LocationData(
            id=world.location or "unknown",
            name="No location set",
        )
    else:
        try:
            location = LocationData.model_validate(location_row["data"])
        except ValidationError as e:
            raise HTTPException(
                status_code=500,
                detail={"message": "stored location is invalid", "errors": e.errors()},
            )

    return build_scene_context(
        session_id=state.session_id,
        character=character,
        world=world,
        location=location,
        log=state.log,
    )
