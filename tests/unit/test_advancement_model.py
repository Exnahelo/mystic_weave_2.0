import pytest
from pydantic import ValidationError

from api.models import AdvancementState, DOMAIN_KEYS


@pytest.mark.unit
def test_advancement_state_defaults_all_domains_zero() -> None:
    advancement = AdvancementState()

    assert set(advancement.points_available_earned.keys()) == set(DOMAIN_KEYS)
    assert set(advancement.tag_advance_counters.keys()) == set(DOMAIN_KEYS)
    assert all(value == 0 for value in advancement.points_available_earned.values())
    assert all(value == 0 for value in advancement.tag_advance_counters.values())
    assert advancement.points_available_awarded == 0
    assert advancement.points_spent == 0
    assert advancement.points_earned_total == 0


@pytest.mark.unit
def test_advancement_state_rejects_negative_values() -> None:
    with pytest.raises(ValidationError):
        AdvancementState(points_available_awarded=-1)

    with pytest.raises(ValidationError):
        AdvancementState(points_available_earned={"power": -1})


@pytest.mark.unit
def test_advancement_state_rejects_unknown_domain() -> None:
    with pytest.raises(ValidationError, match="unknown domain"):
        AdvancementState(points_available_earned={"luck": 1})


@pytest.mark.unit
def test_advancement_state_backfills_missing_domains() -> None:
    advancement = AdvancementState(
        points_available_earned={"power": 2},
        tag_advance_counters={"will": 1},
    )

    assert advancement.points_available_earned["power"] == 2
    assert advancement.points_available_earned["agility"] == 0
    assert advancement.tag_advance_counters["will"] == 1
    assert advancement.tag_advance_counters["presence"] == 0