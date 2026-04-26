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
def test_single_tier_advance_increments_counter_only() -> None:
    updated = _apply_tag_advancement_counters(
        _character(),
        {"knowledge": {"athletics": 1}},
    )

    assert updated["tag_advance_counters"]["power"] == 1
    assert updated["points_available_earned"]["power"] == 0
    assert updated["points_earned_total"] == 0


@pytest.mark.unit
def test_three_advances_convert_to_one_earned_ap() -> None:
    character = _character()

    updated = _apply_tag_advancement_counters(
        character,
        {"knowledge": {"athletics": 1}},
    )
    character["knowledge"] = {"athletics": 1}
    character["advancement"] = updated

    updated = _apply_tag_advancement_counters(
        character,
        {"knowledge": {"athletics": 2}},
    )
    character["knowledge"] = {"athletics": 2}
    character["advancement"] = updated

    updated = _apply_tag_advancement_counters(
        character,
        {"knowledge": {"athletics": 3}},
    )

    assert updated["tag_advance_counters"]["power"] == 0
    assert updated["points_available_earned"]["power"] == 1
    assert updated["points_earned_total"] == 1


@pytest.mark.unit
def test_multi_step_advance_increments_by_step_count() -> None:
    character = _character()
    character["knowledge"] = {"athletics": 1}

    updated = _apply_tag_advancement_counters(
        character,
        {"knowledge": {"athletics": 3}},
    )

    assert updated["tag_advance_counters"]["power"] == 2
    assert updated["points_available_earned"]["power"] == 0


@pytest.mark.unit
def test_multi_step_crossing_threshold_carries_remainder() -> None:
    character = _character()
    character["knowledge"] = {"athletics": 1}
    character["advancement"]["tag_advance_counters"]["power"] = 2

    updated = _apply_tag_advancement_counters(
        character,
        {"knowledge": {"athletics": 3}},
    )

    assert updated["tag_advance_counters"]["power"] == 1
    assert updated["points_available_earned"]["power"] == 1
    assert updated["points_earned_total"] == 1


@pytest.mark.unit
def test_cross_domain_advances_increment_independently() -> None:
    updated = _apply_tag_advancement_counters(
        _character(),
        {"knowledge": {"athletics": 1, "awareness": 1}},
    )

    assert updated["tag_advance_counters"]["power"] == 1
    assert updated["tag_advance_counters"]["perception"] == 1


@pytest.mark.unit
def test_missing_primary_domain_lookup_is_skipped() -> None:
    updated = _apply_tag_advancement_counters(
        _character(),
        {"knowledge": {"unknown_tag": 1}},
    )

    assert updated == zero_advancement()


@pytest.mark.unit
def test_noop_or_decrease_does_not_move_counters() -> None:
    character = _character()
    character["knowledge"] = {"athletics": 2}

    same = _apply_tag_advancement_counters(character, {"knowledge": {"athletics": 2}})
    lower = _apply_tag_advancement_counters(character, {"knowledge": {"athletics": 1}})

    assert same == zero_advancement()
    assert lower == zero_advancement()