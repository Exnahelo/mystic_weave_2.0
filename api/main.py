"""
main.py — FastAPI application entry point.

Initialises the asyncpg connection pool on startup and registers all routers.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import close_pool, create_pool
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
    version="3.0.0",
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
