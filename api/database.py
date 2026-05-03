"""
database.py — asyncpg connection pool utilities.

The pool is stored on the FastAPI app's state object and accessed
via the get_pool() dependency. JSON/JSONB codecs are registered at
pool init so consumers always receive parsed Python objects (not
strings) when reading JSONB columns. This eliminates the
`json.loads(x) if isinstance(x, str) else x` defensive pattern from
routes and repositories.
"""

import json
import os

import asyncpg
from dotenv import load_dotenv
from fastapi import Request

load_dotenv()


async def _register_codecs(conn: asyncpg.Connection) -> None:
    """Register JSON/JSONB codecs so JSONB columns return parsed objects."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
        format="text",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
        format="text",
    )


async def create_pool() -> asyncpg.Pool | None:
    """Create and return an asyncpg connection pool using DATABASE_URL.

    Registers JSON/JSONB codecs on every connection so JSONB columns are
    always returned as parsed Python dicts/lists rather than strings.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None
    pool = await asyncpg.create_pool(database_url, init=_register_codecs)
    return pool


async def close_pool(pool: asyncpg.Pool | None) -> None:
    """Gracefully close the connection pool."""
    if pool is None:
        return
    await pool.close()


def get_pool(request: Request) -> asyncpg.Pool:
    """FastAPI dependency — returns the pool stored on app state."""
    pool = request.app.state.pool
    if pool is None:
        raise RuntimeError("DATABASE_URL is not configured")
    return pool
