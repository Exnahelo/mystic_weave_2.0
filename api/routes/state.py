"""
routes/state.py — GET and POST /state/{session_id}

GET  /state/{session_id}  — load full game state (used at session start)
POST /state/{session_id}  — save full game state + append log entry (used after each turn)

IMPORTANT: The save endpoint performs a deep merge of the incoming character
onto the stored character. This means fields the GPT omits are preserved from
the previous save rather than wiped. Only fields explicitly sent are updated.
"""

from __future__ import annotations

import json
from typing import Any


import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from api.database import get_pool
from api.models import (
    AdvancementState,
    ApplyStateDeltaRequest,
    CharacterModel,
    Equipment,
    GameStateResponse,
    PacingState,
    SaveStateRequest,
    SurvivalState,
    TimeState,
    TypedLogEntry,
    WeatherState,
    WorldModel,
)
from api.sql.game_state_sql import (
    GAME_STATE_UPSERT_PRESERVE_LOG,
    GAME_STATE_UPSERT_WITH_LOG_APPEND,
)
from api.time_advance import advance_time

router = APIRouter()


def _plain_validation_errors(err: ValidationError) -> list[dict[str, Any]]:
    """Return JSON-serializable pydantic errors without python exception objects."""
    cleaned: list[dict[str, Any]] = []
    for item in err.errors():
        clone = dict(item)
        ctx = clone.get("ctx")
        if isinstance(ctx, dict):
            clone["ctx"] = {k: str(v) for k, v in ctx.items()}
        cleaned.append(clone)
    return cleaned


def _serialize_log_entry(entry: str | TypedLogEntry | None) -> str | None:
    """Serialize a log entry into the JSONB array form, or None to skip append."""
    if entry is None:
        return None
    if isinstance(entry, TypedLogEntry):
        return json.dumps([entry.model_dump(exclude_none=True)])
    return json.dumps([entry])


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """
    Deep-merge `incoming` onto `base`.

    Rules:
    - For each key in `incoming`:
      - If the value is a non-empty dict and the base value is also a dict,
        recurse.
      - If the value is a non-empty list, replace the base value.
      - If the value is None and the base has a non-None value, keep the base
        value (prevents accidental nulling of established fields).
      - Otherwise, use the incoming value.
    - Keys in `base` not present in `incoming` are preserved unchanged.
    """
    result = dict(base)
    for key, inc_val in incoming.items():
        base_val = result.get(key)
        if isinstance(inc_val, dict) and isinstance(base_val, dict) and inc_val:
            result[key] = _deep_merge(base_val, inc_val)
        elif inc_val is None and base_val is not None:
            # Don't wipe an established value with None
            pass
        else:
            result[key] = inc_val
    return result


def _normalize_character_state(payload: dict[str, Any]) -> dict[str, Any]:
    """Backfill missing structured character fields for legacy/incomplete payloads."""
    normalized = dict(payload)
    if not isinstance(normalized.get("knowledge"), dict):
        normalized["knowledge"] = {}
    if not isinstance(normalized.get("magic"), dict):
        normalized["magic"] = {}
    # Strip legacy v4 flat fields if a stale payload still carries them.
    normalized.pop("application", None)
    normalized.pop("fields", None)
    advancement = normalized.get("advancement")
    if not isinstance(advancement, dict):
        normalized["advancement"] = AdvancementState().model_dump()
    else:
        adv = dict(advancement)
        adv.setdefault("points_available", 0)
        adv.setdefault("points_spent", 0)
        adv.setdefault("points_earned_total", 0)
        adv.setdefault("tag_counter", 0)
        # Awarded AP is granted through the normal state-save path: the GPT
        # includes settled points_available / points_earned_total values in
        # the next save. No dedicated award_ap endpoint is needed for v4.5.0.
        for stale_key in (
            "points_available_earned",
            "points_available_awarded",
            "tag_advance_counters",
        ):
            adv.pop(stale_key, None)
        normalized["advancement"] = adv
    return normalized


def _apply_tag_advancement_counters(
    existing_character: dict[str, Any],
    delta_character: dict[str, Any],
) -> dict[str, Any]:
    """
    Detect tag tier increases in the delta vs. existing character. Each tier
    advance increments the single tag_counter. Every 3 advances rolls over
    to +1 in points_available (counter resets to 0).

    Walks the v5 nested shape: knowledge groups carry their applications,
    magic fields carry their spells. Group/field tier advances and child
    (application/spell) tier advances both contribute one advance per tier.
    Non-canonical tags are skipped defensively.

    Caller is responsible for merging the returned advancement dict back
    onto the character.
    """
    from api.game_data import get_tag_primary_domain

    advancement = dict(existing_character.get("advancement") or {})
    counter = int(advancement.get("tag_counter", 0) or 0)
    available = int(advancement.get("points_available", 0) or 0)
    earned_total = int(advancement.get("points_earned_total", 0) or 0)

    advances = 0

    # --- Knowledge groups + their nested applications ---
    delta_knowledge = delta_character.get("knowledge") or {}
    existing_knowledge = existing_character.get("knowledge") or {}
    if isinstance(delta_knowledge, dict) and isinstance(existing_knowledge, dict):
        for group_name, group_block in delta_knowledge.items():
            if not isinstance(group_block, dict):
                continue
            existing_group = existing_knowledge.get(group_name) or {}
            existing_group = existing_group if isinstance(existing_group, dict) else {}

            new_group_tier = group_block.get("tier")
            if isinstance(new_group_tier, int):
                old_group_tier = existing_group.get("tier", 0) or 0
                if new_group_tier > old_group_tier:
                    if get_tag_primary_domain(group_name, "knowledge") is not None:
                        advances += new_group_tier - old_group_tier

            delta_apps = group_block.get("applications") or {}
            existing_apps = existing_group.get("applications") or {}
            if isinstance(delta_apps, dict):
                for app, new_app_tier in delta_apps.items():
                    if not isinstance(new_app_tier, int):
                        continue
                    old_app_tier = existing_apps.get(app, 0) if isinstance(existing_apps, dict) else 0
                    old_app_tier = old_app_tier or 0
                    if new_app_tier <= old_app_tier:
                        continue
                    if get_tag_primary_domain(app, "application") is None:
                        continue
                    advances += new_app_tier - old_app_tier

    # --- Magic fields + their nested spells ---
    delta_magic = delta_character.get("magic") or {}
    existing_magic = existing_character.get("magic") or {}
    if isinstance(delta_magic, dict) and isinstance(existing_magic, dict):
        for field_name, field_block in delta_magic.items():
            if not isinstance(field_block, dict):
                continue
            existing_field = existing_magic.get(field_name) or {}
            existing_field = existing_field if isinstance(existing_field, dict) else {}

            new_field_tier = field_block.get("tier")
            if isinstance(new_field_tier, int):
                old_field_tier = existing_field.get("tier", 0) or 0
                if new_field_tier > old_field_tier:
                    if get_tag_primary_domain(field_name, "field") is not None:
                        advances += new_field_tier - old_field_tier

            delta_spells = field_block.get("spells") or {}
            existing_spells = existing_field.get("spells") or {}
            if isinstance(delta_spells, dict):
                for spell, new_spell_tier in delta_spells.items():
                    if not isinstance(new_spell_tier, int):
                        continue
                    old_spell_tier = existing_spells.get(spell, 0) if isinstance(existing_spells, dict) else 0
                    old_spell_tier = old_spell_tier or 0
                    if new_spell_tier <= old_spell_tier:
                        continue
                    if get_tag_primary_domain(spell, "spell") is None:
                        continue
                    advances += new_spell_tier - old_spell_tier

    counter += advances
    while counter >= 3:
        counter -= 3
        available += 1
        earned_total += 1

    advancement["tag_counter"] = counter
    advancement["points_available"] = available
    advancement["points_earned_total"] = earned_total
    advancement.setdefault("points_spent", 0)

    for stale_key in (
        "points_available_earned",
        "points_available_awarded",
        "tag_advance_counters",
    ):
        advancement.pop(stale_key, None)

    return advancement


def _apply_advancement_and_validate_caps(
    existing_character: dict[str, Any],
    incoming_character: dict[str, Any],
) -> dict[str, Any]:
    """
    Run the shared advancement-counter update used by both
    /state/{session_id} (full save) and /state/{session_id}/delta.

    Parent-cap enforcement is structural in v5: KnowledgeGroupRecord and
    MagicFieldRecord raise at model construction if a child tier exceeds
    its parent. The wrapper remains for symmetry and to keep the call site
    in `apply_delta` legible.
    """
    return _apply_tag_advancement_counters(existing_character, incoming_character)


def _normalize_world_state(payload: dict[str, Any]) -> dict[str, Any]:
    """Backfill missing structured world fields for legacy/incomplete payloads."""
    normalized = dict(payload)
    if not isinstance(normalized.get("time"), dict):
        normalized["time"] = TimeState().model_dump()
    if not isinstance(normalized.get("survival"), dict):
        normalized["survival"] = SurvivalState().model_dump()
    if not isinstance(normalized.get("pacing"), dict):
        normalized["pacing"] = PacingState().model_dump()
    return normalized


def _merge_equipment_slots(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Merge equipment by slot so one slot update does not replace the full object."""
    normalized_base = Equipment.model_validate(base).model_dump()
    result = dict(normalized_base)
    for slot in ("worn", "carried", "stashed"):
        if slot in incoming and incoming[slot] is not None:
            result[slot] = incoming[slot]
    return result


def validate_delta(delta: ApplyStateDeltaRequest) -> None:
    """Validate delta-level invariants before state application."""
    if isinstance(delta.log_entry, str) and not delta.log_entry.strip():
        raise ValueError("log_entry is required")
    if not delta.character.has_updates() and not delta.world.has_updates():
        raise ValueError("delta must change state")


def apply_delta(current_state: dict[str, Any], delta: ApplyStateDeltaRequest) -> dict[str, Any]:
    """
    Delta application semantics:

    - Delta payloads are additive and sparse. Any field absent from the delta preserves
      the current stored value unchanged.
    - Character/world scalar fields overwrite the current stored value when present.
    - Dictionary fields such as knowledge and application are deep-merged by key.
    - Equipment merges by slot (`worn`, `carried`, `stashed`) so a slot update does not
      replace the entire equipment object.
    - List fields such as status_effects, reputation, companions, and other list-based
      state replace the stored list when present in the delta.
    - Typed world sub-objects (`economy`, `politics`, `time`, `survival`, `pacing`) replace
      that sub-object as a unit when present in the delta.
    - The log_entry delta is appended to the stored log; it never replaces prior log history.
    - Validation failure occurs when the delta is malformed, contains no changes, or applying
      it produces a final state that fails CharacterModel or WorldModel validation.
    - On any validation failure, no state is committed. The previously stored state and log
      remain unchanged.
    """
    character_delta = delta.character.model_dump(exclude_unset=True, by_alias=True)
    world_delta = delta.world.model_dump(exclude_unset=True)

    existing_character = json.loads(current_state["character"])
    existing_world = json.loads(current_state["world"])

    new_advancement = _apply_advancement_and_validate_caps(existing_character, character_delta)
    character_delta["advancement"] = new_advancement

    normalized_existing_world = _normalize_world_state(existing_world)
    existing_time = TimeState.model_validate(normalized_existing_world["time"])
    new_time = advance_time(existing_time, delta.time_elapsed)

    incoming_time = world_delta.get("time") if isinstance(world_delta.get("time"), dict) else {}
    if "weather" in incoming_time:
        weather_val = incoming_time["weather"]
        if isinstance(weather_val, str):
            weather_val = WeatherState(weather_val)
        new_time = new_time.model_copy(update={"weather": weather_val})
    if "weather_note" in incoming_time:
        new_time = new_time.model_copy(update={"weather_note": incoming_time["weather_note"]})

    equipment_delta = character_delta.pop("equipment", None)
    merged_character = _deep_merge(existing_character, character_delta)
    if equipment_delta is not None:
        merged_character["equipment"] = _merge_equipment_slots(
            existing_character.get("equipment", {}), equipment_delta
        )

    merged_world = _deep_merge(existing_world, world_delta)
    merged_world["time"] = new_time.model_dump(mode="json")

    merged_character = _normalize_character_state(merged_character)
    merged_world = _normalize_world_state(merged_world)

    validated_character = CharacterModel.model_validate(merged_character)
    validated_world = WorldModel.model_validate(merged_world)
    validated_world.pacing.turn_count = validated_world.turn

    return {
        "character": validated_character.model_dump(by_alias=True),
        "world": validated_world.model_dump(),
    }


@router.get("/state/{session_id}", response_model=GameStateResponse)
async def load_state(
    session_id: str,
    pool: asyncpg.Pool = Depends(get_pool),
) -> GameStateResponse:
    """Load the full game state for a session. Returns 404 if not found."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT session_id, character, world, log, updated_at "
            "FROM game_states WHERE session_id = $1",
            session_id,
        )

    if row is None:
        raise HTTPException(status_code=404, detail="session not found")

    try:
        character = CharacterModel.model_validate(
            _normalize_character_state(json.loads(row["character"]))
        )
        world = WorldModel.model_validate(json.loads(row["world"]))
    except ValidationError as e:
        raise HTTPException(status_code=500, detail={"message": "stored game state is invalid", "errors": e.errors()})

    return GameStateResponse(
        session_id=row["session_id"],
        character=character,
        world=world,
        log=json.loads(row["log"]),
        updated_at=row["updated_at"],
    )


@router.post(
    "/state/{session_id}",
    response_model=GameStateResponse,
    description=(
        "Save game state, deep-merge character and world updates onto stored state, "
        "and append one log entry atomically."
    ),
)
async def save_state(
    session_id: str,
    body: SaveStateRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> GameStateResponse:
    """
    Save full game state and append a log entry.

    Character fields are deep-merged onto the stored record so that fields
    the GPT omits (languages, spells, equipment, feat_choices, biography, etc.)
    are preserved from the previous save rather than wiped.

    World fields are deep-merged onto the stored record so that older/minimal
    payloads do not wipe structured state blocks.
    The log_entry is appended atomically in SQL.
    """
    incoming_character = body.character.model_dump(exclude_unset=True, by_alias=True)
    world_json = body.world.model_dump(exclude_unset=True)
    log_payload = _serialize_log_entry(body.log_entry)
    if log_payload is None:
        insert_log = json.dumps([])
        sql = GAME_STATE_UPSERT_PRESERVE_LOG
    else:
        insert_log = log_payload
        sql = GAME_STATE_UPSERT_WITH_LOG_APPEND

    async with pool.acquire() as conn:
        # Load existing state to merge against
        existing_row = await conn.fetchrow(
            "SELECT character, world FROM game_states WHERE session_id = $1",
            session_id,
        )
        if existing_row is not None:
            existing_character: dict[str, Any] = json.loads(existing_row["character"])
            existing_world: dict[str, Any] = json.loads(existing_row["world"])

            # Run advancement counters and parent-cap validation against the
            # incoming payload before merge, mirroring the delta endpoint.
            # First saves (existing_row is None) skip this; counter updates
            # require a prior state to diff against.
            incoming_character["advancement"] = _apply_advancement_and_validate_caps(
                existing_character, incoming_character
            )

            normalized_existing_world = _normalize_world_state(existing_world)
            existing_time = TimeState.model_validate(normalized_existing_world["time"])
            new_time = advance_time(existing_time, body.time_elapsed)

            incoming_time = world_json.get("time") if isinstance(world_json.get("time"), dict) else {}
            if "weather" in incoming_time:
                weather_val = incoming_time["weather"]
                if isinstance(weather_val, str):
                    weather_val = WeatherState(weather_val)
                new_time = new_time.model_copy(update={"weather": weather_val})
            if "weather_note" in incoming_time:
                new_time = new_time.model_copy(update={"weather_note": incoming_time["weather_note"]})

            merged_character = _deep_merge(existing_character, incoming_character)
            merged_world = _deep_merge(existing_world, world_json)
            merged_world["time"] = new_time.model_dump(mode="json")
        else:
            merged_character = incoming_character
            merged_world = world_json

        merged_character = _normalize_character_state(merged_character)
        merged_world = _normalize_world_state(merged_world)

        try:
            validated_character = CharacterModel.model_validate(merged_character)
            validated_world = WorldModel.model_validate(merged_world)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=_plain_validation_errors(e))

        # Authoritative turn counter is world.turn; pacing.turn_count mirrors it.
        validated_world.pacing.turn_count = validated_world.turn

        merged_character_json = validated_character.model_dump(by_alias=True)
        validated_world_json = validated_world.model_dump()

        params = [
            session_id,
            json.dumps(merged_character_json),
            json.dumps(validated_world_json),
            insert_log,
        ]
        if log_payload is not None:
            params.append(log_payload)

        row = await conn.fetchrow(sql, *params)

    try:
        response_character = CharacterModel.model_validate(
            _normalize_character_state(json.loads(row["character"]))
        )
        response_world = WorldModel.model_validate(json.loads(row["world"]))
    except ValidationError as e:
        raise HTTPException(status_code=500, detail={"message": "stored game state is invalid", "errors": e.errors()})

    return GameStateResponse(
        session_id=row["session_id"],
        character=response_character,
        world=response_world,
        log=json.loads(row["log"]),
        updated_at=row["updated_at"],
    )


@router.post(
    "/state/{session_id}/delta",
    response_model=GameStateResponse,
    description=(
        "Apply a validated structured state delta to stored game state, then append one log "
        "entry atomically."
    ),
)
async def save_state_delta(
    session_id: str,
    body: ApplyStateDeltaRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> GameStateResponse:
    """Apply partial typed state updates and persist validated full state."""
    log_payload = _serialize_log_entry(body.log_entry)
    if log_payload is None:
        insert_log = json.dumps([])
        sql = GAME_STATE_UPSERT_PRESERVE_LOG
    else:
        insert_log = log_payload
        sql = GAME_STATE_UPSERT_WITH_LOG_APPEND

    async with pool.acquire() as conn:
        existing_row = await conn.fetchrow(
            "SELECT character, world FROM game_states WHERE session_id = $1",
            session_id,
        )

        if existing_row is None:
            raise HTTPException(status_code=404, detail="session not found")

        try:
            validate_delta(body)
            applied = apply_delta(
                {
                    "character": existing_row["character"],
                    "world": existing_row["world"],
                },
                body,
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=_plain_validation_errors(e))

        params = [
            session_id,
            json.dumps(applied["character"]),
            json.dumps(applied["world"]),
            insert_log,
        ]
        if log_payload is not None:
            params.append(log_payload)

        row = await conn.fetchrow(sql, *params)

    try:
        response_character = CharacterModel.model_validate(
            _normalize_character_state(json.loads(row["character"]))
        )
        response_world = WorldModel.model_validate(json.loads(row["world"]))
    except ValidationError as e:
        raise HTTPException(status_code=500, detail={"message": "stored game state is invalid", "errors": e.errors()})

    return GameStateResponse(
        session_id=row["session_id"],
        character=response_character,
        world=response_world,
        log=json.loads(row["log"]),
        updated_at=row["updated_at"],
    )
