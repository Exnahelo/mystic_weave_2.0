import json
from pathlib import Path

import pytest

from core.pricing import _DENOMINATIONS, load_price_rules


BASE_RULES = {
    "schema_version": 1,
    "components": [
        {"id": "base", "kind": "lookup", "table": {"weapon.simple": 200}},
        {"id": "premium", "kind": "flat", "value_cp": 100},
    ],
    "advisory_bands": {},
    "regional_modifiers": None,
}


def _write_rules(tmp_path: Path, rules: dict) -> Path:
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(rules))
    return path


def test_real_price_rules_loads_cleanly() -> None:
    rules = load_price_rules(Path("data/catalog/economy/price_rules.json"))

    assert rules["schema_version"] == 1


def test_regional_modifiers_must_be_null(tmp_path: Path) -> None:
    rules = {**BASE_RULES, "regional_modifiers": {"capital": 1.2}}

    with pytest.raises(ValueError, match="regional pricing deferred"):
        load_price_rules(_write_rules(tmp_path, rules))


def test_unsupported_schema_version_fails(tmp_path: Path) -> None:
    rules = {**BASE_RULES, "schema_version": 2}

    with pytest.raises(ValueError, match="unsupported schema_version"):
        load_price_rules(_write_rules(tmp_path, rules))


def test_empty_components_fails(tmp_path: Path) -> None:
    rules = {**BASE_RULES, "components": []}

    with pytest.raises(ValueError, match="non-empty"):
        load_price_rules(_write_rules(tmp_path, rules))


def test_duplicate_component_id_fails(tmp_path: Path) -> None:
    rules = {
        **BASE_RULES,
        "components": [
            {"id": "base", "kind": "lookup", "table": {"weapon.simple": 200}},
            {"id": "base", "kind": "flat", "value_cp": 100},
        ],
    }

    with pytest.raises(ValueError, match="duplicate component id"):
        load_price_rules(_write_rules(tmp_path, rules))


def test_unknown_component_kind_fails(tmp_path: Path) -> None:
    rules = {**BASE_RULES, "components": [{"id": "base", "kind": "weird"}]}

    with pytest.raises(ValueError, match="unknown kind"):
        load_price_rules(_write_rules(tmp_path, rules))


def test_lookup_non_int_value_fails(tmp_path: Path) -> None:
    rules = {
        **BASE_RULES,
        "components": [
            {"id": "base", "kind": "lookup", "table": {"weapon.simple": "200"}}
        ],
    }

    with pytest.raises(ValueError, match="non-negative int"):
        load_price_rules(_write_rules(tmp_path, rules))


def test_lookup_negative_value_fails(tmp_path: Path) -> None:
    rules = {
        **BASE_RULES,
        "components": [
            {"id": "base", "kind": "lookup", "table": {"weapon.simple": -1}}
        ],
    }

    with pytest.raises(ValueError, match="non-negative int"):
        load_price_rules(_write_rules(tmp_path, rules))


def test_flat_without_value_cp_fails(tmp_path: Path) -> None:
    rules = {**BASE_RULES, "components": [{"id": "premium", "kind": "flat"}]}

    with pytest.raises(ValueError, match="non-negative int"):
        load_price_rules(_write_rules(tmp_path, rules))


def test_currency_denominations_match_catalog_file() -> None:
    currencies = json.loads(Path("data/catalog/economy/currencies.json").read_text())[
        "currencies"
    ]
    expected = sorted(
        ((entry["id"], entry["value_cp"]) for entry in currencies),
        key=lambda pair: pair[1],
        reverse=True,
    )

    assert _DENOMINATIONS == expected