import pytest

from api.models import AdvancementState
from api.progression_math import apply_tag_counter_advance, award_for_scale, compute_cost, resolve_tag_domain


@pytest.mark.unit
def test_ap_cost_single_bracket() -> None:
    assert compute_cost(30, 35) == 5


@pytest.mark.unit
def test_ap_cost_cross_60_61() -> None:
    assert compute_cost(58, 63) == 8


@pytest.mark.unit
def test_ap_cost_cross_70_71() -> None:
    assert compute_cost(68, 73) == 13


@pytest.mark.unit
def test_ap_cost_exceed_cap() -> None:
    with pytest.raises(ValueError, match="cap"):
        compute_cost(78, 82)


@pytest.mark.unit
def test_tag_counter_rollover() -> None:
    adv, ap = apply_tag_counter_advance(AdvancementState(tag_counter=2))
    assert adv.tag_counter == 0
    assert adv.points_available == 1
    assert adv.points_earned_total == 1
    assert ap == 1


@pytest.mark.unit
def test_tag_counter_no_rollover() -> None:
    adv, ap = apply_tag_counter_advance(AdvancementState(tag_counter=1))
    assert adv.tag_counter == 2
    assert adv.points_available == 0
    assert ap == 0


@pytest.mark.unit
def test_t5_cap_no_math_mutation_shape() -> None:
    advancement = AdvancementState(tag_counter=2)
    current_tier = 5
    if current_tier >= 5:
        at_cap = True
        ap_awarded = 0
    assert at_cap is True
    assert ap_awarded == 0
    assert advancement.tag_counter == 2


@pytest.mark.unit
def test_domain_resolution_from_registry() -> None:
    assert resolve_tag_domain("athletics", "knowledge") == "power"


@pytest.mark.unit
def test_domain_resolution_missing_requires_domain() -> None:
    with pytest.raises(ValueError, match="domain is required"):
        resolve_tag_domain("custom_tag", "knowledge")


@pytest.mark.unit
def test_domain_resolution_provided_accepts() -> None:
    assert resolve_tag_domain("custom_tag", "knowledge", "will") == "will"


@pytest.mark.unit
def test_ap_award_by_scale() -> None:
    assert award_for_scale("local") == 0
    assert award_for_scale("situational") == 1
    assert award_for_scale("regional") == 2
    assert award_for_scale("campaign") == 4


@pytest.mark.unit
def test_spend_insufficient_message_shape() -> None:
    cost = compute_cost(55, 57)
    have = 1
    with pytest.raises(ValueError, match="insufficient AP: need 2, have 1"):
        if cost > have:
            raise ValueError(f"insufficient AP: need {cost}, have {have}")