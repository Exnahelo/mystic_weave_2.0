"""
database.py — asyncpg connection pool and table initialization.

The pool is stored on the FastAPI app's state object and accessed
via the get_pool() dependency. Database schema is managed by Alembic
migrations executed on startup.
"""

import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from fastapi import Request

load_dotenv()


def _run_migrations(database_url: str) -> None:
    """Run Alembic migrations to head using the current DATABASE_URL."""
    # Imported lazily so tooling/tests that don't execute startup are unaffected
    # when dependencies are not yet installed in a fresh environment.
    from alembic import command
    from alembic.config import Config

    repo_root = Path(__file__).resolve().parents[1]
    alembic_ini = repo_root / "alembic.ini"

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(repo_root / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


async def create_pool() -> asyncpg.Pool:
    """Create and return an asyncpg connection pool using DATABASE_URL."""
    database_url = os.environ["DATABASE_URL"]
    _run_migrations(database_url)
    pool = await asyncpg.create_pool(database_url)
    return pool


async def close_pool(pool: asyncpg.Pool) -> None:
    """Gracefully close the connection pool."""
    await pool.close()


def get_pool(request: Request) -> asyncpg.Pool:
    """FastAPI dependency — returns the pool stored on app state."""
    return request.app.state.pool
