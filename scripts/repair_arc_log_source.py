#!/usr/bin/env python3
"""Repair arcs whose log[].source values are outside the schema's valid set.

The ArcBeatLogEntry.source literal union accepts only 'progress' and
'transition'. Manual JSON patches against the arcs.data JSONB column can
introduce other values (e.g., 'settlement_correction'), which then cause
GET /arc/{session_id} to 500 on Pydantic validation.

This script connects to the same DB the API uses (via DATABASE_URL),
finds every arc with at least one bad source value, prints the offending
entry, and prompts the operator for a replacement source per entry. The
JSONB log array is updated in place.

See docs/operations/arc-log-source-integrity.md for the full procedure
and how to choose a replacement source.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import asyncpg

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.models import ARC_BEAT_LOG_VALID_SOURCES  # noqa: E402


SELECT_ALL_ARCS = """
    SELECT id, session_id, data
    FROM arcs
    WHERE data ? 'log'
      AND jsonb_typeof(data->'log') = 'array'
"""

UPDATE_ARC_DATA = """
    UPDATE arcs
    SET data = $1::jsonb
    WHERE id = $2
"""


def _prompt_replacement(arc_id: str, idx: int, entry: dict) -> str:
    valid = ", ".join(repr(v) for v in ARC_BEAT_LOG_VALID_SOURCES)
    print(f"\n  arc_id={arc_id}  log[{idx}]")
    print(f"    text={entry.get('text')!r}")
    print(f"    timestamp={entry.get('timestamp')}")
    print(f"    current source={entry.get('source')!r}")
    while True:
        choice = input(f"    Replacement source ({valid}) or 'skip': ").strip()
        if choice == "skip":
            return ""
        if choice in ARC_BEAT_LOG_VALID_SOURCES:
            return choice
        print(f"    Not a valid source. Pick one of {valid} or 'skip'.")


async def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set.", file=sys.stderr)
        sys.exit(2)

    conn = await asyncpg.connect(database_url)
    try:
        rows = await conn.fetch(SELECT_ALL_ARCS)
        repaired_arcs = 0
        repaired_entries = 0
        skipped_entries = 0

        for row in rows:
            data = row["data"]
            if isinstance(data, str):
                data = json.loads(data)
            log = data.get("log") or []
            if not isinstance(log, list):
                continue

            offending: list[tuple[int, dict]] = [
                (i, entry)
                for i, entry in enumerate(log)
                if isinstance(entry, dict)
                and entry.get("source") not in ARC_BEAT_LOG_VALID_SOURCES
            ]
            if not offending:
                continue

            print(
                f"\n=== arc_id={row['id']} session_id={row['session_id']} "
                f"({len(offending)} bad entr{'y' if len(offending) == 1 else 'ies'}) ==="
            )
            changed = False
            for idx, entry in offending:
                replacement = _prompt_replacement(row["id"], idx, entry)
                if replacement == "":
                    skipped_entries += 1
                    continue
                log[idx] = {**entry, "source": replacement}
                changed = True
                repaired_entries += 1

            if changed:
                data["log"] = log
                await conn.execute(UPDATE_ARC_DATA, json.dumps(data), row["id"])
                repaired_arcs += 1
                print(f"  -> updated arcs.data for {row['id']}")

        print(
            f"\nDone. arcs_repaired={repaired_arcs} "
            f"entries_repaired={repaired_entries} entries_skipped={skipped_entries}"
        )
        if skipped_entries:
            print(
                "Skipped entries remain invalid; the integrity migration will "
                "still fail until they are removed or repaired."
            )
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
