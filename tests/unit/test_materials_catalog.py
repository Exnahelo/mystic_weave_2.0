"""Tests for the canonical materials catalog and its validator integration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MATERIALS_FILE = ROOT / "data" / "catalog" / "crafting" / "materials.json"
REG_DIR = ROOT / "data" / "catalog" / "registries"
BIOME_TYPES_FILE = REG_DIR / "biome_types.json"
MATERIAL_CATEGORIES_FILE = REG_DIR / "material_categories.json"
MAGIC_FIELDS_FILE = REG_DIR / "magic_fields.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _registry_ids(payload: dict, key: str) -> set[str]:
    return {entry["id"] for entry in payload[key]}


@pytest.fixture(scope="module")
def materials() -> list[dict]:
    payload = _load(MATERIALS_FILE)
    assert payload.get("schema_version") == 1
    return payload["materials"]


@pytest.fixture(scope="module")
def biome_ids() -> set[str]:
    return _registry_ids(_load(BIOME_TYPES_FILE), "biome_types")


@pytest.fixture(scope="module")
def category_ids() -> set[str]:
    return _registry_ids(_load(MATERIAL_CATEGORIES_FILE), "material_categories")


@pytest.fixture(scope="module")
def magic_field_ids() -> set[str]:
    return _registry_ids(_load(MAGIC_FIELDS_FILE), "magic_fields")


def test_materials_file_loads_with_schema_version_1() -> None:
    payload = _load(MATERIALS_FILE)
    assert payload.get("schema_version") == 1
    assert isinstance(payload.get("materials"), list)
    assert len(payload["materials"]) > 0


def test_biome_types_registry_loads() -> None:
    payload = _load(BIOME_TYPES_FILE)
    assert payload.get("schema_version") == 1
    assert "biome_types" in payload
    assert len(payload["biome_types"]) >= 10


def test_material_categories_registry_loads() -> None:
    payload = _load(MATERIAL_CATEGORIES_FILE)
    assert payload.get("schema_version") == 1
    assert "material_categories" in payload
    assert len(payload["material_categories"]) >= 5


def test_material_ids_are_unique(materials: list[dict]) -> None:
    ids = [m["id"] for m in materials]
    assert len(ids) == len(set(ids)), f"duplicate material ids: {ids}"


def test_all_materials_have_required_fields(materials: list[dict]) -> None:
    required = {
        "id", "name", "category", "magical_status", "biome_type",
        "scarcity", "treatment_required", "description", "narrative_properties",
    }
    for m in materials:
        missing = required - set(m.keys())
        assert not missing, f"{m.get('id', '?')} missing fields: {missing}"


def test_material_categories_are_in_registry(
    materials: list[dict], category_ids: set[str]
) -> None:
    for m in materials:
        assert m["category"] in category_ids, (
            f"{m['id']} has unknown category {m['category']!r}"
        )


def test_material_biomes_are_in_registry(
    materials: list[dict], biome_ids: set[str]
) -> None:
    for m in materials:
        assert m["biome_type"] in biome_ids, (
            f"{m['id']} has unknown biome_type {m['biome_type']!r}"
        )


def test_magical_status_values_are_valid(materials: list[dict]) -> None:
    valid = {"mundane", "magical-material", "actively-magical"}
    for m in materials:
        assert m["magical_status"] in valid, (
            f"{m['id']} has invalid magical_status {m['magical_status']!r}"
        )


def test_scarcity_values_are_valid(materials: list[dict]) -> None:
    valid = {"common", "uncommon", "rare", "reserved"}
    for m in materials:
        assert m["scarcity"] in valid, (
            f"{m['id']} has invalid scarcity {m['scarcity']!r}"
        )


def test_actively_magical_materials_declare_field(
    materials: list[dict], magic_field_ids: set[str]
) -> None:
    for m in materials:
        if m["magical_status"] == "actively-magical":
            assert m.get("magic_field") is not None, (
                f"{m['id']} is actively-magical but lacks magic_field"
            )
            assert m["magic_field"] in magic_field_ids, (
                f"{m['id']} has unknown magic_field {m['magic_field']!r}"
            )


def test_mundane_materials_have_no_magic_field(materials: list[dict]) -> None:
    for m in materials:
        if m["magical_status"] == "mundane":
            assert m.get("magic_field") is None, (
                f"{m['id']} is mundane but declares magic_field"
            )


def test_narrative_properties_nonempty_strings(materials: list[dict]) -> None:
    for m in materials:
        nps = m["narrative_properties"]
        assert isinstance(nps, list) and len(nps) > 0, (
            f"{m['id']} narrative_properties must be non-empty list"
        )
        for p in nps:
            assert isinstance(p, str) and p.strip(), (
                f"{m['id']} narrative_properties contains empty/non-string entry"
            )


def test_elarith_is_canonical_celestial_metal(materials: list[dict]) -> None:
    """Spot-check on the cornerstone material."""
    elarith = next((m for m in materials if m["id"] == "elarith"), None)
    assert elarith is not None, "elarith material must exist"
    assert elarith["category"] == "metal"
    assert elarith["magical_status"] == "magical-material"
    assert elarith["biome_type"] == "impact-strewn"
    assert elarith["scarcity"] == "reserved"
    assert "starvein" in elarith["aliases"]
    assert "heartfall" in elarith["aliases"]


def test_validate_catalog_script_passes() -> None:
    """End-to-end: the catalog validator runs cleanly with materials present."""
    import subprocess
    result = subprocess.run(
        ["python3", str(ROOT / "scripts" / "validate_catalog.py")],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, (
        f"validate_catalog.py failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "PASS" in result.stdout
