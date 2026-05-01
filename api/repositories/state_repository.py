from __future__ import annotations

import json

import asyncpg

from api.models import CharacterModel, TypedLogEntry, WorldModel
from api.routes.state import _normalize_character_state, _normalize_world_state


class StateRepository:
    """Repository for persisted session character/world state."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get_character(self, session_id: str) -> CharacterModel | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT character FROM game_states WHERE session_id = $1",
                session_id,
            )
        if row is None:
            return None
        return CharacterModel.model_validate(
            _normalize_character_state(json.loads(row["character"]))
        )

    async def get_world(self, session_id: str) -> WorldModel | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT world FROM game_states WHERE session_id = $1",
                session_id,
            )
        if row is None:
            return None
        return WorldModel.model_validate(
            _normalize_world_state(json.loads(row["world"]))
        )

    async def update_character(self, session_id: str, character: CharacterModel) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE game_states SET character = $1::jsonb, updated_at = now() WHERE session_id = $2",
                character.model_dump_json(),
                session_id,
            )

    async def update_world(self, session_id: str, world: WorldModel) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE game_states SET world = $1::jsonb, updated_at = now() WHERE session_id = $2",
                world.model_dump_json(),
                session_id,
            )

    async def append_log_entry(self, session_id: str, entry: TypedLogEntry) -> None:
        """Append a typed log entry to game_states.log for the given session.

        Used by backend-driven log writes (e.g., arc closure summaries).
        Atomic single-statement append; preserves all existing entries.
        """
        entry_json = json.dumps([entry.model_dump(exclude_none=True)])
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE game_states SET log = log || $1::jsonb, updated_at = now() WHERE session_id = $2",
                entry_json,
                session_id,
            )