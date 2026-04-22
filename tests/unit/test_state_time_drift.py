import pytest

from api.models import TimeState
from api.routes.state import _detect_time_drift


TIME_DAY_1_MORNING = TimeState(
    day=1,
    month="Verdantrise",
    year=847,
    time_of_day="morning",
    season="spring",
    festival=None,
    weather="clear",
    weather_note="",
)
TIME_DAY_1_AFTERNOON = TimeState(
    day=1,
    month="Verdantrise",
    year=847,
    time_of_day="afternoon",
    season="spring",
    festival=None,
    weather="clear",
    weather_note="",
)
TIME_DAY_2_MORNING = TimeState(
    day=2,
    month="Verdantrise",
    year=847,
    time_of_day="morning",
    season="spring",
    festival=None,
    weather="clear",
    weather_note="",
)


@pytest.mark.unit
def test_no_drift_when_turn_unchanged() -> None:
    result = _detect_time_drift(
        previous_turn=5,
        previous_time=TIME_DAY_1_MORNING,
        current_turn=5,
        current_time=TIME_DAY_1_MORNING,
    )
    assert result is None


@pytest.mark.unit
def test_no_drift_when_time_advanced_with_turn() -> None:
    result = _detect_time_drift(
        previous_turn=5,
        previous_time=TIME_DAY_1_MORNING,
        current_turn=6,
        current_time=TIME_DAY_1_AFTERNOON,
    )
    assert result is None


@pytest.mark.unit
def test_no_drift_when_day_advanced() -> None:
    result = _detect_time_drift(
        previous_turn=5,
        previous_time=TIME_DAY_1_MORNING,
        current_turn=6,
        current_time=TIME_DAY_2_MORNING,
    )
    assert result is None


@pytest.mark.unit
def test_drift_when_turn_advances_but_time_identical() -> None:
    result = _detect_time_drift(
        previous_turn=5,
        previous_time=TIME_DAY_1_MORNING,
        current_turn=6,
        current_time=TIME_DAY_1_MORNING,
    )
    assert result is not None
    assert result.previous_turn == 5
    assert result.current_turn == 6
    assert "world.time did not change" in result.message


@pytest.mark.unit
def test_drift_across_many_turns() -> None:
    result = _detect_time_drift(
        previous_turn=109,
        previous_time=TIME_DAY_1_AFTERNOON,
        current_turn=110,
        current_time=TIME_DAY_1_AFTERNOON,
    )
    assert result is not None
    assert result.current_turn - result.previous_turn == 1