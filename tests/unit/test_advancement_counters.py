import pytest

from api.routes.state import _apply_tag_advancement_counters
from tests.helpers import zero_advancement


def _character() -> dict:
    return {
        "knowledge": {},
        "magic": {},
        "advancement": zero_advancement(),
    }


def _know(group: str, tier: int, applications: dict[str, int] | None = None) -> dict:
    return {group: {"tier": tier, "applications": applications or {}}}


@pytest.mark.unit
def test_counter_starts_at_zero() -> None:
    assert _character()["advancement"]["tag_counter"] == 0


@pytest.mark.unit
def test_single_tag_advance_increments_counter_only() -> None:
    updated = _apply_tag_advancement_counters(
        _character(),
        {"knowledge": _know("athletics", 1)},
    )

    assert updated["tag_counter"] == 1
    assert updated["points_available"] == 0
    assert updated["points_earned_total"] == 0


@pytest.mark.unit
def test_two_advances_in_same_save_no_ap() -> None:
    updated = _apply_tag_advancement_counters(
        _character(),
        {
            "knowledge": {
                **_know("athletics", 1),
                **_know("awareness", 1),
            }
        },
    )

    assert updated["tag_counter"] == 2
    assert updated["points_available"] == 0
    assert updated["points_earned_total"] == 0


@pytest.mark.unit
def test_three_advances_roll_over_to_one_ap() -> None:
    updated = _apply_tag_advancement_counters(
        _character(),
        {
            "knowledge": {
                **_know("athletics", 1),
                **_know("awareness", 1),
                **_know("survival", 1),
            }
        },
    )

    assert updated["tag_counter"] == 0
    assert updated["points_available"] == 1
    assert updated["points_earned_total"] == 1


@pytest.mark.unit
def test_six_advances_roll_over_to_two_ap() -> None:
    """Three group-tier advances + three application advances under the same parents."""
    updated = _apply_tag_advancement_counters(
        _character(),
        {
            "knowledge": {
                "athletics": {"tier": 1, "applications": {"hauling": 1, "climbing": 1}},
                "awareness": {"tier": 1, "applications": {}},
                "survival": {"tier": 1, "applications": {"swimming": 1}},
            },
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
            "knowledge": {
                "athletics": {"tier": 1, "applications": {"hauling": 1, "climbing": 1}},
                "awareness": {"tier": 1, "applications": {}},
                "survival": {"tier": 1, "applications": {"swimming": 1}},
            },
            "magic": {"sacred": {"tier": 1, "spells": {}}},
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
        {"knowledge": _know("athletics", 1)},
    )
    character["knowledge"] = _know("athletics", 1)
    character["advancement"] = updated

    updated = _apply_tag_advancement_counters(
        character,
        {
            "knowledge": {
                **_know("awareness", 1),
                **_know("survival", 1),
            }
        },
    )

    assert updated["tag_counter"] == 0
    assert updated["points_available"] == 1
    assert updated["points_earned_total"] == 1


@pytest.mark.unit
def test_noop_or_decrease_does_not_move_counters() -> None:
    character = _character()
    character["knowledge"] = _know("athletics", 2)

    same = _apply_tag_advancement_counters(character, {"knowledge": _know("athletics", 2)})
    lower = _apply_tag_advancement_counters(character, {"knowledge": _know("athletics", 1)})

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

    updated = _apply_tag_advancement_counters(character, {"knowledge": _know("athletics", 1)})

    assert "points_available_earned" not in updated
    assert "points_available_awarded" not in updated
    assert "tag_advance_counters" not in updated


@pytest.mark.unit
def test_application_tier_advances_count_individually() -> None:
    """A group at tier 3 with three new applications at tier 1 = 3 advances total."""
    base = _character()
    base["knowledge"] = {"athletics": {"tier": 3, "applications": {}}}

    updated = _apply_tag_advancement_counters(
        base,
        {
            "knowledge": {
                "athletics": {
                    "tier": 3,
                    "applications": {"hauling": 1, "climbing": 1, "swimming": 1},
                }
            }
        },
    )

    assert updated["points_available"] == 1
    assert updated["points_earned_total"] == 1
    assert updated["tag_counter"] == 0


@pytest.mark.unit
def test_field_tier_advances_count() -> None:
    """A magic field tier-up counts as a tag advance."""
    base = _character()
    base["magic"] = {"sacred": {"tier": 1, "spells": {}}}

    updated = _apply_tag_advancement_counters(
        base,
        {"magic": {"sacred": {"tier": 2, "spells": {}}}},
    )

    assert updated["tag_counter"] == 1
    assert updated["points_available"] == 0
