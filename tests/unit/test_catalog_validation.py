from api.items import Effect
from scripts.validate_catalog import _validate_effect_params


EFFECT_CONTRACTS = {
    "light-emit": {
        "radius_bright_ft": {"type": "int", "required": True},
        "radius_dim_ft": {"type": "int", "required": True},
        "duration": {"type": "string", "required": False},
    },
    "attack-bonus-flat": {
        "value": {"type": "int", "required": True},
    },
    "damage-bonus-flat": {
        "value": {"type": "int", "required": True},
        "damage_type": {"type": "string", "required": False},
    },
    "damage-bonus-dice": {
        "dice": {"type": "string", "required": True},
        "damage_type": {"type": "string", "required": True},
    },
}

DAMAGE_TYPE_IDS = {"slashing", "fire"}


def test_valid_flame_tongue_longsword_shaped_effects_pass() -> None:
    effects = [
        Effect(
            id="attack-bonus-flat",
            source="magical",
            applies_to="weapon-attack",
            params={"value": 1},
        ),
        Effect(
            id="damage-bonus-flat",
            source="magical",
            applies_to="weapon-damage",
            params={"value": 1, "damage_type": "slashing"},
        ),
        Effect(
            id="damage-bonus-dice",
            source="magical",
            applies_to="weapon-damage",
            requires_activation=True,
            params={"dice": "2d6", "damage_type": "fire"},
        ),
        Effect(
            id="light-emit",
            source="magical",
            applies_to="scene",
            requires_activation=True,
            params={"radius_bright_ft": 40, "radius_dim_ft": 40},
        ),
    ]

    errors = [
        error
        for effect in effects
        for error in _validate_effect_params(
            "flame-tongue-longsword", effect, EFFECT_CONTRACTS, DAMAGE_TYPE_IDS
        )
    ]

    assert errors == []


def test_missing_required_param_fails() -> None:
    effect = Effect(
        id="light-emit",
        source="mundane",
        params={"radius_bright_ft": 20},
    )

    errors = _validate_effect_params(
        "torch", effect, EFFECT_CONTRACTS, DAMAGE_TYPE_IDS
    )

    assert "torch/light-emit: missing required param 'radius_dim_ft'" in errors


def test_unknown_param_fails() -> None:
    effect = Effect(
        id="attack-bonus-flat",
        source="magical",
        params={"value": 1, "bogus": 1},
    )

    errors = _validate_effect_params(
        "test-item", effect, EFFECT_CONTRACTS, DAMAGE_TYPE_IDS
    )

    assert "test-item/attack-bonus-flat: unknown param 'bogus'" in errors


def test_type_mismatch_fails() -> None:
    effect = Effect(
        id="attack-bonus-flat",
        source="magical",
        params={"value": "1"},
    )

    errors = _validate_effect_params(
        "test-item", effect, EFFECT_CONTRACTS, DAMAGE_TYPE_IDS
    )

    assert "test-item/attack-bonus-flat: param 'value' expected int, got str" in errors


def test_unknown_damage_type_fails() -> None:
    effect = Effect(
        id="damage-bonus-flat",
        source="magical",
        params={"value": 1, "damage_type": "void"},
    )

    errors = _validate_effect_params(
        "test-item", effect, EFFECT_CONTRACTS, DAMAGE_TYPE_IDS
    )

    assert "test-item/damage-bonus-flat: unknown damage_type 'void'" in errors