"""
routes/inventory.py — GET and POST /inventory/{session_id}

GET  /inventory/{session_id}  — load full party inventory
POST /inventory/{session_id}  — save full party inventory (full overwrite)

Inventory is stored as a single JSONB column on game_states.
The GPT loads it at session start and saves it after any turn
where something changes — coin spent, items gained or lost, etc.

The inventory structure is free-form JSONB. The API does not validate
its contents beyond requiring a valid session and valid JSON.
"""

from __future__ import annotations

import json
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from api.database import get_pool

router = APIRouter()


@router.get("/inventory/{session_id}", tags=["inventory"])
async def load_inventory(
    session_id: str,
    pool: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    """
    Load the party inventory for a session.

    Returns 404 if the session does not exist.
    Returns an empty inventory structure if none has been saved yet.
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT inventory FROM game_states WHERE session_id = $1",
            session_id,
        )

    if row is None:
        raise HTTPException(status_code=404, detail="session not found")

    inventory = row["inventory"]
    if inventory is None:
        return {
            "session_id": session_id,
            "inventory": {
                "coin": {"pp": 0, "gp": 0, "sp": 0, "cp": 0},
                "consumables": [],
                "shared_items": [],
                "quest_items": [],
                "party_members": {},
                "notes": [],
            },
        }

    return {
        "session_id": session_id,
        "inventory": json.loads(inventory),
    }


@router.post("/inventory/{session_id}", tags=["inventory"])
async def save_inventory(
    session_id: str,
    body: dict[str, Any],
    pool: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    """
    Save the full party inventory for a session. Full overwrite.

    Call this after any turn where inventory changed:
    - Coin spent or received
    - Items picked up or dropped
    - Consumables used
    - Quest items acquired or resolved

    Returns 404 if the session does not exist.
    """
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT 1 FROM game_states WHERE session_id = $1",
            session_id,
        )
        if not exists:
            raise HTTPException(status_code=404, detail="session not found")

        await conn.execute(
            """
            UPDATE game_states
               SET inventory   = $1::jsonb,
                   updated_at  = now()
             WHERE session_id  = $2
            """,
            json.dumps(body),
            session_id,
        )

    return {
        "session_id": session_id,
        "inventory": body,
    }
