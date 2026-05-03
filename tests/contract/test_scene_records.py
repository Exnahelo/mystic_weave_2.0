"""Contract tests for /scene/declare_resolution and scene record reads (Brief 19)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import scene_records as scene_records_routes


# ---------------------------------------------------------------------------
# Async-context scaffolding
# ---------------------------------------------------------------------------

class _AcquireCtx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return None


class _TxCtx:
    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return None


class FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _AcquireCtx(self._conn)


# ---------------------------------------------------------------------------
# Fake conn — pattern-matches the SQL in api/routes/scene_records.py
# ---------------------------------------------------------------------------

class SceneConn:
    """Stub backing scene_records routes.

    Backs three tables with in-memory dicts: game_states (session_id -> world),
    arcs (id -> {session_id, state, data}), scene_records (scene_id -> row).
    """

    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}  # session_id -> world dict
        self.arcs: dict[str, dict[str, Any]] = {}      # arc_id -> {session_id, state, data}
        self.records: dict[str, dict[str, Any]] = {}   # scene_id -> row dict
        self._monotonic = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)

    def _next_ts(self) -> datetime:
        self._monotonic += timedelta(seconds=1)
        return self._monotonic

    def add_session(self, session_id: str, world: dict[str, Any]) -> None:
        self.sessions[session_id] = world

    def add_arc(self, arc_id: str, session_id: str, state: str, data: dict[str, Any]) -> None:
        self.arcs[arc_id] = {"session_id": session_id, "state": state, "data": data}

    def add_record(self, **row: Any) -> None:
        row.setdefault("resolved_at", self._next_ts())
        row.setdefault("scene_summary", None)
        row.setdefault("scene_actions", [])
        row.setdefault("tag_advance_committed", None)
        row.setdefault("arc_progressed_ids", [])
        row.setdefault("location_id", None)
        row.setdefault("turn_at_resolution", None)
        row.setdefault("time_at_resolution", None)
        self.records[row["scene_id"]] = row

    def transaction(self):
        return _TxCtx()

    async def fetchrow(self, query: str, *args):
        if "SELECT world FROM game_states" in query:
            world = self.sessions.get(args[0])
            if world is None:
                return None
            return {"world": json.dumps(world)}

        if "SELECT resolved_at FROM scene_records WHERE scene_id" in query:
            row = self.records.get(args[0])
            if row is None:
                return None
            return {"resolved_at": row["resolved_at"]}

        if (
            "SELECT scene_id, session_id, resolved_at" in query
            and "scene_id = $2" in query
        ):
            row = self.records.get(args[1])
            if row is None or row["session_id"] != args[0]:
                return None
            return self._row_with_strings(row)

        if "SELECT COUNT(*)" in query and "arc_progressed_ids @>" in query:
            session_id = args[0]
            target_arc_ids = json.loads(args[1])  # always a single-id list
            scene_count = 0
            distinct_locs: set[str] = set()
            for r in self.records.values():
                if r["session_id"] != session_id:
                    continue
                if all(aid in (r["arc_progressed_ids"] or []) for aid in target_arc_ids):
                    scene_count += 1
                    if r.get("location_id"):
                        distinct_locs.add(r["location_id"])
            return {"scene_count": scene_count, "loc_count": len(distinct_locs)}

        return None

    async def fetch(self, query: str, *args):
        if "SELECT id FROM arcs" in query and "ANY($2::text[])" in query:
            session_id = args[0]
            ids = list(args[1])
            return [
                {"id": arc_id}
                for arc_id, info in self.arcs.items()
                if info["session_id"] == session_id and arc_id in ids
            ]

        if "SELECT id, data FROM arcs" in query and "state = 'in_progress'" in query:
            session_id = args[0]
            return [
                {"id": arc_id, "data": json.dumps(info["data"])}
                for arc_id, info in self.arcs.items()
                if info["session_id"] == session_id and info["state"] == "in_progress"
            ]

        if (
            "SELECT scene_id, session_id, resolved_at" in query
            and "scene_records" in query
            and "ORDER BY resolved_at DESC" in query
        ):
            session_id = args[0]
            cursor = None
            limit = args[-1]
            if "resolved_at < $2::timestamptz" in query:
                cursor = args[1]
                if isinstance(cursor, str):
                    cursor = datetime.fromisoformat(cursor)
            rows = sorted(
                (r for r in self.records.values() if r["session_id"] == session_id),
                key=lambda r: r["resolved_at"],
                reverse=True,
            )
            if cursor is not None:
                rows = [r for r in rows if r["resolved_at"] < cursor]
            rows = rows[:limit]
            return [self._row_with_strings(r) for r in rows]

        return []

    async def execute(self, query: str, *args):
        if "INSERT INTO scene_records" in query:
            self.records[args[0]] = {
                "scene_id": args[0],
                "session_id": args[1],
                "scene_summary": args[2],
                "scene_actions": json.loads(args[3]) if isinstance(args[3], str) else args[3],
                "arc_progressed_ids": json.loads(args[4]) if isinstance(args[4], str) else args[4],
                "location_id": args[5],
                "turn_at_resolution": args[6],
                "time_at_resolution": (
                    json.loads(args[7]) if isinstance(args[7], str) and args[7] else None
                ),
                "tag_advance_committed": None,
                "resolved_at": self._next_ts(),
            }
            return "INSERT 0 1"
        return None

    @staticmethod
    def _row_with_strings(row: dict[str, Any]) -> dict[str, Any]:
        """Mimic asyncpg returning JSONB columns as strings."""
        return {
            "scene_id": row["scene_id"],
            "session_id": row["session_id"],
            "resolved_at": row["resolved_at"],
            "scene_summary": row.get("scene_summary"),
            "scene_actions": json.dumps(row.get("scene_actions") or []),
            "tag_advance_committed": row.get("tag_advance_committed"),
            "arc_progressed_ids": json.dumps(row.get("arc_progressed_ids") or []),
            "location_id": row.get("location_id"),
            "turn_at_resolution": row.get("turn_at_resolution"),
            "time_at_resolution": (
                json.dumps(row["time_at_resolution"]) if row.get("time_at_resolution") else None
            ),
        }


def _make_app(conn: SceneConn) -> FastAPI:
    app = FastAPI()
    app.include_router(scene_records_routes.router)
    app.dependency_overrides[get_pool] = lambda: FakePool(conn)
    return app


def _world(location: str = "feywood-river-bend", turn: int = 4) -> dict[str, Any]:
    return {
        "location": location,
        "threat": "low",
        "goal": "patrol the bend",
        "turn": turn,
        "time": {"day": 1, "month": "Verdantrise", "year": 847, "time_of_day": "morning"},
        "companions": [],
        "companion_archive": [],
        "economy": {"wealth_tier": "modest", "coin": 0, "trade_goods": [], "obligations": []},
        "politics": {
            "faction_memberships": [], "active_obligations": [],
            "legal_standing": "unknown", "known_leverage": [],
            "active_tensions": [], "conclave_status": "unknown",
        },
        "survival": {"hunger": "sated", "hydration": "hydrated", "fatigue": "rested", "load": "normal"},
        "pacing": {
            "tension": 3, "last_consequence_weight": "local",
            "turns_since_social_beat": 0, "turns_since_discovery": 0, "turn_count": turn,
        },
    }


def _arc_data(title: str, *, soft: int = 4, hard: int = 6) -> dict[str, Any]:
    return {
        "title": title,
        "state": "in_progress",
        "budget": {
            "resolved_scene_soft_cap": soft,
            "resolved_scene_hard_cap": hard,
            "location_soft_cap": 3,
            "location_hard_cap": 5,
        },
    }


# ---------------------------------------------------------------------------
# /scene/declare_resolution
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_declare_resolution_creates_record() -> None:
    conn = SceneConn()
    conn.add_session("sess1", _world())
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/scene/declare_resolution",
            json={"session_id": "sess1", "scene_summary": "Brookside containment."},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["scene_id"]
    assert body["session_id"] == "sess1"
    assert body["resolved_at"]
    # The scene record was persisted in our fake store.
    assert body["scene_id"] in conn.records
    stored = conn.records[body["scene_id"]]
    assert stored["scene_summary"] == "Brookside containment."


@pytest.mark.contract
def test_declare_resolution_returns_scene_id_uuid() -> None:
    conn = SceneConn()
    conn.add_session("sess1", _world())
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post("/scene/declare_resolution", json={"session_id": "sess1"})

    sid = r.json()["scene_id"]
    # Validates as UUID4 (non-raising).
    uuid.UUID(sid, version=4)


@pytest.mark.contract
def test_declare_resolution_records_scene_actions() -> None:
    conn = SceneConn()
    conn.add_session("sess1", _world())
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/scene/declare_resolution",
            json={
                "session_id": "sess1",
                "scene_actions": [
                    {"type": "spell_cast", "spell": "seedwake", "outcome": "success"},
                    {"type": "perception_roll", "application": "spoor_reading", "outcome": "partial"},
                ],
            },
        )

    assert r.status_code == 200
    stored_actions = conn.records[r.json()["scene_id"]]["scene_actions"]
    assert len(stored_actions) == 2
    assert stored_actions[0]["type"] == "spell_cast"
    assert stored_actions[0]["spell"] == "seedwake"
    assert stored_actions[1]["type"] == "perception_roll"


@pytest.mark.contract
def test_declare_resolution_validates_arc_ids() -> None:
    conn = SceneConn()
    conn.add_session("sess1", _world())
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/scene/declare_resolution",
            json={"session_id": "sess1", "arc_progressed_ids": ["arc-not-real"]},
        )

    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["error"] == "unknown_arc_ids"
    assert detail["unknown_arc_ids"] == ["arc-not-real"]


@pytest.mark.contract
def test_declare_resolution_uses_world_location_when_omitted() -> None:
    conn = SceneConn()
    conn.add_session("sess1", _world(location="feywood-vault"))
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post("/scene/declare_resolution", json={"session_id": "sess1"})

    assert r.status_code == 200
    body = r.json()
    assert body["location_id"] == "feywood-vault"
    assert body["turn_at_resolution"] == 4


@pytest.mark.contract
def test_declare_resolution_uses_provided_location_when_given() -> None:
    conn = SceneConn()
    conn.add_session("sess1", _world(location="feywood-vault"))
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/scene/declare_resolution",
            json={"session_id": "sess1", "location_id": "feywood-overlook"},
        )

    assert r.status_code == 200
    assert r.json()["location_id"] == "feywood-overlook"


@pytest.mark.contract
def test_declare_resolution_404_unknown_session() -> None:
    conn = SceneConn()
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post("/scene/declare_resolution", json={"session_id": "missing"})

    assert r.status_code == 404


@pytest.mark.contract
def test_declare_resolution_envelope_counts_scenes_for_progressed_arcs() -> None:
    conn = SceneConn()
    conn.add_session("sess1", _world())
    conn.add_arc("arc-A", "sess1", "in_progress", _arc_data("Patrol the bend", soft=4, hard=6))
    # Pre-existing scene records that contributed to arc-A
    for i in range(2):
        conn.add_record(
            scene_id=f"prior-{i}", session_id="sess1",
            arc_progressed_ids=["arc-A"], location_id=f"loc-{i}",
        )
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/scene/declare_resolution",
            json={"session_id": "sess1", "arc_progressed_ids": ["arc-A"], "location_id": "loc-X"},
        )

    assert r.status_code == 200
    statuses = r.json()["arc_envelope_status"]
    arc_a = next(s for s in statuses if s["arc_id"] == "arc-A")
    # 2 prior + 1 just-declared
    assert arc_a["resolved_scenes_used"] == 3
    assert arc_a["soft_cap_approaching"] is False
    assert arc_a["hard_cap_reached"] is False


@pytest.mark.contract
def test_declare_resolution_suggests_at_soft_cap() -> None:
    conn = SceneConn()
    conn.add_session("sess1", _world())
    conn.add_arc("arc-A", "sess1", "in_progress", _arc_data("Patrol", soft=2, hard=4))
    conn.add_record(scene_id="prior-0", session_id="sess1", arc_progressed_ids=["arc-A"])
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/scene/declare_resolution",
            json={"session_id": "sess1", "arc_progressed_ids": ["arc-A"]},
        )

    body = r.json()
    arc_a = next(s for s in body["arc_envelope_status"] if s["arc_id"] == "arc-A")
    assert arc_a["resolved_scenes_used"] == 2
    assert arc_a["soft_cap_approaching"] is True
    assert arc_a["hard_cap_reached"] is False
    assert any("soft cap" in s for s in body["suggestions"])


@pytest.mark.contract
def test_declare_resolution_suggests_at_hard_cap() -> None:
    conn = SceneConn()
    conn.add_session("sess1", _world())
    conn.add_arc("arc-A", "sess1", "in_progress", _arc_data("Patrol", soft=2, hard=4))
    for i in range(3):
        conn.add_record(scene_id=f"prior-{i}", session_id="sess1", arc_progressed_ids=["arc-A"])
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/scene/declare_resolution",
            json={"session_id": "sess1", "arc_progressed_ids": ["arc-A"]},
        )

    body = r.json()
    arc_a = next(s for s in body["arc_envelope_status"] if s["arc_id"] == "arc-A")
    assert arc_a["resolved_scenes_used"] == 4
    assert arc_a["hard_cap_reached"] is True
    assert any("hard cap" in s for s in body["suggestions"])


@pytest.mark.contract
def test_declare_resolution_no_suggestions_when_under_soft_cap() -> None:
    conn = SceneConn()
    conn.add_session("sess1", _world())
    conn.add_arc("arc-A", "sess1", "in_progress", _arc_data("Patrol", soft=4, hard=6))
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/scene/declare_resolution",
            json={"session_id": "sess1", "arc_progressed_ids": ["arc-A"]},
        )

    body = r.json()
    assert body["suggestions"] == []
    arc_a = next(s for s in body["arc_envelope_status"] if s["arc_id"] == "arc-A")
    assert arc_a["soft_cap_approaching"] is False
    assert arc_a["hard_cap_reached"] is False


# ---------------------------------------------------------------------------
# GET /scene/record/{session_id}/{scene_id}
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_get_scene_record_returns_full_record() -> None:
    conn = SceneConn()
    conn.add_record(
        scene_id="scene-1", session_id="sess1",
        scene_summary="The hush at the brook",
        scene_actions=[{"type": "spell_cast", "spell": "seedwake", "outcome": "success"}],
        arc_progressed_ids=["arc-A"],
        location_id="feywood-river-bend",
        turn_at_resolution=4,
    )
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.get("/scene/record/sess1/scene-1")

    assert r.status_code == 200
    body = r.json()
    assert body["scene_id"] == "scene-1"
    assert body["scene_summary"] == "The hush at the brook"
    assert body["arc_progressed_ids"] == ["arc-A"]
    assert body["location_id"] == "feywood-river-bend"


@pytest.mark.contract
def test_get_scene_record_404_unknown_id() -> None:
    conn = SceneConn()
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.get("/scene/record/sess1/nope")

    assert r.status_code == 404


@pytest.mark.contract
def test_list_scene_records_paginated() -> None:
    conn = SceneConn()
    for i in range(5):
        conn.add_record(scene_id=f"s{i}", session_id="sess1")
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.get("/scene/records/sess1", params={"limit": 2})

    assert r.status_code == 200
    body = r.json()
    assert len(body["records"]) == 2
    assert body["has_more"] is True
    assert body["next_cursor"] is not None

    with TestClient(app) as client:
        r2 = client.get(
            "/scene/records/sess1",
            params={"limit": 2, "cursor": body["next_cursor"]},
        )

    body2 = r2.json()
    assert len(body2["records"]) == 2
    assert body2["has_more"] is True
    # Different page
    seen_ids_p1 = {rec["scene_id"] for rec in body["records"]}
    seen_ids_p2 = {rec["scene_id"] for rec in body2["records"]}
    assert not (seen_ids_p1 & seen_ids_p2)


@pytest.mark.contract
def test_list_scene_records_empty_session() -> None:
    conn = SceneConn()
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.get("/scene/records/sess1")

    assert r.status_code == 200
    body = r.json()
    assert body["records"] == []
    assert body["has_more"] is False
    assert body["next_cursor"] is None
