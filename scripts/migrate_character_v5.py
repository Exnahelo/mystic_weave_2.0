#!/usr/bin/env python3
"""Migrate stored character JSONB documents to schema v5.0.0.

v4: knowledge / application / fields as flat dict[str, int].
v5: knowledge as dict[group, {tier, applications}], magic as dict[field, {tier, spells}].

Idempotent — running on an already-v5 record is a no-op.

Usage:
    python3 scripts/migrate_character_v5.py --dry-run
    python3 scripts/migrate_character_v5.py --session <session_id>
"""

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

from api.game_data import get_application_group  # noqa: E402
from api.models import CharacterModel  # noqa: E402

MIGRATION_LOG_ENTRY = "Schema migrated to v5.0.0 — nested knowledge/magic records."


def _is_already_v5(character: dict[str, Any]) -> bool:
    """Heuristic: a v5 knowledge entry is a dict with a 'tier' key."""
    knowledge = character.get("knowledge")
    if not isinstance(knowledge, dict) or not knowledge:
        # Empty or missing knowledge: presence of `magic` (and absence of v4
        # `application`/`fields`) signals v5.
        return "magic" in character and "application" not in character and "fields" not in character
    first = next(iter(knowledge.values()), None)
    return isinstance(first, dict) and "tier" in first


def migrate_character_v4_to_v5(character: dict[str, Any]) -> dict[str, Any]:
    """Pure transform from v4 flat shape to v5 nested shape.

    Idempotent: passes already-v5 records through unchanged. Raises ValueError
    if a v4 record carries an application whose parent group cannot be looked
    up in the canonical applications.json — such a record is malformed and
    should be inspected manually.
    """
    if _is_already_v5(character):
        return character

    migrated = dict(character)

    flat_knowledge_raw = migrated.pop("knowledge", {}) or {}
    flat_application = migrated.pop("application", {}) or {}
    flat_fields = migrated.pop("fields", {}) or {}

    flat_knowledge: dict[str, int] = {
        k: v for k, v in flat_knowledge_raw.items() if isinstance(v, int)
    }

    nested_knowledge: dict[str, dict[str, Any]] = {
        group: {"tier": tier, "applications": {}}
        for group, tier in flat_knowledge.items()
    }

    for app, app_tier in flat_application.items():
        if not isinstance(app_tier, int):
            continue
        parent = get_application_group(app)
        if parent is None:
            raise ValueError(
                f"application {app!r} has no parent group; v4 record is malformed"
            )
        if parent not in nested_knowledge:
            # v4 record granted an application without explicitly granting
            # the parent group. Auto-add at app_tier — the minimum that
            # satisfies the v5 parent-cap rule.
            nested_knowledge[parent] = {"tier": app_tier, "applications": {}}
        nested_knowledge[parent]["applications"][app] = app_tier

    nested_magic: dict[str, dict[str, Any]] = {
        field: {"tier": tier, "spells": {}}
        for field, tier in flat_fields.items()
        if isinstance(tier, int)
    }

    migrated["knowledge"] = nested_knowledge
    migrated["magic"] = nested_magic
    return migrated


def migrate_character_document(character: dict[str, Any]) -> tuple[dict[str, Any], bool, CharacterModel]:
    """Migrate a v4 record and validate the v5 result.

    Returns (migrated_dict, changed_flag, validated_model).
    """
    was_v5 = _is_already_v5(character)
    migrated = migrate_character_v4_to_v5(character)
    validated = CharacterModel.model_validate(migrated)
    return migrated, not was_v5, validated


def get_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL environment variable not set.")
    return database_url


async def _run(dry_run: bool, session_id: str | None) -> int:
    database_url = get_database_url()
    conn = await asyncpg.connect(database_url)
    processed = 0
    migrated_count = 0
    already_v5 = 0
    skipped_invalid = 0

    try:
        if session_id:
            rows = await conn.fetch(
                "SELECT session_id, character, log FROM game_states WHERE session_id = $1",
                session_id,
            )
        else:
            rows = await conn.fetch(
                "SELECT session_id, character, log FROM game_states ORDER BY session_id"
            )

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
                already_v5 += 1
                continue

            migrated_count += 1

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
            f"AlreadyV5={already_v5} SkippedInvalid={skipped_invalid} DryRun={dry_run}"
        )
        return 0
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate stored character JSONB documents to schema v5.0.0."
    )
    parser.add_argument("--dry-run", action="store_true", help="Report sessions needing migration without writing")
    parser.add_argument("--session", help="Migrate a single session ID")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_run(args.dry_run, args.session)))


if __name__ == "__main__":
    main()
