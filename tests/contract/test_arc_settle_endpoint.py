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


def _create_start_in_progress(client: TestClient, *, session_id: str = "sess-settle", formal: bool = True) -> dict:
    arc = client.post(f"/arc/{session_id}/create", json=_payload(formal)).json()
    for from_state, to_state in [("proposed", "available"), ("available", "in_progress")]:
        response = client.post(f"/arc/{session_id}/{arc['id']}/transition", json={"from_state": from_state, "to_state": to_state, "reason": "advance"})
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
    assert body["arc"]["state"] == "complete"
    assert body["arc"]["settlement"]["awarded_ap"] == 2
    assert body["arc"]["settlement"]["notes"] == "done"
    assert fetched.json()["settlement"]["outcome"] == "complete"
    assert body["arc"]["timestamps"]["closed_at"] is not None
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
    assert response.json()["arc"]["state"] == "failed"


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


@pytest.mark.contract
def test_settlement_updates_character_advancement() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start_ready(client)
        response = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete", "awarded_ap": 2})
    assert response.status_code == 200
    assert conn.character["advancement"]["points_available"] == 2
    assert conn.character["advancement"]["points_earned_total"] == 2


@pytest.mark.contract
def test_settlement_updates_character_reputation() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start_ready(client)
        # The default envelope allows zero reputation; widen in stored arc data for this integration assertion.
        stored = next(row for row in conn.rows if row["id"] == arc["id"])
        data = __import__("json").loads(stored["data"])
        data["rewards"]["reputation"]["max_positive_delta"] = 10
        stored["data"] = __import__("json").dumps(data)
        response = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete", "awarded_ap": 1, "reputation_changes": [{"faction": "House Heartwood", "delta": 5}]})
    assert response.status_code == 200
    assert conn.character["reputation"][0]["faction"] == "House Heartwood"
    assert conn.character["reputation"][0]["standing"] == 5


@pytest.mark.contract
def test_settlement_updates_world_economy_coin() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start_ready(client)
        stored = next(row for row in conn.rows if row["id"] == arc["id"])
        data = __import__("json").loads(stored["data"])
        data["rewards"]["economy"]["coin_cd_max"] = 500
        stored["data"] = __import__("json").dumps(data)
        response = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete", "awarded_ap": 1, "coin_cd_awarded": 500})
    assert response.status_code == 200
    assert conn.world["economy"]["coin"] == 1500


@pytest.mark.contract
def test_emergent_arc_settlement_updates_state_but_not_ap() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start_ready(client, formal=False)
        stored = next(row for row in conn.rows if row["id"] == arc["id"])
        data = __import__("json").loads(stored["data"])
        data["rewards"]["reputation"]["max_positive_delta"] = 10
        stored["data"] = __import__("json").dumps(data)
        response = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete", "reputation_changes": [{"faction": "Greenshields", "delta": 5}]})
    assert response.status_code == 200
    assert conn.character["advancement"]["points_available"] == 0
    assert conn.character["reputation"][0]["standing"] == 5


@pytest.mark.contract
def test_failed_arc_settlement_applies_non_ap_rewards() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start_in_progress(client)
        stored = next(row for row in conn.rows if row["id"] == arc["id"])
        data = __import__("json").loads(stored["data"])
        data["rewards"]["reputation"]["max_negative_delta"] = 10
        stored["data"] = __import__("json").dumps(data)
        response = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "failed", "reputation_changes": [{"faction": "House Heartwood", "delta": -5}]})
    assert response.status_code == 200
    assert conn.character["reputation"][0]["standing"] == -5


@pytest.mark.contract
def test_settle_response_includes_consequence_events() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start_ready(client)
        response = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete", "awarded_ap": 1})
    body = response.json()
    assert body["consequence_events"] == [f"ap_awarded:arc={arc['id']}:amount=1"]
    assert body["arc"]["consequence_events_emitted"] == body["consequence_events"]


@pytest.mark.contract
def test_settle_response_indicates_character_updated() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start_ready(client)
        response = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete", "awarded_ap": 1})
    assert response.json()["character_updated"] is True
    assert response.json()["world_updated"] is True


@pytest.mark.contract
def test_settle_with_no_rewards_still_terminal_states_arc() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_start_ready(client)
        response = client.post(f"/arc/sess-settle/{arc['id']}/settle", json={"outcome": "complete"})
    assert response.status_code == 200
    assert response.json()["arc"]["state"] == "complete"
    assert response.json()["arc"]["settlement"]["awarded_ap"] == 0


@pytest.mark.contract
def test_settle_parent_with_unsettled_formal_child_rejected() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        parent = _create_start_in_progress(client, session_id="sess-settle")
        child_resp = client.post(f"/arc/sess-settle/{parent['id']}/spawn", json={"child_title": "Child", "child_summary": "Child arc", "child_primary_type": "task_local", "child_subtype": "investigation", "child_stake_scale": "local", "child_formal_contract_qualified": True, "child_patron_npc_id": "npc", "child_explicit_objective": "do", "child_expected_return": "report", "ap_ownership": "child", "reason": "split"})
        assert child_resp.status_code == 200
        client.post(f"/arc/sess-settle/{parent['id']}/transition", json={"from_state": "in_progress", "to_state": "ready_to_close", "reason": "ready"})
        response = client.post(f"/arc/sess-settle/{parent['id']}/settle", json={"outcome": "complete"})
    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "child_ap_unsettled"


@pytest.mark.contract
def test_settle_child_first_then_parent_succeeds() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        parent = _create_start_in_progress(client, session_id="sess-settle")
        child = client.post(f"/arc/sess-settle/{parent['id']}/spawn", json={"child_title": "Child", "child_summary": "Child arc", "child_primary_type": "task_local", "child_subtype": "investigation", "child_stake_scale": "local", "child_formal_contract_qualified": True, "child_patron_npc_id": "npc", "child_explicit_objective": "do", "child_expected_return": "report", "ap_ownership": "child", "reason": "split"}).json()
        stored_child = next(row for row in conn.rows if row["id"] == child["id"])
        child_data = __import__("json").loads(stored_child["data"])
        child_data["closure_conditions"] = {"all_of": [{"type": "resolved_scene_count_at_least", "payload": {"count": 0}}], "any_of": [], "none_of": []}
        stored_child["data"] = __import__("json").dumps(child_data)
        for from_state, to_state in [("proposed", "available"), ("available", "in_progress"), ("in_progress", "ready_to_close")]:
            assert client.post(f"/arc/sess-settle/{child['id']}/transition", json={"from_state": from_state, "to_state": to_state, "reason": "advance"}).status_code == 200
        assert client.post(f"/arc/sess-settle/{child['id']}/settle", json={"outcome": "complete", "awarded_ap": 1}).status_code == 200
        assert client.post(f"/arc/sess-settle/{parent['id']}/transition", json={"from_state": "in_progress", "to_state": "ready_to_close", "reason": "ready"}).status_code == 200
        response = client.post(f"/arc/sess-settle/{parent['id']}/settle", json={"outcome": "complete"})
    assert response.status_code == 200