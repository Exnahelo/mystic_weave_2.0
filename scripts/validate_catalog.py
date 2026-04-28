"""
Validates the item catalog against the schema and the controlled vocabularies.

Reports per-item validation results and derived indexes.
"""

import json
import sys
from pathlib import Path

from pydantic import ValidationError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.items import Item, derive_indexes  # noqa: E402


CATALOG_DIR = ROOT / "data" / "catalog"
ITEMS_DIR = CATALOG_DIR / "items"
MECH_DIR = CATALOG_DIR / "mechanics"


def load_vocab(path: Path, key: str, id_field: str = "id") -> set[str]:
    data = json.loads(path.read_text())
    return {entry[id_field] for entry in data[key]}


def _validate_effect_params(
    item_id: str,
    eff: object,
    effect_contracts: dict[str, dict],
    damage_type_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    contract = effect_contracts[eff.id]
    provided = set(eff.params.keys())
    declared = set(contract.keys())

    # Required params present
    for pname, pspec in contract.items():
        if pspec.get("required", False) and pname not in provided:
            errors.append(f"{item_id}/{eff.id}: missing required param '{pname}'")

    # No unknown params
    for pname in provided - declared:
        errors.append(f"{item_id}/{eff.id}: unknown param '{pname}'")

    # Type check
    type_map = {
        "int": int,
        "string": str,
        "bool": bool,
        "float": (int, float),
    }
    for pname, value in eff.params.items():
        if pname not in contract:
            continue  # already reported above
        expected = contract[pname]["type"]
        if expected not in type_map:
            errors.append(
                f"{item_id}/{eff.id}: param '{pname}' has "
                f"unsupported declared type '{expected}' in registry"
            )
            continue
        if not isinstance(value, type_map[expected]):
            errors.append(
                f"{item_id}/{eff.id}: param '{pname}' expected "
                f"{expected}, got {type(value).__name__}"
            )

    # Cross-reference: damage_type must be in damage_types.json
    if "damage_type" in eff.params:
        dt = eff.params["damage_type"]
        if dt not in damage_type_ids:
            errors.append(f"{item_id}/{eff.id}: unknown damage_type '{dt}'")

    return errors


def main() -> int:
    # Load controlled vocabularies
    effect_ids = load_vocab(MECH_DIR / "effects.json", "effects")
    with (MECH_DIR / "effects.json").open() as f:
        effect_contracts = {e["id"]: e["params"] for e in json.load(f)["effects"]}
    affordance_ids = load_vocab(MECH_DIR / "affordances.json", "affordances")
    tag_ids = load_vocab(MECH_DIR / "tags.json", "tags")
    damage_type_ids = load_vocab(MECH_DIR / "damage_types.json", "damage_types")
    rarity_ids = load_vocab(MECH_DIR / "rarities.json", "rarities")
    property_ids = load_vocab(MECH_DIR / "item_properties.json", "item_properties")
    market_tag_ids = load_vocab(
        CATALOG_DIR / "economy" / "market_tags.json", "market_tags"
    )

    # Load all item files
    item_files = sorted(ITEMS_DIR.glob("**/*.json"))
    print(f"Found {len(item_files)} item file(s)\n")

    errors = 0
    seen_ids: dict[str, Path] = {}

    for path in item_files:
        rel = path.relative_to(ROOT)
        print(f"--- {rel} ---")

        # File-level: stem <-> id invariant
        raw = json.loads(path.read_text())
        stem = path.stem
        expected_stem = raw.get("id", "").replace("-", "_")
        if stem != expected_stem:
            print(f"  FAIL stem<->id: stem={stem} id={raw.get('id')}")
            errors += 1

        # Namespace uniqueness within catalog/items/**
        item_id = raw.get("id")
        if item_id in seen_ids:
            print(f"  FAIL duplicate id: also at {seen_ids[item_id]}")
            errors += 1
        else:
            seen_ids[item_id] = rel

        # Schema validation
        try:
            item = Item.model_validate(raw)
        except ValidationError as e:
            print(f"  FAIL schema:\n{e}")
            errors += 1
            continue

        # Vocabulary cross-checks
        for tag in item.tags:
            if tag not in tag_ids:
                print(f"  WARN unknown tag: {tag}")
        for aff in item.affordances:
            if aff not in affordance_ids:
                print(f"  WARN unknown affordance: {aff}")
        if item.worldness.rarity not in rarity_ids:
            print(f"  FAIL unknown rarity: {item.worldness.rarity}")
            errors += 1
        for mt in item.worldness.availability.market_tags:
            if mt not in market_tag_ids:
                print(f"  WARN unknown market_tag: {mt}")
        if item.modules.weapon:
            for prop in item.modules.weapon.properties:
                if prop not in property_ids:
                    print(f"  WARN unknown weapon property: {prop}")
            for dmg in item.modules.weapon.damage:
                if dmg.type not in damage_type_ids:
                    print(f"  FAIL unknown damage type: {dmg.type}")
                    errors += 1
        for eff in item.modules.effects:
            if eff.id not in effect_ids:
                print(f"  FAIL unknown effect id: {eff.id}")
                errors += 1
                continue
            for message in _validate_effect_params(
                item.id, eff, effect_contracts, damage_type_ids
            ):
                print(f"  FAIL {message}")
                errors += 1

        idx = derive_indexes(item)
        flags = [k for k, v in idx.items() if v]
        print(f"  OK: {item.id} -- derived: {flags}")

    print(f"\n{'PASS' if errors == 0 else f'FAIL ({errors} errors)'}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())