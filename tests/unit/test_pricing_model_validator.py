import pytest
from pydantic import ValidationError

from api.items import Pricing, PricingComponentRef, PricingInputs


def test_authored_with_canonical_value_constructs() -> None:
    pricing = Pricing(model="authored", canonical_value_cp=1500)

    assert pricing.model == "authored"
    assert pricing.canonical_value_cp == 1500
    assert pricing.inputs is None


def test_authored_without_canonical_value_fails() -> None:
    with pytest.raises(ValidationError, match="requires canonical_value_cp"):
        Pricing(model="authored")


def test_authored_with_inputs_fails() -> None:
    inputs = PricingInputs(components=[PricingComponentRef(id="base_weapon")])

    with pytest.raises(ValidationError, match="must not have inputs"):
        Pricing(model="authored", canonical_value_cp=1500, inputs=inputs)


def test_computed_with_inputs_constructs() -> None:
    inputs = PricingInputs(components=[PricingComponentRef(id="base_weapon")])
    pricing = Pricing(model="computed", inputs=inputs)

    assert pricing.model == "computed"
    assert pricing.inputs == inputs
    assert pricing.canonical_value_cp is None


def test_computed_without_inputs_fails() -> None:
    with pytest.raises(ValidationError, match="requires inputs"):
        Pricing(model="computed")


def test_computed_with_canonical_value_fails() -> None:
    inputs = PricingInputs(components=[PricingComponentRef(id="base_weapon")])

    with pytest.raises(ValidationError, match="must not author canonical_value_cp"):
        Pricing(model="computed", canonical_value_cp=1500, inputs=inputs)


def test_pricing_inputs_empty_components_fails() -> None:
    with pytest.raises(ValidationError):
        PricingInputs(components=[])


@pytest.mark.parametrize("bad_id", ["BaseWeapon", "base-weapon"])
def test_pricing_component_ref_invalid_id_pattern_fails(bad_id: str) -> None:
    with pytest.raises(ValidationError):
        PricingComponentRef(id=bad_id)


def test_pricing_component_ref_extra_field_fails() -> None:
    with pytest.raises(ValidationError):
        PricingComponentRef(id="base_weapon", extra_field=True)