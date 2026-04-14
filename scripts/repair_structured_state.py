#!/usr/bin/env python3
"""Repair structured character/world state for an existing session."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Any

import asyncpg

from api.models import (
    AdvancementState,
    CharacterModel,
    PacingState,
    SurvivalState,
    TimeState,
    WorldModel,
)

CANONICAL_REPAIRS: dict[str, dict[str, Any]] = {
    "9ac30cc0": {
        "character": {
            "knowledge": {
                "sacred": 1,
                "command": 3,
                "courage": 1,
                "warding": 1,
                "diplomacy": 1,
                "discipline": 2,
            },
            "application": {
                "bless_water": 1,
                "sacred_rites": 2,
                "dragon_breath": 2,
                "shields_armor": 2,
                "warding_circle": 1,
                "musical_instruments": 1,
                "consecrate_threshold": 1,
                "purify_food_and_drink": 1,
            },
            "magic_fields": ["sacred", "warding"],
            "draconic_traits": ["radiant_breath_lineage", "dragon_breath"],
            "advancement": {
                "points_spent": 2,
                "points_available": 1,
                "points_earned_total": 3,
            },
        },
        "log_entry": "Structured canon fields restored from session continuity data.",
    }
}


def _apply_structured_repair(
    character: dict[str, Any],
    world: dict[str, Any],
    repair: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    patched_character = dict(character)
    patched_world = dict(world)

    patched_character["knowledge"] = dict(repair["character"]["knowledge"])
    patched_character["application"] = dict(repair["character"]["application"])
    patched_character["magic_fields"] = list(repair["character"]["magic_fields"])
    patched_character["draconic_traits"] = list(repair["character"]["draconic_traits"])
    patched_character["advancement"] = AdvancementState(
        **repair["character"]["advancement"]
    ).model_dump()

    if not isinstance(patched_world.get("time"), dict):
        patched_world["time"] = TimeState().model_dump()
    if not isinstance(patched_world.get("survival"), dict):
        patched_world["survival"] = SurvivalState().model_dump()
    if not isinstance(patched_world.get("pacing"), dict):
        patched_world["pacing"] = PacingState().model_dump()

    return patched_character, patched_world


async def _run(session_id: str, dry_run: bool) -> None:
    database_url = os.environ["DATABASE_URL"]
    repair = CANONICAL_REPAIRS.get(session_id)
    if repair is None:
        raise SystemExit(f"No canonical structured repair configured for session '{session_id}'.")

    conn = await asyncpg.connect(database_url)
    try:
        row = await conn.fetchrow(
            "SELECT session_id, character, world, log FROM game_states WHERE session_id = $1",
            session_id,
        )
        if row is None:
            raise SystemExit(f"Session '{session_id}' not found.")

        character = json.loads(row["character"])
        world = json.loads(row["world"])
        log = json.loads(row["log"])

        repaired_character, repaired_world = _apply_structured_repair(character, world, repair)
        validated_character = CharacterModel.model_validate(repaired_character)
        validated_world = WorldModel.model_validate(repaired_world)

        updated_log = list(log)
        updated_log.append(repair["log_entry"])

        if dry_run:
            print(json.dumps({
                "session_id": session_id,
                "character": validated_character.model_dump(by_alias=True),
                "world": validated_world.model_dump(),
                "appended_log_entry": repair["log_entry"],
            }, indent=2))
            return

        await conn.execute(
            """
            UPDATE game_states
               SET character = $2::jsonb,
                   world = $3::jsonb,
                   log = $4::jsonb,
                   updated_at = now()
             WHERE session_id = $1
            """,
            session_id,
            json.dumps(validated_character.model_dump(by_alias=True)),
            json.dumps(validated_world.model_dump()),
            json.dumps(updated_log),
        )
        print(f"Repaired structured state for session '{session_id}'.")
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Repair structured character/world state for a session.")
    parser.add_argument("session_id", help="Session ID to repair")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print patched state without writing")
    args = parser.parse_args()
    asyncio.run(_run(args.session_id, args.dry_run))


if __name__ == "__main__":
    main()