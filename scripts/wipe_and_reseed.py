#!/usr/bin/env python3
"""
wipe_and_reseed.py — Full backend wipe and location reseed.

WHAT THIS DOES:
  1. Truncates all session/play tables: game_states, arcs, arc_transitions,
     scene_records (all character data, all arcs, all scene boundaries gone).
  2. Truncates reference tables: locations, world_graph (eliminates GPT-created
     drift; restores canonical location set from data/world/).
  3. Reseeds locations from data/world/ via the existing seed_locations logic.

WHAT THIS DOES NOT DO:
  - Schema changes. Migrations are managed by alembic; this script assumes
    the schema is already at head.
  - File-system changes. data/world/, prompts/, schemas/ all untouched.
  - Backups. If you need a backup of game_states.log or other content,
    take it before running this script.

SAFETY:
  - Prints DB host before any destructive operation.
  - Requires typing 'WIPE' (case-sensitive) at confirmation prompt.
  - Truncate runs in a transaction; if anything fails, rolls back.
  - Reseed runs after truncate succeeds; failures here leave you with an
    empty locations table, fixable by re-running scripts/seed_locations.py.

USAGE:
  python3 scripts/wipe_and_reseed.py

  Or to skip the confirmation prompt (use with extreme care, not recommended):
  python3 scripts/wipe_and_reseed.py --yes-i-am-sure
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import asyncpg
except ImportError:
    print("asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)

from dotenv import load_dotenv

load_dotenv()


SESSION_TABLES = ("scene_records", "arc_transitions", "arcs", "game_states")
REFERENCE_TABLES = ("world_graph", "locations")


def safe_db_label(database_url: str) -> str:
    """Return a host:db label safe to print (no password)."""
    parsed = urlparse(database_url)
    host = parsed.hostname or "?"
    port = parsed.port or "?"
    db = parsed.path.lstrip("/") or "?"
    user = parsed.username or "?"
    return f"{user}@{host}:{port}/{db}"


async def get_row_counts(conn: asyncpg.Connection, tables: tuple[str, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in tables:
        try:
            counts[table] = await conn.fetchval(f"SELECT count(*) FROM {table}")
        except asyncpg.UndefinedTableError:
            counts[table] = -1  # table doesn't exist
    return counts


def print_counts(label: str, counts: dict[str, int]) -> None:
    print(f"\n  {label}:")
    for table, n in counts.items():
        if n == -1:
            print(f"    {table:20} (table missing)")
        else:
            print(f"    {table:20} {n:>8} rows")


async def truncate_all(database_url: str) -> None:
    """Truncate session and reference tables in one transaction."""
    pool = await asyncpg.create_pool(database_url)
    try:
        async with pool.acquire() as conn:
            print("\nCurrent row counts:")
            session_counts = await get_row_counts(conn, SESSION_TABLES)
            ref_counts = await get_row_counts(conn, REFERENCE_TABLES)
            print_counts("session/play tables", session_counts)
            print_counts("reference tables", ref_counts)

            print("\nTruncating in transaction...")
            async with conn.transaction():
                # CASCADE handles FK relationships (arc_transitions -> arcs,
                # arcs -> game_states, scene_records -> game_states,
                # world_graph -> locations).
                tables_csv = ", ".join(SESSION_TABLES + REFERENCE_TABLES)
                await conn.execute(f"TRUNCATE TABLE {tables_csv} CASCADE")
            print("  Truncate committed.")

            print("\nPost-truncate row counts:")
            session_counts = await get_row_counts(conn, SESSION_TABLES)
            ref_counts = await get_row_counts(conn, REFERENCE_TABLES)
            print_counts("session/play tables", session_counts)
            print_counts("reference tables", ref_counts)
    finally:
        await pool.close()


async def reseed_locations(database_url: str) -> None:
    """Reseed locations and world_graph from data/world/ canonical files.

    This duplicates the logic of scripts/seed_locations.py inline so the
    wipe-and-reseed flow runs as a single connection lifecycle. Behavior
    must match seed_locations.py exactly; if that script changes, mirror
    here.
    """
    canonical_world_dir = Path(__file__).parent.parent / "data" / "world"
    non_location_types = {"order", "civic-structure"}

    if not canonical_world_dir.exists():
        print(f"\nCanonical world directory not found: {canonical_world_dir}")
        print("Create data/world/ and add canonical .json files to seed locations.")
        return

    canonical_files = sorted(canonical_world_dir.rglob("*.json"))
    canonical_files = [
        p for p in canonical_files
        if not p.name.startswith("_")
        and p.name not in {"region.json", "settlement.json", "district.json", "region_zone.json"}
        and not p.parent.name == "schemas"
    ]

    if not canonical_files:
        print(f"\nNo canonical location .json files found in {canonical_world_dir}")
        return

    print(f"\nFound {len(canonical_files)} canonical location file(s).")

    locations = []
    for path in canonical_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  SKIP {path.name} — JSON parse error: {e}")
            continue

        if not data or "id" not in data or "name" not in data:
            print(f"  SKIP {path.name} — missing required fields")
            continue

        if data.get("type") in non_location_types:
            print(f"  SKIP {path.name} — non-location type '{data.get('type')}'")
            continue

        locations.append({
            "id": str(data["id"]),
            "name": str(data["name"]),
            "type": str(data.get("type", "unknown")),
            "description": str(data.get("summary") or data.get("description", "")),
            "tags": list(data.get("tags", [])),
            "connections": list(data.get("connections", [])),
            "threat_level": int(data.get("threat_level", 0)),
            "known_npcs": list(data.get("known_npcs", [])),
            "discovered": bool(data.get("discovered", True)),
        })

    if not locations:
        print("No valid locations to seed.")
        return

    pool = await asyncpg.create_pool(database_url)
    try:
        async with pool.acquire() as conn:
            for loc in locations:
                await conn.execute(
                    """
                    INSERT INTO locations (id, name, data, updated_at)
                    VALUES ($1, $2, $3::jsonb, now())
                    ON CONFLICT (id) DO UPDATE
                      SET name = EXCLUDED.name,
                          data = EXCLUDED.data,
                          updated_at = now()
                    """,
                    loc["id"],
                    loc["name"],
                    json.dumps(loc),
                )

            edge_count = 0
            for loc in locations:
                for conn_id in loc["connections"]:
                    target_exists = await conn.fetchval(
                        "SELECT 1 FROM locations WHERE id = $1", conn_id
                    )
                    if target_exists:
                        await conn.execute(
                            "INSERT INTO world_graph (from_id, to_id) "
                            "VALUES ($1, $2) ON CONFLICT DO NOTHING",
                            loc["id"],
                            conn_id,
                        )
                        edge_count += 1
                    else:
                        print(f"  WARN: connection target '{conn_id}' missing — skip edge from '{loc['id']}'")

            print(f"\nReseed complete: {len(locations)} locations, {edge_count} graph edges.")

            print("\nFinal reference table counts:")
            ref_counts = await get_row_counts(conn, REFERENCE_TABLES)
            print_counts("reference tables", ref_counts)
    finally:
        await pool.close()


async def main_async(skip_confirm: bool) -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL environment variable not set.")
        print("Add it to .env or export it before running this script.")
        sys.exit(1)

    print("=" * 60)
    print("WIPE AND RESEED")
    print("=" * 60)
    print(f"\nTarget database: {safe_db_label(database_url)}")
    print("\nThis will:")
    print("  1. TRUNCATE: game_states, arcs, arc_transitions, scene_records")
    print("  2. TRUNCATE: locations, world_graph")
    print("  3. RESEED:   locations and world_graph from data/world/")
    print("\nAll session/character/arc/scene data will be PERMANENTLY DELETED.")
    print("This is NOT a soft delete. There is no undo.")

    if not skip_confirm:
        print("\nType 'WIPE' (uppercase, exact) to confirm, or anything else to cancel.")
        try:
            answer = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            sys.exit(1)
        if answer != "WIPE":
            print("Cancelled — input did not match 'WIPE'.")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("STEP 1/2: Truncating tables")
    print("=" * 60)
    await truncate_all(database_url)

    print("\n" + "=" * 60)
    print("STEP 2/2: Reseeding locations")
    print("=" * 60)
    await reseed_locations(database_url)

    print("\n" + "=" * 60)
    print("DONE.")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Create a new session via POST /session/new")
    print("  - Apply Sylvara's saved character/world/log via /state/{session_id}")
    print("  - Verify with GET /state/{session_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Full wipe and location reseed")
    parser.add_argument(
        "--yes-i-am-sure",
        action="store_true",
        help="Skip the confirmation prompt. Use with extreme care.",
    )
    args = parser.parse_args()
    asyncio.run(main_async(skip_confirm=args.yes_i_am_sure))


if __name__ == "__main__":
    main()