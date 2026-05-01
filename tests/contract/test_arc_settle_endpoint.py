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


def _payload(formal: bool = True) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Settle Arc",
        "summary": "Settle test arc.",
        "primary_type": "mission_multi_leg",
        "subtype": "investigation",
        "stake_scale": "situational",
        "origin_type": "declared" if formal else "emergent",
        "formal_contract_qualified": formal,
        "closure_conditions": {"all_of": [{"type": "resolved_scene_count_at_least", "payload": {"count": 0}}]},
    }
    if formal:
        payload.update({"patron_npc_id": "npc-test", "explicit_objective": "Do it", "expected_return": "Report"})
    return payload


def _create_start_ready(client: TestClient, formal: bool = True) -> dict:
    arc = client.post("/arc/sess-settle/create", json=_payload(formal)).json()
    for from_state, to_state in [("proposed", "available"), ("available", "in_progress"), ("in_progress", "ready_to_close")]:
        response = client.post(f"/arc/sess-settle/{arc['id']}/transition", json={"from_state": from_state, "to_state": to_state, "reason": "advance"})
        assert response.status_code == 200
    return arc


@pytest.mark.contract
def test_settle_happy_path_formal_arc_complete_records_settlement() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start_ready(client)
        response = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete", "awarded_ap": 2, "coin_cd_awarded": 0, "notes": "done"})
        fetched = client.get(f"/arc/sess-settle/{arc['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "complete"
    assert body["settlement"]["awarded_ap"] == 2
    assert body["settlement"]["notes"] == "done"
    assert fetched.json()["settlement"]["outcome"] == "complete"
    assert body["timestamps"]["closed_at"] is not None
    assert conn.transitions[-1]["triggering_event"] == "settle"


@pytest.mark.contract
def test_settle_failed_happy_path_no_ap() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = client.post("/arc/sess-settle/create", json=_payload()).json()
        for fs, ts in [("proposed", "available"), ("available", "in_progress")]:
            assert client.post(f"/arc/sess-settle/{arc['id']}/transition", json={"from_state": fs, "to_state": ts, "reason": "start"}).status_code == 200
        response = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "failed", "awarded_ap": 0})
    assert response.status_code == 200
    assert response.json()["state"] == "failed"


@pytest.mark.contract
def test_settle_rejects_ap_on_failure() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = client.post("/arc/sess-settle/create", json=_payload()).json()
        for fs, ts in [("proposed", "available"), ("available", "in_progress")]:
            client.post(f"/arc/sess-settle/{arc['id']}/transition", json={"from_state": fs, "to_state": ts, "reason": "start"})
        response = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "failed", "awarded_ap": 1})
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "ap_on_failure_not_allowed"


@pytest.mark.contract
def test_settle_rejects_ap_on_emergent_arc() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start_ready(client, formal=False)
        response = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete", "awarded_ap": 1})
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "emergent_arc_no_ap"


@pytest.mark.contract
def test_settle_rejects_ap_outside_envelope() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start_ready(client)
        response = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete", "awarded_ap": 5})
    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "ap_outside_envelope"


@pytest.mark.contract
def test_settle_wrong_state_and_twice_rejected() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = client.post("/arc/sess-settle/create", json=_payload()).json()
        wrong = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete", "awarded_ap": 1})
        arc = _create_start_ready(client)
        assert client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete", "awarded_ap": 1}).status_code == 200
        twice = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete", "awarded_ap": 1})
    assert wrong.status_code == 409
    assert twice.status_code == 409


@pytest.mark.contract
def test_settle_reputation_bounds() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start_ready(client)
        bad = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete", "awarded_ap": 1, "reputation_changes": [{"faction": "f", "delta": 1}]})
        arc2 = _create_start_ready(client)
        good = client.post(f"/arc/sess-settle/{arc2['id']}/settle", json={"outcome": "complete", "awarded_ap": 1, "reputation_changes": [{"faction": "f", "delta": 0}]})
    assert bad.status_code == 422
    assert bad.json()["detail"]["error"] == "reputation_positive_outside_envelope"
    assert good.status_code == 200