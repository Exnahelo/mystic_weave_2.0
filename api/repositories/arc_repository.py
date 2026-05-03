from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

import asyncpg

from api.models import Arc, ArcConsumption, ArcState, ArcTimestamps, ArcTransitionLogEntry


class ArcNotFoundError(Exception):
    """Raised when an arc cannot be found for a repository update."""

    def __init__(self, arc_id: str) -> None:
        super().__init__(f"Arc {arc_id} not found")
        self.arc_id = arc_id


def _coerce_jsonb_data(data: Any) -> Any:
    """Passthrough kept for callsite stability — pool registers a JSONB codec
    so asyncpg always returns parsed Python objects. Retained because Brief
    19.5 only swept routes; arc_repository's call sites get inlined when this
    module is next significantly touched.
    """
    return data


class ArcRepository:
    """Repository for Arc records."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def create(self, arc: Arc) -> None:
        """Insert a new Arc record. Raises if ID collision."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO arcs (
                    id, session_id, primary_type, state, parent_arc_id, data,
                    created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $7)
                """,
                arc.id,
                arc.session_id,
                arc.primary_type,
                arc.state,
                arc.parent_arc_id,
                arc.model_dump_json(),
                arc.timestamps.created_at,
            )

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

    async def get_by_id_unsafe(self, arc_id: str) -> Arc | None:
        """
        Fetch by arc_id without session scoping. Used internally for updates
        after the route layer has already validated session ownership.
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT data FROM arcs WHERE id = $1",
                arc_id,
            )
            if row is None:
                return None
            return Arc.model_validate(_coerce_jsonb_data(row["data"]))

    async def update_arc(
        self,
        arc_id: str,
        new_state: ArcState,
        consumption: ArcConsumption,
        timestamps: ArcTimestamps,
        full_arc: Arc | None = None,
    ) -> None:
        """
        Update an arc's state, consumption, and timestamps atomically.

        If full_arc is provided, it is used as the source of truth for the
        serialized data column. This is required when updating list fields
        like spawned_arc_ids, merge_source_arc_ids, or settlement that aren't
        covered by the state/consumption/timestamps tuple.
        """
        if full_arc is None:
            arc = await self.get_by_id_unsafe(arc_id)
            if arc is None:
                raise ArcNotFoundError(arc_id)
            arc.state = new_state
            arc.consumption = consumption
            arc.timestamps = timestamps
        else:
            arc = full_arc
            arc.state = new_state
            arc.consumption = consumption
            arc.timestamps = timestamps

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE arcs
                SET state = $1, data = $2, updated_at = $3
                WHERE id = $4
                """,
                new_state,
                arc.model_dump_json(),
                timestamps.last_progressed_at or datetime.now(timezone.utc),
                arc_id,
            )

    async def append_transition_log(
        self,
        entry: ArcTransitionLogEntry,
    ) -> None:
        """Append an audit record for a state transition."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO arc_transitions (
                    arc_id, session_id, from_state, to_state, reason,
                    transitioned_at, resolved_scenes_at_transition,
                    locations_visited_at_transition, triggering_event
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                entry.arc_id,
                entry.session_id,
                entry.from_state,
                entry.to_state,
                entry.reason,
                entry.transitioned_at,
                entry.resolved_scenes_at_transition,
                json.dumps(entry.locations_visited_at_transition),
                entry.triggering_event,
            )

    async def get_transition_log(
        self,
        arc_id: str,
    ) -> list[ArcTransitionLogEntry]:
        """Fetch the full transition history for an arc, oldest first."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT arc_id, session_id, from_state, to_state, reason,
                       transitioned_at, resolved_scenes_at_transition,
                       locations_visited_at_transition, triggering_event
                FROM arc_transitions
                WHERE arc_id = $1
                ORDER BY transitioned_at ASC, id ASC
                """,
                arc_id,
            )
            return [
                ArcTransitionLogEntry(
                    arc_id=row["arc_id"],
                    session_id=row["session_id"],
                    from_state=row["from_state"],
                    to_state=row["to_state"],
                    reason=row["reason"],
                    transitioned_at=row["transitioned_at"],
                    resolved_scenes_at_transition=row["resolved_scenes_at_transition"],
                    locations_visited_at_transition=_coerce_jsonb_data(
                        row["locations_visited_at_transition"]
                    ),
                    triggering_event=row["triggering_event"],
                )
                for row in rows
            ]

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