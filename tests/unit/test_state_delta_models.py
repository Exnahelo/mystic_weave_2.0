import pytest
from pydantic import ValidationError

from api.models import ApplyStateDeltaRequest, CharacterModel, SaveStateRequest, TypedLogEntry
from api.routes.state import validate_delta


@pytest.mark.unit
def test_apply_state_delta_accepts_partial_character_only() -> None:
    body = ApplyStateDeltaRequest.model_validate(
        {
            "character": {"notes": "new note"},
            "log_entry": "delta",
        }
    )
    assert body.character.notes == "new note"
    assert body.world.location is None


@pytest.mark.unit
def test_apply_state_delta_accepts_magic_dict() -> None:
    body = ApplyStateDeltaRequest.model_validate(
        {
            "character": {
                "magic": {
                    "sacred": {"tier": 2},
                    "warding": {"tier": 1, "spells": {"alarm_sigil": 1}},
                }
            },
            "log_entry": "delta",
        }
    )
    assert body.character.magic["sacred"].tier == 2
    assert body.character.magic["warding"].spells == {"alarm_sigil": 1}


@pytest.mark.unit
def test_apply_state_delta_accepts_partial_knowledge_without_tier() -> None:
    """A delta can advance applications without restating the parent tier."""
    body = ApplyStateDeltaRequest.model_validate(
        {
            "character": {"knowledge": {"tracking": {"applications": {"spoor_reading": 3}}}},
            "log_entry": "advance child only",
        }
    )
    assert body.character.knowledge["tracking"].tier is None
    assert body.character.knowledge["tracking"].applications == {"spoor_reading": 3}


@pytest.mark.unit
def test_apply_state_delta_rejects_legacy_application_field() -> None:
    """v4 flat `application` field is no longer accepted on the delta."""
    with pytest.raises(ValidationError):
        ApplyStateDeltaRequest.model_validate(
            {"character": {"application": {"tracking": 1}}, "log_entry": "legacy"}
        )


@pytest.mark.unit
def test_apply_state_delta_rejects_legacy_fields_field() -> None:
    """v4 flat `fields` field is no longer accepted on the delta."""
    with pytest.raises(ValidationError):
        ApplyStateDeltaRequest.model_validate(
            {"character": {"fields": {"sacred": 1}}, "log_entry": "legacy"}
        )


@pytest.mark.unit
def test_apply_state_delta_rejects_tag_tiers_outside_one_to_five() -> None:
    # Knowledge group tier out of range
    with pytest.raises(ValidationError):
        ApplyStateDeltaRequest.model_validate(
            {
                "character": {"knowledge": {"tracking": {"tier": 0, "applications": {}}}},
                "log_entry": "bad tag tier",
            }
        )
    with pytest.raises(ValidationError):
        ApplyStateDeltaRequest.model_validate(
            {
                "character": {"knowledge": {"tracking": {"tier": 6, "applications": {}}}},
                "log_entry": "bad tag tier",
            }
        )

    # Application tier out of range
    with pytest.raises(ValidationError):
        ApplyStateDeltaRequest.model_validate(
            {
                "character": {
                    "knowledge": {"tracking": {"tier": 3, "applications": {"spoor_reading": 0}}}
                },
                "log_entry": "bad tag tier",
            }
        )

    # Magic field tier out of range
    with pytest.raises(ValidationError):
        ApplyStateDeltaRequest.model_validate(
            {
                "character": {"magic": {"sacred": {"tier": 6}}},
                "log_entry": "bad tag tier",
            }
        )


@pytest.mark.unit
def test_character_model_rejects_tag_tiers_outside_one_to_five() -> None:
    base_character = {
        "name": "Sylvara",
        "ancestry": "drakari",
        "culture": "hollow_crown",
        "focus": "stalker",
        "background": "scout",
        "hp": {"current": 10, "max": 10},
        "domains": {
            "power": 10,
            "agility": 10,
            "perception": 10,
            "endurance": 10,
            "intellect": 10,
            "will": 10,
            "presence": 10,
        },
    }

    CharacterModel.model_validate(
        {**base_character, "knowledge": {"wilderness": {"tier": 5, "applications": {}}}}
    )

    with pytest.raises(ValidationError):
        CharacterModel.model_validate(
            {**base_character, "knowledge": {"wilderness": {"tier": 0, "applications": {}}}}
        )

    with pytest.raises(ValidationError):
        CharacterModel.model_validate(
            {
                **base_character,
                "knowledge": {
                    "tracking": {"tier": 3, "applications": {"spoor_reading": 6}}
                },
            }
        )


@pytest.mark.unit
def test_apply_state_delta_rejects_noop_delta() -> None:
    with pytest.raises(ValidationError):
        ApplyStateDeltaRequest.model_validate(
            {
                "character": {},
                "world": {},
                "log_entry": "noop",
            }
        )


@pytest.mark.unit
def test_apply_state_delta_rejects_unknown_keys() -> None:
    with pytest.raises(ValidationError):
        ApplyStateDeltaRequest.model_validate(
            {
                "character": {"bogus": True},
                "log_entry": "bad",
            }
        )


@pytest.mark.unit
def test_validate_delta_accepts_valid_delta() -> None:
    body = ApplyStateDeltaRequest.model_validate(
        {"character": {"notes": "changed"}, "log_entry": "turn summary"}
    )
    assert validate_delta(body) is None


@pytest.mark.unit
def test_validate_delta_rejects_blank_log_entry() -> None:
    body = ApplyStateDeltaRequest.model_validate(
        {"character": {"notes": "changed"}, "log_entry": "   "}
    )
    with pytest.raises(ValueError, match="log_entry is required"):
        validate_delta(body)


def test_typed_log_entry_accepts_valid_enum_value():
    entry = TypedLogEntry(type="world_change", text="Companion added: id_x")
    assert entry.type == "world_change"
    assert entry.text == "Companion added: id_x"


def test_typed_log_entry_rejects_unknown_type():
    with pytest.raises(ValidationError):
        TypedLogEntry(type="unknown_type", text="not valid")


def test_typed_log_entry_rejects_empty_text():
    with pytest.raises(ValidationError):
        TypedLogEntry(type="world_change", text="")


def test_typed_log_entry_closure_summary_accepts_no_payload():
    """closure_summary without payload is valid; payload is optional."""
    entry = TypedLogEntry(type="closure_summary", text="Arc closed.")
    assert entry.payload is None


def test_typed_log_entry_closure_summary_accepts_empty_payload():
    """closure_summary with empty payload is now valid (was forbidden pre-Brief 12)."""
    entry = TypedLogEntry(type="closure_summary", text="Arc closed.", payload={})
    assert entry.payload == {}


def test_typed_log_entry_closure_summary_accepts_payload():
    entry = TypedLogEntry(
        type="closure_summary",
        text="Arc settled.",
        payload={"arc_id": "arc_x", "outcome": "complete"},
    )
    assert entry.payload == {"arc_id": "arc_x", "outcome": "complete"}


def test_typed_log_entry_world_change_rejects_payload():
    with pytest.raises(ValidationError):
        TypedLogEntry(
            type="world_change",
            text="Companion added.",
            payload={"id": "ignored"},
        )


def test_apply_state_delta_request_accepts_omitted_log_entry():
    req = ApplyStateDeltaRequest.model_validate({
        "character": {"hp": {"current": 50}},
        "world": {},
    })
    assert req.log_entry is None


def test_apply_state_delta_request_accepts_string_log_entry():
    req = ApplyStateDeltaRequest.model_validate({
        "character": {"hp": {"current": 50}},
        "world": {},
        "log_entry": "Legacy plain text entry.",
    })
    assert req.log_entry == "Legacy plain text entry."


def test_apply_state_delta_request_accepts_typed_log_entry():
    req = ApplyStateDeltaRequest.model_validate({
        "character": {"hp": {"current": 50}},
        "world": {},
        "log_entry": {"type": "narrative_non_arc", "text": "A rare non-arc beat."},
    })
    assert isinstance(req.log_entry, TypedLogEntry)
    assert req.log_entry.type == "narrative_non_arc"


def test_save_state_request_accepts_typed_log_entry():
    req = SaveStateRequest.model_validate({
        "log_entry": {"type": "compression", "text": "Compressed travel beats."},
    })
    assert isinstance(req.log_entry, TypedLogEntry)
