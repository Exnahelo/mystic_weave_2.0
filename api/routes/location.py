"""
routes/location.py — Location graph endpoints

GET  /location/{location_id}      — load location data before describing any place
POST /location                    — create or update a location (discovered locations must be saved immediately)
GET  /location/{location_id}/connections   — get valid movement options from current location
"""

from __future__ import annotations

import json

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.database import get_pool
from api.models import (
    ConnectionInfo,
    ConnectionsResponse,
    LocationData,
    LocationResponse,
)

router = APIRouter()


@router.get("/location/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: str,
    pool: asyncpg.Pool = Depends(get_pool),
) -> LocationResponse:
    """
    Load location data. The GPT must call this before describing any place.
    Returns 404 if the location does not exist in the database.
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, data, updated_at FROM locations WHERE id = $1",
            location_id,
        )

    if row is None:
        raise HTTPException(status_code=404, detail="location not found")

    return LocationResponse(
        id=row["id"],
        name=row["name"],
        data=row["data"],
        updated_at=row["updated_at"],
    )


@router.post(
    "/location",
    response_model=LocationResponse,
    status_code=201,
    description=(
        "Create or update a location via UPSERT, and persist valid world-graph "
        "connections from the payload."
    ),
    responses={200: {"model": LocationResponse, "description": "Location updated"}},
)
async def upsert_location(
    body: LocationData,
    response: Response,
    pool: asyncpg.Pool = Depends(get_pool),
) -> LocationResponse:
    """
    Create or update a location.

    The GPT calls this when:
    - A player discovers a new location via an exploration action
    - The GPT invents a new detail (NPC name, building) that must persist

    Uses UPSERT so the same endpoint handles both creation and updates.
    Also upserts world_graph edges based on the connections array in the data.
    """
    data_dict = body.model_dump()

    async with pool.acquire() as conn:
        existed = await conn.fetchval("SELECT 1 FROM locations WHERE id = $1", body.id)

        row = await conn.fetchrow(
            """
            INSERT INTO locations (id, name, data, updated_at)
            VALUES ($1, $2, $3::jsonb, now())
            ON CONFLICT (id) DO UPDATE
              SET name       = EXCLUDED.name,
                  data       = EXCLUDED.data,
                  updated_at = now()
            RETURNING id, name, data, updated_at
            """,
            body.id,
            body.name,
            json.dumps(data_dict),
        )

        # Treat the saved connections array as authoritative for this source.
        # Remove outbound graph edges that were present in an earlier version of
        # the location but are no longer listed in the updated payload.
        await conn.execute(
            """
            DELETE FROM world_graph
             WHERE from_id = $1
               AND NOT (to_id = ANY($2::text[]))
            """,
            body.id,
            body.connections,
        )

        # Upsert world_graph edges for each connection listed in the data.
        # We only insert edges where the target location already exists,
        # to avoid FK violations. If a target did not exist at the time a source
        # location was saved, we backfill those edges when that target is later
        # created (see query below).
        for target_id in body.connections:
            target_exists = await conn.fetchval(
                "SELECT 1 FROM locations WHERE id = $1", target_id
            )
            if target_exists:
                await conn.execute(
                    """
                    INSERT INTO world_graph (from_id, to_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                    """,
                    body.id,
                    target_id,
                )

        # Backfill inbound edges from previously saved locations that already
        # referenced this location in their `data.connections` array.
        inbound_rows = await conn.fetch(
            """
            SELECT id
              FROM locations
             WHERE id <> $1
               AND (data->'connections') ? $1
            """,
            body.id,
        )
        for inbound in inbound_rows:
            await conn.execute(
                """
                INSERT INTO world_graph (from_id, to_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
                """,
                inbound["id"],
                body.id,
            )

    if existed:
        response.status_code = status.HTTP_200_OK

    return LocationResponse(
        id=row["id"],
        name=row["name"],
        data=row["data"],
        updated_at=row["updated_at"],
    )


@router.get("/location/{location_id}/connections", response_model=ConnectionsResponse)
async def get_connections(
    location_id: str,
    pool: asyncpg.Pool = Depends(get_pool),
) -> ConnectionsResponse:
    """
    Return all valid movement options from the given location.

    The GPT may only move the player to locations listed here.
    Movement to unlisted locations is not permitted.
    """
    async with pool.acquire() as conn:
        # Verify location exists
        exists = await conn.fetchval(
            "SELECT 1 FROM locations WHERE id = $1", location_id
        )
        if not exists:
            raise HTTPException(status_code=404, detail="location not found")

        rows = await conn.fetch(
            """
            SELECT to_id, traversal, distance
            FROM world_graph
            WHERE from_id = $1
            """,
            location_id,
        )

    connections = [
        ConnectionInfo(
            to_id=row["to_id"],
            traversal=row["traversal"],
            distance=row["distance"],
        )
        for row in rows
    ]

    return ConnectionsResponse(from_id=location_id, connections=connections)
