from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import arc as arc_routes
from tests.contract.test_arc_transition_endpoint import ArcTransitionConn, FakePool


def _make_app(conn: ArcTransitionConn) -> FastAPI:
    app = FastAPI()
    app.include_router(arc_routes.router)
    app.dependency_overrides[get_pool] = lambda: FakePool(conn)
    return app


def _payload() -> dict[str, object]:
    return {
        "title": "Progress Arc",
        "summary": "A test arc.",
        "primary_type": "mission_multi_leg",
        "subtype": "investigation",
        "stake_scale": "situational",
        "origin_type": "emergent",
        "closure_conditions": {"all_of": [{"type": "resolved_scene_count_at_least", "payload": {"count": 0}}]},
    }


def _create_and_start(client: TestClient, session_id: str = "sess-progress") -> dict:
    created = client.post(f"/arc/{session_id}/create", json=_payload())
    assert created.status_code == 200
    arc = created.json()
    for from_state, to_state in [("proposed", "available"), ("available", "in_progress")]:
        response = client.post(
            f"/arc/{session_id}/{arc['id']}/transition",
            json={"from_state": from_state, "to_state": to_state, "reason": "start"},
        )
        assert response.status_code == 200
    return arc


def _progress(client: TestClient, arc_id: str, payload: dict[str, object] | None = None, session_id: str = "sess-progress"):
    return client.post(f"/arc/{session_id}/{arc_id}/progress", json=payload or {})


@pytest.mark.contract
def test_progress_happy_path_single_progress() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create_and_start(client)
        response = _progress(client, arc["id"])

    assert response.status_code == 200
    body = response.json()
    assert body["arc"]["consumption"]["resolved_scenes_used"] == 1
    assert body["warning"] is None


@pytest.mark.contract
def test_progress_soft_cap_warning() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create_and_start(client)
        for _ in range(6):
            response = _progress(client, arc["id"])

    assert response.json()["soft_cap_reached"] is True
    assert "Soft scope cap" in response.json()["warning"]


@pytest.mark.contract
def test_progress_hard_cap_auto_transition() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create_and_start(client)
        for _ in range(10):
            response = _progress(client, arc["id"])

    body = response.json()
    assert body["hard_cap_reached"] is True
    assert body["auto_transitioned_to_at_scope_cap"] is True
    assert body["arc"]["state"] == "at_scope_cap"
    assert conn.transitions[-1]["triggering_event"] == "progress_call"
    assert "Hard cap reached" in conn.transitions[-1]["reason"]


@pytest.mark.contract
def test_progress_refused_at_scope_cap() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create_and_start(client)
        for _ in range(10):
            assert _progress(client, arc["id"]).status_code == 200
        response = _progress(client, arc["id"])

    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "arc_at_scope_cap"


@pytest.mark.contract
def test_progress_refused_on_non_active_state() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        created = client.post("/arc/sess-progress/create", json=_payload()).json()
        response = _progress(client, created["id"])

    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "arc_not_in_progress"


@pytest.mark.contract
def test_progress_refused_after_complete() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create_and_start(client)
        for from_state, to_state in [("in_progress", "ready_to_close"), ("ready_to_close", "complete")]:
            assert client.post(f"/arc/sess-progress/{arc['id']}/transition", json={"from_state": from_state, "to_state": to_state, "reason": "close"}).status_code == 200
        response = _progress(client, arc["id"])

    assert response.status_code == 409


@pytest.mark.contract
def test_progress_location_accumulation_unique_only() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create_and_start(client)
        _progress(client, arc["id"], {"location_id": "A"})
        _progress(client, arc["id"], {"location_id": "A"})
        response = _progress(client, arc["id"], {"location_id": "B"})

    assert response.json()["arc"]["consumption"]["locations_visited"] == ["A", "B"]


@pytest.mark.contract
def test_progress_location_hard_cap_auto_transitions() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create_and_start(client)
        for idx in range(5):
            response = _progress(client, arc["id"], {"location_id": f"loc-{idx}"})

    assert response.json()["auto_transitioned_to_at_scope_cap"] is True
    assert response.json()["arc"]["state"] == "at_scope_cap"


@pytest.mark.contract
def test_progress_resolved_scene_optional() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create_and_start(client)
        response = _progress(client, arc["id"], {"resolved_scene_occurred": False})

    assert response.json()["arc"]["consumption"]["resolved_scenes_used"] == 0


@pytest.mark.contract
def test_progress_discoveries_and_major_conflicts_tracked() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create_and_start(client)
        response = _progress(client, arc["id"], {"discovery_logged": True, "major_conflict_resolved": True})

    consumption = response.json()["arc"]["consumption"]
    assert consumption["discoveries_logged"] == 1
    assert consumption["major_conflicts_resolved"] == 1


@pytest.mark.contract
def test_progress_last_progressed_at_updated() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create_and_start(client)
        response = _progress(client, arc["id"])

    assert response.json()["arc"]["timestamps"]["last_progressed_at"] is not None


@pytest.mark.contract
def test_progress_arc_not_found() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        response = _progress(client, "arc-missing")

    assert response.status_code == 404