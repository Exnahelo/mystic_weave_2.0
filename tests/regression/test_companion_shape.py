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
                "character": (args[1] if isinstance(args[1], (dict, list)) else json.loads(args[1])),
                "world": (args[2] if isinstance(args[2], (dict, list)) else json.loads(args[2])),
                "log": [],
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
            row["character"] = (args[1] if isinstance(args[1], (dict, list)) else json.loads(args[1]))
            row["world"] = (args[2] if isinstance(args[2], (dict, list)) else json.loads(args[2]))
            row["log"] = row["log"] + (args[4] if isinstance(args[4], (dict, list)) else json.loads(args[4]))
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


def _flat_creature(companion_id: str = "test_id", name: str = "X") -> dict:
    return {
        "id": companion_id,
        "tier": "creature",
        "name": name,
        "species": "wolf",
        "subspecies": "moonthorn_wolf",
        "subtype": "moonthorn_wolf",
        "size": "medium",
        "age_category": "adult",
        "tactical_roles": ["guard"],
        "training_level": "trained",
        "bond_level": "bonded",
        "natural_abilities": ["keen_senses"],
        "learned_commands": ["heel"],
        "movement_modes": ["walk"],
        "natural_weapons": ["bite"],
        "carrying_capacity": "small",
        "hp": {"current": 10, "max": 10},
        "domains": {"physical": 40, "instinct": 38, "composure": 35},
        "temperament": "Alert",
        "bond_links": {"primary": "krath"},
    }


@pytest.mark.regression
def test_delta_rejects_nested_companion_wrapper_and_accepts_flat_shape() -> None:
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

        nested = client.post(
            f"/state/{session_id}/delta",
            json={
                "world": {
                    "companions": [
                        {
                            "id": "test_id",
                            "companion": {
                                "tier": "creature",
                                "name": "X",
                                "species": "wolf",
                            },
                        }
                    ]
                },
                "log_entry": "Attempt nested companion wrapper.",
            },
        )
        assert nested.status_code == 422

        flat = client.post(
            f"/state/{session_id}/delta",
            json={
                "world": {"companions": [_flat_creature()]},
                "log_entry": "Save flat companion.",
            },
        )
        assert flat.status_code == 200

        reread = client.get(f"/state/{session_id}")
        assert reread.status_code == 200
        companion = reread.json()["world"]["companions"][0]
        assert companion["id"] == "test_id"
        assert companion["name"] == "X"
        assert companion["species"] == "wolf"