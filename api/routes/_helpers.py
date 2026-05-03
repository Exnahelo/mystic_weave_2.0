"""Shared helpers for the api.routes package.

Place small utilities here when they're used by more than one route module
and don't justify a dedicated module of their own.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError


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
