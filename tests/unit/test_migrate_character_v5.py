"""Tests for the v4→v5 character migration (Brief 13)."""
from __future__ import annotations

import pytest

from scripts.migrate_character_v5 import (
    migrate_character_document,
    migrate_character_v4_to_v5,
)
from tests.helpers import zero_advancement


def _v4_character() -> dict:
    """A canonical v4-shaped character payload."""
    return {
        "name": "Krath",
        "ancestry": "human",
        "culture": "drakenvale_city",
        "focus": "devoted",
        "background": "soldier",
        "hp": {"current": 100, "max": 100},
        "domains": {
            "power": 45,
            "agility": 35,
            "perception": 35,
            "endurance": 43,
            "intellect": 25,
            "will": 47,
            "presence": 55,
        },
        "knowledge": {"athletics": 2},
        "application": {"hauling": 1, "acrobatics": 1},
        "fields": {"sacred": 1, "warding": 1},
        "status_effects": [],
        "notes": "",
        "identity": {
            "origin": "",
            "motivations": [],
            "quirks": [],
            "bonds": [],
            "flaws": [],
            "wound": "",
            "alignment": {"order": "neutral", "intent": "neutral", "ethos_note": ""},
        },
        "equipment": {"worn": [], "carried": [], "stashed": []},
        "reputation": [],
        "advancement": zero_advancement(),
    }


@pytest.mark.unit
def test_migrate_v4_to_v5_basic_shape() -> None:
    migrated = migrate_character_v4_to_v5(_v4_character())

    assert "application" not in migrated
    assert "fields" not in migrated
    assert isinstance(migrated["knowledge"], dict)
    assert isinstance(migrated["magic"], dict)

    athletics = migrated["knowledge"]["athletics"]
    assert athletics["tier"] == 2
    assert "hauling" in athletics["applications"]
    assert athletics["applications"]["hauling"] == 1


@pytest.mark.unit
def test_migrate_v4_to_v5_places_applications_under_parent_groups() -> None:
    migrated = migrate_character_v4_to_v5(_v4_character())

    # 'acrobatics' lives under 'mobility' per applications.json — the v4
    # record granted it without an explicit mobility group, so the migration
    # auto-adds the parent at the application's tier.
    assert "mobility" in migrated["knowledge"]
    assert "acrobatics" in migrated["knowledge"]["mobility"]["applications"]
    assert migrated["knowledge"]["mobility"]["applications"]["acrobatics"] == 1


@pytest.mark.unit
def test_migrate_v4_to_v5_auto_adds_orphan_parent_group() -> None:
    """An application whose parent group isn't explicitly granted gets auto-parent."""
    payload = _v4_character()
    payload["knowledge"] = {}  # no explicit groups
    migrated = migrate_character_v4_to_v5(payload)

    # Each application's parent group must now appear in knowledge at app's tier.
    parent_groups = set(migrated["knowledge"].keys())
    assert parent_groups, "auto-added parent groups should populate knowledge"
    for group_block in migrated["knowledge"].values():
        for app_tier in group_block["applications"].values():
            assert app_tier <= group_block["tier"], "auto-added parent satisfies cap"


@pytest.mark.unit
def test_migrate_v4_to_v5_folds_fields_into_magic() -> None:
    migrated = migrate_character_v4_to_v5(_v4_character())

    assert migrated["magic"]["sacred"] == {"tier": 1, "spells": {}}
    assert migrated["magic"]["warding"] == {"tier": 1, "spells": {}}


@pytest.mark.unit
def test_migrate_v4_to_v5_idempotent_on_v5_record() -> None:
    """Running on an already-v5 record leaves it unchanged."""
    once = migrate_character_v4_to_v5(_v4_character())
    twice = migrate_character_v4_to_v5(once)
    assert twice == once


@pytest.mark.unit
def test_migrate_character_document_validates_against_character_model() -> None:
    """Migrated record round-trips through CharacterModel.model_validate."""
    migrated, changed, validated = migrate_character_document(_v4_character())
    assert changed is True
    assert validated.knowledge["athletics"].tier == 2
    assert validated.magic["sacred"].tier == 1
    # Nested applications validated under the v5 parent-cap rule.
    assert "hauling" in validated.knowledge["athletics"].applications


@pytest.mark.unit
def test_migrate_character_document_no_op_on_v5_returns_unchanged_flag() -> None:
    once, _, _ = migrate_character_document(_v4_character())
    again_migrated, again_changed, _ = migrate_character_document(once)
    assert again_changed is False
    assert again_migrated == once


@pytest.mark.unit
def test_migrate_v4_to_v5_drops_empty_application_dict_safely() -> None:
    payload = _v4_character()
    payload["application"] = {}
    payload["fields"] = {}
    migrated = migrate_character_v4_to_v5(payload)
    assert migrated["knowledge"]["athletics"]["applications"] == {}
    assert migrated["magic"] == {}
