#!/usr/bin/env python3
"""Migrate stored character advancement JSONB to v4.2.0 fungible AP."""

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

from api.models import CharacterModel  # noqa: E402

MIGRATION_LOG_ENTRY = "Schema migrated to advancement v4.2.0 — fungible AP."


def migrate_advancement_payload(character: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Return (migrated_character, changed)."""
    old = character.get("advancement", {}) or {}
    points_spent = int(old.get("points_spent", 0) or 0)
    points_earned_total = old.get("points_earned_total")
    if points_earned_total is None:
        earned = old.get("points_available_earned") or {}
        points_earned_total = sum(int(v or 0) for v in earned.values()) + points_spent
    points_earned_total = int(points_earned_total or 0)
    points_available = points_earned_total - points_spent

    new_advancement = {
        "points_available": max(points_available, 0),
        "points_spent": points_spent,
        "points_earned_total": points_earned_total,
        "tag_counter": 0,
    }

    migrated = dict(character)
    migrated["advancement"] = new_advancement
    migrated.setdefault("pending_tag_proposals", [])

    for key in ("tag_advance_counters", "points_available_earned", "points_available_awarded"):
        migrated.pop(key, None)

    changed = old != new_advancement or "pending_tag_proposals" not in character
    return migrated, changed


def migrate_character_document(character: dict[str, Any]) -> tuple[dict[str, Any], bool, CharacterModel]:
    migrated, changed = migrate_advancement_payload(character)
    validated = CharacterModel.model_validate(migrated)
    return migrated, changed, validated


def get_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL environment variable not set.")
    return database_url


async def _run(dry_run: bool, session_id: str | None) -> int:
    conn = await asyncpg.connect(get_database_url())
    processed = 0
    needing_migration = 0
    migrated_count = 0
    skipped_invalid = 0

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
                migrated_character, changed, validated = migrate_character_document(character)
            except Exception as exc:
                skipped_invalid += 1
                print(f"SKIP {sid}: invalid migrated character ({exc})")
                continue

            if not changed:
                continue
            needing_migration += 1
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
            migrated_count += 1

        print(
            f"Processed={processed} NeedsMigration={needing_migration} "
            f"Migrated={migrated_count} SkippedInvalid={skipped_invalid} DryRun={dry_run}"
        )
        return 0
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate advancement JSONB documents to schema v4.2.0.")
    parser.add_argument("--dry-run", action="store_true", help="Report sessions needing migration without writing")
    parser.add_argument("--session", help="Migrate a single session ID")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args.dry_run, args.session)))


if __name__ == "__main__":
    main()