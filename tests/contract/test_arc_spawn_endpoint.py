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


def _parent_payload(formal: bool = True) -> dict[str, object]:
    payload = {
        "title": "Parent Arc",
        "summary": "Parent arc.",
        "primary_type": "undertaking_regional",
        "subtype": "investigation",
        "stake_scale": "regional",
        "origin_type": "declared" if formal else "emergent",
        "formal_contract_qualified": formal,
        "closure_conditions": {"all_of": [{"type": "resolved_scene_count_at_least", "payload": {"count": 0}}]},
    }
    if formal:
        payload.update({"patron_npc_id": "npc-test", "explicit_objective": "Investigate", "expected_return": "Report"})
    return payload


def _child_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "child_title": "Child Arc",
        "child_summary": "Child arc.",
        "child_primary_type": "mission_multi_leg",
        "child_subtype": "investigation",
        "child_stake_scale": "situational",
        "ap_ownership": "parent",
        "reason": "branch",
    }
    payload.update(overrides)
    return payload


def _create_parent(client: TestClient, formal: bool = True, start: bool = True) -> dict:
    parent = client.post("/arc/sess-spawn/create", json=_parent_payload(formal)).json()
    if start:
        for fs, ts in [("proposed", "available"), ("available", "in_progress")]:
            assert client.post(f"/arc/sess-spawn/{parent['id']}/transition", json={"from_state": fs, "to_state": ts, "reason": "start"}).status_code == 200
    return parent


@pytest.mark.contract
def test_spawn_child_happy_path_tracks_parent_and_audit_log() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        parent = _create_parent(client)
        response = client.post(f"/arc/sess-spawn/{parent['id']}/spawn", json=_child_payload())
        fetched_parent = client.get(f"/arc/sess-spawn/{parent['id']}")
    assert response.status_code == 200
    child = response.json()
    assert child["parent_arc_id"] == parent["id"]
    assert child["id"] in fetched_parent.json()["spawned_arc_ids"]
    assert conn.transitions[-1]["triggering_event"] == "spawn"


@pytest.mark.contract
def test_spawn_from_proposed_rejected() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        parent = _create_parent(client, start=False)
        response = client.post(f"/arc/sess-spawn/{parent['id']}/spawn", json=_child_payload())
    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "parent_not_in_spawnable_state"


@pytest.mark.contract
def test_spawn_from_terminal_rejected() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        parent = _create_parent(client)
        assert client.post(f"/arc/sess-spawn/{parent['id']}/transition", json={"from_state": "in_progress", "to_state": "ready_to_close", "reason": "ready"}).status_code == 200
        assert client.post(f"/arc/sess-spawn/{parent['id']}/settle", json={"outcome": "complete", "awarded_ap": 3}).status_code == 200
        response = client.post(f"/arc/sess-spawn/{parent['id']}/spawn", json=_child_payload())
    assert response.status_code == 409


@pytest.mark.contract
def test_spawn_ap_ownership_validation() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        emergent_parent = _create_parent(client, formal=False)
        no_parent_ap = client.post(f"/arc/sess-spawn/{emergent_parent['id']}/spawn", json=_child_payload(ap_ownership="parent"))
        formal_parent = _create_parent(client, formal=True)
        child_no_ap = client.post(f"/arc/sess-spawn/{formal_parent['id']}/spawn", json=_child_payload(ap_ownership="child"))
    assert no_parent_ap.status_code == 409
    assert no_parent_ap.json()["detail"]["error"] == "emergent_parent_no_ap_to_partition"
    assert child_no_ap.status_code == 409
    assert child_no_ap.json()["detail"]["error"] == "emergent_child_cannot_own_ap"


@pytest.mark.contract
def test_spawn_formal_parent_emergent_child_parent_ownership_succeeds_zero_ap() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        parent = _create_parent(client)
        response = client.post(f"/arc/sess-spawn/{parent['id']}/spawn", json=_child_payload(ap_ownership="parent"))
    assert response.status_code == 200
    assert response.json()["rewards"]["ap_award"] == {"min": 0, "max": 0, "fixed": False}


@pytest.mark.contract
def test_spawn_formal_child_child_ownership_succeeds_full_ap() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        parent = _create_parent(client)
        response = client.post(f"/arc/sess-spawn/{parent['id']}/spawn", json=_child_payload(
            ap_ownership="child",
            child_formal_contract_qualified=True,
            child_patron_npc_id="npc-child",
            child_explicit_objective="Do child",
            child_expected_return="Report child",
        ))
    assert response.status_code == 200
    assert response.json()["rewards"]["ap_award"] == {"min": 1, "max": 2, "fixed": False}


@pytest.mark.contract
def test_spawn_formal_child_requires_provenance() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        parent = _create_parent(client)
        response = client.post(f"/arc/sess-spawn/{parent['id']}/spawn", json=_child_payload(child_formal_contract_qualified=True, ap_ownership="child"))
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "insufficient_provenance"


@pytest.mark.contract
def test_spawn_multiple_children_tracked() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        parent = _create_parent(client)
        child_ids = [client.post(f"/arc/sess-spawn/{parent['id']}/spawn", json=_child_payload(child_title=f"Child {i}")).json()["id"] for i in range(3)]
        fetched = client.get(f"/arc/sess-spawn/{parent['id']}").json()
    assert fetched["spawned_arc_ids"] == child_ids