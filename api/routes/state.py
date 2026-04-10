"""
routes/state.py — GET and POST /state/{session_id}

GET  /state/{session_id}  — load full game state (used at session start)
POST /state/{session_id}  — save full game state + append log entry (used after each turn)

IMPORTANT: The save endpoint performs a deep merge of the incoming character
onto the stored character. This means fields the GPT omits are preserved from
the previous save rather than wiped. Only fields explicitly sent are updated.
"""

from __future__ import annotations

import json
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from api.database import get_pool
from api.models import CharacterModel, GameStateResponse, SaveStateRequest, WorldModel

router = APIRouter()


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """
    Deep-merge `incoming` onto `base`.

    Rules:
    - For each key in `incoming`:
      - If the value is a non-empty dict and the base value is also a dict,
        recurse.
      - If the value is a non-empty list, replace the base value.
      - If the value is None and the base has a non-None value, keep the base
        value (prevents accidental nulling of established fields).
      - Otherwise, use the incoming value.
    - Keys in `base` not present in `incoming` are preserved unchanged.
    """
    result = dict(base)
    for key, inc_val in incoming.items():
        base_val = result.get(key)
        if isinstance(inc_val, dict) and isinstance(base_val, dict) and inc_val:
            result[key] = _deep_merge(base_val, inc_val)
        elif inc_val is None and base_val is not None:
            # Don't wipe an established value with None
            pass
        else:
            result[key] = inc_val
    return result


@router.get("/state/{session_id}", response_model=GameStateResponse)
async def load_state(
    session_id: str,
    pool: asyncpg.Pool = Depends(get_pool),
) -> GameStateResponse:
    """Load the full game state for a session. Returns 404 if not found."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT session_id, character, world, log, updated_at "
            "FROM game_states WHERE session_id = $1",
            session_id,
        )

    if row is None:
        raise HTTPException(status_code=404, detail="session not found")

    try:
        character = CharacterModel.model_validate(json.loads(row["character"]))
        world = WorldModel.model_validate(json.loads(row["world"]))
    except ValidationError as e:
        raise HTTPException(status_code=500, detail={"message": "stored game state is invalid", "errors": e.errors()})

    return GameStateResponse(
        session_id=row["session_id"],
        character=character,
        world=world,
        log=json.loads(row["log"]),
        updated_at=row["updated_at"],
    )


@router.post("/state/{session_id}", response_model=GameStateResponse)
async def save_state(
    session_id: str,
    body: SaveStateRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> GameStateResponse:
    """
    Save full game state and append a log entry.

    Character fields are deep-merged onto the stored record so that fields
    the GPT omits (languages, spells, equipment, feat_choices, biography, etc.)
    are preserved from the previous save rather than wiped.

    World is replaced in full (it is small and always fully specified).
    The log_entry is appended atomically in SQL.
    """
    incoming_character = body.character.model_dump(by_alias=True)
    world_json = body.world.model_dump()
    log_entry_json = json.dumps([body.log_entry])

    async with pool.acquire() as conn:
        # Load existing character to merge against
        existing_row = await conn.fetchrow(
            "SELECT character FROM game_states WHERE session_id = $1",
            session_id,
        )

        if existing_row is not None:
            existing_character: dict[str, Any] = json.loads(existing_row["character"])
            merged_character = _deep_merge(existing_character, incoming_character)
        else:
            merged_character = incoming_character

        try:
            validated_character = CharacterModel.model_validate(merged_character)
            validated_world = WorldModel.model_validate(world_json)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())

        merged_character_json = validated_character.model_dump(by_alias=True)
        validated_world_json = validated_world.model_dump()

        row = await conn.fetchrow(
            """
            INSERT INTO game_states (session_id, character, world, log, updated_at)
            VALUES ($1, $2::jsonb, $3::jsonb, $4::jsonb, now())
            ON CONFLICT (session_id) DO UPDATE
              SET character   = EXCLUDED.character,
                  world       = EXCLUDED.world,
                  log         = game_states.log || $5::jsonb,
                  updated_at  = now()
            RETURNING session_id, character, world, log, updated_at
            """,
            session_id,
            json.dumps(merged_character_json),
            json.dumps(validated_world_json),
            json.dumps([body.log_entry]),   # initial log on INSERT
            log_entry_json,                 # appended entry on UPDATE
        )

    try:
        response_character = CharacterModel.model_validate(json.loads(row["character"]))
        response_world = WorldModel.model_validate(json.loads(row["world"]))
    except ValidationError as e:
        raise HTTPException(status_code=500, detail={"message": "stored game state is invalid", "errors": e.errors()})

    return GameStateResponse(
        session_id=row["session_id"],
        character=response_character,
        world=response_world,
        log=json.loads(row["log"]),
        updated_at=row["updated_at"],
    )
