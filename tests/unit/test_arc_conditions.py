from __future__ import annotations

from datetime import datetime, timezone

import pytest

from api.arc_conditions import (
    ConditionEvaluationError,
    evaluate_condition,
    evaluate_condition_set,
    is_empty,
)
from api.models import Arc, ArcCondition, ArcConditionSet


def _arc(**overrides: object) -> Arc:
    payload = {
        "id": "arc-cond",
        "session_id": "sess-cond",
        "title": "Condition Arc",
        "summary": "Condition test arc.",
        "primary_type": "mission_multi_leg",
        "subtype": "investigation",
        "stake_scale": "situational",
        "origin_type": "emergent",
        "state": "in_progress",
        "budget": {
            "resolved_scene_soft_cap": 6,
            "resolved_scene_hard_cap": 10,
            "location_soft_cap": 3,
            "location_hard_cap": 5,
        },
        "rewards": {"ap_award": {"min": 0, "max": 0, "fixed": False}},
        "timestamps": {"created_at": datetime.now(timezone.utc).isoformat()},
    }
    payload.update(overrides)
    return Arc.model_validate(payload)


@pytest.mark.unit
def test_resolved_scene_count_at_least_true() -> None:
    arc = _arc(consumption={"resolved_scenes_used": 5})
    assert evaluate_condition(ArcCondition(type="resolved_scene_count_at_least", payload={"count": 3}), arc)


@pytest.mark.unit
def test_resolved_scene_count_at_least_false() -> None:
    arc = _arc(consumption={"resolved_scenes_used": 5})
    assert not evaluate_condition(ArcCondition(type="resolved_scene_count_at_least", payload={"count": 10}), arc)


@pytest.mark.unit
def test_location_visited_true() -> None:
    arc = _arc(consumption={"locations_visited": ["A"]})
    assert evaluate_condition(ArcCondition(type="location_visited", payload={"location_id": "A"}), arc)


@pytest.mark.unit
def test_location_visited_false() -> None:
    arc = _arc(consumption={"locations_visited": ["A"]})
    assert not evaluate_condition(ArcCondition(type="location_visited", payload={"location_id": "B"}), arc)


@pytest.mark.unit
def test_world_flag_present_true() -> None:
    assert evaluate_condition(ArcCondition(type="world_flag_present", payload={"flag": "done"}), _arc(), {"done": True})


@pytest.mark.unit
def test_world_flag_present_false() -> None:
    assert not evaluate_condition(ArcCondition(type="world_flag_present", payload={"flag": "done"}), _arc(), {})


@pytest.mark.unit
def test_report_delivered_requires_flag_id() -> None:
    with pytest.raises(ConditionEvaluationError):
        evaluate_condition(ArcCondition(type="report_delivered"), _arc())


@pytest.mark.unit
def test_unknown_condition_type_raises() -> None:
    """The evaluator rejects unknown types at evaluation time. Note that
    request-model validators (ArcCreateRequest, ArcSpawnRequest) reject
    unknown types earlier at create/spawn time. The evaluator only sees
    unknown types when loading legacy stored arcs whose data predates the
    registry."""
    with pytest.raises(ConditionEvaluationError):
        evaluate_condition(ArcCondition(type="made_up"), _arc())


@pytest.mark.unit
def test_empty_condition_set_returns_false() -> None:
    condition_set = ArcConditionSet()
    assert is_empty(condition_set)
    assert not evaluate_condition_set(condition_set, _arc())


@pytest.mark.unit
def test_all_of_all_true_returns_true() -> None:
    arc = _arc(consumption={"resolved_scenes_used": 3, "locations_visited": ["A"]})
    condition_set = ArcConditionSet(all_of=[
        ArcCondition(type="resolved_scene_count_at_least", payload={"count": 3}),
        ArcCondition(type="location_visited", payload={"location_id": "A"}),
    ])
    assert evaluate_condition_set(condition_set, arc)


@pytest.mark.unit
def test_all_of_one_false_returns_false() -> None:
    arc = _arc(consumption={"resolved_scenes_used": 3})
    condition_set = ArcConditionSet(all_of=[
        ArcCondition(type="resolved_scene_count_at_least", payload={"count": 3}),
        ArcCondition(type="location_visited", payload={"location_id": "A"}),
    ])
    assert not evaluate_condition_set(condition_set, arc)


@pytest.mark.unit
def test_any_of_at_least_one_true_returns_true() -> None:
    arc = _arc(consumption={"resolved_scenes_used": 3})
    condition_set = ArcConditionSet(any_of=[
        ArcCondition(type="resolved_scene_count_at_least", payload={"count": 9}),
        ArcCondition(type="resolved_scene_count_at_least", payload={"count": 3}),
    ])
    assert evaluate_condition_set(condition_set, arc)


@pytest.mark.unit
def test_any_of_all_false_returns_false() -> None:
    condition_set = ArcConditionSet(any_of=[
        ArcCondition(type="resolved_scene_count_at_least", payload={"count": 9}),
        ArcCondition(type="location_visited", payload={"location_id": "A"}),
    ])
    assert not evaluate_condition_set(condition_set, _arc())


@pytest.mark.unit
def test_none_of_all_false_returns_true() -> None:
    condition_set = ArcConditionSet(none_of=[
        ArcCondition(type="resolved_scene_count_at_least", payload={"count": 9}),
    ])
    assert evaluate_condition_set(condition_set, _arc())


@pytest.mark.unit
def test_none_of_one_true_returns_false() -> None:
    condition_set = ArcConditionSet(none_of=[
        ArcCondition(type="resolved_scene_count_at_least", payload={"count": 0}),
    ])
    assert not evaluate_condition_set(condition_set, _arc())


@pytest.mark.unit
def test_combined_condition_set_evaluates_correctly() -> None:
    arc = _arc(consumption={"resolved_scenes_used": 5, "locations_visited": ["A", "B"]})
    condition_set = ArcConditionSet(
        all_of=[ArcCondition(type="resolved_scene_count_at_least", payload={"count": 3})],
        any_of=[ArcCondition(type="location_visited", payload={"location_id": "B"})],
        none_of=[ArcCondition(type="location_visited", payload={"location_id": "C"})],
    )
    assert evaluate_condition_set(condition_set, arc)