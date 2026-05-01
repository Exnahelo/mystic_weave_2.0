"""
Arc condition evaluation.

Pure functions only. Given an ArcConditionSet and the relevant context
(arc, world flags, etc.), determines whether the conditions are met.

The condition vocabulary is defined in data/catalog/registries/arc_types.json.
This module implements evaluators for each condition type.
"""

from typing import Any

from api.models import Arc, ArcCondition, ArcConditionSet


class ConditionEvaluationError(Exception):
    """Raised when a condition cannot be evaluated (unknown type, malformed payload)."""

    pass


def evaluate_condition(
    condition: ArcCondition,
    arc: Arc,
    world_flags: dict[str, Any] | None = None,
) -> bool:
    """
    Evaluate a single condition against arc state.

    world_flags is provided when the route layer has access to world state.
    For conditions that don't reference world state, it's unused.
    """
    cond_type = condition.type
    payload = condition.payload
    flags = world_flags or {}

    if cond_type == "resolved_scene_count_at_least":
        threshold = payload.get("count", 0)
        return arc.consumption.resolved_scenes_used >= threshold

    if cond_type == "resolved_scene_count_at_most":
        threshold = payload.get("count", 0)
        return arc.consumption.resolved_scenes_used <= threshold

    if cond_type == "location_visited":
        location_id = payload.get("location_id")
        return location_id in arc.consumption.locations_visited

    if cond_type == "location_count_at_least":
        threshold = payload.get("count", 0)
        return len(arc.consumption.locations_visited) >= threshold

    if cond_type == "world_flag_present":
        flag_name = payload.get("flag")
        return flag_name in flags

    if cond_type == "player_declared_completion":
        return flags.get("player_declared_completion") == arc.id

    if cond_type == "player_declared_abandonment":
        return flags.get("player_declared_abandonment") == arc.id

    if cond_type in (
        "npc_contact_made",
        "faction_contact_made",
        "evidence_grade_at_least",
        "target_item_recovered",
        "target_delivered",
        "target_destroyed",
        "target_secured",
        "target_survived",
        "time_limit_exceeded",
        "threat_state_changed",
        "npc_state_changed",
        "evidence_chain_complete",
        "report_delivered",
        "decision_made",
        "faction_state_changed",
        "objective_branch_chosen",
    ):
        flag_id = payload.get("flag_id")
        if flag_id is None:
            raise ConditionEvaluationError(
                f"Condition '{cond_type}' requires payload.flag_id"
            )
        return flag_id in flags

    raise ConditionEvaluationError(f"Unknown condition type: '{cond_type}'")


def evaluate_condition_set(
    condition_set: ArcConditionSet,
    arc: Arc,
    world_flags: dict[str, Any] | None = None,
) -> bool:
    """
    Evaluate a full condition set: all_of must be true, any_of must have
    at least one true (if non-empty), none_of must all be false.

    Empty condition set is treated as unsatisfied to prevent silent
    auto-closure of arcs without authored closure conditions. Callers
    should use is_empty() before evaluating if "no conditions" should
    mean something specific.
    """
    if is_empty(condition_set):
        return False

    if condition_set.all_of:
        if not all(evaluate_condition(c, arc, world_flags) for c in condition_set.all_of):
            return False

    if condition_set.any_of:
        if not any(evaluate_condition(c, arc, world_flags) for c in condition_set.any_of):
            return False

    if condition_set.none_of:
        if any(evaluate_condition(c, arc, world_flags) for c in condition_set.none_of):
            return False

    return True


def is_empty(condition_set: ArcConditionSet) -> bool:
    """Check if a condition set has any conditions defined."""
    return not (
        condition_set.all_of
        or condition_set.any_of
        or condition_set.none_of
    )