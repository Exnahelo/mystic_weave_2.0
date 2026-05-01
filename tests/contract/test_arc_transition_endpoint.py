from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.repositories.arc_repository import ArcRepository
from api.routes import arc as arc_routes


class _AcquireCtx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return None


class FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _AcquireCtx(self._conn)


class ArcTransitionConn:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.transitions: list[dict] = []

    async def execute(self, query, *args):
        if "INSERT INTO arcs" in query:
            self.rows.append({"id": args[0], "session_id": args[1], "state": args[3], "data": args[5]})
        elif "UPDATE arcs" in query:
            for row in self.rows:
                if row["id"] == args[3]:
                    row["state"] = args[0]
                    row["data"] = args[1]
                    break
        elif "INSERT INTO arc_transitions" in query:
            self.transitions.append(
                {
                    "arc_id": args[0],
                    "session_id": args[1],
                    "from_state": args[2],
                    "to_state": args[3],
                    "reason": args[4],
                    "transitioned_at": args[5],
                    "resolved_scenes_at_transition": args[6],
                    "locations_visited_at_transition": args[7],
                    "triggering_event": args[8],
                }
            )
        return "OK"

    async def fetchrow(self, query, *args):
        if "WHERE session_id = $1 AND id = $2" in query:
            for row in self.rows:
                if row["session_id"] == args[0] and row["id"] == args[1]:
                    return {"data": row["data"]}
        if "WHERE id = $1" in query:
            for row in self.rows:
                if row["id"] == args[0]:
                    return {"data": row["data"]}
        return None

    async def fetch(self, query, *args):
        if "FROM arc_transitions" in query:
            return [
                entry for entry in self.transitions
                if entry["arc_id"] == args[0]
            ]
        return []


def _make_app(conn: ArcTransitionConn) -> FastAPI:
    app = FastAPI()
    app.include_router(arc_routes.router)
    app.dependency_overrides[get_pool] = lambda: FakePool(conn)
    return app


def _payload() -> dict[str, object]:
    return {
        "title": "Transition Arc",
        "summary": "A test arc.",
        "primary_type": "mission_multi_leg",
        "subtype": "investigation",
        "stake_scale": "situational",
        "origin_type": "emergent",
    }


def _create(client: TestClient, session_id: str = "sess-transition") -> dict:
    response = client.post(f"/arc/{session_id}/create", json=_payload())
    assert response.status_code == 200
    return response.json()


def _transition(client: TestClient, arc_id: str, from_state: str, to_state: str, session_id: str = "sess-transition"):
    return client.post(
        f"/arc/{session_id}/{arc_id}/transition",
        json={"from_state": from_state, "to_state": to_state, "reason": f"{from_state}->{to_state}"},
    )


@pytest.mark.contract
def test_transition_happy_path_proposed_to_available_writes_audit_log() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create(client)
        response = _transition(client, arc["id"], "proposed", "available")

    assert response.status_code == 200
    assert response.json()["state"] == "available"
    assert len(conn.transitions) == 1
    assert conn.transitions[0]["from_state"] == "proposed"
    assert conn.transitions[0]["to_state"] == "available"


@pytest.mark.contract
def test_transition_happy_path_full_lifecycle_logs_each_step() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create(client)
        for from_state, to_state in [
            ("proposed", "available"),
            ("available", "in_progress"),
            ("in_progress", "ready_to_close"),
            ("ready_to_close", "complete"),
        ]:
            response = _transition(client, arc["id"], from_state, to_state)
            assert response.status_code == 200

    assert [t["to_state"] for t in conn.transitions] == ["available", "in_progress", "ready_to_close", "complete"]


@pytest.mark.contract
def test_transition_stale_from_state_rejected() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create(client)
        response = _transition(client, arc["id"], "in_progress", "ready_to_close")

    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "stale_from_state"


@pytest.mark.contract
def test_transition_illegal_backwards_rejected_with_allowed_transitions() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create(client)
        assert _transition(client, arc["id"], "proposed", "available").status_code == 200
        assert _transition(client, arc["id"], "available", "in_progress").status_code == 200
        response = _transition(client, arc["id"], "in_progress", "proposed")

    assert response.status_code == 422
    assert "allowed_transitions" in response.json()["detail"]


@pytest.mark.contract
def test_transition_illegal_skip_state_rejected() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create(client)
        response = _transition(client, arc["id"], "proposed", "complete")

    assert response.status_code == 422


@pytest.mark.contract
def test_transition_from_terminal_rejected() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create(client)
        for from_state, to_state in [("proposed", "available"), ("available", "in_progress"), ("in_progress", "ready_to_close"), ("ready_to_close", "complete")]:
            assert _transition(client, arc["id"], from_state, to_state).status_code == 200
        response = _transition(client, arc["id"], "complete", "in_progress")

    assert response.status_code == 422


@pytest.mark.contract
def test_transition_audit_log_persisted_fetchable_via_repo() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create(client)
        assert _transition(client, arc["id"], "proposed", "available").status_code == 200

    import asyncio
    log = asyncio.run(ArcRepository(FakePool(conn)).get_transition_log(arc["id"]))
    assert len(log) == 1
    assert log[0].from_state == "proposed"
    assert log[0].to_state == "available"


@pytest.mark.contract
def test_transition_multiple_logs_in_order() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create(client)
        for from_state, to_state in [("proposed", "available"), ("available", "in_progress"), ("in_progress", "ready_to_close"), ("ready_to_close", "complete")]:
            assert _transition(client, arc["id"], from_state, to_state).status_code == 200

    assert [entry["from_state"] for entry in conn.transitions] == ["proposed", "available", "in_progress", "ready_to_close"]


@pytest.mark.contract
def test_transition_closed_at_timestamp_set_on_terminal() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create(client)
        for from_state, to_state in [("proposed", "available"), ("available", "in_progress"), ("in_progress", "ready_to_close"), ("ready_to_close", "complete")]:
            response = _transition(client, arc["id"], from_state, to_state)

    assert response.json()["timestamps"]["closed_at"] is not None


@pytest.mark.contract
def test_transition_closed_at_not_set_on_non_terminal() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create(client)
        assert _transition(client, arc["id"], "proposed", "available").status_code == 200
        response = _transition(client, arc["id"], "available", "in_progress")

    assert response.json()["timestamps"]["closed_at"] is None


@pytest.mark.contract
def test_transition_arc_not_found() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        response = _transition(client, "arc-missing", "proposed", "available")

    assert response.status_code == 404


@pytest.mark.contract
def test_transition_wrong_session_returns_404() -> None:
    conn = ArcTransitionConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        arc = _create(client, session_id="session-a")
        response = _transition(client, arc["id"], "proposed", "available", session_id="session-b")

    assert response.status_code == 404