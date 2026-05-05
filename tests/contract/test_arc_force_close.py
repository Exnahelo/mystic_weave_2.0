"""Tests for POST /arc/{session_id}/{arc_id}/force_close — admin escape hatch."""
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


def _payload(formal: bool = True) -> dict:
    payload: dict = {
        "title": "Force close target",
        "summary": "Test arc for force_close validation.",
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


def _create_in_progress(client: TestClient, session_id: str = "sess-fc", formal: bool = True) -> dict:
    arc = client.post(f"/arc/{session_id}/create", json=_payload(formal)).json()
    for from_state, to_state in [("proposed", "available"), ("available", "in_progress")]:
        response = client.post(
            f"/arc/{session_id}/{arc['id']}/transition",
            json={"from_state": from_state, "to_state": to_state, "reason": "advance"},
        )
        assert response.status_code == 200, response.text
    return arc


@pytest.mark.contract
def test_force_close_complete_bypasses_condition_evaluation() -> None:
    """An in_progress arc force-closes to complete without ready_to_close."""
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_in_progress(client)
        response = client.post(
            f"/arc/sess-fc/{arc['id']}/force_close",
            json={
                "reason": "stuck arc with invalid closure conditions",
                "outcome": "complete",
                "awarded_ap": 0,
            },
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["arc"]["state"] == "complete"
    assert body["arc"]["timestamps"]["closed_at"] is not None
    assert conn.transitions[-1]["triggering_event"] == "force_close"


@pytest.mark.contract
def test_force_close_records_admin_correction_log_entry() -> None:
    """force_close records a TypedLogEntry of type=admin_correction with
    the reason text, prefixed with [operational_constraint]."""
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_in_progress(client)
        response = client.post(
            f"/arc/sess-fc/{arc['id']}/force_close",
            json={
                "reason": "registry drift left arc unreachable",
                "outcome": "complete",
            },
        )
    assert response.status_code == 200, response.text
    admin_entries = [e for e in conn.log if e.get("type") == "admin_correction"]
    assert len(admin_entries) == 1, f"expected one admin_correction, got {conn.log}"
    text = admin_entries[0]["text"]
    assert "operational_constraint" in text
    assert "registry drift left arc unreachable" in text
    assert arc["id"] in text


@pytest.mark.contract
def test_force_close_failed_outcome() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_in_progress(client)
        response = client.post(
            f"/arc/sess-fc/{arc['id']}/force_close",
            json={"reason": "narrator-side abandonment of failed work", "outcome": "failed"},
        )
    assert response.status_code == 200, response.text
    assert response.json()["arc"]["state"] == "failed"


@pytest.mark.contract
def test_force_close_abandoned_skips_settlement() -> None:
    """Abandoned outcome transitions arc without producing a closure_summary."""
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_in_progress(client)
        response = client.post(
            f"/arc/sess-fc/{arc['id']}/force_close",
            json={"reason": "player disengaged from this thread entirely", "outcome": "abandoned"},
        )
    assert response.status_code == 200, response.text
    assert response.json()["arc"]["state"] == "abandoned"
    closure_entries = [e for e in conn.log if e.get("type") == "closure_summary"]
    assert len(closure_entries) == 0, "abandoned should not produce closure_summary"


@pytest.mark.contract
def test_force_close_rejects_short_reason() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_in_progress(client)
        response = client.post(
            f"/arc/sess-fc/{arc['id']}/force_close",
            json={"reason": "short", "outcome": "complete"},
        )
    assert response.status_code == 422


@pytest.mark.contract
def test_force_close_rejects_terminal_arc() -> None:
    """An already-terminal arc cannot be force-closed again."""
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_in_progress(client)
        first = client.post(
            f"/arc/sess-fc/{arc['id']}/force_close",
            json={"reason": "first force_close call to set terminal state", "outcome": "complete"},
        )
        assert first.status_code == 200
        second = client.post(
            f"/arc/sess-fc/{arc['id']}/force_close",
            json={"reason": "second call should be rejected because terminal", "outcome": "failed"},
        )
    assert second.status_code == 409


@pytest.mark.contract
def test_force_close_failed_with_ap_rejected() -> None:
    """Failed outcome cannot award AP, same policy as /settle."""
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create_in_progress(client)
        response = client.post(
            f"/arc/sess-fc/{arc['id']}/force_close",
            json={"reason": "mismatched ap on failed force_close", "outcome": "failed", "awarded_ap": 1},
        )
    assert response.status_code == 422
    assert "ap_on_failure_not_allowed" in response.text
