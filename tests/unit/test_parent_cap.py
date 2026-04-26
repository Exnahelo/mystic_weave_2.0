import pytest

from api.game_data import validate_application_parent_cap


@pytest.mark.unit
def test_application_advance_within_parent_cap_passes() -> None:
    validate_application_parent_cap(
        {"knowledge": {"athletics": 2}, "application": {"hauling": 1}},
        {"hauling": 2},
    )


@pytest.mark.unit
def test_application_advance_beyond_parent_raises() -> None:
    with pytest.raises(ValueError, match="cannot advance"):
        validate_application_parent_cap(
            {"knowledge": {"athletics": 1}, "application": {"hauling": 1}},
            {"hauling": 2},
        )


@pytest.mark.unit
def test_seeded_above_case_can_stay_put() -> None:
    validate_application_parent_cap(
        {"knowledge": {"athletics": 1}, "application": {"hauling": 2}},
        {"hauling": 2},
    )


@pytest.mark.unit
def test_seeded_above_case_cannot_advance_further() -> None:
    with pytest.raises(ValueError, match="seeded above"):
        validate_application_parent_cap(
            {"knowledge": {"athletics": 1}, "application": {"hauling": 2}},
            {"hauling": 3},
        )


@pytest.mark.unit
def test_unknown_application_is_skipped() -> None:
    validate_application_parent_cap(
        {"knowledge": {}, "application": {}},
        {"unknown_application": 3},
    )