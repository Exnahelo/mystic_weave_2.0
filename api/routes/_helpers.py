"""Shared helpers for the api.routes package.

Place small utilities here when they're used by more than one route module
and don't justify a dedicated module of their own.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import asyncpg
from fastapi import Depends, HTTPException
from pydantic import ValidationError

from api.database import get_pool

if TYPE_CHECKING:
    from api.repositories.state_repository import StateRepository


def plain_validation_errors(err: ValidationError) -> list[dict[str, Any]]:
    """Return JSON-serializable pydantic errors without python exception objects.

    Pydantic's `errors()` output can contain Exception instances inside the
    `ctx` dict for some error kinds. FastAPI's default JSON encoder cannot
    serialize those. This helper stringifies any `ctx` values so the errors
    list survives a 422 response body.
    """
    cleaned: list[dict[str, Any]] = []
    for item in err.errors():
        clone = dict(item)
        ctx = clone.get("ctx")
        if isinstance(ctx, dict):
            clone["ctx"] = {k: str(v) for k, v in ctx.items()}
        cleaned.append(clone)
    return cleaned


def get_state_repository(
    pool: asyncpg.Pool = Depends(get_pool),
) -> "StateRepository":
    """FastAPI dependency for shared StateRepository access.

    Imports StateRepository lazily because state_repository imports the
    `_normalize_*` helpers from `api.routes.state`, which in turn imports
    this module — a top-level import would close the cycle.
    """
    from api.repositories.state_repository import StateRepository
    return StateRepository(pool)


# ---------------------------------------------------------------------------
# Common HTTP error responses
# ---------------------------------------------------------------------------

def session_not_found(session_id: str | None = None) -> HTTPException:
    """Standard 404 for missing session. Caller raises the result."""
    detail: dict[str, Any] = {"error": "session_not_found"}
    if session_id is not None:
        detail["session_id"] = session_id
    return HTTPException(status_code=404, detail=detail)


def scene_not_found(session_id: str | None = None, scene_id: str | None = None) -> HTTPException:
    """Standard 404 for missing scene record."""
    detail: dict[str, Any] = {"error": "scene_record_not_found"}
    if session_id is not None:
        detail["session_id"] = session_id
    if scene_id is not None:
        detail["scene_id"] = scene_id
    return HTTPException(status_code=404, detail=detail)


def tag_not_held(message: str) -> HTTPException:
    """Standard 422 for character not holding the proposed tag.

    Takes a context-specific message because the kind of tag (application,
    spell, group, field) shows up in the message body in production.
    """
    return HTTPException(
        status_code=422,
        detail={"error": "tag_not_held", "message": message},
    )


def at_max_tier(current_tier: int) -> HTTPException:
    """Standard 422 for tag already at tier 5."""
    return HTTPException(
        status_code=422,
        detail={"error": "at_max_tier", "current_tier": current_tier},
    )
