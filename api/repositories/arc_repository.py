from __future__ import annotations

import json
from typing import Any, Optional

import asyncpg

from api.models import Arc


def _coerce_jsonb_data(data: Any) -> Any:
    """Handle asyncpg JSONB codecs returning either text or decoded objects."""
    if isinstance(data, str):
        return json.loads(data)
    return data


class ArcRepository:
    """Read-only repository for Arc records. Write operations land in later commits."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def get_by_id(self, session_id: str, arc_id: str) -> Optional[Arc]:
        """Fetch a single arc by ID, scoped to session."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT data FROM arcs WHERE session_id = $1 AND id = $2",
                session_id,
                arc_id,
            )
            if row is None:
                return None
            return Arc.model_validate(_coerce_jsonb_data(row["data"]))

    async def list_by_session(self, session_id: str) -> list[Arc]:
        """Fetch all arcs for a session."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT data FROM arcs WHERE session_id = $1 ORDER BY created_at",
                session_id,
            )
            return [Arc.model_validate(_coerce_jsonb_data(row["data"])) for row in rows]

    async def list_active_by_session(self, session_id: str) -> list[Arc]:
        """Fetch arcs in active states (in_progress, at_scope_cap)."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT data FROM arcs
                WHERE session_id = $1 AND state IN ('in_progress', 'at_scope_cap')
                ORDER BY created_at
                """,
                session_id,
            )
            return [Arc.model_validate(_coerce_jsonb_data(row["data"])) for row in rows]

    async def list_children(self, session_id: str, parent_arc_id: str) -> list[Arc]:
        """Fetch all child arcs of a given parent."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT data FROM arcs
                WHERE session_id = $1 AND parent_arc_id = $2
                ORDER BY created_at
                """,
                session_id,
                parent_arc_id,
            )
            return [Arc.model_validate(_coerce_jsonb_data(row["data"])) for row in rows]