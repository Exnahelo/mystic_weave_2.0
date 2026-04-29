#!/usr/bin/env python3
"""Validate core game data JSON files for structure and integrity."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

DOMAIN_KEYS = {
    "power",
    "agility",
    "perception",
    "endurance",
    "intellect",
    "will",
    "presence",
}

FIELD_KEYS = {
    "sacred",
    "warding",
    "binding",
    "elemental",
    "druidry",
    "illusion",
    "runecraft",
    "alchemy",
    "necromancy",
}
BEAST_BIOMES = {
    "feywood",
    "wetlands",
    "volcanic_highlands",
    "alpine_peaks",
    "draconic_grasslands",
    "temperate_forest",
    "crystal_caverns",
    "shadowed_hollows",
    "generalist",
}
CREATURE_DOMAIN_KEYS = {"physical", "instinct", "composure"}
TACTICAL_ROLE_VALUES = {"mount", "pack", "scout", "guard", "hunter", "companion"}
TRAINING_LEVEL_VALUES = {"untrained", "basic", "trained", "expert"}
BOND_LEVEL_VALUES = {"wary", "accepting", "bonded", "devoted"}
AGE_CATEGORY_VALUES = {"juvenile", "young_adult", "adult", "mature", "elder"}
CREATURE_SIZE_VALUES = {"tiny", "small", "medium", "large", "huge"}
CARRYING_CAPACITY_VALUES = {"none", "small", "medium", "large"}
MOVEMENT_MODE_VALUES = {"walk", "fly", "swim", "climb", "burrow"}
NATURAL_WEAPON_VALUES = {"bite", "claw", "hoof", "tail_slam", "breath", "sting", "none"}

SPELL_FIELDS = FIELD_KEYS
TRAIT_TYPES = {"passive", "conditional", "active"}
TRAIT_USAGES = {"always", "per_scene", "per_day"}
TRAIT_FATIGUE = {"none", "fatiguing"}
SNAKE_CASE_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
KEBAB_CASE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WORLD_META_TAGS = {"canonical", "canonical-realm", "placeholder", "TODO", "draft"}

VALID_KNOWLEDGE_GROUPS: set[str] = set()
VALID_MAGIC_FIELDS: set[str] = set()
VALID_APPLICATIONS: set[str] = set()
VALID_BEAST_NATURAL_ABILITIES: set[str] = set()


def _failures_append(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def _load_json(path: Path) -> list[dict]:
    if path.name.startswith("_"):
        return []
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError(f"{path.name}: expected top-level list")
    return [
        row for row in payload
        if not (isinstance(row, dict) and str(row.get("index", "")).startswith("_"))
    ]


def _load_tag_file(path: Path) -> list[dict]:
    return _load_json(path)


def _validate_snake_case(label: str, value: object, failures: list[str]) -> None:
    _failures_append(
        failures,
        isinstance(value, str) and bool(SNAKE_CASE_RE.fullmatch(value)),
        f"{label} must be snake_case",
    )


def _validate_character_tag_refs(
    label: str,
    row: dict,
    failures: list[str],
) -> None:
    knowledge_tags = row.get("knowledge_tags")
    application_tags = row.get("application_tags")
    field_tags = row.get("field_tags")

    if isinstance(knowledge_tags, dict):
        for tag in knowledge_tags:
            if tag in VALID_APPLICATIONS:
                failures.append(f"unknown tag slot: application '{tag}' placed in knowledge_tags in {label}")
            elif tag in VALID_MAGIC_FIELDS:
                failures.append(f"unknown tag slot: magic field '{tag}' placed in knowledge_tags in {label}")
            elif tag not in VALID_KNOWLEDGE_GROUPS:
                failures.append(f"unknown tag '{tag}' in {label}.knowledge_tags")

    if isinstance(application_tags, dict):
        for tag in application_tags:
            if tag in VALID_KNOWLEDGE_GROUPS:
                failures.append(f"unknown tag slot: knowledge group '{tag}' placed in application_tags in {label}")
            elif tag in VALID_MAGIC_FIELDS:
                failures.append(f"unknown tag slot: magic field '{tag}' placed in application_tags in {label}")
            elif tag not in VALID_APPLICATIONS:
                failures.append(f"unknown tag '{tag}' in {label}.application_tags")

    if isinstance(field_tags, dict):
        for tag in field_tags:
            if tag not in VALID_MAGIC_FIELDS:
                failures.append(f"unknown tag '{tag}' in {label}.field_tags")


def _validate_tag_dict(
    label: str,
    tag_group: object,
    group_name: str,
    failures: list[str],
    *,
    allow_empty: bool = False,
) -> None:
    _failures_append(failures, isinstance(tag_group, dict), f"{label}.{group_name} must be object")
    if not isinstance(tag_group, dict):
        return
    if not allow_empty:
        _failures_append(failures, len(tag_group) > 0, f"{label}.{group_name} must include at least one tag")
    for tkey, tval in tag_group.items():
        _failures_append(failures, isinstance(tkey, str) and tkey, f"{label}.{group_name} contains invalid tag key")
        _failures_append(
            failures,
            isinstance(tval, int) and 1 <= tval <= 5,
            f"{label}.{group_name}.{tkey} tier must be int between 1 and 5",
        )


def _validate_field_tags(label: str, field_tags: object, failures: list[str]) -> None:
    _failures_append(failures, isinstance(field_tags, dict), f"{label}.field_tags must be object")
    if not isinstance(field_tags, dict):
        return
    for key, val in field_tags.items():
        _failures_append(failures, key in FIELD_KEYS, f"{label}.field_tags.{key} must be one of {sorted(FIELD_KEYS)}")
        _failures_append(
            failures,
            isinstance(val, int) and 1 <= val <= 5,
            f"{label}.field_tags.{key} tier must be int between 1 and 5",
        )


def _validate_knowledge_groups(path: Path, failures: list[str]) -> None:
    rows = _load_tag_file(path)
    seen_indices: set[str] = set()
    _failures_append(failures, len(rows) == 30, f"{path.name}: expected 30 entries")

    for i, row in enumerate(rows):
        label = f"{path.name}[{i}]"
        _failures_append(failures, isinstance(row, dict), f"{label}: expected object")
        if not isinstance(row, dict):
            continue
        idx = row.get("index")
        if isinstance(idx, str) and idx.startswith("_"):
            continue
        _failures_append(failures, isinstance(idx, str) and idx, f"{label}.index must be non-empty string")
        _validate_snake_case(f"{label}.index", idx, failures)
        if isinstance(idx, str):
            _failures_append(failures, idx not in seen_indices, f"{label}.index duplicated: {idx}")
            seen_indices.add(idx)
        _failures_append(failures, row.get("primary_domain") in DOMAIN_KEYS, f"{label}.primary_domain must be one of {sorted(DOMAIN_KEYS)}")
        secondary = row.get("secondary_domain")
        _failures_append(
            failures,
            secondary is None or secondary in DOMAIN_KEYS,
            f"{label}.secondary_domain must be null or one of {sorted(DOMAIN_KEYS)}",
        )
        _failures_append(failures, row.get("kind") == "mundane", f"{label}.kind must equal 'mundane'")
        _failures_append(failures, isinstance(row.get("description"), str) and row.get("description").strip(), f"{label}.description must be non-empty string")
        examples = row.get("examples")
        _failures_append(failures, isinstance(examples, list) and len(examples) > 0, f"{label}.examples must be non-empty list")


def _validate_magic_fields(path: Path, failures: list[str]) -> None:
    rows = _load_tag_file(path)
    seen_indices: set[str] = set()
    _failures_append(failures, len(rows) == 9, f"{path.name}: expected 9 entries")
    indices = {row.get("index") for row in rows if isinstance(row, dict)}
    _failures_append(failures, "druidry" in indices, f"{path.name}: druidry entry missing")
    _failures_append(failures, "nature" not in indices, f"{path.name}: nature entry must be absent")

    for i, row in enumerate(rows):
        label = f"{path.name}[{i}]"
        _failures_append(failures, isinstance(row, dict), f"{label}: expected object")
        if not isinstance(row, dict):
            continue
        idx = row.get("index")
        if isinstance(idx, str) and idx.startswith("_"):
            continue
        _failures_append(failures, isinstance(idx, str) and idx, f"{label}.index must be non-empty string")
        _validate_snake_case(f"{label}.index", idx, failures)
        if isinstance(idx, str):
            _failures_append(failures, idx not in seen_indices, f"{label}.index duplicated: {idx}")
            seen_indices.add(idx)
        _failures_append(failures, row.get("primary_domain") in DOMAIN_KEYS, f"{label}.primary_domain must be one of {sorted(DOMAIN_KEYS)}")
        secondary = row.get("secondary_domain")
        _failures_append(
            failures,
            secondary is None or secondary in DOMAIN_KEYS,
            f"{label}.secondary_domain must be null or one of {sorted(DOMAIN_KEYS)}",
        )
        _failures_append(failures, row.get("kind") == "magical", f"{label}.kind must equal 'magical'")
        _failures_append(failures, isinstance(row.get("description"), str) and row.get("description").strip(), f"{label}.description must be non-empty string")
        examples = row.get("examples")
        _failures_append(failures, isinstance(examples, list) and len(examples) > 0, f"{label}.examples must be non-empty list")


def _validate_applications(path: Path, failures: list[str]) -> None:
    rows = _load_tag_file(path)
    seen_indices: set[str] = set()
    _failures_append(failures, len(rows) == 148, f"{path.name}: expected 148 entries")

    for i, row in enumerate(rows):
        label = f"{path.name}[{i}]"
        _failures_append(failures, isinstance(row, dict), f"{label}: expected object")
        if not isinstance(row, dict):
            continue
        idx = row.get("index")
        if isinstance(idx, str) and idx.startswith("_"):
            continue
        _failures_append(failures, isinstance(idx, str) and idx, f"{label}.index must be non-empty string")
        _validate_snake_case(f"{label}.index", idx, failures)
        if isinstance(idx, str):
            _failures_append(failures, idx not in seen_indices, f"{label}.index duplicated: {idx}")
            seen_indices.add(idx)
        group = row.get("group")
        _failures_append(
            failures,
            isinstance(group, str) and group in VALID_KNOWLEDGE_GROUPS,
            f"{label}.group must reference a knowledge_groups.json index",
        )
        primary = row.get("primary_domain")
        _failures_append(
            failures,
            primary in DOMAIN_KEYS or primary == "varies",
            f"{label}.primary_domain must be one of {sorted(DOMAIN_KEYS)} or 'varies'",
        )
        _failures_append(failures, isinstance(row.get("description"), str) and row.get("description").strip(), f"{label}.description must be non-empty string")
        examples = row.get("examples")
        _failures_append(failures, isinstance(examples, list) and len(examples) >= 1, f"{label}.examples must include at least 1 entry")


def _validate_domain_bonuses(label: str, bonuses: object, failures: list[str]) -> None:
    _failures_append(failures, isinstance(bonuses, dict), f"{label}.domain_bonuses must be object")
    if not isinstance(bonuses, dict):
        return
    _failures_append(failures, set(bonuses.keys()) == DOMAIN_KEYS, f"{label}.domain_bonuses keys mismatch")
    total = 0
    for dkey, val in bonuses.items():
        _failures_append(failures, isinstance(val, int), f"{label}.domain_bonuses.{dkey} must be int")
        if isinstance(val, int):
            total += val
            _failures_append(failures, val >= 0, f"{label}.domain_bonuses.{dkey} must be >= 0")
    _failures_append(failures, total == 10, f"{label}.domain_bonuses total must be 10 (got {total})")


def _validate_ancestries(path: Path, failures: list[str]) -> None:
    ancestries = _load_json(path)
    seen_indices: set[str] = set()
    _failures_append(failures, len(ancestries) == 8, f"{path.name}: expected 8 ancestry entries")

    for i, row in enumerate(ancestries):
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

        domains = row.get("domains")
        _failures_append(failures, isinstance(domains, dict), f"{label}.domains must be object")
        if isinstance(domains, dict):
            _failures_append(failures, set(domains.keys()) == DOMAIN_KEYS, f"{label}.domains keys mismatch")
            total = 0
            for dkey, val in domains.items():
                _failures_append(failures, isinstance(val, int), f"{label}.domains.{dkey} must be int")
                if isinstance(val, int):
                    total += val
                    _failures_append(failures, 1 <= val <= 60, f"{label}.domains.{dkey} must be between 1 and 60")
            _failures_append(failures, total == 280, f"{label}.domains total must be 280 (got {total})")

        traits = row.get("traits")
        _failures_append(failures, isinstance(traits, list), f"{label}.traits must be list")
        if not isinstance(traits, list):
            continue

        for t_idx, trait in enumerate(traits):
            trait_label = f"{label}.traits[{t_idx}]"
            _failures_append(failures, isinstance(trait, dict), f"{trait_label} must be object")
            if not isinstance(trait, dict):
                continue
            _failures_append(failures, isinstance(trait.get("name"), str) and trait.get("name"), f"{trait_label}.name must be non-empty string")
            _failures_append(failures, trait.get("type") in TRAIT_TYPES, f"{trait_label}.type must be one of {sorted(TRAIT_TYPES)}")
            _failures_append(
                failures,
                isinstance(trait.get("description"), str) and trait.get("description"),
                f"{trait_label}.description must be non-empty string",
            )

            application_tag = trait.get("application_tag")
            _failures_append(
                failures,
                application_tag is None or (isinstance(application_tag, str) and application_tag in VALID_APPLICATIONS),
                f"{trait_label}.application_tag must be a valid application tag or null",
            )
            roll_domain = trait.get("roll_domain")
            _failures_append(
                failures,
                roll_domain is None or roll_domain in DOMAIN_KEYS or roll_domain == "will_or_power",
                f"{trait_label}.roll_domain must be domain key, 'will_or_power', or null",
            )
            usage = trait.get("usage")
            _failures_append(
                failures,
                usage is None or usage in TRAIT_USAGES,
                f"{trait_label}.usage must be one of {sorted(TRAIT_USAGES)} or null",
            )
            fatigue = trait.get("fatigue")
            _failures_append(
                failures,
                fatigue is None or fatigue in TRAIT_FATIGUE,
                f"{trait_label}.fatigue must be one of {sorted(TRAIT_FATIGUE)} or null",
            )
            _failures_append(
                failures,
                trait.get("mechanical_note") is None or isinstance(trait.get("mechanical_note"), str),
                f"{trait_label}.mechanical_note must be string or null",
            )


def _validate_cultures(path: Path, failures: list[str]) -> None:
    cultures = _load_json(path)
    seen_indices: set[str] = set()
    _failures_append(failures, len(cultures) == 11, f"{path.name}: expected 11 culture entries")

    for i, row in enumerate(cultures):
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
        _validate_domain_bonuses(label, row.get("domain_bonuses"), failures)
        _validate_tag_dict(label, row.get("knowledge_tags"), "knowledge_tags", failures)
        _validate_tag_dict(label, row.get("application_tags"), "application_tags", failures)
        _validate_field_tags(label, row.get("field_tags"), failures)
        _validate_character_tag_refs(label, row, failures)


def _validate_tag_rows(path: Path, failures: list[str], expected_count: int) -> None:
    rows = _load_json(path)
    seen_indices: set[str] = set()
    is_focus = path.name == "focus.json"
    is_background = path.name == "background.json"

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

        if is_background:
            _validate_domain_bonuses(label, row.get("domain_bonuses"), failures)

        _validate_tag_dict(label, row.get("knowledge_tags"), "knowledge_tags", failures)
        _validate_tag_dict(label, row.get("application_tags"), "application_tags", failures)
        _validate_field_tags(label, row.get("field_tags"), failures)
        _validate_character_tag_refs(label, row, failures)

        if is_focus:
            signature_tag = row.get("signature_tag")
            _failures_append(failures, isinstance(signature_tag, str) and signature_tag, f"{label}.signature_tag must be non-empty string")
            knowledge_tags = row.get("knowledge_tags")
            if isinstance(signature_tag, str) and isinstance(knowledge_tags, dict):
                _failures_append(
                    failures,
                    knowledge_tags.get(signature_tag) == 2,
                    f"{label}.signature_tag must appear in knowledge_tags at tier 2",
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

        _failures_append(failures, set(row.keys()) == required_keys, f"{label}: keys must match {sorted(required_keys)}")
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
        _failures_append(failures, isinstance(field, str) and field in SPELL_FIELDS, f"{label}.field must be one of {sorted(SPELL_FIELDS)}")
        primary = row.get("primary_domain")
        _failures_append(failures, isinstance(primary, str) and primary in DOMAIN_KEYS, f"{label}.primary_domain must be one of {sorted(DOMAIN_KEYS)}")
        alternate = row.get("alternate_domain")
        _failures_append(
            failures,
            alternate is None or (isinstance(alternate, str) and alternate in DOMAIN_KEYS),
            f"{label}.alternate_domain must be null or one of {sorted(DOMAIN_KEYS)}",
        )
        tier = row.get("tier")
        _failures_append(failures, isinstance(tier, int) and 1 <= tier <= 5, f"{label}.tier must be int between 1 and 5")


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
        roll_tag = row.get("roll_tag")
        _failures_append(
            failures,
            roll_tag is None or roll_tag in VALID_APPLICATIONS,
            f"unknown tag '{roll_tag}' in {path.name} item roll_tag",
        )
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


def _validate_items_roll_tags(path: Path, failures: list[str]) -> None:
    rows = _load_json(path)
    for i, row in enumerate(rows):
        label = f"{path.name}[{i}]"
        if not isinstance(row, dict):
            continue
        roll_tag = row.get("roll_tag")
        _failures_append(
            failures,
            roll_tag is None or roll_tag in VALID_APPLICATIONS,
            f"unknown tag '{roll_tag}' in {label}.roll_tag",
        )


def _validate_simple_catalog(path: Path, failures: list[str]) -> list[dict]:
    rows = _load_json(path)
    seen_ids: set[str] = set()
    for i, row in enumerate(rows):
        label = f"{path.name}[{i}]"
        _failures_append(failures, isinstance(row, dict), f"{label}: expected object")
        if not isinstance(row, dict):
            continue
        required = {"id", "display_name", "description"}
        _failures_append(failures, required.issubset(row.keys()), f"{label}: missing one of {sorted(required)}")
        item_id = row.get("id")
        _validate_snake_case(f"{label}.id", item_id, failures)
        if isinstance(item_id, str):
            _failures_append(failures, item_id not in seen_ids, f"{label}.id duplicated: {item_id}")
            seen_ids.add(item_id)
        _failures_append(failures, isinstance(row.get("display_name"), str) and row.get("display_name").strip(), f"{label}.display_name must be non-empty string")
        _failures_append(failures, isinstance(row.get("description"), str) and row.get("description").strip(), f"{label}.description must be non-empty string")
    return rows


def _validate_beast_creatures(path: Path, failures: list[str]) -> None:
    rows = _load_json(path)
    seen_subspecies: set[str] = set()
    required_keys = {
        "species",
        "subspecies",
        "display_name",
        "biome",
        "size",
        "age_category",
        "tactical_roles_defaults",
        "natural_abilities",
        "natural_weapons",
        "movement_modes",
        "carrying_capacity",
        "base_domains",
        "base_hp",
        "temperament",
        "description",
    }

    for i, row in enumerate(rows):
        label = f"{path.name}[{i}]"
        _failures_append(failures, isinstance(row, dict), f"{label}: expected object")
        if not isinstance(row, dict):
            continue
        _failures_append(failures, required_keys.issubset(row.keys()), f"{label}: missing required keys")
        _validate_snake_case(f"{label}.species", row.get("species"), failures)
        _validate_snake_case(f"{label}.subspecies", row.get("subspecies"), failures)
        subspecies = row.get("subspecies")
        if isinstance(subspecies, str):
            _failures_append(failures, subspecies not in seen_subspecies, f"{label}.subspecies duplicated: {subspecies}")
            seen_subspecies.add(subspecies)
        _failures_append(failures, isinstance(row.get("display_name"), str) and row.get("display_name").strip(), f"{label}.display_name must be non-empty string")
        _failures_append(failures, row.get("biome") in BEAST_BIOMES, f"{label}.biome must be one of {sorted(BEAST_BIOMES)}")
        _failures_append(failures, row.get("size") in CREATURE_SIZE_VALUES, f"{label}.size must be one of {sorted(CREATURE_SIZE_VALUES)}")
        _failures_append(failures, row.get("age_category") in AGE_CATEGORY_VALUES, f"{label}.age_category must be one of {sorted(AGE_CATEGORY_VALUES)}")
        roles = row.get("tactical_roles_defaults")
        _failures_append(
            failures,
            isinstance(roles, list) and len(roles) >= 1,
            f"{label}.tactical_roles_defaults must be a non-empty list",
        )
        if isinstance(roles, list):
            for r_idx, role in enumerate(roles):
                _failures_append(
                    failures,
                    role in TACTICAL_ROLE_VALUES,
                    f"{label}.tactical_roles_defaults[{r_idx}] must be a valid tactical role (got {role!r})",
                )
            _failures_append(
                failures,
                len(roles) == len(set(roles)),
                f"{label}.tactical_roles_defaults must not contain duplicates",
            )
        _failures_append(failures, row.get("carrying_capacity") in CARRYING_CAPACITY_VALUES, f"{label}.carrying_capacity must be one of {sorted(CARRYING_CAPACITY_VALUES)}")

        natural_abilities = row.get("natural_abilities")
        _failures_append(failures, isinstance(natural_abilities, list), f"{label}.natural_abilities must be list")
        if isinstance(natural_abilities, list):
            for ability in natural_abilities:
                _failures_append(failures, isinstance(ability, str) and ability in VALID_BEAST_NATURAL_ABILITIES, f"{label}.natural_abilities contains unknown id: {ability}")

        natural_weapons = row.get("natural_weapons")
        _failures_append(failures, isinstance(natural_weapons, list), f"{label}.natural_weapons must be list")
        if isinstance(natural_weapons, list):
            for weapon in natural_weapons:
                _failures_append(failures, weapon in NATURAL_WEAPON_VALUES, f"{label}.natural_weapons contains invalid value: {weapon}")

        movement_modes = row.get("movement_modes")
        _failures_append(failures, isinstance(movement_modes, list), f"{label}.movement_modes must be list")
        if isinstance(movement_modes, list):
            for movement_mode in movement_modes:
                _failures_append(failures, movement_mode in MOVEMENT_MODE_VALUES, f"{label}.movement_modes contains invalid value: {movement_mode}")

        base_domains = row.get("base_domains")
        _failures_append(failures, isinstance(base_domains, dict), f"{label}.base_domains must be object")
        if isinstance(base_domains, dict):
            _failures_append(failures, set(base_domains.keys()) == CREATURE_DOMAIN_KEYS, f"{label}.base_domains keys must be exactly {sorted(CREATURE_DOMAIN_KEYS)}")
            for dkey, val in base_domains.items():
                _failures_append(failures, isinstance(val, int) and 25 <= val <= 60, f"{label}.base_domains.{dkey} must be int 25-60")

        base_hp = row.get("base_hp")
        _failures_append(failures, isinstance(base_hp, dict), f"{label}.base_hp must be object")
        if isinstance(base_hp, dict):
            current = base_hp.get("current")
            maximum = base_hp.get("max")
            _failures_append(failures, isinstance(current, int), f"{label}.base_hp.current must be int")
            _failures_append(failures, isinstance(maximum, int), f"{label}.base_hp.max must be int")
            if isinstance(current, int) and isinstance(maximum, int):
                _failures_append(failures, maximum >= current >= 0, f"{label}.base_hp must satisfy max >= current >= 0")

        _failures_append(failures, isinstance(row.get("temperament"), str) and row.get("temperament").strip(), f"{label}.temperament must be non-empty string")
        _failures_append(failures, isinstance(row.get("description"), str) and row.get("description").strip(), f"{label}.description must be non-empty string")


def _validate_beast_exceptional(path: Path, failures: list[str]) -> None:
    rows = _load_json(path)
    for i, row in enumerate(rows):
        label = f"{path.name}[{i}]"
        _failures_append(failures, isinstance(row, dict), f"{label}: expected object")
        if not isinstance(row, dict):
            continue
        _failures_append(failures, isinstance(row.get("species"), str) and row.get("species").strip(), f"{label}.species must be non-empty string")
        _failures_append(failures, isinstance(row.get("subspecies"), str) and row.get("subspecies").strip(), f"{label}.subspecies must be non-empty string")


def _validate_world_yaml(path: Path, failures: list[str]) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    label = path.relative_to(path.parents[2]).as_posix()
    if not isinstance(data, dict):
        failures.append(f"{label}: expected top-level mapping")
        return

    world_id = data.get("id")
    if not isinstance(world_id, str) or not world_id:
        failures.append(f"{label}: id must be non-empty string")
    else:
        expected_stem = world_id.replace("-", "_")
        if path.stem != expected_stem:
            failures.append(f"{label}: stem/id mismatch stem={path.stem} id={world_id}")

    tags = data.get("tags", [])
    if not isinstance(tags, list):
        failures.append(f"{label}: tags must be a list")
        return

    seen: set[str] = set()
    for index, tag in enumerate(tags):
        if not isinstance(tag, str):
            failures.append(f"{label}: tags[{index}] must be string")
            continue
        if not KEBAB_CASE_RE.fullmatch(tag):
            failures.append(f"{label}: tags[{index}] must be kebab-case (got {tag})")
        if tag in WORLD_META_TAGS:
            failures.append(f"{label}: forbidden meta tag {tag}")
        if tag in seen:
            failures.append(f"{label}: duplicate tag {tag}")
        seen.add(tag)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"

    global VALID_KNOWLEDGE_GROUPS, VALID_MAGIC_FIELDS, VALID_APPLICATIONS, VALID_BEAST_NATURAL_ABILITIES
    VALID_KNOWLEDGE_GROUPS = {g["index"] for g in _load_tag_file(data_dir / "tags" / "knowledge_groups.json")}
    VALID_MAGIC_FIELDS = {f["index"] for f in _load_tag_file(data_dir / "tags" / "magic_fields.json")}
    VALID_APPLICATIONS = {a["index"] for a in _load_tag_file(data_dir / "tags" / "applications.json")}

    failures: list[str] = []
    _validate_knowledge_groups(data_dir / "tags" / "knowledge_groups.json", failures)
    _validate_magic_fields(data_dir / "tags" / "magic_fields.json", failures)
    _validate_applications(data_dir / "tags" / "applications.json", failures)
    _validate_ancestries(data_dir / "characters" / "ancestry.json", failures)
    _validate_cultures(data_dir / "characters" / "culture.json", failures)
    _validate_tag_rows(data_dir / "characters" / "focus.json", failures, expected_count=9)
    _validate_tag_rows(data_dir / "characters" / "background.json", failures, expected_count=8)
    legacy_items_dir = data_dir / "items"
    if legacy_items_dir.exists():
        _validate_apparel(legacy_items_dir / "apparel.json", failures)
        for item_file in legacy_items_dir.glob("*.json"):
            if item_file.name.startswith("_"):
                continue
            _validate_items_roll_tags(item_file, failures)

    beast_dir = data_dir / "companions"
    natural_ability_rows = _validate_simple_catalog(beast_dir / "natural_abilities.json", failures)
    VALID_BEAST_NATURAL_ABILITIES = {row["id"] for row in natural_ability_rows if isinstance(row, dict) and isinstance(row.get("id"), str)}
    _validate_simple_catalog(beast_dir / "learned_commands.json", failures)
    _validate_simple_catalog(beast_dir / "tactical_roles.json", failures)
    _validate_beast_creatures(beast_dir / "creatures.json", failures)
    _validate_beast_exceptional(beast_dir / "exceptional.json", failures)

    magic_dir = data_dir / "magic"
    for spell_file in sorted(magic_dir.glob("*.json")):
        if spell_file.name == "fields.json" or spell_file.name.startswith("_"):
            continue
        _validate_spells(spell_file, failures)

    for world_file in sorted((data_dir / "world").rglob("*.yaml")):
        if world_file.name.startswith("_"):
            continue
        _validate_world_yaml(world_file, failures)

    if failures:
        print("❌ Data validation failed")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)

    print("✅ Data validation passed")


if __name__ == "__main__":
    main()
