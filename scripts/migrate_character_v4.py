#!/usr/bin/env python3
"""Migrate stored character JSONB documents to schema v4.0.0."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import asyncpg

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.models import CharacterModel

MIGRATION_LOG_ENTRY = "Schema migrated to v4.0.0 — ancestry/culture/fields."
DEFAULT_CULTURE = "drakenvale_city"


def migrate_character_payload(character: dict[str, Any]) -> tuple[dict[str, Any], bool, bool]:
    migrated = dict(character)
    changed = False
    used_default_culture = False

    if "species" in migrated:
        migrated["ancestry"] = migrated.pop("species")
        changed = True

    if "culture" not in migrated:
        migrated["culture"] = DEFAULT_CULTURE
        changed = True
        used_default_culture = True

    if "fields" not in migrated:
        magic_fields = migrated.get("magic_fields")
        if isinstance(magic_fields, list):
            migrated["fields"] = {
                str(field): 1
                for field in magic_fields
                if isinstance(field, str) and field
            }
        else:
            migrated["fields"] = {}
        changed = True

    for legacy_key in ("magic_fields", "draconic_traits", "level", "species_traits"):
        if legacy_key in migrated:
            migrated.pop(legacy_key, None)
            changed = True

    return migrated, changed, used_default_culture


def migrate_character_document(character: dict[str, Any]) -> tuple[dict[str, Any], bool, bool, CharacterModel]:
    """Pure transform for a stored character payload plus post-migration validation."""
    migrated, changed, used_default_culture = migrate_character_payload(character)
    validated = CharacterModel.model_validate(migrated)
    return migrated, changed, used_default_culture, validated


def get_database_url() -> str:
    """Return DATABASE_URL or exit cleanly with a clear message."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL environment variable not set.")
    return database_url


async def _run(dry_run: bool, session_id: str | None) -> int:
    database_url = get_database_url()
    conn = await asyncpg.connect(database_url)
    processed = 0
    migrated_count = 0
    skipped_invalid = 0
    defaulted_culture = 0

    try:
        if session_id:
            rows = await conn.fetch(
                "SELECT session_id, character, log FROM game_states WHERE session_id = $1",
                session_id,
            )
        else:
            rows = await conn.fetch("SELECT session_id, character, log FROM game_states ORDER BY session_id")

        for row in rows:
            processed += 1
            sid = row["session_id"]
            character = json.loads(row["character"])
            log = json.loads(row["log"])

            try:
                migrated_character, changed, used_default, validated = migrate_character_document(character)
            except Exception as exc:
                skipped_invalid += 1
                print(f"SKIP {sid}: invalid migrated character ({exc})")
                continue

            migrated_count += 1
            if used_default:
                defaulted_culture += 1
                print(f"DEFAULT CULTURE {sid}: set culture to {DEFAULT_CULTURE}")

            if dry_run:
                continue

            updated_log = list(log)
            updated_log.append(MIGRATION_LOG_ENTRY)
            await conn.execute(
                """
                UPDATE game_states
                   SET character = $2::jsonb,
                       log = $3::jsonb,
                       updated_at = now()
                 WHERE session_id = $1
                """,
                sid,
                json.dumps(validated.model_dump()),
                json.dumps(updated_log),
            )

        print(
            f"Processed={processed} Migrated={migrated_count} "
            f"SkippedInvalid={skipped_invalid} DefaultCulture={defaulted_culture} DryRun={dry_run}"
        )
        return 0
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate stored character JSONB documents to schema v4.0.0.")
    parser.add_argument("--dry-run", action="store_true", help="Report sessions needing migration without writing")
    parser.add_argument("--session", help="Migrate a single session ID")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args.dry_run, args.session)))


if __name__ == "__main__":
    main()