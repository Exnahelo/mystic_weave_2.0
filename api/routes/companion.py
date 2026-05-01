"""routes/companion.py — companion CRUD and transition endpoints."""

from __future__ import annotations

import json
from datetime import datetime, UTC
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError

from api.companions import (
    ArchivedCompanionEnvelope,
    Companion,
    CompanionRecord,
    CreatureCompanion,
    CreatureCompanionRecord,
    ExceptionalCompanion,
    ExceptionalCompanionRecord,
    SapientCompanion,
    SapientCompanionRecord,
    derive_sapient_slug,
    generate_companion_id,
)
from api.database import get_pool
from api.models import CharacterModel, WorldModel
from api.routes.state import _normalize_character_state
from api.schemas.companion_schemas import CompanionResponse, CreateCompanionRequest, TransitionCompanionRequest

router = APIRouter()


def _plain_validation_errors(err: ValidationError) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for item in err.errors():
        clone = dict(item)
        ctx = clone.get("ctx")
        if isinstance(ctx, dict):
            clone["ctx"] = {k: str(v) for k, v in ctx.items()}
        cleaned.append(clone)
    return cleaned


def _character_id_from_character(character: CharacterModel) -> str:
    return derive_sapient_slug(character.name)


async def _load_session_state(conn: asyncpg.Connection, session_id: str) -> tuple[CharacterModel, WorldModel]:
    row = await conn.fetchrow(
        "SELECT character, world FROM game_states WHERE session_id = $1",
        session_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="session not found")

    try:
        character = CharacterModel.model_validate(
            _normalize_character_state(json.loads(row["character"]))
        )
        world = WorldModel.model_validate(json.loads(row["world"]))
    except ValidationError as err:
        raise HTTPException(
            status_code=500,
            detail={"message": "stored game state is invalid", "errors": _plain_validation_errors(err)},
        )
    return character, world


async def _persist_world_update(
    conn: asyncpg.Connection,
    session_id: str,
    character: CharacterModel,
    world: WorldModel,
    log_entry: str,
) -> None:
    log_entry_json = json.dumps([log_entry])
    await conn.fetchrow(
        """
        INSERT INTO game_states (session_id, character, world, log, updated_at)
        VALUES ($1, $2::jsonb, $3::jsonb, $4::jsonb, now())
        ON CONFLICT (session_id) DO UPDATE
          SET character   = EXCLUDED.character,
              world       = EXCLUDED.world,
              log         = game_states.log || $5::jsonb,
              updated_at  = now()
        RETURNING session_id
        """,
        session_id,
        json.dumps(character.model_dump(by_alias=True)),
        json.dumps(world.model_dump()),
        json.dumps([log_entry]),
        log_entry_json,
    )


def _derive_companion_slug(companion: Companion) -> str:
    if isinstance(companion, SapientCompanion):
        return derive_sapient_slug(companion.name)
    if companion.subspecies:
        return companion.subspecies
    if companion.subtype:
        return companion.subtype
    return companion.species


def _companion_to_record(companion_id: str, companion: Companion) -> CompanionRecord:
    payload = {"id": companion_id, **companion.model_dump()}
    if isinstance(companion, SapientCompanion):
        return SapientCompanionRecord.model_validate(payload)
    if isinstance(companion, ExceptionalCompanion):
        return ExceptionalCompanionRecord.model_validate(payload)
    return CreatureCompanionRecord.model_validate(payload)


def _record_to_companion(record: CompanionRecord) -> Companion:
    payload = record.model_dump(exclude={"id"})
    if isinstance(record, SapientCompanionRecord):
        return SapientCompanion.model_validate(payload)
    if isinstance(record, ExceptionalCompanionRecord):
        return ExceptionalCompanion.model_validate(payload)
    return CreatureCompanion.model_validate(payload)


@router.post("/companion/new", response_model=CompanionResponse, status_code=201)
async def create_companion(
    body: CreateCompanionRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> CompanionResponse:
    async with pool.acquire() as conn:
        character, world = await _load_session_state(conn, body.session_id)

        known_handler_ids = {_character_id_from_character(character)}
        if body.handler_id not in known_handler_ids:
            raise HTTPException(status_code=409, detail="handler_id does not match a known character_id in this session")

        derived_slug = _derive_companion_slug(body.companion)
        if isinstance(body.companion, SapientCompanion) and not derived_slug:
            raise HTTPException(status_code=422, detail="unable to derive sapient companion slug from name")

        existing_ids = {entry.id for entry in world.companions}
        companion_id = generate_companion_id(body.handler_id, derived_slug, existing_ids)
        world.companions.append(_companion_to_record(companion_id, body.companion))
        await _persist_world_update(conn, body.session_id, character, world, f"Companion added: {companion_id}")

    return CompanionResponse(companion_id=companion_id, companion=body.companion, archived=False)


@router.post("/companion/{companion_id}/transition", response_model=CompanionResponse)
async def transition_companion(
    companion_id: str,
    body: TransitionCompanionRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> CompanionResponse:
    async with pool.acquire() as conn:
        character, world = await _load_session_state(conn, body.session_id)

        target_index = next((idx for idx, entry in enumerate(world.companions) if entry.id == companion_id), None)
        if target_index is None:
            raise HTTPException(status_code=404, detail="companion not found")

        existing_companion = world.companions[target_index]
        if not isinstance(existing_companion, CreatureCompanionRecord):
            raise HTTPException(status_code=422, detail="only CreatureCompanion records can transition")

        transition_entry = {
            "from_tier": "creature",
            "to_tier": "exceptional",
            "from_subspecies": existing_companion.subspecies,
            "trigger": body.trigger,
            "transitioned_at": datetime.now(UTC).isoformat(),
        }
        new_tier_history = [*body.new_companion.tier_history, transition_entry]
        new_companion = body.new_companion.model_copy(update={"tier_history": new_tier_history})

        world.companion_archive.append(
            ArchivedCompanionEnvelope(
                id=existing_companion.id,
                companion=_record_to_companion(existing_companion),
                archived_at=datetime.now(UTC).isoformat(),
            )
        )
        world.companions[target_index] = _companion_to_record(existing_companion.id, new_companion)
        await _persist_world_update(
            conn,
            body.session_id,
            character,
            world,
            f"Companion transitioned: {existing_companion.id}",
        )

    return CompanionResponse(companion_id=existing_companion.id, companion=new_companion, archived=False)


@router.get("/companion/{companion_id}", response_model=CompanionResponse)
async def get_companion(
    companion_id: str,
    session_id: str = Query(...),
    include_archived: bool = Query(False),
    pool: asyncpg.Pool = Depends(get_pool),
) -> CompanionResponse:
    async with pool.acquire() as conn:
        _, world = await _load_session_state(conn, session_id)

    for entry in world.companions:
        if entry.id == companion_id:
            return CompanionResponse(companion_id=entry.id, companion=_record_to_companion(entry), archived=False)

    if include_archived:
        for entry in world.companion_archive:
            if entry.id == companion_id:
                return CompanionResponse(companion_id=entry.id, companion=entry.companion, archived=True)

    raise HTTPException(status_code=404, detail="companion not found")