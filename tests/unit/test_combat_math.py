import pytest

from api.game_data import compute_max_hp, get_armor, get_shield, resolve_attack


class FakeDice:
    def __init__(self, *values: int):
        self.values = list(values)

    def __call__(self, _expr: str) -> int:
        if not self.values:
            raise AssertionError("FakeDice exhausted")
        return self.values.pop(0)


@pytest.mark.unit
def test_compute_max_hp_heavy_armor_floor_and_ceiling() -> None:
    armor = get_armor("armor_plate_01")

    assert compute_max_hp(armor, 0, None, 0) == {
        "max_hp": 120,
        "base": 100,
        "armor_contribution": 20,
        "shield_contribution": 0,
    }
    assert compute_max_hp(armor, 5, None, 0) == {
        "max_hp": 200,
        "base": 100,
        "armor_contribution": 100,
        "shield_contribution": 0,
    }


@pytest.mark.unit
def test_compute_max_hp_unarmored_and_shield_stack() -> None:
    unarmored = get_armor("armor_unarmored_01")
    shield = get_shield("shield_01")

    assert compute_max_hp(unarmored, 0, None, 0) == {
        "max_hp": 100,
        "base": 100,
        "armor_contribution": 0,
        "shield_contribution": 0,
    }
    assert compute_max_hp(unarmored, 5, None, 0) == {
        "max_hp": 100,
        "base": 100,
        "armor_contribution": 0,
        "shield_contribution": 0,
    }
    assert compute_max_hp(unarmored, 0, shield, 0) == {
        "max_hp": 105,
        "base": 100,
        "armor_contribution": 0,
        "shield_contribution": 5,
    }
    assert compute_max_hp(get_armor("armor_plate_01"), 3, shield, 2) == {
        "max_hp": 183,
        "base": 100,
        "armor_contribution": 68,
        "shield_contribution": 15,
    }


@pytest.mark.unit
def test_resolve_attack_critical_hit_path_applies_ammo_then_agility() -> None:
    result = resolve_attack(
        weapon_id="weapon_sword_01",
        weapon_tier=3,
        ammo_id="ammo_arrows_broadhead_01",
        defender_is_unarmored=False,
        defender_agility_tier=2,
        dice=FakeDice(1),
    )

    assert result["critical_hit"] is True
    assert result["hit"] is True
    assert result["roll_2"] is None
    assert result["rebound"] is None
    assert result["damage"]["weapon_base"] == 15
    assert result["damage"]["effective_base"] == 15
    assert result["damage"]["ammo_modifier"] == 5
    assert result["damage"]["margin_multiplier"] == 3.0
    assert result["damage"]["pre_reduction"] == 50
    assert result["damage"]["final"] == 40


@pytest.mark.unit
def test_resolve_attack_fumble_path_has_rebound_only() -> None:
    result = resolve_attack(
        weapon_id="weapon_sword_01",
        weapon_tier=2,
        defender_is_unarmored=False,
        dice=FakeDice(100, 6),
    )

    assert result["hit"] is False
    assert result["fumble"] is True
    assert result["critical_hit"] is False
    assert result["roll_2"] is None
    assert result["rebound"] == {"attacker_damage": 10}
    assert result["damage"]["final"] == 0


@pytest.mark.unit
def test_resolve_attack_miss_path_does_not_roll_second_stage() -> None:
    result = resolve_attack(
        weapon_id="weapon_sword_01",
        weapon_tier=0,
        defender_is_unarmored=False,
        dice=FakeDice(90),
    )

    assert result["hit"] is False
    assert result["roll_2"] is None
    assert result["damage"]["final"] == 0
    assert result["events"] == ["roll_1", "miss"]


@pytest.mark.unit
def test_resolve_attack_hit_path_computes_damage_formula() -> None:
    result = resolve_attack(
        weapon_id="weapon_sword_01",
        weapon_tier=3,
        ammo_id="ammo_arrows_broadhead_01",
        defender_is_unarmored=False,
        defender_agility_tier=1,
        dice=FakeDice(50, 80, 30),
    )

    assert result["roll_2"] == {"attacker": 80, "defender": 30, "margin": 50}
    assert result["damage"]["margin_multiplier"] == 1.5
    assert result["damage"]["pre_reduction"] == 27
    assert result["damage"]["final"] == 24
    assert result["hit"] is True


@pytest.mark.unit
def test_resolve_attack_tie_path_zeroes_damage() -> None:
    result = resolve_attack(
        weapon_id="weapon_sword_01",
        weapon_tier=3,
        defender_is_unarmored=False,
        dice=FakeDice(40, 55, 55),
    )

    assert result["tied"] is True
    assert result["hit"] is False
    assert result["damage"]["final"] == 0
    assert result["events"] == ["roll_1", "hit", "roll_2", "tied"]


@pytest.mark.unit
def test_resolve_attack_unarmored_threshold_reduction_and_clamp() -> None:
    reduced = resolve_attack(
        weapon_id="weapon_sword_01",
        weapon_tier=1,
        defender_is_unarmored=True,
        defender_unarmored_tier=5,
        dice=FakeDice(31),
    )
    assert reduced["roll_1"]["base_target"] == 55
    assert reduced["roll_1"]["target"] == 30
    assert reduced["hit"] is False

    lowest_valid = resolve_attack(
        weapon_id="weapon_sword_01",
        weapon_tier=0,
        defender_is_unarmored=True,
        defender_unarmored_tier=5,
        dice=FakeDice(21),
    )
    assert lowest_valid["roll_1"]["target"] == 20
    assert lowest_valid["hit"] is False


@pytest.mark.unit
def test_resolve_attack_off_hand_halves_effective_base() -> None:
    result = resolve_attack(
        weapon_id="weapon_greatsword_01",
        weapon_tier=3,
        use_off_hand=True,
        defender_is_unarmored=False,
        dice=FakeDice(40, 90, 10),
    )

    assert result["damage"]["weapon_base"] == 25
    assert result["damage"]["effective_base"] == 12


@pytest.mark.unit
def test_resolve_attack_negative_margin_reduces_damage_and_minus_100_floors_to_zero() -> None:
    reduced = resolve_attack(
        weapon_id="weapon_sword_01",
        weapon_tier=3,
        defender_is_unarmored=False,
        dice=FakeDice(40, 20, 80),
    )
    assert reduced["roll_2"]["margin"] == -60
    assert reduced["damage"]["pre_reduction"] == 6
    assert reduced["damage"]["final"] == 6
    assert reduced["hit"] is True

    floored = resolve_attack(
        weapon_id="weapon_sword_01",
        weapon_tier=3,
        defender_is_unarmored=False,
        dice=FakeDice(40, 1, 100),
    )
    assert floored["roll_2"]["margin"] == -99
    assert floored["damage"]["final"] == 0
    assert floored["hit"] is False
