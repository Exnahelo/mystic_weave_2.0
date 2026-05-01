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
def test_apply_state_delta_accepts_fields_dict() -> None:
    body = ApplyStateDeltaRequest.model_validate(
        {
            "character": {"fields": {"sacred": 2, "warding": 1}},
            "log_entry": "delta",
        }
    )
    assert body.character.fields == {"sacred": 2, "warding": 1}


@pytest.mark.unit
def test_apply_state_delta_rejects_tag_tiers_outside_one_to_five() -> None:
    for tag_block in ("knowledge", "application", "fields"):
        with pytest.raises(ValidationError):
            ApplyStateDeltaRequest.model_validate(
                {
                    "character": {tag_block: {"tracking": 0}},
                    "log_entry": "bad tag tier",
                }
            )

        with pytest.raises(ValidationError):
            ApplyStateDeltaRequest.model_validate(
                {
                    "character": {tag_block: {"tracking": 6}},
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

    CharacterModel.model_validate({**base_character, "knowledge": {"wilderness": 5}})

    with pytest.raises(ValidationError):
        CharacterModel.model_validate({**base_character, "knowledge": {"wilderness": 0}})

    with pytest.raises(ValidationError):
        CharacterModel.model_validate({**base_character, "application": {"tracking": 6}})


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
        TypedLogEntry(type="closure_summary", text="not yet")


def test_typed_log_entry_rejects_empty_text():
    with pytest.raises(ValidationError):
        TypedLogEntry(type="world_change", text="")


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
