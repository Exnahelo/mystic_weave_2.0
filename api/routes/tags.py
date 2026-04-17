"""
routes/tags.py — GET /tags

Returns the canonical tag vocabularies for knowledge groups, magic fields,
and applications.
"""

from __future__ import annotations

from fastapi import APIRouter

from api.game_data import list_applications, list_knowledge_groups, list_magic_fields
from api.models import ApplicationEntry, KnowledgeGroupEntry, MagicFieldEntry, TagsResponse

router = APIRouter()


@router.get("/tags", response_model=TagsResponse, tags=["tags"])
async def get_tags() -> TagsResponse:
    """Return the canonical tag vocabularies: knowledge groups, magic fields, applications."""
    return TagsResponse(
        knowledge_groups=[KnowledgeGroupEntry(**g) for g in list_knowledge_groups()],
        magic_fields=[MagicFieldEntry(**f) for f in list_magic_fields()],
        applications=[ApplicationEntry(**a) for a in list_applications()],
    )