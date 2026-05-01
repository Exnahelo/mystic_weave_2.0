#!/usr/bin/env python3
"""Validate canonical flat item catalog and registries."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.items import Item  # noqa: E402

CATALOG_DIR = ROOT / "data" / "catalog"
ITEMS_DIR = CATALOG_DIR / "items"
REG_DIR = CATALOG_DIR / "registries"

REGISTRY_KEYS = {
    "item_tags.json": "item_tags",
    "market_tags.json": "market_tags",
    "combat_knowledge.json": "combat_knowledge",
    "combat_applications.json": "combat_applications",
    "magic_fields.json": "magic_fields",
    "item_subcategories.json": "item_subcategories",
    "rarities.json": "rarities",
    "legality.json": "legality",
}

CATEGORY_DIRS = {
    "weapon": "weapons",
    "armor": "armor",
    "shield": "shields",
    "ammunition": "ammunition",
    "apparel": "apparel",
    "gear": "gear",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registries() -> dict[str, Any]:
    registries: dict[str, Any] = {}
    for filename, key in REGISTRY_KEYS.items():
        path = REG_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"missing registry: {path}")
        payload = _load_json(path)
        if payload.get("schema_version") != 1:
            raise ValueError(f"{filename}: schema_version must be 1")
        if key not in payload:
            raise ValueError(f"{filename}: missing key {key!r}")
        registries[key] = payload[key]
    return registries


def registry_ids(entries: list[dict[str, Any]], label: str) -> set[str]:
    ids: set[str] = set()
    for entry in entries:
        item_id = entry.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError(f"{label}: invalid id entry {entry!r}")
        if item_id in ids:
            raise ValueError(f"{label}: duplicate id {item_id!r}")
        ids.add(item_id)
    return ids


def build_registry_indexes(registries: dict[str, Any]) -> dict[str, Any]:
    knowledge_ids = registry_ids(registries["combat_knowledge"], "combat_knowledge")
    application_parent = {
        entry["id"]: entry["knowledge_group"]
        for entry in registries["combat_applications"]
    }
    for app, group in application_parent.items():
        if group not in knowledge_ids:
            raise ValueError(f"combat_applications.{app}: unknown knowledge_group {group}")
    subcategories = {
        category: {entry["id"] for entry in entries}
        for category, entries in registries["item_subcategories"].items()
    }
    return {
        "item_tags": registry_ids(registries["item_tags"], "item_tags"),
        "market_tags": registry_ids(registries["market_tags"], "market_tags"),
        "combat_knowledge": knowledge_ids,
        "combat_applications": set(application_parent),
        "application_parent": application_parent,
        "magic_fields": registry_ids(registries["magic_fields"], "magic_fields"),
        "rarities": registry_ids(registries["rarities"], "rarities"),
        "legality": registry_ids(registries["legality"], "legality"),
        "subcategories": subcategories,
    }


def load_catalog_item_files() -> list[Path]:
    if not ITEMS_DIR.exists():
        return []
    return sorted(p for p in ITEMS_DIR.rglob("*.json") if not p.name.startswith("_"))


def validate_catalog() -> list[str]:
    failures: list[str] = []
    try:
        indexes = build_registry_indexes(load_registries())
    except Exception as exc:
        return [f"registry load failed: {exc}"]

    seen_ids: dict[str, Path] = {}
    items: list[tuple[Path, Item]] = []
    paths = load_catalog_item_files()
    for path in paths:
        rel = path.relative_to(ROOT)
        try:
            raw = _load_json(path)
        except Exception as exc:
            failures.append(f"{rel}: invalid JSON: {exc}")
            continue
        item_id = raw.get("id")
        expected_stem = str(item_id).replace("-", "_")
        if path.stem != expected_stem:
            failures.append(f"{rel}: stem/id mismatch stem={path.stem} id={item_id}")
        if item_id in seen_ids:
            failures.append(f"{rel}: duplicate id {item_id!r} also at {seen_ids[item_id]}")
        elif isinstance(item_id, str):
            seen_ids[item_id] = rel
        try:
            item = Item.model_validate(raw)
        except ValidationError as exc:
            failures.append(f"{rel}: schema validation failed: {exc}")
            continue
        expected_dir = CATEGORY_DIRS[item.category]
        if path.parent.name != expected_dir:
            failures.append(f"{rel}: category {item.category!r} must live under {expected_dir}/")
        items.append((path, item))

    weapon_ids = {item.id for _, item in items if item.category == "weapon"}
    for path, item in items:
        rel = path.relative_to(ROOT)
        for tag in item.tags:
            if tag not in indexes["item_tags"]:
                failures.append(f"{rel}: unknown tag {tag!r}")
        for market_tag in item.market_tags:
            if market_tag not in indexes["market_tags"]:
                failures.append(f"{rel}: unknown market_tag {market_tag!r}")
        if item.rarity not in indexes["rarities"]:
            failures.append(f"{rel}: unknown rarity {item.rarity!r}")
        if item.legality not in indexes["legality"]:
            failures.append(f"{rel}: unknown legality {item.legality!r}")
        if item.magic_field is not None and item.magic_field not in indexes["magic_fields"]:
            failures.append(f"{rel}: unknown magic_field {item.magic_field!r}")
        if item.subcategory is not None:
            allowed = indexes["subcategories"].get(item.category)
            if allowed is None:
                failures.append(f"{rel}: subcategory not allowed for category {item.category!r}")
            elif item.subcategory not in allowed:
                failures.append(f"{rel}: unknown subcategory {item.subcategory!r}")
        if item.knowledge_tag is not None and item.knowledge_tag not in indexes["combat_knowledge"]:
            failures.append(f"{rel}: unknown knowledge_tag {item.knowledge_tag!r}")
        if item.application_tag is not None:
            if item.application_tag not in indexes["combat_applications"]:
                failures.append(f"{rel}: unknown application_tag {item.application_tag!r}")
            else:
                expected = indexes["application_parent"][item.application_tag]
                if item.knowledge_tag != expected:
                    failures.append(
                        f"{rel}: application_tag {item.application_tag!r} requires knowledge_tag {expected!r}"
                    )
        if item.category == "ammunition":
            for weapon_id in item.used_with:
                if weapon_id not in weapon_ids:
                    failures.append(f"{rel}: used_with references unknown weapon {weapon_id!r}")
    return failures


def main() -> int:
    item_count = len(load_catalog_item_files())
    failures = validate_catalog()
    if failures:
        print(f"FAIL ({len(failures)} errors, {item_count} item files)")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"PASS ({item_count} item files, 0 errors)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
