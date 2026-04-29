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
from api.game_data import validate_application_parent_cap
from api.models import (
    AdvancementState,
    DOMAIN_KEYS,
    ApplyStateDeltaRequest,
    CharacterModel,
    Equipment,
    GameStateResponse,
    PacingState,
    SaveStateRequest,
    SurvivalState,
    TimeState,
    TimeDriftWarning,
    WorldModel,
)

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
    if not isinstance(normalized.get("application"), dict):
        normalized["application"] = {}
    if not isinstance(normalized.get("fields"), dict):
        normalized["fields"] = {}
    advancement = normalized.get("advancement")
    if not isinstance(advancement, dict):
        normalized["advancement"] = AdvancementState().model_dump()
    else:
        adv = dict(advancement)
        adv.setdefault("points_available_earned", {d: 0 for d in DOMAIN_KEYS})
        adv.setdefault("points_available_awarded", 0)
        adv.setdefault("points_spent", 0)
        adv.setdefault("points_earned_total", 0)
        adv.setdefault("tag_advance_counters", {d: 0 for d in DOMAIN_KEYS})
        adv.pop("points_available", None)
        normalized["advancement"] = adv
    return normalized


def _apply_tag_advancement_counters(
    existing_character: dict[str, Any],
    delta_character: dict[str, Any],
) -> dict[str, Any]:
    """
    Detect tag tier increases in the delta vs. the existing character and
    update the advancement.tag_advance_counters and points_available_earned
    accordingly. Returns the updated advancement dict to be merged.

    Counters increment by (new_tier - old_tier). Every 3 in a domain
    converts to +1 earned AP in that domain.

    Caller is responsible for merging the returned advancement dict back
    onto the character.
    """
    from api.game_data import get_tag_primary_domain

    advancement = dict(existing_character.get("advancement") or {})
    counters = dict(advancement.get("tag_advance_counters") or {})
    earned = dict(advancement.get("points_available_earned") or {})

    for domain in DOMAIN_KEYS:
        counters.setdefault(domain, 0)
        earned.setdefault(domain, 0)

    earned_total_delta = 0

    for tag_kind in ("knowledge", "application", "fields"):
        delta_block = delta_character.get(tag_kind) or {}
        existing_block = existing_character.get(tag_kind) or {}
        if not isinstance(delta_block, dict) or not isinstance(existing_block, dict):
            continue

        kind_for_lookup = "field" if tag_kind == "fields" else tag_kind

        for tag_index, new_tier in delta_block.items():
            if not isinstance(new_tier, int):
                continue
            old_tier = existing_block.get(tag_index, 0) or 0
            if new_tier <= old_tier:
                continue
            steps = new_tier - old_tier

            domain = get_tag_primary_domain(tag_index, kind_for_lookup)
            if domain is None or domain not in counters:
                continue

            counters[domain] += steps
            while counters[domain] >= 3:
                counters[domain] -= 3
                earned[domain] += 1
                earned_total_delta += 1

    advancement["tag_advance_counters"] = counters
    advancement["points_available_earned"] = earned
    advancement["points_earned_total"] = (
        (advancement.get("points_earned_total") or 0) + earned_total_delta
    )
    advancement.setdefault("points_available_awarded", 0)
    advancement.setdefault("points_spent", 0)

    return advancement


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


# Canonical month ordering for the Oath Calendar (prompts/calendar.md).
# Used for time monotonicity checks — incoming time must not be earlier than
# stored time on the world timeline.
MONTH_ORDER = (
    "Ashwake", "Embertide", "Mistbreak", "Verdantrise",
    "Clearwater", "Goldmere", "Scaletide", "Amberveil",
    "Ashenfall", "Ironmoor", "Dimlight", "Deepwarden",
)
TIME_OF_DAY_ORDER = ("dawn", "morning", "midday", "afternoon", "dusk", "night")


def _time_to_tuple(t: TimeState) -> tuple[int, int, int, int]:
    """Convert TimeState to a comparable (year, month_idx, day, time_of_day_idx) tuple.

    Unknown month or time_of_day values fall back to position 0 — defensive but
    shouldn't occur with validated TimeState input.
    """
    month_idx = MONTH_ORDER.index(t.month) if t.month in MONTH_ORDER else 0
    tod_value = t.time_of_day.value if hasattr(t.time_of_day, "value") else str(t.time_of_day)
    tod_idx = TIME_OF_DAY_ORDER.index(tod_value) if tod_value in TIME_OF_DAY_ORDER else 0
    return (t.year, month_idx, t.day, tod_idx)


def _detect_time_drift(
    previous_turn: int,
    previous_time: TimeState,
    current_turn: int,
    current_time: TimeState,
) -> TimeDriftWarning | None:
    """
    Return a warning if turn advanced but time did not.

    Time is considered advanced if day, month, year, or time_of_day changed.
    """
    if current_turn <= previous_turn:
        return None

    time_changed = (
        current_time.day != previous_time.day
        or current_time.month != previous_time.month
        or current_time.year != previous_time.year
        or current_time.time_of_day != previous_time.time_of_day
    )
    if time_changed:
        return None

    return TimeDriftWarning(
        previous_turn=previous_turn,
        current_turn=current_turn,
        previous_time=previous_time,
        current_time=current_time,
        message=(
            f"Turn advanced from {previous_turn} to {current_turn} but world.time did not "
            f"change. Review the Ptarian calendar travel table and advance time_of_day, "
            f"day, or both in your next save if the scene consumed in-world time."
        ),
    )


def validate_delta(delta: ApplyStateDeltaRequest) -> None:
    """Validate delta-level invariants before state application."""
    if not delta.log_entry.strip():
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
    character_delta = delta.character.model_dump(exclude_none=True, by_alias=True)
    world_delta = delta.world.model_dump(exclude_none=True)

    existing_character = json.loads(current_state["character"])
    existing_world = json.loads(current_state["world"])

    new_advancement = _apply_tag_advancement_counters(existing_character, character_delta)
    character_delta["advancement"] = new_advancement

    application_delta = character_delta.get("application")
    if isinstance(application_delta, dict) and application_delta:
        try:
            validate_application_parent_cap(existing_character, application_delta)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={"message": "parent-cap violation", "error": str(exc)},
            )

    equipment_delta = character_delta.pop("equipment", None)
    merged_character = _deep_merge(existing_character, character_delta)
    if equipment_delta is not None:
        merged_character["equipment"] = _merge_equipment_slots(
            existing_character.get("equipment", {}), equipment_delta
        )

    merged_world = _deep_merge(existing_world, world_delta)

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
    log_entry_json = json.dumps([body.log_entry])

    async with pool.acquire() as conn:
        # Load existing state to merge against
        existing_row = await conn.fetchrow(
            "SELECT character, world FROM game_states WHERE session_id = $1",
            session_id,
        )
        previous_turn: int | None = None
        previous_time: TimeState | None = None

        if existing_row is not None:
            existing_character: dict[str, Any] = json.loads(existing_row["character"])
            existing_world: dict[str, Any] = json.loads(existing_row["world"])
            merged_character = _deep_merge(existing_character, incoming_character)
            merged_world = _deep_merge(existing_world, world_json)
            normalized_existing_world = _normalize_world_state(existing_world)
            previous_turn = int(normalized_existing_world.get("turn", 1))
            previous_time = TimeState.model_validate(normalized_existing_world["time"])
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
        drift_warning = None
        if previous_turn is not None and previous_time is not None:
            drift_warning = _detect_time_drift(
                previous_turn=previous_turn,
                previous_time=previous_time,
                current_turn=validated_world.turn,
                current_time=validated_world.time,
            )

        # Enforce: if turn advanced, the request body must include a `time`
        # block (acknowledgment). Echoing the previous time_of_day is allowed
        # — that affirms a deliberate no-advance turn. Silent omission is
        # rejected so time drift cannot accumulate unnoticed.
        if (
            previous_turn is not None
            and validated_world.turn > previous_turn
            and not isinstance(world_json.get("time"), dict)
        ):
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "time_acknowledgment_required",
                    "message": (
                        f"Turn advanced from {previous_turn} to {validated_world.turn} "
                        f"but request body included no world.time field. "
                        f"Resubmit with world.time advanced per the Travel Time Reference "
                        f"in prompts/calendar.md, or include world.time with the current "
                        f"time_of_day to affirm a deliberate no-advance turn."
                    ),
                    "previous_turn": previous_turn,
                    "current_turn": validated_world.turn,
                    "previous_time": previous_time.model_dump() if previous_time else None,
                },
            )

        # Enforce: time must be monotonically forward. Reject if incoming
        # world.time represents an older world-timeline position than the
        # stored time. Catches the case where the GPT regenerates a default
        # time block (e.g. day=1) and would silently overwrite the stored
        # day. Only enforced when a time block was sent and prior state exists.
        if (
            previous_time is not None
            and isinstance(world_json.get("time"), dict)
        ):
            previous_tuple = _time_to_tuple(previous_time)
            current_tuple = _time_to_tuple(validated_world.time)
            if current_tuple < previous_tuple:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "time_regression_rejected",
                        "message": (
                            f"Incoming world.time is earlier than stored time. "
                            f"Time may not move backward. If this turn is in the same "
                            f"in-world moment, echo the stored time_of_day, day, month, "
                            f"and year. If the stored time is wrong, fix it by sending "
                            f"a forward time. Stored: day {previous_time.day} of "
                            f"{previous_time.month} {previous_time.year} "
                            f"({previous_time.time_of_day}); incoming: day "
                            f"{validated_world.time.day} of {validated_world.time.month} "
                            f"{validated_world.time.year} ({validated_world.time.time_of_day})."
                        ),
                        "previous_time": previous_time.model_dump(),
                        "incoming_time": validated_world.time.model_dump(),
                    },
                )

        row = await conn.fetchrow(
            """
            INSERT INTO game_states (session_id, character, world, log, updated_at)
            VALUES ($1, $2::jsonb, $3::jsonb, $4::jsonb, now())
            ON CONFLICT (session_id) DO UPDATE
              SET character   = EXCLUDED.character,
                  world       = EXCLUDED.world,
                  log         = game_states.log || $5::jsonb,
                  updated_at  = now()
            RETURNING session_id, character, world, log, updated_at
            """,
            session_id,
            json.dumps(merged_character_json),
            json.dumps(validated_world_json),
            json.dumps([body.log_entry]),   # initial log on INSERT
            log_entry_json,                 # appended entry on UPDATE
        )

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
        time_drift_warning=drift_warning,
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
    log_entry_json = json.dumps([body.log_entry])
    drift_warning = None

    async with pool.acquire() as conn:
        existing_row = await conn.fetchrow(
            "SELECT character, world FROM game_states WHERE session_id = $1",
            session_id,
        )

        if existing_row is None:
            raise HTTPException(status_code=404, detail="session not found")

        try:
            validate_delta(body)
            normalized_existing_world = _normalize_world_state(json.loads(existing_row["world"]))
            previous_turn = int(normalized_existing_world.get("turn", 1))
            previous_time = TimeState.model_validate(normalized_existing_world["time"])
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

        applied_world = WorldModel.model_validate(applied["world"])
        drift_warning = _detect_time_drift(
            previous_turn=previous_turn,
            previous_time=previous_time,
            current_turn=applied_world.turn,
            current_time=applied_world.time,
        )

        # Enforce: if turn advanced, the delta must include a `time` field
        # (acknowledgment). Setting time with the current time_of_day echoed
        # is allowed — that affirms a deliberate no-advance turn. Silent
        # omission is rejected.
        if applied_world.turn > previous_turn and body.world.time is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "time_acknowledgment_required",
                    "message": (
                        f"Turn advanced from {previous_turn} to {applied_world.turn} "
                        f"but delta included no world.time field. "
                        f"Resubmit with world.time advanced per the Travel Time Reference "
                        f"in prompts/calendar.md, or include world.time with the current "
                        f"time_of_day to affirm a deliberate no-advance turn."
                    ),
                    "previous_turn": previous_turn,
                    "current_turn": applied_world.turn,
                    "previous_time": previous_time.model_dump(),
                },
            )

        # Enforce: time must be monotonically forward. Reject if applied
        # world.time represents an older timeline position than stored time.
        # Only enforced when a time field was sent in the delta.
        if body.world.time is not None:
            previous_tuple = _time_to_tuple(previous_time)
            current_tuple = _time_to_tuple(applied_world.time)
            if current_tuple < previous_tuple:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "time_regression_rejected",
                        "message": (
                            f"Incoming world.time is earlier than stored time. "
                            f"Time may not move backward. If this turn is in the same "
                            f"in-world moment, echo the stored day, month, year, and "
                            f"time_of_day. Stored: day {previous_time.day} of "
                            f"{previous_time.month} {previous_time.year} "
                            f"({previous_time.time_of_day}); incoming: day "
                            f"{applied_world.time.day} of {applied_world.time.month} "
                            f"{applied_world.time.year} ({applied_world.time.time_of_day})."
                        ),
                        "previous_time": previous_time.model_dump(),
                        "incoming_time": applied_world.time.model_dump(),
                    },
                )

        row = await conn.fetchrow(
            """
            INSERT INTO game_states (session_id, character, world, log, updated_at)
            VALUES ($1, $2::jsonb, $3::jsonb, $4::jsonb, now())
            ON CONFLICT (session_id) DO UPDATE
              SET character   = EXCLUDED.character,
                  world       = EXCLUDED.world,
                  log         = game_states.log || $5::jsonb,
                  updated_at  = now()
            RETURNING session_id, character, world, log, updated_at
            """,
            session_id,
            json.dumps(applied["character"]),
            json.dumps(applied["world"]),
            json.dumps([body.log_entry]),   # initial log on INSERT
            log_entry_json,                 # appended entry on UPDATE
        )

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
        time_drift_warning=drift_warning,
    )
