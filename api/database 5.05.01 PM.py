"""
database.py — asyncpg connection pool and table initialization.

The pool is stored on the FastAPI app's state object and accessed
via the get_pool() dependency. Tables are created on startup if they
do not already exist.
"""

import os
import asyncpg
from dotenv import load_dotenv
from fastapi import Request

load_dotenv()


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS game_states (
    session_id   TEXT PRIMARY KEY,
    character    JSONB NOT NULL,
    world        JSONB NOT NULL,
    log          JSONB NOT NULL DEFAULT '[]',
    inventory    JSONB DEFAULT NULL,
    updated_at   TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS locations (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    data         JSONB NOT NULL,
    updated_at   TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS world_graph (
    from_id      TEXT REFERENCES locations(id),
    to_id        TEXT REFERENCES locations(id),
    traversal    TEXT,
    distance     TEXT,
    PRIMARY KEY (from_id, to_id)
);
"""


async def create_pool() -> asyncpg.Pool:
    """Create and return an asyncpg connection pool using DATABASE_URL."""
    database_url = os.environ["DATABASE_URL"]
    pool = await asyncpg.create_pool(database_url)
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLES_SQL)
    return pool


async def close_pool(pool: asyncpg.Pool) -> None:
    """Gracefully close the connection pool."""
    await pool.close()


def get_pool(request: Request) -> asyncpg.Pool:
    """FastAPI dependency — returns the pool stored on app state."""
    return request.app.state.pool
