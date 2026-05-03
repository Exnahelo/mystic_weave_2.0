import pytest

from scripts.migrate_character_v4 import (
    DEFAULT_CULTURE,
    get_database_url,
    migrate_character_document,
    migrate_character_payload,
)
from tests.helpers import zero_advancement


@pytest.mark.unit
def test_migrate_character_payload_renames_species_and_removes_legacy_keys() -> None:
    payload = {
        "name": "Krath",
        'species': "drakari",
        "focus": "devoted",
        "background": "acolyte",
        "hp": {"current": 100, "max": 100},
        "domains": {
            "power": 45,
            "agility": 35,
            "perception": 35,
            "endurance": 40,
            "intellect": 30,
            "will": 45,
            "presence": 50,
        },
        "knowledge": {"discipline": 2},
        "application": {"sacred_rites": 1},
        "status_effects": [],
        "notes": "",
        "identity": {},
        "equipment": {"worn": [], "carried": [], "stashed": []},
        "reputation": [],
        "advancement": zero_advancement(),
        "magic_fields": ["sacred", "warding"],
        "draconic_traits": ["dragon_breath"],
        "level": 1,
        "species_traits": ["legacy"],
    }

    migrated, changed, used_default = migrate_character_payload(payload)

    assert changed is True
    assert used_default is True
    assert migrated["ancestry"] == "drakari"
    assert migrated["culture"] == DEFAULT_CULTURE
    assert migrated["fields"] == {"sacred": 1, "warding": 1}
    assert 'species' not in migrated
    assert "magic_fields" not in migrated
    assert "draconic_traits" not in migrated
    assert "level" not in migrated
    assert "species_traits" not in migrated


@pytest.mark.unit
def test_migrate_character_payload_preserves_existing_culture_and_fields() -> None:
    payload = {
        "name": "T",
        "ancestry": "human",
        "culture": "drakenvale_city",
        "focus": "speaker",
        "background": "noble",
        "hp": {"current": 100, "max": 100},
        "domains": {
            "power": 40,
            "agility": 40,
            "perception": 40,
            "endurance": 40,
            "intellect": 47,
            "will": 46,
            "presence": 47,
        },
        "knowledge": {"persuasion": 2},
        "application": {"musical_instruments": 1},
        "fields": {"illusion": 1},
        "status_effects": [],
        "notes": "",
        "identity": {},
        "equipment": {"worn": [], "carried": [], "stashed": []},
        "reputation": [],
        "advancement": zero_advancement(),
    }

    migrated, changed, used_default = migrate_character_payload(payload)

    assert changed is False
    assert used_default is False
    assert migrated == payload


@pytest.mark.unit
def test_migrate_character_document_validates_output() -> None:
    payload = {
        "name": "Krath",
        'species': "drakari",
        "focus": "devoted",
        "background": "acolyte",
        "hp": {"current": 100, "max": 100},
        "domains": {
            "power": 45,
            "agility": 35,
            "perception": 35,
            "endurance": 40,
            "intellect": 30,
            "will": 45,
            "presence": 50,
        },
        "knowledge": {"athletics": 2},
        "application": {"hauling": 1},
        "status_effects": [],
        "notes": "",
        "identity": {},
        "equipment": {"worn": [], "carried": [], "stashed": []},
        "reputation": [],
        "advancement": zero_advancement(),
    }

    migrated, changed, used_default, validated = migrate_character_document(payload)

    assert changed is True
    assert used_default is True
    assert validated.ancestry == "drakari"
    assert validated.culture == DEFAULT_CULTURE
    assert migrated["ancestry"] == validated.ancestry
    # Document migration chains through the v5 transform; flat shape is gone.
    assert "application" not in migrated
    assert "fields" not in migrated
    assert validated.knowledge["athletics"].tier == 2
    assert validated.knowledge["athletics"].applications["hauling"] == 1


@pytest.mark.unit
def test_get_database_url_exits_cleanly_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(SystemExit, match=r"DATABASE_URL environment variable not set\."):
        get_database_url()