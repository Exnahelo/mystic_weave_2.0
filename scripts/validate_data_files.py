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


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"

    failures: list[str] = []
    _validate_species(data_dir / "species.json", failures)
    _validate_tag_rows(data_dir / "focus.json", failures, expected_count=7)
    _validate_tag_rows(data_dir / "backgrounds.json", failures, expected_count=8)

    if failures:
        print("❌ Data validation failed")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)

    print("✅ Data validation passed")


if __name__ == "__main__":
    main()
