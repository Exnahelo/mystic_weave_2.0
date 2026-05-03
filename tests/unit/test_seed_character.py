import pytest

from api.game_data import seed_character
from tests.helpers import zero_advancement


@pytest.mark.unit
def test_seed_character_applies_adjustments_and_tags() -> None:
    character = seed_character(
        name="Krath",
        ancestry_index="drakari",
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
    assert character["knowledge"]["discipline"]["tier"] == 2
    # Drakari ancestry no longer grants application tags via traits
    # (Magical Inheritance is a creation-time choice, not a fixed grant)
    assert "application" not in character
    for group in character["knowledge"].values():
        assert "dragon_breath" not in group["applications"]


@pytest.mark.unit
def test_seed_character_populates_stacked_fields() -> None:
    character = seed_character(
        name="Krath",
        ancestry_index="drakari",
        culture_index="draconic_grasslands",
        focus_index="devoted",
        background_index="acolyte",
    )

    assert character["magic"]["sacred"]["tier"] == 3
    assert character["magic"]["sacred"]["spells"] == {}
    assert "fields" not in character


@pytest.mark.unit
def test_seed_character_applies_culture_domain_bonuses() -> None:
    character = seed_character(
        name="Krath",
        ancestry_index="drakari",
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
    assert set(character["advancement"]) == {
        "points_available",
        "points_spent",
        "points_earned_total",
        "tag_counter",
    }


@pytest.mark.unit
def test_seed_character_produces_nested_knowledge() -> None:
    """v5 shape: knowledge is dict[group, {tier, applications}]; no flat application/fields."""
    from api.models import CharacterModel

    character = seed_character(
        name="Sylvara",
        ancestry_index="drakari",
        culture_index="drakenvale_city",
        focus_index="stalker",
        background_index="outlander",
    )

    assert "application" not in character
    assert "fields" not in character
    assert isinstance(character["knowledge"], dict)
    assert isinstance(character["magic"], dict)

    for group_name, group_block in character["knowledge"].items():
        assert isinstance(group_block, dict)
        assert "tier" in group_block
        assert "applications" in group_block
        for app_tier in group_block["applications"].values():
            assert app_tier <= group_block["tier"], (
                f"application under {group_name} exceeds parent tier"
            )

    # Round-trips through CharacterModel — proves the seeded shape is valid v5.
    CharacterModel.model_validate(character)


@pytest.mark.unit
def test_seed_character_bumps_parent_tier_when_application_exceeds() -> None:
    """When stacked application tier exceeds the stacked parent group tier,
    the seeder bumps the parent up to the application's tier.

    Regression: elf/feywood_wilds/warden/outlander stacks ecology to T3 across
    three layers, but only one layer grants nature (T1, stacking to T2). Brief
    13's structural parent-cap rejected the result with a 500. Brief 15 fixes
    the seeder.
    """
    from api.models import CharacterModel

    character = seed_character(
        name="Sylvara",
        ancestry_index="elf",
        culture_index="feywood_wilds",
        focus_index="warden",
        background_index="outlander",
    )

    assert character["knowledge"]["nature"]["applications"]["ecology"] == 3
    assert character["knowledge"]["nature"]["tier"] >= 3

    # Whole record validates under v5 parent-cap.
    CharacterModel.model_validate(character)
