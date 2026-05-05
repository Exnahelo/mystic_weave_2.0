from __future__ import annotations

import json
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator

import asyncpg

from api.models import CharacterModel, TypedLogEntry, WorldModel
from api.routes.state import _normalize_character_state, _normalize_world_state


@dataclass(frozen=True)
class FullState:
    """Composed read of a session's character, world, and log.

    Returned by `StateRepository.get_state_full` and the transactional
    variant. The character/world fields are raw dicts (codec-parsed
    JSONB), not validated Pydantic models, so consumers can decide
    whether to validate or operate on them as JSONB blobs.
    """
    session_id: str
    character: dict[str, Any]
    world: dict[str, Any]
    log: list[Any]
    updated_at: datetime | None


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
            _normalize_character_state(row["character"])
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
            _normalize_world_state(row["world"])
        )

    async def update_character(self, session_id: str, character: CharacterModel) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE game_states SET character = $1::jsonb, updated_at = now() WHERE session_id = $2",
                character.model_dump(mode="json"),
                session_id,
            )

    async def update_world(self, session_id: str, world: WorldModel) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE game_states SET world = $1::jsonb, updated_at = now() WHERE session_id = $2",
                world.model_dump(mode="json"),
                session_id,
            )

    async def append_log_entry(self, session_id: str, entry: TypedLogEntry) -> None:
        """Append a typed log entry to game_states.log for the given session.

        Used by backend-driven log writes (e.g., arc closure summaries).
        Atomic single-statement append; preserves all existing entries.
        """
        entry_payload = [entry.model_dump(exclude_none=True)]
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE game_states SET log = log || $1::jsonb, updated_at = now() WHERE session_id = $2",
                entry_payload,
                session_id,
            )

    async def get_state_full(self, session_id: str) -> FullState | None:
        """Load character + world + log + updated_at in a single query.

        Returns raw JSONB-parsed dicts/lists rather than Pydantic models so
        callers can choose whether to validate (e.g., the orchestrator may
        want to mutate before validating).
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT session_id, character, world, log, updated_at "
                "FROM game_states WHERE session_id = $1",
                session_id,
            )
        if row is None:
            return None
        return FullState(
            session_id=row["session_id"],
            character=row["character"],
            world=row["world"],
            log=row["log"],
            updated_at=row["updated_at"],
        )

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator["TransactionalStateRepository"]:
        """Yield a TransactionalStateRepository sharing one connection inside a transaction.

        Usage:
            async with state_repo.transaction() as txn:
                state = await txn.get_state_full(sid, lock=True)
                # ... mutations ...
                await txn.update_character_with_log(sid, char, log)

        Brief 20's orchestrator will use this to compose multiple operations
        atomically. Brief 19.5 introduces the surface; existing transactional
        routes migrate as they're next touched (per the incremental refactor
        policy).
        """
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield TransactionalStateRepository(conn)


class TransactionalStateRepository:
    """A StateRepository variant reusing one connection inside a transaction.

    Methods accept an optional `lock=True` to issue FOR UPDATE row locks.
    Returns raw JSONB-parsed dicts/lists; callers validate as needed.
    """

    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    async def get_character(self, session_id: str, *, lock: bool = False) -> dict[str, Any] | None:
        """Read character JSONB, optionally with FOR UPDATE row lock."""
        sql = "SELECT character FROM game_states WHERE session_id = $1"
        if lock:
            sql += " FOR UPDATE"
        row = await self._conn.fetchrow(sql, session_id)
        return row["character"] if row else None

    async def get_state_full(self, session_id: str, *, lock: bool = False) -> FullState | None:
        sql = (
            "SELECT session_id, character, world, log, updated_at "
            "FROM game_states WHERE session_id = $1"
        )
        if lock:
            sql += " FOR UPDATE"
        row = await self._conn.fetchrow(sql, session_id)
        if row is None:
            return None
        return FullState(
            session_id=row["session_id"],
            character=row["character"],
            world=row["world"],
            log=row["log"],
            updated_at=row["updated_at"],
        )

    async def update_character_with_log(
        self,
        session_id: str,
        character: dict[str, Any],
        new_log: list[Any],
    ) -> None:
        """Atomic update of character + log within the open transaction."""
        await self._conn.execute(
            "UPDATE game_states SET character = $1::jsonb, log = $2::jsonb, "
            "updated_at = NOW() WHERE session_id = $3",
            character,
            new_log,
            session_id,
        )

    async def update_character(self, session_id: str, character: CharacterModel) -> None:
        """Update character within the open transaction."""
        await self._conn.execute(
            "UPDATE game_states SET character = $1::jsonb, updated_at = now() WHERE session_id = $2",
            character.model_dump(mode="json"),
            session_id,
        )

    async def update_world(self, session_id: str, world: WorldModel) -> None:
        """Update world within the open transaction."""
        await self._conn.execute(
            "UPDATE game_states SET world = $1::jsonb, updated_at = now() WHERE session_id = $2",
            world.model_dump(mode="json"),
            session_id,
        )

    async def append_log_entry(self, session_id: str, entry: TypedLogEntry) -> None:
        """Append a typed log entry to game_states.log within the open transaction."""
        entry_payload = [entry.model_dump(exclude_none=True)]
        await self._conn.execute(
            "UPDATE game_states SET log = log || $1::jsonb, updated_at = now() WHERE session_id = $2",
            entry_payload,
            session_id,
        )