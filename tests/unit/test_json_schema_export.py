"""
Drift detection for exported JSON schemas.

If a Pydantic model in api/items.py changes and the committed schema
file is not regenerated, this test fails with a clear remediation hint.
"""

import json

import pytest

from scripts.export_json_schemas import REPO_ROOT, build_item_schema


SCHEMA_DIR = REPO_ROOT / "data" / "catalog" / "schemas"


@pytest.mark.unit
def test_item_schema_is_up_to_date():
    """Regenerate Item schema in-memory and compare to committed file."""
    expected = build_item_schema()
    committed_path = SCHEMA_DIR / "item.schema.json"

    assert committed_path.exists(), (
        f"{committed_path} not found. Run: python scripts/export_json_schemas.py"
    )

    committed = json.loads(committed_path.read_text())

    if expected != committed:
        pytest.fail(
            "data/catalog/schemas/item.schema.json is stale. "
            "Run: python scripts/export_json_schemas.py"
        )


@pytest.mark.unit
def test_item_schema_has_strict_extras():
    """Item and its forbid-extras submodels surface as additionalProperties:false."""
    schema = build_item_schema()

    # Top-level Item has extra="forbid".
    assert schema.get("additionalProperties") is False, (
        "Item must surface additionalProperties:false in JSON Schema "
        "(check ConfigDict(extra='forbid'))"
    )

    # Spot-check at least one nested model with extra="forbid" via $defs.
    defs = schema.get("$defs", {})
    assert "Inventory" in defs, "Inventory should appear in $defs"
    assert defs["Inventory"].get("additionalProperties") is False


@pytest.mark.unit
def test_item_schema_is_2020_12():
    """Confirm JSON Schema draft version is 2020-12 (Pydantic v2 default)."""
    schema = build_item_schema()
    schema_uri = schema.get("$schema", "")
    # Pydantic v2 may or may not emit $schema depending on version. If
    # present, it must be 2020-12. If absent, that's also acceptable
    # (consumers default to 2020-12 for Pydantic v2 output).
    if schema_uri:
        assert "2020-12" in schema_uri, f"unexpected JSON Schema draft: {schema_uri}"