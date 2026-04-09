import pytest

from api.game_data import seed_character


@pytest.mark.unit
def test_seed_character_applies_adjustments_and_tags() -> None:
    character = seed_character(
        name="Krath",
        species_index="dragonborn",
        focus_index="devoted",
        background_index="soldier",
        adjustment_points={"will": 2, "endurance": 3},
    )

    assert character["name"] == "Krath"
    assert character["domains"]["will"] == 47
    assert character["domains"]["endurance"] == 43
    assert character["domains"]["presence"] == 55
    assert character["knowledge"]["discipline"] == 2


@pytest.mark.unit
def test_seed_character_rejects_adjustment_pool_over_5() -> None:
    with pytest.raises(ValueError, match="Adjustment pool"):
        seed_character(
            name="Bad",
            species_index="human",
            focus_index="champion",
            background_index="soldier",
            adjustment_points={"power": 3, "endurance": 3},
        )
