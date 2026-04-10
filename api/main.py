"""
main.py — FastAPI application entry point.

Initialises the asyncpg connection pool on startup and registers all routers.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import close_pool, create_pool
from api.game_data import (
    data_fingerprint,
    list_backgrounds,
    list_focus,
    list_species,
)
from api.routes import character, location, options, roll, session, state


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create the DB pool on startup; close it on shutdown."""
    app.state.pool = await create_pool()
    yield
    await close_pool(app.state.pool)


app = FastAPI(
    title="Mystic Weave",
    description=(
        "Persistent game state backend for a text-based RPG powered by a custom GPT. "
        "The GPT is the narrator; this API is the memory. "
        "d100 roll-under resolution with domain scores and competency tiers."
    ),
    version="3.1.0",
    lifespan=lifespan,
)

# Allow all origins — required for GPT builder Actions to reach the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(state.router)
app.include_router(session.router)
app.include_router(character.router)
app.include_router(roll.router)
app.include_router(location.router)
app.include_router(options.router)


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    """Root — confirms the API is running."""
    return {"status": "ok", "service": "mystic-weave"}


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint — used by Railway and uptime monitors."""
    return {"status": "ok", "service": "mystic-weave"}


@app.get("/version", tags=["health"])
async def version() -> dict[str, str | int]:
    """Deployment/version metadata for sanity checks across environments."""
    git_sha = os.getenv("RAILWAY_GIT_COMMIT_SHA") or os.getenv("GIT_SHA") or "unknown"
    species_count = len(list_species())
    focus_count = len(list_focus())
    backgrounds_count = len(list_backgrounds())
    return {
        "service": "mystic-weave",
        "api_version": app.version,
        "git_sha": git_sha,
        "data_fingerprint": data_fingerprint(),
        "species_count": species_count,
        "focus_count": focus_count,
        "backgrounds_count": backgrounds_count,
    }
