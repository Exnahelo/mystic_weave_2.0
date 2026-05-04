"""routes/scene_records.py — Scene record CRUD endpoints (Brief 19).

Owns the persistent `scene_records` table. Distinct from routes/scene.py,
which serves /scene/{session_id} for scene-context reads.

POST /scene/declare_resolution    — narrator-facing; records a scene boundary
GET  /scene/record/{session_id}/{scene_id}  — admin/orchestrator read
GET  /scene/records/{session_id}            — admin/orchestrator paginated read

Activates the optional `scene_id` parameter on /progression/scan and
/progression/commit (Brief 18) by giving it a real backing record. Once a
scene record exists, /progression/commit can mark it `tag_advance_committed`
so a second commit on the same scene is rejected (one-tag-per-scene
enforcement at the database layer).
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query

from api.database import get_pool
from api.routes._helpers import scene_not_found, session_not_found
from api.models.progression import (
    ArcEnvelopeStatus,
    DeclareSceneResolutionRequest,
    DeclareSceneResolutionResponse,
    SceneRecord,
    SceneRecordsListResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _validate_arc_ids(
    conn: asyncpg.Connection,
    session_id: str,
    arc_ids: list[str],
) -> list[str]:
    """Verify each arc_id exists for the session. Returns list of unknown ids."""
    if not arc_ids:
        return []
    rows = await conn.fetch(
        "SELECT id FROM arcs WHERE session_id = $1 AND id = ANY($2::text[])",
        session_id,
        arc_ids,
    )
    found = {r["id"] for r in rows}
    return [aid for aid in arc_ids if aid not in found]


async def _gather_arc_envelope_status(
    conn: asyncpg.Connection,
    session_id: str,
) -> list[ArcEnvelopeStatus]:
    """Compute envelope status for all in-progress arcs in this session.

    Counts resolved scenes per arc by JSONB containment on
    scene_records.arc_progressed_ids. The just-declared scene is already
    persisted by the time this runs.
    """
    arcs = await conn.fetch(
        "SELECT id, data FROM arcs WHERE session_id = $1 AND state = 'in_progress'",
        session_id,
    )

    status_list: list[ArcEnvelopeStatus] = []
    for arc_row in arcs:
        arc_data = arc_row["data"]
        arc_id = arc_row["id"]
        budget = arc_data.get("budget", {}) or {}
        scene_soft = budget.get("resolved_scene_soft_cap", 0) or 0
        scene_hard = budget.get("resolved_scene_hard_cap", 0) or 0
        loc_soft = budget.get("location_soft_cap", 0) or 0
        loc_hard = budget.get("location_hard_cap", 0) or 0

        scene_count_row = await conn.fetchrow(
            """
            SELECT COUNT(*) AS scene_count,
                   COUNT(DISTINCT location_id) FILTER (WHERE location_id IS NOT NULL) AS loc_count
              FROM scene_records
             WHERE session_id = $1
               AND arc_progressed_ids @> $2::jsonb
            """,
            session_id,
            json.dumps([arc_id]),
        )
        scene_count = (scene_count_row["scene_count"] or 0) if scene_count_row else 0
        loc_count = (scene_count_row["loc_count"] or 0) if scene_count_row else 0

        soft_approaching = scene_count >= scene_soft if scene_soft > 0 else False
        hard_reached = scene_count >= scene_hard if scene_hard > 0 else False

        status_list.append(ArcEnvelopeStatus(
            arc_id=arc_id,
            title=arc_data.get("title", ""),
            state=arc_data.get("state", "in_progress"),
            resolved_scenes_used=scene_count,
            resolved_scene_soft_cap=scene_soft,
            resolved_scene_hard_cap=scene_hard,
            locations_visited=loc_count,
            location_soft_cap=loc_soft,
            location_hard_cap=loc_hard,
            soft_cap_approaching=soft_approaching,
            hard_cap_reached=hard_reached,
        ))

    return status_list


def _build_suggestions(envelope_status: list[ArcEnvelopeStatus]) -> list[str]:
    """Generate suggest-level guidance based on envelope status."""
    suggestions: list[str] = []
    for status in envelope_status:
        if status.hard_cap_reached:
            suggestions.append(
                f"arc {status.arc_id} ({status.title}) at hard cap "
                f"({status.resolved_scenes_used}/{status.resolved_scene_hard_cap} scenes); "
                f"transition to ready_to_close or settle"
            )
        elif status.soft_cap_approaching:
            suggestions.append(
                f"arc {status.arc_id} ({status.title}) at soft cap "
                f"({status.resolved_scenes_used}/{status.resolved_scene_soft_cap} scenes); "
                f"consider closure path"
            )
    return suggestions


# ---------------------------------------------------------------------------
# POST /scene/declare_resolution
# ---------------------------------------------------------------------------

async def declare_scene_in_transaction(
    conn: asyncpg.Connection,
    *,
    session_id: str,
    scene_summary: str | None,
    scene_actions: list[dict[str, Any]],
    location_id: str | None,
    arc_progressed_ids: list[str],
) -> dict[str, Any]:
    """Record a scene boundary using the given (already-open) transactional connection.

    Performs the same scene_records insert, arc_progressed_ids validation,
    envelope status computation, and suggestion building as the
    /scene/declare_resolution endpoint, but does not open or close the
    transaction.

    `scene_actions` is `list[dict]` (not `list[SceneAction]`) so the
    orchestrator can pass already-dumped action dicts without a re-walk.

    Returns a dict matching DeclareSceneResolutionResponse fields plus
    `session_id` for caller convenience:
    {scene_id, session_id, resolved_at, location_id, turn_at_resolution,
     arc_envelope_status, suggestions}.
    """
    row = await conn.fetchrow(
        "SELECT world FROM game_states WHERE session_id = $1",
        session_id,
    )
    if row is None:
        raise session_not_found(session_id)
    world = row["world"] or {}

    unknown = await _validate_arc_ids(conn, session_id, arc_progressed_ids)
    if unknown:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "unknown_arc_ids",
                "message": "One or more arc_progressed_ids do not belong to this session.",
                "unknown_arc_ids": unknown,
            },
        )

    resolved_location = location_id or world.get("location")
    turn = world.get("turn")
    time_state = world.get("time")

    scene_id = str(uuid.uuid4())

    await conn.execute(
        """
        INSERT INTO scene_records (
            scene_id, session_id, scene_summary, scene_actions,
            arc_progressed_ids, location_id, turn_at_resolution,
            time_at_resolution
        ) VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7, $8::jsonb)
        """,
        scene_id,
        session_id,
        scene_summary,
        json.dumps(scene_actions),
        json.dumps(arc_progressed_ids),
        resolved_location,
        turn,
        json.dumps(time_state) if time_state else None,
    )

    ts_row = await conn.fetchrow(
        "SELECT resolved_at FROM scene_records WHERE scene_id = $1",
        scene_id,
    )
    resolved_at_value = ts_row["resolved_at"] if ts_row else None
    resolved_at = (
        resolved_at_value.isoformat()
        if hasattr(resolved_at_value, "isoformat")
        else str(resolved_at_value)
    )

    envelope_status = await _gather_arc_envelope_status(conn, session_id)
    suggestions = _build_suggestions(envelope_status)

    return {
        "scene_id": scene_id,
        "session_id": session_id,
        "resolved_at": resolved_at,
        "location_id": resolved_location,
        "turn_at_resolution": turn,
        "arc_envelope_status": envelope_status,
        "suggestions": suggestions,
    }


@router.post(
    "/scene/declare_resolution",
    response_model=DeclareSceneResolutionResponse,
    tags=["scene"],
    description=(
        "Record a scene boundary. Generates scene_id, persists structured "
        "actions and arc-progression contributions, returns envelope status "
        "for active arcs with suggest-level guidance for soft/hard caps."
    ),
)
async def declare_scene_resolution(
    body: DeclareSceneResolutionRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> DeclareSceneResolutionResponse:
    """Record a scene boundary and return envelope status."""
    actions_dicts = [a.model_dump() for a in body.scene_actions]
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await declare_scene_in_transaction(
                conn,
                session_id=body.session_id,
                scene_summary=body.scene_summary,
                scene_actions=actions_dicts,
                location_id=body.location_id,
                arc_progressed_ids=body.arc_progressed_ids,
            )
    return DeclareSceneResolutionResponse(**result)


# ---------------------------------------------------------------------------
# GET /scene/record/{session_id}/{scene_id}
# ---------------------------------------------------------------------------

def _row_to_scene_record(row: Any) -> SceneRecord:
    resolved_at = row["resolved_at"]
    return SceneRecord(
        scene_id=row["scene_id"],
        session_id=row["session_id"],
        resolved_at=resolved_at.isoformat() if hasattr(resolved_at, "isoformat") else str(resolved_at),
        scene_summary=row["scene_summary"],
        scene_actions=row["scene_actions"] or [],
        tag_advance_committed=row["tag_advance_committed"],
        arc_progressed_ids=row["arc_progressed_ids"] or [],
        location_id=row["location_id"],
        turn_at_resolution=row["turn_at_resolution"],
        time_at_resolution=row["time_at_resolution"],
    )


@router.get(
    "/scene/record/{session_id}/{scene_id}",
    response_model=SceneRecord,
    tags=["scene"],
    description="Read a single scene record. Internal/admin use; not in GPT spec.",
)
async def get_scene_record(
    session_id: str,
    scene_id: str,
    pool: asyncpg.Pool = Depends(get_pool),
) -> SceneRecord:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT scene_id, session_id, resolved_at, scene_summary, scene_actions,
                   tag_advance_committed, arc_progressed_ids, location_id,
                   turn_at_resolution, time_at_resolution
              FROM scene_records
             WHERE session_id = $1 AND scene_id = $2
            """,
            session_id, scene_id,
        )
    if row is None:
        raise scene_not_found(session_id, scene_id)
    return _row_to_scene_record(row)


# ---------------------------------------------------------------------------
# GET /scene/records/{session_id}
# ---------------------------------------------------------------------------

@router.get(
    "/scene/records/{session_id}",
    response_model=SceneRecordsListResponse,
    tags=["scene"],
    description="Paginated list of scene records. Internal/admin use; not in GPT spec.",
)
async def list_scene_records(
    session_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    pool: asyncpg.Pool = Depends(get_pool),
) -> SceneRecordsListResponse:
    """Cursor-paginated list. Cursor is the resolved_at of the last item from the previous page."""
    async with pool.acquire() as conn:
        if cursor:
            rows = await conn.fetch(
                """
                SELECT scene_id, session_id, resolved_at, scene_summary, scene_actions,
                       tag_advance_committed, arc_progressed_ids, location_id,
                       turn_at_resolution, time_at_resolution
                  FROM scene_records
                 WHERE session_id = $1 AND resolved_at < $2::timestamptz
                 ORDER BY resolved_at DESC
                 LIMIT $3
                """,
                session_id, cursor, limit + 1,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT scene_id, session_id, resolved_at, scene_summary, scene_actions,
                       tag_advance_committed, arc_progressed_ids, location_id,
                       turn_at_resolution, time_at_resolution
                  FROM scene_records
                 WHERE session_id = $1
                 ORDER BY resolved_at DESC
                 LIMIT $2
                """,
                session_id, limit + 1,
            )

    has_more = len(rows) > limit
    page = rows[:limit]
    if has_more and page:
        last = page[-1]["resolved_at"]
        next_cursor = last.isoformat() if hasattr(last, "isoformat") else str(last)
    else:
        next_cursor = None

    records = [_row_to_scene_record(r) for r in page]
    return SceneRecordsListResponse(
        session_id=session_id,
        records=records,
        has_more=has_more,
        next_cursor=next_cursor,
    )
