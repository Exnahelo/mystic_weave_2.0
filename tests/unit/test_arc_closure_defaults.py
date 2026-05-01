from __future__ import annotations

from api.arc_conditions import is_empty
from api.game_data import list_arc_subtypes
from api.models import ArcConditionSet
from api.routes.arc import SUBTYPE_DEFAULT_CLOSURE_CONDITIONS, ensure_closure_conditions
from api.schemas.arc_schemas import ArcCreateRequest


def _request(**overrides: object) -> ArcCreateRequest:
    payload: dict[str, object] = {
        "title": "Closure Test",
        "summary": "Closure default test arc.",
        "primary_type": "mission_multi_leg",
        "subtype": "investigation",
        "stake_scale": "situational",
        "origin_type": "emergent",
        "formal_contract_qualified": False,
    }
    payload.update(overrides)
    return ArcCreateRequest.model_validate(payload)


def test_each_registry_subtype_has_specific_or_default_closure_template() -> None:
    assert "_default" in SUBTYPE_DEFAULT_CLOSURE_CONDITIONS
    for subtype in list_arc_subtypes():
        template = SUBTYPE_DEFAULT_CLOSURE_CONDITIONS.get(
            subtype,
            SUBTYPE_DEFAULT_CLOSURE_CONDITIONS["_default"],
        )
        condition_set = ArcConditionSet.model_validate(template)
        assert not is_empty(condition_set)


def test_ensure_closure_conditions_preserves_authored_conditions() -> None:
    authored = {
        "all_of": [
            {"type": "world_flag_present", "payload": {"flag": "authored_done"}}
        ]
    }
    req = _request(closure_conditions=authored)

    assert ensure_closure_conditions(req) == req.closure_conditions


def test_ensure_closure_conditions_populates_from_subtype_default() -> None:
    closure_conditions = ensure_closure_conditions(_request(subtype="investigation"))

    assert closure_conditions.model_dump() == ArcConditionSet.model_validate(
        SUBTYPE_DEFAULT_CLOSURE_CONDITIONS["investigation"]
    ).model_dump()


def test_ensure_closure_conditions_falls_back_for_unknown_subtype() -> None:
    req = _request()
    object.__setattr__(req, "subtype", "unrecognized_subtype")

    assert ensure_closure_conditions(req).model_dump() == ArcConditionSet.model_validate(
        SUBTYPE_DEFAULT_CLOSURE_CONDITIONS["_default"]
    ).model_dump()