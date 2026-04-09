#!/usr/bin/env python3
"""
seed_locations.py — Convert Obsidian markdown files to Postgres location records.

Usage:
    python3 scripts/seed_locations.py

Reads all .md files from /obsidian/world/, parses YAML front matter,
and upserts each location into the `locations` and `world_graph` tables.

Markdown file format expected:
---
id: thornvale
name: Thornvale
type: village
description: A quiet farming settlement at the edge of the Ashwood.
tags: [rural, low-threat, trade-road]
connections: [ashwood-east, kings-road-north]
threat_level: 2
known_npcs: [aldric-the-smith, wren-innkeeper]
discovered: true
---

Any body text after the front matter is ignored (or can be used as
additional description if the description field is absent).
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import asyncpg
except ImportError:
    print("asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()

OBSIDIAN_DIR = Path(__file__).parent.parent / "prompts" / "world"
FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_location_file(path: Path) -> dict | None:
    """Parse a markdown file and return a location dict, or None if invalid."""
    text = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_RE.match(text)
    if not match:
        print(f"  SKIP {path.name} — no YAML front matter found")
        return None

    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        print(f"  SKIP {path.name} — YAML parse error: {e}")
        return None

    if not data or "id" not in data or "name" not in data:
        print(f"  SKIP {path.name} — missing required fields (id, name)")
        return None

    # Normalise fields with defaults
    return {
        "id": str(data["id"]),
        "name": str(data["name"]),
        "type": str(data.get("type", "unknown")),
        "description": str(data.get("description", "")),
        "tags": list(data.get("tags", [])),
        "connections": list(data.get("connections", [])),
        "threat_level": int(data.get("threat_level", 0)),
        "known_npcs": list(data.get("known_npcs", [])),
        "discovered": bool(data.get("discovered", True)),
    }


async def seed(database_url: str) -> None:
    if not OBSIDIAN_DIR.exists():
        print(f"Obsidian world directory not found: {OBSIDIAN_DIR}")
        print("Create /obsidian/world/ and add .md files to seed locations.")
        return

    md_files = sorted(OBSIDIAN_DIR.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {OBSIDIAN_DIR}")
        return

    print(f"Found {len(md_files)} markdown file(s) in {OBSIDIAN_DIR}")

    locations = []
    for path in md_files:
        loc = parse_location_file(path)
        if loc:
            locations.append(loc)
            print(f"  Parsed: {loc['id']} ({loc['name']})")

    if not locations:
        print("No valid locations to seed.")
        return

    pool = await asyncpg.create_pool(database_url)

    async with pool.acquire() as conn:
        # Upsert all locations first (so FK references resolve)
        for loc in locations:
            await conn.execute(
                """
                INSERT INTO locations (id, name, data, updated_at)
                VALUES ($1, $2, $3::jsonb, now())
                ON CONFLICT (id) DO UPDATE
                  SET name       = EXCLUDED.name,
                      data       = EXCLUDED.data,
                      updated_at = now()
                """,
                loc["id"],
                loc["name"],
                json.dumps(loc),
            )
            print(f"  Upserted location: {loc['id']}")

        # Now upsert world_graph edges
        edge_count = 0
        for loc in locations:
            for conn_id in loc["connections"]:
                # Only insert if target exists
                target_exists = await conn.fetchval(
                    "SELECT 1 FROM locations WHERE id = $1", conn_id
                )
                if target_exists:
                    await conn.execute(
                        """
                        INSERT INTO world_graph (from_id, to_id)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                        """,
                        loc["id"],
                        conn_id,
                    )
                    edge_count += 1
                else:
                    print(f"  WARN: connection target '{conn_id}' not found — skipping edge from '{loc['id']}'")

    await pool.close()
    print(f"\nDone. Seeded {len(locations)} location(s) and {edge_count} graph edge(s).")


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL environment variable not set.")
        print("Add it to .env or export it before running this script.")
        sys.exit(1)

    asyncio.run(seed(database_url))


if __name__ == "__main__":
    main()
