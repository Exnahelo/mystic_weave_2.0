from api.items import Effect, Item
from scripts.validate_catalog import _infer_band_key, _validate_effect_params


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


def _item(modules: dict) -> Item:
    return Item(
        id="test-item",
        name="Test Item",
        description="A test item.",
        worldness={"pricing": {"model": "authored", "canonical_value_cp": 100}},
        modules=modules,
    )


def test_infer_band_key_longsword_like_item_returns_martial_weapon() -> None:
    item = _item(
        {
            "weapon": {
                "weapon_type": "longsword",
                "training": "martial",
                "hands": "one-or-two",
                "range": {"type": "melee", "normal_ft": 5},
                "damage": [{"dice": "1d8", "type": "slashing"}],
            }
        }
    )

    assert _infer_band_key(item) == "weapon.martial"


def test_infer_band_key_simple_weapon_returns_simple_weapon() -> None:
    item = _item(
        {
            "weapon": {
                "weapon_type": "club",
                "training": "simple",
                "hands": "one",
                "range": {"type": "melee", "normal_ft": 5},
                "damage": [{"dice": "1d4", "type": "bludgeoning"}],
            }
        }
    )

    assert _infer_band_key(item) == "weapon.simple"


def test_infer_band_key_flame_tongue_like_item_skips_attunement() -> None:
    item = _item(
        {
            "weapon": {
                "weapon_type": "longsword",
                "training": "martial",
                "hands": "one-or-two",
                "range": {"type": "melee", "normal_ft": 5},
                "damage": [{"dice": "1d8", "type": "slashing"}],
            },
            "attunement": {"required": True},
        }
    )

    assert _infer_band_key(item) is None


def test_infer_band_key_magical_effect_skips_band() -> None:
    item = _item(
        {
            "weapon": {
                "weapon_type": "longsword",
                "training": "martial",
                "hands": "one-or-two",
                "range": {"type": "melee", "normal_ft": 5},
                "damage": [{"dice": "1d8", "type": "slashing"}],
            },
            "effects": [
                {
                    "id": "attack-bonus-flat",
                    "source": "magical",
                    "params": {"value": 1},
                }
            ],
        }
    )

    assert _infer_band_key(item) is None


def test_infer_band_key_activation_skips_band() -> None:
    item = _item(
        {
            "weapon": {
                "weapon_type": "longsword",
                "training": "martial",
                "hands": "one-or-two",
                "range": {"type": "melee", "normal_ft": 5},
                "damage": [{"dice": "1d8", "type": "slashing"}],
            },
            "activation": {"type": "bonus-action"},
        }
    )

    assert _infer_band_key(item) is None


def test_infer_band_key_no_recognized_module_returns_none() -> None:
    item = _item({})

    assert _infer_band_key(item) is None