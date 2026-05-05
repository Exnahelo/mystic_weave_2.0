"""Validate ArcCondition.type against the registry condition_types list."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import arc as arc_routes
from tests.contract.test_arc_transition_endpoint import ArcTransitionConn, FakePool


def _app(conn: ArcTransitionConn) -> FastAPI:
    app = FastAPI()
    app.include_router(arc_routes.router)
    app.dependency_overrides[get_pool] = lambda: FakePool(conn)
    return app


def _base_payload() -> dict:
    return {
        "title": "registry-validated arc",
        "summary": "test arc for condition-type validation",
        "primary_type": "task_local",
        "subtype": "investigation",
        "stake_scale": "local",
        "origin_type": "emergent",
    }


@pytest.mark.contract
def test_arc_create_rejects_invalid_closure_condition_type() -> None:
    """Closure conditions with invalid type labels are rejected at create time
    with a clear Pydantic validation error naming the invalid label."""
    conn = ArcTransitionConn()
    payload = {
        **_base_payload(),
        "closure_conditions": {
            "all_of": [{"type": "target_identified", "payload": {}}]
        },
    }
    with TestClient(_app(conn)) as client:
        response = client.post("/arc/sess-cond/create", json=payload)
    assert response.status_code == 422
    assert "target_identified" in response.text


@pytest.mark.contract
def test_arc_create_rejects_invalid_failure_condition_type() -> None:
    """Failure conditions are validated against the same registry."""
    conn = ArcTransitionConn()
    payload = {
        **_base_payload(),
        "failure_conditions": {
            "any_of": [{"type": "totally_made_up_condition", "payload": {}}]
        },
    }
    with TestClient(_app(conn)) as client:
        response = client.post("/arc/sess-cond/create", json=payload)
    assert response.status_code == 422
    assert "totally_made_up_condition" in response.text


@pytest.mark.contract
def test_arc_create_accepts_valid_condition_types() -> None:
    """Closure conditions with registry-valid type labels are accepted."""
    conn = ArcTransitionConn()
    payload = {
        **_base_payload(),
        "closure_conditions": {
            "all_of": [
                {"type": "evidence_chain_complete", "payload": {"flag_id": "complete"}},
                {"type": "report_delivered", "payload": {"flag_id": "report"}},
            ]
        },
        "failure_conditions": {
            "any_of": [{"type": "target_destroyed", "payload": {"flag_id": "target_destroyed"}}]
        },
    }
    with TestClient(_app(conn)) as client:
        response = client.post("/arc/sess-cond/create", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["state"] == "proposed"
    assert body["closure_conditions"]["all_of"][0]["type"] == "evidence_chain_complete"


@pytest.mark.contract
def test_arc_create_rejects_missing_flag_id_payload() -> None:
    """flag_id-group conditions with empty payload are rejected at create."""
    conn = ArcTransitionConn()
    payload = {
        **_base_payload(),
        "closure_conditions": {
            "all_of": [{"type": "target_secured", "payload": {}}]
        },
    }
    with TestClient(_app(conn)) as client:
        response = client.post("/arc/sess-cond/create", json=payload)
    assert response.status_code == 422
    assert "target_secured" in response.text
    assert "flag_id" in response.text


@pytest.mark.contract
def test_arc_create_rejects_missing_count_payload() -> None:
    """count-group conditions with empty payload are rejected at create."""
    conn = ArcTransitionConn()
    payload = {
        **_base_payload(),
        "closure_conditions": {
            "all_of": [{"type": "resolved_scene_count_at_least", "payload": {}}]
        },
    }
    with TestClient(_app(conn)) as client:
        response = client.post("/arc/sess-cond/create", json=payload)
    assert response.status_code == 422
    assert "resolved_scene_count_at_least" in response.text
    assert "count" in response.text


@pytest.mark.contract
def test_arc_create_rejects_wrong_type_count_payload() -> None:
    """count-group conditions with non-int count are rejected at create."""
    conn = ArcTransitionConn()
    payload = {
        **_base_payload(),
        "closure_conditions": {
            "all_of": [
                {"type": "resolved_scene_count_at_least", "payload": {"count": "five"}}
            ]
        },
    }
    with TestClient(_app(conn)) as client:
        response = client.post("/arc/sess-cond/create", json=payload)
    assert response.status_code == 422
    assert "resolved_scene_count_at_least" in response.text
    assert "count" in response.text


@pytest.mark.contract
def test_arc_create_rejects_missing_location_id_payload() -> None:
    """location_visited with empty payload is rejected at create."""
    conn = ArcTransitionConn()
    payload = {
        **_base_payload(),
        "closure_conditions": {
            "all_of": [{"type": "location_visited", "payload": {}}]
        },
    }
    with TestClient(_app(conn)) as client:
        response = client.post("/arc/sess-cond/create", json=payload)
    assert response.status_code == 422
    assert "location_visited" in response.text
    assert "location_id" in response.text


@pytest.mark.contract
def test_arc_create_rejects_missing_world_flag_payload() -> None:
    """world_flag_present with empty payload is rejected at create."""
    conn = ArcTransitionConn()
    payload = {
        **_base_payload(),
        "closure_conditions": {
            "all_of": [{"type": "world_flag_present", "payload": {}}]
        },
    }
    with TestClient(_app(conn)) as client:
        response = client.post("/arc/sess-cond/create", json=payload)
    assert response.status_code == 422
    assert "world_flag_present" in response.text
    assert "flag" in response.text


@pytest.mark.contract
def test_arc_create_accepts_no_payload_condition_types() -> None:
    """player_declared_completion accepts an empty payload (no required fields)."""
    conn = ArcTransitionConn()
    payload = {
        **_base_payload(),
        "closure_conditions": {
            "all_of": [{"type": "player_declared_completion", "payload": {}}]
        },
    }
    with TestClient(_app(conn)) as client:
        response = client.post("/arc/sess-cond/create", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["closure_conditions"]["all_of"][0]["type"] == "player_declared_completion"


@pytest.mark.contract
def test_arc_create_accumulates_multiple_payload_errors() -> None:
    """Multiple malformed conditions in one set produce a single 422 with both errors."""
    conn = ArcTransitionConn()
    payload = {
        **_base_payload(),
        "closure_conditions": {
            "all_of": [
                {"type": "target_secured", "payload": {}},
                {"type": "resolved_scene_count_at_least", "payload": {}},
            ]
        },
    }
    with TestClient(_app(conn)) as client:
        response = client.post("/arc/sess-cond/create", json=payload)
    assert response.status_code == 422
    body_text = response.text
    assert "target_secured" in body_text
    assert "resolved_scene_count_at_least" in body_text
    assert "flag_id" in body_text
    assert "count" in body_text


@pytest.mark.contract
def test_arc_spawn_rejects_malformed_child_payload() -> None:
    """Spawn endpoint rejects malformed payloads in child_closure_conditions."""
    conn = ArcTransitionConn()
    parent_payload = {
        "title": "Parent Arc",
        "summary": "Parent arc.",
        "primary_type": "undertaking_regional",
        "subtype": "investigation",
        "stake_scale": "regional",
        "origin_type": "declared",
        "formal_contract_qualified": True,
        "patron_npc_id": "npc-test",
        "explicit_objective": "Investigate",
        "expected_return": "Report",
        "closure_conditions": {
            "all_of": [{"type": "resolved_scene_count_at_least", "payload": {"count": 0}}]
        },
    }
    child_payload = {
        "child_title": "Child Arc",
        "child_summary": "Child arc.",
        "child_primary_type": "mission_multi_leg",
        "child_subtype": "investigation",
        "child_stake_scale": "situational",
        "ap_ownership": "parent",
        "reason": "branch",
        "child_closure_conditions": {
            "all_of": [{"type": "target_secured", "payload": {}}]
        },
    }
    with TestClient(_app(conn)) as client:
        parent = client.post("/arc/sess-cond-spawn/create", json=parent_payload).json()
        for fs, ts in [("proposed", "available"), ("available", "in_progress")]:
            client.post(
                f"/arc/sess-cond-spawn/{parent['id']}/transition",
                json={"from_state": fs, "to_state": ts, "reason": "start"},
            )
        response = client.post(
            f"/arc/sess-cond-spawn/{parent['id']}/spawn", json=child_payload
        )
    assert response.status_code == 422
    assert "target_secured" in response.text
    assert "flag_id" in response.text
