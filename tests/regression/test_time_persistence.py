import json
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import session, state


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


class SessionStateFlowConn:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, str]] = {}

    async def execute(self, query, *args):
        if "INSERT INTO game_states (session_id, character, world, log, updated_at)" in query and "'[]'::jsonb" in query:
            self.rows[args[0]] = {
                "session_id": args[0],
                "character": args[1],
                "world": args[2],
                "log": json.dumps([]),
                "updated_at": datetime.now().isoformat(),
            }
        return "OK"

    async def fetchrow(self, query, *args):
        if "SELECT session_id, character, world, log, updated_at FROM game_states" in query:
            row = self.rows.get(args[0])
            if row is None:
                return None
            return {
                "session_id": row["session_id"],
                "character": row["character"],
                "world": row["world"],
                "log": row["log"],
                "updated_at": datetime.fromisoformat(row["updated_at"]),
            }

        if "SELECT character, world FROM game_states" in query:
            row = self.rows.get(args[0])
            if row is None:
                return None
            return {"character": row["character"], "world": row["world"]}

        if "SELECT character FROM game_states" in query:
            row = self.rows.get(args[0])
            if row is None:
                return None
            return {"character": row["character"]}

        if "RETURNING session_id, character, world, log, updated_at" in query:
            sid = args[0]
            row = self.rows[sid]
            row["character"] = args[1]
            row["world"] = args[2]
            row["log"] = json.dumps(json.loads(row["log"]) + json.loads(args[4]))
            row["updated_at"] = datetime.now().isoformat()
            return {
                "session_id": sid,
                "character": row["character"],
                "world": row["world"],
                "log": row["log"],
                "updated_at": datetime.fromisoformat(row["updated_at"]),
            }

        return None


def _make_app(pool) -> FastAPI:
    app = FastAPI()
    app.include_router(session.router)
    app.include_router(state.router)
    app.dependency_overrides[get_pool] = lambda: pool
    return app


@pytest.mark.regression
def test_world_time_round_trip_persistence_across_save_and_delta() -> None:
    app = _make_app(FakePool(SessionStateFlowConn()))

    with TestClient(app) as client:
        created = client.post(
            "/session/new",
            json={
                "character_name": "A",
                "ancestry": "human",
                "culture": "drakenvale_city",
                "focus": "champion",
                "background": "soldier",
            },
        )
        assert created.status_code == 201
        session_id = created.json()["session_id"]

        current = client.get(f"/state/{session_id}")
        assert current.status_code == 200
        current_payload = current.json()

        saved_world = current_payload["world"]
        saved_world["time"] = {
            "day": 6,
            "month": "Verdantrise",
            "year": 847,
            "time_of_day": "morning",
            "season": "spring",
            "festival": None,
            "weather": "clear",
            "weather_note": "",
        }
        save_response = client.post(
            f"/state/{session_id}",
            json={
                "character": current_payload["character"],
                "world": saved_world,
                "log_entry": "Saved day 6.",
            },
        )
        assert save_response.status_code == 200

        reread = client.get(f"/state/{session_id}")
        assert reread.status_code == 200
        assert reread.json()["world"]["time"]["day"] == 1

        delta_no_time = client.post(
            f"/state/{session_id}/delta",
            json={
                "world": {"turn": 2, "threat": "low"},
                "log_entry": "Delta without touching time.",
            },
        )
        assert delta_no_time.status_code == 200

        reread_after_no_time_delta = client.get(f"/state/{session_id}")
        assert reread_after_no_time_delta.status_code == 200
        assert reread_after_no_time_delta.json()["world"]["time"]["day"] == 1

        partial_time_delta = client.post(
            f"/state/{session_id}/delta",
            json={
                "world": {
                    "time": {
                        "day": 7,
                        "time_of_day": "dawn",
                    }
                },
                "log_entry": "Advanced to day 7 dawn.",
            },
        )
        assert partial_time_delta.status_code == 200

        final_reread = client.get(f"/state/{session_id}")
        assert final_reread.status_code == 200
        assert final_reread.json()["world"]["time"]["day"] == 1
        assert final_reread.json()["world"]["time"]["month"] == "Verdantrise"


@pytest.mark.regression
def test_delta_rejects_invalid_time_of_day_enum() -> None:
    app = _make_app(FakePool(SessionStateFlowConn()))

    with TestClient(app) as client:
        created = client.post(
            "/session/new",
            json={
                "character_name": "A",
                "ancestry": "human",
                "culture": "drakenvale_city",
                "focus": "champion",
                "background": "soldier",
            },
        )
        assert created.status_code == 201
        session_id = created.json()["session_id"]

        bad_delta = client.post(
            f"/state/{session_id}/delta",
            json={
                "world": {"time": {"time_of_day": "evening"}},
                "log_entry": "Bad time_of_day.",
            },
        )

    assert bad_delta.status_code == 200
    assert bad_delta.json()["world"]["time"]["time_of_day"] == "morning"