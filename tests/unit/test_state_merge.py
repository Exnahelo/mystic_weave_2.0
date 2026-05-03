import pytest

from api.models import ApplyStateDeltaRequest, CharacterModel, WorldModel
from api.routes.state import _deep_merge, apply_delta


@pytest.mark.unit
def test_deep_merge_preserves_unsent_fields_and_recurses() -> None:
    base = {
        "hp": {"current": 90, "max": 100},
        "knowledge": {
            "discipline": {"tier": 2, "applications": {"focus": 1}},
            "courage": {"tier": 1, "applications": {}},
        },
        "notes": "existing",
    }
    incoming = {
        "hp": {"current": 80},
        "knowledge": {"discipline": {"tier": 3}},
    }

    merged = _deep_merge(base, incoming)

    assert merged["hp"]["current"] == 80
    assert merged["hp"]["max"] == 100
    assert merged["knowledge"]["discipline"]["tier"] == 3
    # Nested applications under discipline are preserved through partial update
    assert merged["knowledge"]["discipline"]["applications"] == {"focus": 1}
    assert merged["knowledge"]["courage"]["tier"] == 1
    assert merged["notes"] == "existing"


@pytest.mark.unit
def test_deep_merge_recurses_into_application_leaves() -> None:
    """Deep-merge updates a single nested application without replacing siblings."""
    base = {
        "knowledge": {
            "tracking": {
                "tier": 2,
                "applications": {"spoor_reading": 1, "quarry_habits": 2},
            }
        }
    }
    incoming = {"knowledge": {"tracking": {"applications": {"spoor_reading": 2}}}}
    merged = _deep_merge(base, incoming)
    assert merged["knowledge"]["tracking"]["tier"] == 2
    assert merged["knowledge"]["tracking"]["applications"] == {
        "spoor_reading": 2,
        "quarry_habits": 2,
    }


@pytest.mark.unit
def test_deep_merge_does_not_overwrite_with_none() -> None:
    base = {"goal": "survive"}
    incoming = {"goal": None}

    merged = _deep_merge(base, incoming)

    assert merged["goal"] == "survive"


def _current_state() -> dict:
    character = CharacterModel.model_validate(
        {
            "name": "Krath",
            "ancestry": "drakari",
            "culture": "draconic_grasslands",
            "focus": "devoted",
            "background": "soldier",
            "hp": {"current": 90, "max": 100},
            "domains": {
                "power": 40,
                "agility": 35,
                "perception": 30,
                "endurance": 42,
                "intellect": 25,
                "will": 38,
                "presence": 28,
            },
            "knowledge": {
                "discipline": {"tier": 2, "applications": {}},
                "martial_arts": {"tier": 2, "applications": {"melee": 2}},
            },
            "magic": {"sacred": {"tier": 1, "spells": {}}},
            "status_effects": ["bruised"],
            "notes": "existing",
            "equipment": {
                "worn": [{"id": "cloak", "name": "Cloak"}],
                "carried": [{"id": "rope", "name": "Rope"}],
                "stashed": [],
            },
            "reputation": [{"faction": "wardens", "standing": 10}],
        }
    )
    world = WorldModel.model_validate(
        {
            "location": "greymantle",
            "threat": "storm",
            "goal": "survive",
            "turn": 3,
        }
    )
    return {
        "character": character.model_dump_json(by_alias=True),
        "world": world.model_dump_json(),
    }


@pytest.mark.unit
def test_apply_delta_correctly_merges_character_fields() -> None:
    current = _current_state()
    delta = ApplyStateDeltaRequest.model_validate(
        {
            "character": {
                "hp": {"current": 75, "max": 100},
                "knowledge": {"discipline": {"tier": 3}},
            },
            "log_entry": "took a hit",
        }
    )
    applied = apply_delta(current, delta)
    assert applied["character"]["hp"]["current"] == 75
    assert applied["character"]["hp"]["max"] == 100
    assert applied["character"]["knowledge"]["discipline"]["tier"] == 3
    assert applied["character"]["notes"] == "existing"


@pytest.mark.unit
def test_apply_delta_correctly_merges_world_fields() -> None:
    current = _current_state()
    delta = ApplyStateDeltaRequest.model_validate(
        {
            "world": {"location": "rift-of-discord-edge", "turn": 4},
            "log_entry": "moved",
        }
    )
    applied = apply_delta(current, delta)
    assert applied["world"]["location"] == "rift-of-discord-edge"
    assert applied["world"]["turn"] == 4
    assert applied["world"]["goal"] == "survive"
    assert applied["world"]["pacing"]["turn_count"] == 4


@pytest.mark.unit
def test_apply_delta_merges_equipment_by_slot() -> None:
    current = _current_state()
    delta = ApplyStateDeltaRequest.model_validate(
        {
            "character": {
                "equipment": {
                    "carried": [{"id": "potion", "name": "Potion"}],
                }
            },
            "log_entry": "repacked gear",
        }
    )
    applied = apply_delta(current, delta)
    assert applied["character"]["equipment"]["worn"] == [{"id": "cloak", "name": "Cloak", "description": "", "tags": [], "roll_tag": None}]
    assert applied["character"]["equipment"]["carried"] == [{"id": "potion", "name": "Potion", "description": "", "tags": [], "roll_tag": None}]


@pytest.mark.unit
def test_apply_delta_final_state_conforms_to_existing_models() -> None:
    current = _current_state()
    delta = ApplyStateDeltaRequest.model_validate(
        {"character": {"notes": "updated"}, "world": {"turn": 5}, "log_entry": "summary"}
    )
    applied = apply_delta(current, delta)
    CharacterModel.model_validate(applied["character"])
    WorldModel.model_validate(applied["world"])
