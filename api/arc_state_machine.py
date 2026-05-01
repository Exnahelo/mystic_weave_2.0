"""
Arc state machine: transition matrix and validation logic.

Pure functions only. No DB access, no I/O. The state machine validates
whether a proposed transition is legal given the current arc state.
Other validation (closure conditions met, cap enforcement) happens in
the route layer.
"""
from typing import Final

from api.models import ArcState


# Transition matrix per Arc System v1 design.
# Maps each state to the set of states it may transition into.
ALLOWED_TRANSITIONS: Final[dict[ArcState, frozenset[ArcState]]] = {
    "proposed": frozenset(["available", "abandoned"]),
    "available": frozenset(["in_progress", "abandoned"]),
    "in_progress": frozenset([
        "ready_to_close",
        "at_scope_cap",
        "failed",
        "abandoned",
        "replaced_by_successor",
        "merged_into_parent",
    ]),
    "at_scope_cap": frozenset([
        "ready_to_close",
        "failed",
        "replaced_by_successor",
        "merged_into_parent",
    ]),
    "ready_to_close": frozenset(["complete", "failed"]),
    # Terminal states have no outbound transitions
    "complete": frozenset(),
    "failed": frozenset(),
    "abandoned": frozenset(),
    "replaced_by_successor": frozenset(),
    "merged_into_parent": frozenset(),
}


# Terminal states cannot be transitioned out of.
TERMINAL_STATES: Final[frozenset[ArcState]] = frozenset([
    "complete",
    "failed",
    "abandoned",
    "replaced_by_successor",
    "merged_into_parent",
])


# States in which an arc consumes scene/location budget through /progress.
ACTIVE_STATES: Final[frozenset[ArcState]] = frozenset([
    "in_progress",
    "at_scope_cap",
])


def is_transition_allowed(from_state: ArcState, to_state: ArcState) -> bool:
    """Check if a transition from one state to another is permitted."""
    return to_state in ALLOWED_TRANSITIONS.get(from_state, frozenset())


def get_allowed_transitions(from_state: ArcState) -> frozenset[ArcState]:
    """Return the set of states the given state may transition into."""
    return ALLOWED_TRANSITIONS.get(from_state, frozenset())


def is_terminal(state: ArcState) -> bool:
    """Check if the state is terminal (no outbound transitions)."""
    return state in TERMINAL_STATES


def is_active(state: ArcState) -> bool:
    """Check if the arc is in an active state that consumes budget."""
    return state in ACTIVE_STATES