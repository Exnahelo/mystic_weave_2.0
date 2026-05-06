from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.models import Arc
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


class ArcRouteConn:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    async def execute(self, query, *args):
        if "INSERT INTO arcs" in query:
            self.rows.append(
                {
                    "id": args[0],
                    "session_id": args[1],
                    "primary_type": args[2],
                    "state": args[3],
                    "parent_arc_id": args[4],
                    "data": args[5] if isinstance(args[5], dict) else json.loads(args[5]),
                    "created_at": args[6],
                }
            )
        return "OK"

    async def fetchrow(self, query, *args):
        if "WHERE session_id = $1 AND id = $2" in query:
            for row in self.rows:
                if row["session_id"] == args[0] and row["id"] == args[1]:
                    return {"data": row["data"]}
        return None

    async def fetch(self, query, *args):
        if "state IN ('in_progress', 'at_scope_cap')" in query:
            return [
                {"data": row["data"]}
                for row in self.rows
                if row["session_id"] == args[0] and row["state"] in {"in_progress", "at_scope_cap"}
            ]
        if "WHERE session_id = $1" in query:
            return [
                {"data": row["data"]}
                for row in self.rows
                if row["session_id"] == args[0]
            ]
        return []


def _make_app(conn: ArcRouteConn) -> FastAPI:
    app = FastAPI()
    app.include_router(arc_routes.router)
    app.dependency_overrides[get_pool] = lambda: FakePool(conn)
    return app


def _payload(title: str = "Arc") -> dict[str, object]:
    return {
        "title": title,
        "summary": "A test arc.",
        "primary_type": "task_local",
        "subtype": "investigation",
        "stake_scale": "local",
        "origin_type": "emergent",
    }


def _create(client: TestClient, session_id: str = "sess-read", title: str = "Arc") -> dict:
    response = client.post(f"/arc/{session_id}/create", json=_payload(title))
    assert response.status_code == 200
    return response.json()


def _set_row_state(conn: ArcRouteConn, arc_id: str, state: str) -> None:
    for row in conn.rows:
        if row["id"] == arc_id:
            row["state"] = state
            data = row["data"]  # codec stores parsed dict
            data["state"] = state
            row["data"] = Arc.model_validate(data).model_dump()
            return
    raise AssertionError(f"arc row not found: {arc_id}")


@pytest.mark.contract
def test_get_single_arc_found() -> None:
    conn = ArcRouteConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        created = _create(client)
        response = client.get(f"/arc/sess-read/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


@pytest.mark.contract
def test_get_single_arc_not_found() -> None:
    conn = ArcRouteConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        response = client.get("/arc/sess-read/arc-missing")

    assert response.status_code == 404


@pytest.mark.contract
def test_get_single_arc_wrong_session_returns_404() -> None:
    conn = ArcRouteConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        created = _create(client, session_id="session-a")
        response = client.get(f"/arc/session-b/{created['id']}")

    assert response.status_code == 404


@pytest.mark.contract
def test_get_list_empty_session() -> None:
    conn = ArcRouteConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        response = client.get("/arc/empty-session")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.contract
def test_get_list_multiple_arcs() -> None:
    conn = ArcRouteConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        _create(client, title="Arc 1")
        _create(client, title="Arc 2")
        _create(client, title="Arc 3")
        response = client.get("/arc/sess-read")

    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.contract
def test_get_list_returns_arcs_with_valid_log_entries() -> None:
    """GET /arc/{session_id} returns 200 for arcs whose log[] contains
    entries with all valid source values ('progress' and 'transition').

    Brief A regression guard: a manual JSON patch in the 2026-05-05 Phase 9b
    session injected source='settlement_correction' into one arc, causing
    GET /arc/{session_id} to 500 on Arc model validation. The schema's
    literal union is the contract; this test pins the happy path.
    """
    conn = ArcRouteConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        created = _create(client, session_id="sess-log", title="Logged Arc")
        for row in conn.rows:
            if row["id"] == created["id"]:
                data = dict(row["data"])
                data["log"] = [
                    {
                        "text": "first beat",
                        "timestamp": datetime(2026, 5, 5, 12, 0, tzinfo=timezone.utc).isoformat(),
                        "source": "progress",
                    },
                    {
                        "text": "state moved to in_progress",
                        "timestamp": datetime(2026, 5, 5, 12, 5, tzinfo=timezone.utc).isoformat(),
                        "source": "transition",
                    },
                ]
                row["data"] = Arc.model_validate(data).model_dump(mode="json")
                break

        response = client.get("/arc/sess-log")

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 1
    log = body[0]["log"]
    assert [entry["source"] for entry in log] == ["progress", "transition"]


@pytest.mark.contract
def test_get_active_filters_correctly() -> None:
    conn = ArcRouteConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        proposed = _create(client, title="Proposed")
        active = _create(client, title="Active")
        _set_row_state(conn, active["id"], "in_progress")
        response = client.get("/arc/sess-read/active")

    assert response.status_code == 200
    body = response.json()
    assert [arc["id"] for arc in body] == [active["id"]]
    assert proposed["id"] not in [arc["id"] for arc in body]