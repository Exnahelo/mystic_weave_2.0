import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

import api.game_data as game_data
from api.models import Arc, ArcBudget, ArcConsumption


def _minimal_arc_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "arc-test-001",
        "session_id": "test-session",
        "title": "Test Arc",
        "summary": "Sample for validation",
        "primary_type": "mission_multi_leg",
        "subtype": "investigation",
        "stake_scale": "situational",
        "origin_type": "declared",
        "state": "proposed",
        "budget": {
            "resolved_scene_soft_cap": 6,
            "resolved_scene_hard_cap": 10,
            "location_soft_cap": 3,
            "location_hard_cap": 5,
        },
        "rewards": {
            "ap_award": {"min": 1, "max": 2, "fixed": False},
        },
        "timestamps": {
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    payload.update(overrides)
    return payload


@pytest.fixture(autouse=True)
def clear_arc_registry_cache() -> None:
    game_data.load_arc_types.cache_clear()
    game_data._load_json.cache_clear()
    yield
    game_data.load_arc_types.cache_clear()
    game_data._load_json.cache_clear()


@pytest.mark.unit
def test_minimal_valid_arc_construction_succeeds() -> None:
    arc = Arc.model_validate(_minimal_arc_payload())

    assert arc.id == "arc-test-001"
    assert arc.primary_type == "mission_multi_leg"
    assert arc.consumption.resolved_scenes_used == 0
    assert arc.flags.ap_ownership == "none"


@pytest.mark.unit
def test_invalid_primary_type_rejected() -> None:
    with pytest.raises(ValidationError):
        Arc.model_validate(_minimal_arc_payload(primary_type="invalid_type"))


@pytest.mark.unit
def test_invalid_state_rejected() -> None:
    with pytest.raises(ValidationError):
        Arc.model_validate(_minimal_arc_payload(state="blocked"))


@pytest.mark.unit
def test_invalid_stake_scale_rejected() -> None:
    with pytest.raises(ValidationError):
        Arc.model_validate(_minimal_arc_payload(stake_scale="global"))


@pytest.mark.unit
def test_invalid_origin_type_rejected() -> None:
    with pytest.raises(ValidationError):
        Arc.model_validate(_minimal_arc_payload(origin_type="external"))


@pytest.mark.unit
def test_negative_values_on_consumption_fields_rejected() -> None:
    for field in (
        "resolved_scenes_used",
        "turns_spent",
        "discoveries_logged",
        "major_conflicts_resolved",
        "escalations_used",
    ):
        with pytest.raises(ValidationError):
            ArcConsumption.model_validate({field: -1})


@pytest.mark.unit
def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        Arc.model_validate(_minimal_arc_payload(unexpected="value"))


@pytest.mark.unit
def test_arc_budget_rejects_soft_cap_higher_than_hard_cap() -> None:
    with pytest.raises(ValidationError):
        ArcBudget.model_validate(
            {
                "resolved_scene_soft_cap": 11,
                "resolved_scene_hard_cap": 10,
                "location_soft_cap": 3,
                "location_hard_cap": 5,
            }
        )

    with pytest.raises(ValidationError):
        ArcBudget.model_validate(
            {
                "resolved_scene_soft_cap": 6,
                "resolved_scene_hard_cap": 10,
                "location_soft_cap": 6,
                "location_hard_cap": 5,
            }
        )


@pytest.mark.unit
def test_registry_loader_returns_type_ids_and_default_envelopes() -> None:
    assert game_data.list_arc_type_ids() == [
        "task_local",
        "contract_delicate",
        "mission_multi_leg",
        "undertaking_regional",
        "arc_campaign",
    ]

    defaults = game_data.get_arc_type_defaults("mission_multi_leg")
    assert defaults["stake_scale_default"] == "situational"
    assert defaults["ap_award_min"] == 1
    assert defaults["ap_award_max"] == 2
    assert defaults["scene_soft_cap"] == 6
    assert defaults["scene_hard_cap"] == 10
    assert defaults["location_soft_cap"] == 3
    assert defaults["location_hard_cap"] == 5
    assert game_data.list_arc_state_ids()[0] == "proposed"
    assert "campaign" in game_data.list_arc_stake_scales()
    assert "derived" in game_data.list_arc_origin_types()
    assert "investigation" in game_data.list_arc_subtypes()
    assert "objective_branch_chosen" in game_data.list_arc_condition_types()


@pytest.mark.unit
def test_registry_loader_calibrated_defaults_match_json_file() -> None:
    registry_path = Path("data/catalog/registries/arc_types.json")
    raw = json.loads(registry_path.read_text(encoding="utf-8"))

    assert game_data.load_arc_types()["types"] == raw["types"]
    for entry in raw["types"]:
        assert game_data.get_arc_type_defaults(entry["id"]) == entry