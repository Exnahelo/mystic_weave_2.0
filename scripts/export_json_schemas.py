"""
Generate JSON Schema files from Pydantic models for non-Python consumers.

Currently exports:
  - data/catalog/schemas/item.schema.json (from api.items.Item)

Run from repo root:
    python scripts/export_json_schemas.py

Idempotent: running with no model changes produces no file diff.
The corresponding unit test fails if the committed schema is stale.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from api.items import Item  # noqa: E402

SCHEMA_DIR = REPO_ROOT / "data" / "catalog" / "schemas"


def build_item_schema() -> dict:
    """Generate the Item JSON Schema with stable, sorted output."""
    return Item.model_json_schema(mode="validation")


def write_schema(schema: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(schema, indent=2, sort_keys=True) + "\n"
    path.write_text(serialized)


def main() -> None:
    item_schema = build_item_schema()
    item_path = SCHEMA_DIR / "item.schema.json"
    write_schema(item_schema, item_path)
    print(f"wrote {item_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()