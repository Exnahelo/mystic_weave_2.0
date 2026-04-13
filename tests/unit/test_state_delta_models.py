import pytest
from pydantic import ValidationError

from api.models import ApplyStateDeltaRequest


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
