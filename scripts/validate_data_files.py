#!/usr/bin/env python3
"""Validate core game data JSON files for structure and integrity."""

from __future__ import annotations

import json
import sys
from pathlib import Path

DOMAIN_KEYS = {
    "power",
    "agility",
    "perception",
    "endurance",
    "intellect",
    "will",
    "presence",
}

SPELL_FIELDS = {
    "sacred",
    "warding",
    "binding",
    "elemental",
    "nature",
    "illusion",
    "runecraft",
    "necromancy",
    "alchemy",
}


def _failures_append(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def _load_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError(f"{path.name}: expected top-level list")
    return payload


def _validate_species(path: Path, failures: list[str]) -> None:
    species = _load_json(path)
    seen_indices: set[str] = set()

    _failures_append(failures, len(species) == 8, f"{path.name}: expected 8 species entries")

    for i, row in enumerate(species):
        label = f"{path.name}[{i}]"
        _failures_append(failures, isinstance(row, dict), f"{label}: expected object")
        if not isinstance(row, dict):
            continue

        idx = row.get("index")
        _failures_append(failures, isinstance(idx, str) and idx, f"{label}.index must be non-empty string")
        if isinstance(idx, str):
            _failures_append(failures, idx not in seen_indices, f"{label}.index duplicated: {idx}")
            seen_indices.add(idx)

        _failures_append(failures, isinstance(row.get("name"), str) and row.get("name"), f"{label}.name must be non-empty string")

        primary = row.get("primary_domain")
        _failures_append(
            failures,
            (primary is None) or (isinstance(primary, str) and primary in DOMAIN_KEYS),
            f"{label}.primary_domain must be null or one of domain keys",
        )

        domains = row.get("domains")
        _failures_append(failures, isinstance(domains, dict), f"{label}.domains must be object")
        if isinstance(domains, dict):
            _failures_append(failures, set(domains.keys()) == DOMAIN_KEYS, f"{label}.domains keys mismatch")
            total = 0
            for dkey, val in domains.items():
                _failures_append(failures, isinstance(val, int), f"{label}.domains.{dkey} must be int")
                if isinstance(val, int):
                    total += val
                    _failures_append(
                        failures,
                        1 <= val <= 60,
                        f"{label}.domains.{dkey} must be between 1 and 60",
                    )
            _failures_append(failures, total == 280, f"{label}.domains total must be 280 (got {total})")


def _validate_tag_rows(path: Path, failures: list[str], expected_count: int) -> None:
    rows = _load_json(path)
    seen_indices: set[str] = set()

    _failures_append(failures, len(rows) == expected_count, f"{path.name}: expected {expected_count} entries")

    for i, row in enumerate(rows):
        label = f"{path.name}[{i}]"
        _failures_append(failures, isinstance(row, dict), f"{label}: expected object")
        if not isinstance(row, dict):
            continue

        idx = row.get("index")
        _failures_append(failures, isinstance(idx, str) and idx, f"{label}.index must be non-empty string")
        if isinstance(idx, str):
            _failures_append(failures, idx not in seen_indices, f"{label}.index duplicated: {idx}")
            seen_indices.add(idx)

        _failures_append(failures, isinstance(row.get("name"), str) and row.get("name"), f"{label}.name must be non-empty string")
        _failures_append(
            failures,
            isinstance(row.get("description"), str) and row.get("description"),
            f"{label}.description must be non-empty string",
        )

        k_tags = row.get("knowledge_tags")
        a_tags = row.get("application_tags")
        _failures_append(failures, isinstance(k_tags, dict), f"{label}.knowledge_tags must be object")
        _failures_append(failures, isinstance(a_tags, dict), f"{label}.application_tags must be object")

        for tag_group, group_name in ((k_tags, "knowledge_tags"), (a_tags, "application_tags")):
            if isinstance(tag_group, dict):
                _failures_append(
                    failures,
                    len(tag_group) > 0,
                    f"{label}.{group_name} must include at least one tag",
                )
                for tkey, tval in tag_group.items():
                    _failures_append(
                        failures,
                        isinstance(tkey, str) and tkey,
                        f"{label}.{group_name} contains invalid tag key",
                    )
                    _failures_append(
                        failures,
                        isinstance(tval, int) and 1 <= tval <= 5,
                        f"{label}.{group_name}.{tkey} tier must be int between 1 and 5",
                    )


def _validate_spells(path: Path, failures: list[str]) -> None:
    rows = _load_json(path)
    seen_indices: set[str] = set()

    _failures_append(failures, len(rows) > 0, f"{path.name}: expected at least 1 spell entry")

    required_keys = {
        "index",
        "name",
        "field",
        "tier",
        "primary_domain",
        "alternate_domain",
        "description",
    }

    for i, row in enumerate(rows):
        label = f"{path.name}[{i}]"
        _failures_append(failures, isinstance(row, dict), f"{label}: expected object")
        if not isinstance(row, dict):
            continue

        _failures_append(
            failures,
            set(row.keys()) == required_keys,
            f"{label}: keys must match {sorted(required_keys)}",
        )

        idx = row.get("index")
        _failures_append(failures, isinstance(idx, str) and idx, f"{label}.index must be non-empty string")
        if isinstance(idx, str):
            _failures_append(failures, idx not in seen_indices, f"{label}.index duplicated: {idx}")
            seen_indices.add(idx)

        _failures_append(failures, isinstance(row.get("name"), str) and row.get("name"), f"{label}.name must be non-empty string")
        _failures_append(
            failures,
            isinstance(row.get("description"), str) and row.get("description"),
            f"{label}.description must be non-empty string",
        )

        field = row.get("field")
        _failures_append(
            failures,
            isinstance(field, str) and field in SPELL_FIELDS,
            f"{label}.field must be one of {sorted(SPELL_FIELDS)}",
        )

        primary = row.get("primary_domain")
        _failures_append(
            failures,
            isinstance(primary, str) and primary in DOMAIN_KEYS,
            f"{label}.primary_domain must be one of {sorted(DOMAIN_KEYS)}",
        )

        alternate = row.get("alternate_domain")
        _failures_append(
            failures,
            alternate is None or (isinstance(alternate, str) and alternate in DOMAIN_KEYS),
            f"{label}.alternate_domain must be null or one of {sorted(DOMAIN_KEYS)}",
        )

        tier = row.get("tier")
        _failures_append(
            failures,
            isinstance(tier, int) and 1 <= tier <= 5,
            f"{label}.tier must be int between 1 and 5",
        )


def _validate_apparel(path: Path, failures: list[str]) -> None:
    rows = _load_json(path)
    seen_ids: set[str] = set()
    valid_subcategories = {"footwear", "handwear", "outerwear", "clothing"}

    for i, row in enumerate(rows):
        label = f"{path.name}[{i}]"
        _failures_append(failures, isinstance(row, dict), f"{label}: expected object")
        if not isinstance(row, dict):
            continue

        item_id = row.get("id")
        _failures_append(failures, isinstance(item_id, str) and item_id, f"{label}.id must be non-empty string")
        if isinstance(item_id, str):
            _failures_append(failures, item_id not in seen_ids, f"{label}.id duplicated: {item_id}")
            seen_ids.add(item_id)

        _failures_append(failures, isinstance(row.get("name"), str) and row.get("name"), f"{label}.name must be non-empty string")
        _failures_append(failures, row.get("category") == "apparel", f"{label}.category must equal 'apparel'")
        _failures_append(
            failures,
            isinstance(row.get("subcategory"), str) and row.get("subcategory") in valid_subcategories,
            f"{label}.subcategory must be one of {sorted(valid_subcategories)}",
        )
        _failures_append(failures, isinstance(row.get("tags"), list) and len(row.get("tags", [])) > 0, f"{label}.tags must be non-empty list")
        _failures_append(failures, isinstance(row.get("value_cd"), int), f"{label}.value_cd must be int")
        _failures_append(failures, isinstance(row.get("rarity"), str) and row.get("rarity"), f"{label}.rarity must be non-empty string")
        _failures_append(
            failures,
            isinstance(row.get("description"), str) and bool(row.get("description", "").strip()),
            f"{label}.description must be non-empty string",
        )
        _failures_append(
            failures,
            isinstance(row.get("narrative_effects"), list) and len(row.get("narrative_effects", [])) > 0,
            f"{label}.narrative_effects must be non-empty list",
        )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"

    failures: list[str] = []
    _validate_species(data_dir / "characters" / "ancestry.json", failures)
    _validate_tag_rows(data_dir / "characters" / "focus.json", failures, expected_count=7)
    _validate_tag_rows(data_dir / "characters" / "backgrounds.json", failures, expected_count=8)
    _validate_apparel(data_dir / "items" / "apparel.json", failures)

    magic_dir = data_dir / "magic"
    for spell_file in sorted(magic_dir.glob("*.json")):
        if spell_file.name == "fields.json":
            continue
        _validate_spells(spell_file, failures)

    if failures:
        print("❌ Data validation failed")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)

    print("✅ Data validation passed")


if __name__ == "__main__":
    main()
