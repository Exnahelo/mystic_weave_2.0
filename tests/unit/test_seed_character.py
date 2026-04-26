import pytest

from api.game_data import seed_character
from tests.helpers import zero_advancement


@pytest.mark.unit
def test_seed_character_applies_adjustments_and_tags() -> None:
    character = seed_character(
        name="Krath",
        ancestry_index="dragonborn",
        culture_index="draconic_grasslands",
        focus_index="devoted",
        background_index="soldier",
        adjustment_points={"will": 5, "endurance": 5},
    )

    assert character["name"] == "Krath"
    assert character["domains"]["intellect"] == 33
    assert character["domains"]["will"] == 56
    assert character["domains"]["endurance"] == 48
    assert character["domains"]["presence"] == 54
    assert character["knowledge"]["discipline"] == 2
    assert character["application"]["dragon_breath"] == 1


@pytest.mark.unit
def test_seed_character_populates_stacked_fields() -> None:
    character = seed_character(
        name="Krath",
        ancestry_index="dragonborn",
        culture_index="draconic_grasslands",
        focus_index="devoted",
        background_index="acolyte",
    )

    assert character["fields"]["sacred"] == 3


@pytest.mark.unit
def test_seed_character_applies_culture_domain_bonuses() -> None:
    character = seed_character(
        name="Krath",
        ancestry_index="dragonborn",
        culture_index="draconic_grasslands",
        focus_index="devoted",
        background_index="soldier",
    )

    assert character["domains"]["intellect"] == 33
    assert character["domains"]["presence"] == 54


@pytest.mark.unit
def test_seed_character_rejects_adjustment_pool_over_10() -> None:
    with pytest.raises(ValueError, match="Adjustment pool"):
        seed_character(
            name="Bad",
            ancestry_index="human",
            culture_index="drakenvale_city",
            focus_index="champion",
            background_index="soldier",
            adjustment_points={"power": 5, "endurance": 5, "will": 1},
        )


@pytest.mark.unit
def test_seed_character_rejects_adjustment_over_5_per_domain() -> None:
    with pytest.raises(ValueError, match=r"Max \+5 per domain"):
        seed_character(
            name="Bad",
            ancestry_index="human",
            culture_index="drakenvale_city",
            focus_index="champion",
            background_index="soldier",
            adjustment_points={"power": 6},
        )


@pytest.mark.unit
def test_seed_character_uses_new_advancement_shape() -> None:
    character = seed_character(
        name="Krath",
        ancestry_index="human",
        culture_index="drakenvale_city",
        focus_index="champion",
        background_index="soldier",
    )

    assert character["advancement"] == zero_advancement()
