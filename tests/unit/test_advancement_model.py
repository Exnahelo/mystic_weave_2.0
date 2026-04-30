import pytest
from pydantic import ValidationError

from api.models import AdvancementState


@pytest.mark.unit
def test_advancement_state_defaults_zero() -> None:
    advancement = AdvancementState()

    assert advancement.points_available == 0
    assert advancement.points_spent == 0
    assert advancement.points_earned_total == 0
    assert advancement.tag_counter == 0


@pytest.mark.unit
def test_advancement_state_rejects_negative_values() -> None:
    with pytest.raises(ValidationError):
        AdvancementState(points_available=-1)

    with pytest.raises(ValidationError):
        AdvancementState(points_spent=-1)


@pytest.mark.unit
def test_advancement_state_rejects_negative_total() -> None:
    with pytest.raises(ValidationError):
        AdvancementState(points_earned_total=-1)


@pytest.mark.unit
def test_advancement_state_rejects_counter_outside_rollover_range() -> None:
    with pytest.raises(ValidationError):
        AdvancementState(tag_counter=3)