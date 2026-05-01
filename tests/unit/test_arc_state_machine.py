from __future__ import annotations

from typing import get_args

import pytest

from api.arc_state_machine import (
    ACTIVE_STATES,
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    get_allowed_transitions,
    is_active,
    is_terminal,
    is_transition_allowed,
)
from api.models import ArcState


ARC_STATES = set(get_args(ArcState))


@pytest.mark.unit
def test_every_matrix_state_is_valid_arc_state() -> None:
    assert set(ALLOWED_TRANSITIONS).issubset(ARC_STATES)
    assert all(target in ARC_STATES for targets in ALLOWED_TRANSITIONS.values() for target in targets)


@pytest.mark.unit
def test_every_arc_state_has_matrix_entry() -> None:
    assert set(ALLOWED_TRANSITIONS) == ARC_STATES


@pytest.mark.unit
def test_terminal_states_have_no_outbound_transitions() -> None:
    for state in TERMINAL_STATES:
        assert ALLOWED_TRANSITIONS[state] == frozenset()


@pytest.mark.unit
def test_active_states_are_subset_of_non_terminal() -> None:
    assert ACTIVE_STATES.isdisjoint(TERMINAL_STATES)


@pytest.mark.unit
def test_is_transition_allowed_happy_path() -> None:
    assert is_transition_allowed("proposed", "available") is True


@pytest.mark.unit
def test_is_transition_allowed_illegal() -> None:
    assert is_transition_allowed("complete", "in_progress") is False


@pytest.mark.unit
def test_is_transition_allowed_from_terminal() -> None:
    assert all(not is_transition_allowed("complete", state) for state in ARC_STATES)


@pytest.mark.unit
def test_is_transition_allowed_self_loop() -> None:
    assert is_transition_allowed("in_progress", "in_progress") is False


@pytest.mark.unit
def test_is_terminal_correctness() -> None:
    for state in ARC_STATES:
        assert is_terminal(state) is (state in TERMINAL_STATES)


@pytest.mark.unit
def test_is_active_correctness() -> None:
    for state in ARC_STATES:
        assert is_active(state) is (state in {"in_progress", "at_scope_cap"})


@pytest.mark.unit
def test_get_allowed_transitions_happy_path() -> None:
    assert get_allowed_transitions("proposed") == frozenset(["available", "abandoned"])


@pytest.mark.unit
def test_get_allowed_transitions_unknown_state_defensive() -> None:
    assert get_allowed_transitions("unknown") == frozenset()  # type: ignore[arg-type]