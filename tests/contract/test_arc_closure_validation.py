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


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Closure Arc",
        "summary": "Closure arc.",
        "primary_type": "mission_multi_leg",
        "subtype": "investigation",
        "stake_scale": "situational",
        "origin_type": "emergent",
    }
    payload.update(overrides)
    return payload


def _create_start(client: TestClient, payload: dict[str, object]) -> dict:
    arc = client.post("/arc/sess-closure/create", json=payload).json()
    for fs, ts in [("proposed", "available"), ("available", "in_progress")]:
        assert client.post(f"/arc/sess-closure/{arc['id']}/transition", json={"from_state": fs, "to_state": ts, "reason": "start"}).status_code == 200
    return arc


@pytest.mark.contract
def test_ready_to_close_with_defaulted_closure_conditions_unmet_rejected() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start(client, _payload())
        response = client.post(f"/arc/sess-closure/{arc['id']}/transition", json={"from_state": "in_progress", "to_state": "ready_to_close", "reason": "ready"})
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "closure_conditions_unmet"
    assert response.json()["detail"]["closure_conditions"]["any_of"]


@pytest.mark.contract
def test_ready_to_close_with_unmet_conditions_rejected() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start(client, _payload(closure_conditions={"all_of": [{"type": "resolved_scene_count_at_least", "payload": {"count": 3}}]}))
        response = client.post(f"/arc/sess-closure/{arc['id']}/transition", json={"from_state": "in_progress", "to_state": "ready_to_close", "reason": "ready"})
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "closure_conditions_unmet"


@pytest.mark.contract
def test_ready_to_close_with_met_consumption_condition_succeeds() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start(client, _payload(closure_conditions={"all_of": [{"type": "resolved_scene_count_at_least", "payload": {"count": 3}}]}))
        for _ in range(3):
            assert client.post(f"/arc/sess-closure/{arc['id']}/progress", json={}).status_code == 200
        response = client.post(f"/arc/sess-closure/{arc['id']}/transition", json={"from_state": "in_progress", "to_state": "ready_to_close", "reason": "ready"})
    assert response.status_code == 200


@pytest.mark.contract
def test_ready_to_close_with_world_flag_condition_succeeds() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start(client, _payload(closure_conditions={"all_of": [{"type": "report_delivered", "payload": {"flag_id": "report-ok"}}]}))
        response = client.post(f"/arc/sess-closure/{arc['id']}/transition", json={"from_state": "in_progress", "to_state": "ready_to_close", "reason": "ready", "world_flags": {"report-ok": True}})
    assert response.status_code == 200


@pytest.mark.contract
def test_failed_without_authored_failure_conditions_succeeds() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start(client, _payload())
        response = client.post(f"/arc/sess-closure/{arc['id']}/transition", json={"from_state": "in_progress", "to_state": "failed", "reason": "fail"})
    assert response.status_code == 200


@pytest.mark.contract
def test_failed_with_unmet_conditions_requires_force() -> None:
    conn = ArcTransitionConn()
    payload = _payload(failure_conditions={"all_of": [{"type": "world_flag_present", "payload": {"flag": "failed"}}]})
    with TestClient(_app(conn)) as client:
        arc = _create_start(client, payload)
        rejected = client.post(f"/arc/sess-closure/{arc['id']}/transition", json={"from_state": "in_progress", "to_state": "failed", "reason": "fail"})
        forced = client.post(f"/arc/sess-closure/{arc['id']}/transition", json={"from_state": "in_progress", "to_state": "failed", "reason": "fail", "force": True})
    assert rejected.status_code == 422
    assert rejected.json()["detail"]["error"] == "failure_conditions_unmet_no_force"
    assert forced.status_code == 200


@pytest.mark.contract
def test_merged_into_parent_updates_parent_and_without_parent_rejected() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        parent = client.post("/arc/sess-closure/create", json={
            "title": "Parent",
            "summary": "Parent",
            "primary_type": "mission_multi_leg",
            "subtype": "investigation",
            "stake_scale": "situational",
            "origin_type": "declared",
            "formal_contract_qualified": True,
            "patron_npc_id": "npc-parent",
            "explicit_objective": "Parent objective",
            "expected_return": "Parent return",
            "closure_conditions": {"all_of": [{"type": "resolved_scene_count_at_least", "payload": {"count": 0}}]},
        }).json()
        for fs, ts in [("proposed", "available"), ("available", "in_progress")]:
            assert client.post(f"/arc/sess-closure/{parent['id']}/transition", json={"from_state": fs, "to_state": ts, "reason": "start parent"}).status_code == 200
        child = client.post(f"/arc/sess-closure/{parent['id']}/spawn", json={"child_title": "Child", "child_summary": "Child", "child_primary_type": "mission_multi_leg", "child_subtype": "investigation", "child_stake_scale": "situational", "ap_ownership": "parent", "reason": "spawn"}).json()
        for fs, ts in [("proposed", "available"), ("available", "in_progress")]:
            assert client.post(f"/arc/sess-closure/{child['id']}/transition", json={"from_state": fs, "to_state": ts, "reason": "start child"}).status_code == 200
        merged = client.post(f"/arc/sess-closure/{child['id']}/transition", json={"from_state": "in_progress", "to_state": "merged_into_parent", "reason": "merge"})
        fetched_parent = client.get(f"/arc/sess-closure/{parent['id']}").json()
        no_parent = client.post(f"/arc/sess-closure/{parent['id']}/transition", json={"from_state": "in_progress", "to_state": "merged_into_parent", "reason": "merge"})
    assert merged.status_code == 200
    assert child["id"] in fetched_parent["merge_source_arc_ids"]
    assert no_parent.status_code == 409
    assert no_parent.json()["detail"]["error"] == "no_parent_to_merge_into"