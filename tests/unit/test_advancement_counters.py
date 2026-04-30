import pytest

from api.routes.state import _apply_tag_advancement_counters
from tests.helpers import zero_advancement


def _character() -> dict:
    return {
        "knowledge": {},
        "application": {},
        "fields": {},
        "advancement": zero_advancement(),
    }


@pytest.mark.unit
def test_counter_starts_at_zero() -> None:
    assert _character()["advancement"]["tag_counter"] == 0


@pytest.mark.unit
def test_single_tag_advance_increments_counter_only() -> None:
    updated = _apply_tag_advancement_counters(
        _character(),
        {"knowledge": {"athletics": 1}},
    )

    assert updated["tag_counter"] == 1
    assert updated["points_available"] == 0
    assert updated["points_earned_total"] == 0


@pytest.mark.unit
def test_two_advances_in_same_save_no_ap() -> None:
    updated = _apply_tag_advancement_counters(
        _character(),
        {"knowledge": {"athletics": 1, "awareness": 1}},
    )

    assert updated["tag_counter"] == 2
    assert updated["points_available"] == 0
    assert updated["points_earned_total"] == 0


@pytest.mark.unit
def test_three_advances_roll_over_to_one_ap() -> None:
    updated = _apply_tag_advancement_counters(
        _character(),
        {"knowledge": {"athletics": 1, "awareness": 1, "survival": 1}},
    )

    assert updated["tag_counter"] == 0
    assert updated["points_available"] == 1
    assert updated["points_earned_total"] == 1


@pytest.mark.unit
def test_six_advances_roll_over_to_two_ap() -> None:
    updated = _apply_tag_advancement_counters(
        _character(),
        {
            "knowledge": {"athletics": 1, "awareness": 1, "survival": 1},
            "application": {"hauling": 1, "climbing": 1, "swimming": 1},
        },
    )

    assert updated["tag_counter"] == 0
    assert updated["points_available"] == 2
    assert updated["points_earned_total"] == 2


@pytest.mark.unit
def test_seven_advances_roll_over_to_two_ap_with_one_counter() -> None:
    updated = _apply_tag_advancement_counters(
        _character(),
        {
            "knowledge": {"athletics": 1, "awareness": 1, "survival": 1},
            "application": {"hauling": 1, "climbing": 1, "swimming": 1},
            "fields": {"sacred": 1},
        },
    )

    assert updated["tag_counter"] == 1
    assert updated["points_available"] == 2
    assert updated["points_earned_total"] == 2


@pytest.mark.unit
def test_counter_persists_across_saves() -> None:
    character = _character()

    updated = _apply_tag_advancement_counters(
        character,
        {"knowledge": {"athletics": 1}},
    )
    character["knowledge"] = {"athletics": 1}
    character["advancement"] = updated

    updated = _apply_tag_advancement_counters(
        character,
        {"knowledge": {"awareness": 1, "survival": 1}},
    )

    assert updated["tag_counter"] == 0
    assert updated["points_available"] == 1
    assert updated["points_earned_total"] == 1


@pytest.mark.unit
def test_noop_or_decrease_does_not_move_counters() -> None:
    character = _character()
    character["knowledge"] = {"athletics": 2}

    same = _apply_tag_advancement_counters(character, {"knowledge": {"athletics": 2}})
    lower = _apply_tag_advancement_counters(character, {"knowledge": {"athletics": 1}})

    assert same == zero_advancement()
    assert lower == zero_advancement()


@pytest.mark.unit
def test_strips_legacy_advancement_fields() -> None:
    character = _character()
    character["advancement"] = {
        **zero_advancement(),
        "points_available_earned": {"power": 1},
        "points_available_awarded": 2,
        "tag_advance_counters": {"power": 1},
    }

    updated = _apply_tag_advancement_counters(character, {"knowledge": {"athletics": 1}})

    assert "points_available_earned" not in updated
    assert "points_available_awarded" not in updated
    assert "tag_advance_counters" not in updated