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
from fastapi.openapi.utils import get_openapi

from api.database import close_pool, create_pool
from api.game_data import (
    combat_rules_fingerprint,
    data_fingerprint,
    list_ancestries,
    list_backgrounds,
    list_cultures,
    list_focus,
)
from api.models import ArcTransitionLogEntry, HealthResponse, VersionResponse
from api.routes import advancement, arc, catalog, character, combat, companion, location, narrator, npcs, options, progression, registry, roll, scene, scene_records, session, state, tags


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
    version="5.5.0",
    servers=[
        {
            "url": "https://mysticweave-production.up.railway.app",
            "description": "Production (Railway)",
        }
    ],
    lifespan=lifespan,
)


def custom_openapi() -> dict:
    """Generate OpenAPI and include standalone audit-log schemas."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=app.servers,
    )
    schema.setdefault("components", {}).setdefault("schemas", {})[
        "ArcTransitionLogEntry"
    ] = ArcTransitionLogEntry.model_json_schema(ref_template="#/components/schemas/{model}")
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

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
app.include_router(advancement.router)
app.include_router(arc.router)
app.include_router(roll.router)
app.include_router(combat.router)
app.include_router(location.router)
app.include_router(options.router)
app.include_router(catalog.router)
app.include_router(scene.router)
app.include_router(tags.router)
app.include_router(companion.router)
app.include_router(npcs.router)
app.include_router(registry.router)
app.include_router(progression.router)
app.include_router(scene_records.router)
app.include_router(narrator.router)


@app.get("/", tags=["health"], response_model=HealthResponse)
async def root() -> HealthResponse:
    """Root — confirms the API is running."""
    return {"status": "ok", "service": "mystic-weave"}


@app.get("/health", tags=["health"], response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint — used by Railway and uptime monitors."""
    return {"status": "ok", "service": "mystic-weave"}


@app.get("/version", tags=["health"], response_model=VersionResponse)
async def version() -> VersionResponse:
    """Deployment/version metadata for sanity checks across environments."""
    git_sha = os.getenv("RAILWAY_GIT_COMMIT_SHA") or os.getenv("GIT_SHA") or "unknown"
    ancestry_count = len(list_ancestries())
    culture_count = len(list_cultures())
    focus_count = len(list_focus())
    backgrounds_count = len(list_backgrounds())
    return {
        "service": "mystic-weave",
        "api_version": app.version,
        "git_sha": git_sha,
        "data_fingerprint": data_fingerprint(),
        "combat_rules_fingerprint": combat_rules_fingerprint(),
        "ancestry_count": ancestry_count,
        "culture_count": culture_count,
        "focus_count": focus_count,
        "backgrounds_count": backgrounds_count,
    }
