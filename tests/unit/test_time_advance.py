import pytest
from pydantic import ValidationError

from api.models import TimeElapsed, TimeState, WeatherState
from api.time_advance import advance_time


def time_state(**overrides) -> TimeState:
    payload = {
        "day": 1,
        "month": "Verdantrise",
        "year": 847,
        "time_of_day": "dawn",
        "season": "spring",
        "festival": None,
        "weather": "clear",
        "weather_note": "bright and cold",
    }
    payload.update(overrides)
    return TimeState.model_validate(payload)


def assert_time(
    actual: TimeState,
    *,
    day: int,
    month: str,
    year: int,
    time_of_day: str,
    season: str,
    festival: str | None = None,
) -> None:
    assert actual.day == day
    assert actual.month == month
    assert actual.year == year
    assert actual.time_of_day == time_of_day
    assert actual.season == season
    assert actual.festival == festival


def test_noop_is_identical_state() -> None:
    current = time_state(day=2, time_of_day="afternoon", weather="mist", weather_note="low fog")

    advanced = advance_time(current, TimeElapsed())

    assert advanced == current


def test_weather_and_weather_note_preserved_across_advance() -> None:
    current = time_state(weather=WeatherState.storm, weather_note="thunder over the ridge")

    advanced = advance_time(current, TimeElapsed(days=3, steps=2))

    assert advanced.weather == WeatherState.storm
    assert advanced.weather_note == "thunder over the ridge"


@pytest.mark.parametrize(
    ("start_band", "steps", "expected_band", "expected_day"),
    [
        ("dawn", 1, "morning", 2),
        ("midday", 2, "dusk", 2),
        ("night", 1, "dawn", 3),
        ("dawn", 5, "night", 2),
        ("night", 2, "morning", 3),
        ("dusk", 6, "dusk", 3),
        ("dawn", 12, "dawn", 4),
    ],
)
def test_step_advances(start_band: str, steps: int, expected_band: str, expected_day: int) -> None:
    advanced = advance_time(time_state(day=2, time_of_day=start_band), TimeElapsed(steps=steps))

    assert_time(
        advanced,
        day=expected_day,
        month="Verdantrise",
        year=847,
        time_of_day=expected_band,
        season="spring",
    )


@pytest.mark.parametrize(
    ("current", "elapsed", "expected"),
    [
        (
            time_state(day=10, month="Verdantrise", time_of_day="midday"),
            TimeElapsed(days=1),
            {"day": 11, "month": "Verdantrise", "year": 847, "time_of_day": "midday", "season": "spring"},
        ),
        (
            time_state(day=10, month="Verdantrise", time_of_day="afternoon"),
            TimeElapsed(),
            {"day": 10, "month": "Verdantrise", "year": 847, "time_of_day": "afternoon", "season": "spring"},
        ),
        (
            time_state(day=28, month="Verdantrise", time_of_day="afternoon"),
            TimeElapsed(days=7),
            {"day": 5, "month": "Clearwater", "year": 847, "time_of_day": "afternoon", "season": "spring"},
        ),
        (
            time_state(day=12, month="Verdantrise", time_of_day="midday"),
            TimeElapsed(days=30),
            {"day": 12, "month": "Clearwater", "year": 847, "time_of_day": "midday", "season": "spring"},
        ),
    ],
)
def test_day_advancement(current: TimeState, elapsed: TimeElapsed, expected: dict) -> None:
    assert_time(advance_time(current, elapsed), **expected)


@pytest.mark.parametrize(
    ("current", "elapsed", "expected"),
    [
        (
            time_state(day=28, month="Deepwarden", year=847, time_of_day="midday"),
            TimeElapsed(days=5),
            {"day": 3, "month": "Ashwake", "year": 848, "time_of_day": "midday", "season": "winter"},
        ),
        (
            time_state(day=30, month="Verdantrise", time_of_day="midday"),
            TimeElapsed(days=1),
            {"day": 1, "month": "Clearwater", "year": 847, "time_of_day": "midday", "season": "spring"},
        ),
        (
            time_state(day=30, month="Verdantrise", time_of_day="dusk"),
            TimeElapsed(steps=6),
            {"day": 1, "month": "Clearwater", "year": 847, "time_of_day": "dusk", "season": "spring"},
        ),
        (
            time_state(day=30, month="Deepwarden", year=847, time_of_day="midday"),
            TimeElapsed(days=1),
            {
                "day": 1,
                "month": "Ashwake",
                "year": 848,
                "time_of_day": "midday",
                "season": "winter",
                "festival": "New Year's Dawn",
            },
        ),
        (
            time_state(day=30, month="Deepwarden", year=847, time_of_day="night"),
            TimeElapsed(steps=1),
            {
                "day": 1,
                "month": "Ashwake",
                "year": 848,
                "time_of_day": "dawn",
                "season": "winter",
                "festival": "New Year's Dawn",
            },
        ),
    ],
)
def test_month_and_year_rollover(current: TimeState, elapsed: TimeElapsed, expected: dict) -> None:
    assert_time(advance_time(current, elapsed), **expected)


@pytest.mark.parametrize(
    ("current", "elapsed", "expected_festival"),
    [
        (time_state(day=29, month="Deepwarden"), TimeElapsed(days=1), "The Day of Founding"),
        (time_state(day=30, month="Deepwarden"), TimeElapsed(days=1), "New Year's Dawn"),
        (time_state(day=30, month="Mistbreak"), TimeElapsed(days=1), "The Verdant Gate"),
        (time_state(day=30, month="Goldmere"), TimeElapsed(days=1), "Highscale"),
        (time_state(day=30, month="Amberveil"), TimeElapsed(days=1), "Highharvestide"),
        (time_state(day=30, month="Ashenfall"), TimeElapsed(days=1), "The Day of Remembrance"),
    ],
)
def test_festival_detection(current: TimeState, elapsed: TimeElapsed, expected_festival: str) -> None:
    assert advance_time(current, elapsed).festival == expected_festival


@pytest.mark.parametrize(
    ("current", "elapsed"),
    [
        (time_state(day=1, month="Verdantrise", festival="The Verdant Gate"), TimeElapsed(days=1)),
        (time_state(day=1, month="Verdantrise"), TimeElapsed(days=1)),
    ],
)
def test_non_festival_days_have_no_festival(current: TimeState, elapsed: TimeElapsed) -> None:
    advanced = advance_time(current, elapsed)

    assert advanced.day == 2
    assert advanced.month == "Verdantrise"
    assert advanced.festival is None


@pytest.mark.parametrize(
    ("current", "expected_month", "expected_season"),
    [
        (time_state(day=30, month="Mistbreak", season="winter"), "Verdantrise", "spring"),
        (time_state(day=30, month="Goldmere", season="spring"), "Scaletide", "summer"),
        (time_state(day=30, month="Ashenfall", season="summer"), "Ironmoor", "autumn"),
        (time_state(day=30, month="Deepwarden", season="autumn"), "Ashwake", "winter"),
        (time_state(day=10, month="Clearwater", season="spring"), "Clearwater", "spring"),
    ],
)
def test_season_transitions(current: TimeState, expected_month: str, expected_season: str) -> None:
    advanced = advance_time(current, TimeElapsed(days=1))

    assert advanced.month == expected_month
    assert advanced.season == expected_season


@pytest.mark.parametrize(
    ("start_band", "expected_day"),
    [
        ("dawn", 2),
        ("morning", 2),
        ("midday", 2),
        ("afternoon", 2),
        ("dusk", 2),
        ("night", 2),
    ],
)
def test_until_dawn_semantics(start_band: str, expected_day: int) -> None:
    advanced = advance_time(time_state(time_of_day=start_band), TimeElapsed(until="dawn"))

    assert_time(
        advanced,
        day=expected_day,
        month="Verdantrise",
        year=847,
        time_of_day="dawn",
        season="spring",
    )


def test_until_dawn_crosses_month_boundary() -> None:
    advanced = advance_time(
        time_state(day=30, month="Verdantrise", time_of_day="night"),
        TimeElapsed(until="dawn"),
    )

    assert_time(advanced, day=1, month="Clearwater", year=847, time_of_day="dawn", season="spring")


def test_until_dawn_crosses_year_boundary() -> None:
    advanced = advance_time(
        time_state(day=30, month="Deepwarden", year=847, time_of_day="night"),
        TimeElapsed(until="dawn"),
    )

    assert_time(
        advanced,
        day=1,
        month="Ashwake",
        year=848,
        time_of_day="dawn",
        season="winter",
        festival="New Year's Dawn",
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"steps": 1, "until": "dawn"},
        {"days": 1, "until": "dawn"},
        {"steps": 13},
        {"days": 31},
        {"steps": -1},
        {"days": -1},
        {"until": "dusk"},
    ],
)
def test_time_elapsed_validation_rejection(payload: dict) -> None:
    with pytest.raises(ValidationError):
        TimeElapsed(**payload)


def test_multiple_month_advance_edge_case() -> None:
    advanced = advance_time(
        time_state(day=15, month="Mistbreak", season="winter"),
        TimeElapsed(days=30),
    )

    assert_time(advanced, day=15, month="Verdantrise", year=847, time_of_day="dawn", season="spring")


def test_two_day_advance_via_steps_only_edge_case() -> None:
    advanced = advance_time(time_state(time_of_day="dawn"), TimeElapsed(steps=12))

    assert_time(advanced, day=3, month="Verdantrise", year=847, time_of_day="dawn", season="spring")