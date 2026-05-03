"""routes/registry.py — GET /registry/{name}

Single-entity lookup across all canonical registries: applications,
knowledge groups, magic fields, and spells. Returns the matching entity
with a `kind` discriminator, or a 404 with closest-match suggestions.

The narrator GPT calls this to verify a tag's classification before
submitting it to a state mutation. Names are globally unique across the
four registries (audited at brief landing), so the first match is the
only match.
"""

from __future__ import annotations

from difflib import get_close_matches
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.game_data import (
    list_applications,
    list_knowledge_groups,
    list_magic_fields,
    list_spells,
)

router = APIRouter()


class RegistryEntry(BaseModel):
    """A single registry entry with kind discriminator."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="The canonical name of the entity.")
    kind: Literal["application", "knowledge_group", "magic_field", "spell"] = Field(
        description="Which registry the entity belongs to."
    )
    data: dict[str, Any] = Field(
        description="The full registry record. Shape varies by kind."
    )


def _all_registry_names() -> list[str]:
    """Aggregate every canonical name across the four registries.

    Magic fields use 'id' as their canonical key; the other three use 'index'.
    """
    names = [e["index"] for e in list_applications() if "index" in e]
    names.extend(e["index"] for e in list_knowledge_groups() if "index" in e)
    names.extend(e["id"] for e in list_magic_fields() if "id" in e)
    names.extend(e["index"] for e in list_spells() if "index" in e)
    return names


@router.get(
    "/registry/{name}",
    response_model=RegistryEntry,
    tags=["registry"],
    description=(
        "Look up a single entity by canonical name across applications, "
        "knowledge groups, magic fields, and spells. Returns the matching "
        "record with a kind discriminator, or 404 with closest-match "
        "suggestions. Use to verify a tag's classification before state "
        "mutation."
    ),
)
async def get_registry_entry(name: str) -> RegistryEntry:
    """Look up a registry entry by name across all four registries."""

    for entry in list_applications():
        if entry.get("index") == name:
            return RegistryEntry(name=name, kind="application", data=entry)

    for entry in list_knowledge_groups():
        if entry.get("index") == name:
            return RegistryEntry(name=name, kind="knowledge_group", data=entry)

    for entry in list_magic_fields():
        # Magic fields use 'id' as the canonical key, not 'index'.
        if entry.get("id") == name:
            return RegistryEntry(name=name, kind="magic_field", data=entry)

    for entry in list_spells():
        if entry.get("index") == name:
            return RegistryEntry(name=name, kind="spell", data=entry)

    suggestions = get_close_matches(name, _all_registry_names(), n=5, cutoff=0.6)

    raise HTTPException(
        status_code=404,
        detail={
            "error": "unknown_registry_name",
            "message": f"Unknown registry name '{name}'.",
            "name": name,
            "suggestions": suggestions,
            "registries_searched": [
                "applications",
                "knowledge_groups",
                "magic_fields",
                "spells",
            ],
        },
    )
