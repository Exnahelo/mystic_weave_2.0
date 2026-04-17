import pytest
from pydantic import ValidationError

from api.models import ApplyStateDeltaRequest
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
