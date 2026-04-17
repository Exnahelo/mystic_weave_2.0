"""
database.py — asyncpg connection pool utilities.

The pool is stored on the FastAPI app's state object and accessed
via the get_pool() dependency.
"""

import os

import asyncpg
from dotenv import load_dotenv
from fastapi import Request

load_dotenv()


async def create_pool() -> asyncpg.Pool | None:
    """Create and return an asyncpg connection pool using DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None
    pool = await asyncpg.create_pool(database_url)
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
