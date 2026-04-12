import pytest

from pydantic import ValidationError

from api.models import ConsequenceWeight, PacingState, WorldModel


@pytest.mark.unit
def test_pacing_state_defaults() -> None:
    pacing = PacingState()
    assert pacing.tension == 3
    assert pacing.last_consequence_weight == ConsequenceWeight.local
    assert pacing.turns_since_social_beat == 0
    assert pacing.turns_since_discovery == 0
    assert pacing.turn_count == 0


@pytest.mark.unit
def test_pacing_tension_is_clamped() -> None:
    assert PacingState(tension=99).tension == 10
    assert PacingState(tension=-7).tension == 0


@pytest.mark.unit
def test_pacing_counters_must_be_non_negative() -> None:
    with pytest.raises(ValidationError):
        PacingState(turns_since_social_beat=-1)


@pytest.mark.unit
def test_pacing_rejects_invalid_consequence_weight() -> None:
    with pytest.raises(ValidationError):
        PacingState(last_consequence_weight="epic")


@pytest.mark.unit
def test_world_turn_is_authoritative_for_pacing_turn_count() -> None:
    world = WorldModel(location="x", threat="low", goal="y", turn=7)
    assert world.pacing.turn_count == 7
