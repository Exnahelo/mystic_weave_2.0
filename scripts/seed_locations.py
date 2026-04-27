#!/usr/bin/env python3
"""
seed_locations.py — Convert prompt world YAML files to Postgres location records.

Usage:
    python3 scripts/seed_locations.py

Reads all canonical world .yaml files from data/world/, parses the YAML payload,
and upserts each location into the `locations` and `world_graph` tables.

Location file format expected:
id, name, type, region_id, summary, connections, tags
"""

from __future__ import annotations

import asyncio
import json
import os
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

CANONICAL_WORLD_DIR = Path(__file__).parent.parent / "data" / "world"

# Types that live under data/world/ but are not navigable location nodes.
# Files with these types are skipped by the seeder.
NON_LOCATION_TYPES = {"order", "civic-structure"}


def parse_location_file(path: Path) -> dict | None:
    """Parse a location YAML file and return a location dict, or None if invalid."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
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
        "description": str(data.get("summary") or data.get("description", "")),
        "tags": list(data.get("tags", [])),
        "connections": list(data.get("connections", [])),
        "threat_level": int(data.get("threat_level", 0)),
        "known_npcs": list(data.get("known_npcs", [])),
        "discovered": bool(data.get("discovered", True)),
    }


async def seed(database_url: str) -> None:
    if not CANONICAL_WORLD_DIR.exists():
        print(f"Canonical world directory not found: {CANONICAL_WORLD_DIR}")
        print("Create data/world/ and add canonical .yaml files to seed locations.")
        return

    canonical_files = sorted(CANONICAL_WORLD_DIR.rglob("*.yaml"))
    canonical_files = [p for p in canonical_files if not p.name.startswith("_") and p.name not in {"region.yaml", "settlement.yaml", "district.yaml", "region_zone.yaml"} and not p.parent.name == "schemas"]

    if not canonical_files:
        print(f"No canonical location .yaml files found in {CANONICAL_WORLD_DIR}")
        return

    print(f"Found {len(canonical_files)} canonical location file(s) in {CANONICAL_WORLD_DIR}")

    locations = []
    for path in canonical_files:
        loc = parse_location_file(path)
        if loc:
            if loc["type"] in NON_LOCATION_TYPES:
                print(f"  SKIP {path.name} — non-location type '{loc['type']}'")
                continue
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
