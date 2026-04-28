import pytest

from api.items import PricingComponentRef, PricingInputs
from core.pricing import cp_to_denominations, narrate_price, resolve_price_cp


RULES = {
    "components": [
        {
            "id": "base",
            "kind": "lookup",
            "table": {"weapon.simple": 200, "weapon.martial": 1500},
        },
        {
            "id": "magical_rarity",
            "kind": "lookup",
            "table": {"rare": 500000},
        },
        {"id": "attunement_premium", "kind": "flat", "value_cp": 10000},
    ]
}


def _inputs(*refs: PricingComponentRef) -> PricingInputs:
    return PricingInputs(components=list(refs))


def test_resolve_martial_weapon_only() -> None:
    inputs = _inputs(PricingComponentRef(id="base", key="weapon.martial"))

    assert resolve_price_cp(inputs, RULES) == 1500


def test_resolve_magical_martial_weapon() -> None:
    inputs = _inputs(
        PricingComponentRef(id="base", key="weapon.martial"),
        PricingComponentRef(id="magical_rarity", key="rare"),
        PricingComponentRef(id="attunement_premium"),
    )

    assert resolve_price_cp(inputs, RULES) == 511500


def test_resolve_unknown_component_id_fails() -> None:
    inputs = _inputs(PricingComponentRef(id="missing"))

    with pytest.raises(ValueError, match="unknown pricing component"):
        resolve_price_cp(inputs, RULES)


def test_lookup_component_without_key_fails() -> None:
    inputs = _inputs(PricingComponentRef(id="base"))

    with pytest.raises(ValueError, match="requires key"):
        resolve_price_cp(inputs, RULES)


def test_lookup_component_with_missing_key_fails() -> None:
    inputs = _inputs(PricingComponentRef(id="base", key="weapon.exotic"))

    with pytest.raises(ValueError, match="has no entry for key"):
        resolve_price_cp(inputs, RULES)


def test_flat_component_with_key_fails() -> None:
    inputs = _inputs(PricingComponentRef(id="attunement_premium", key="rare"))

    with pytest.raises(ValueError, match="must not have key"):
        resolve_price_cp(inputs, RULES)


def test_zero_cp_denominations_returns_empty_dict() -> None:
    assert cp_to_denominations(0) == {}


def test_denominations_default_skips_electrum() -> None:
    assert cp_to_denominations(1547) == {"gp": 15, "sp": 4, "cp": 7}


def test_denominations_with_electrum() -> None:
    assert cp_to_denominations(50, use_electrum=True) == {"ep": 1}


def test_denominations_default_no_electrum() -> None:
    assert cp_to_denominations(50) == {"sp": 5}


def test_denominations_negative_value_fails() -> None:
    with pytest.raises(ValueError):
        cp_to_denominations(-1)


def test_narrate_zero_price() -> None:
    assert narrate_price(0) == "nothing"


def test_narrate_cp_only() -> None:
    assert narrate_price(7) == "7 cp"


def test_narrate_gold_and_silver() -> None:
    assert narrate_price(150) == "1 gp 5 sp"


def test_narrate_mixed_denominations() -> None:
    assert narrate_price(1547) == "15 gp 4 sp 7 cp"