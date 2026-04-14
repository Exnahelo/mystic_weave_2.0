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


async def create_pool() -> asyncpg.Pool:
    """Create and return an asyncpg connection pool using DATABASE_URL."""
    database_url = os.environ["DATABASE_URL"]
    pool = await asyncpg.create_pool(database_url)
    return pool


async def close_pool(pool: asyncpg.Pool) -> None:
    """Gracefully close the connection pool."""
    await pool.close()


def get_pool(request: Request) -> asyncpg.Pool:
    """FastAPI dependency — returns the pool stored on app state."""
    return request.app.state.pool
