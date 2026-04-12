import json
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import scene


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


class SceneConn:
    def __init__(self, *, state_row=None, location_row=None):
        self.state_row = state_row
        self.location_row = location_row

    async def fetchrow(self, query, *args):
        if "FROM game_states" in query:
            return self.state_row
        if "FROM locations" in query:
            return self.location_row
        return None


def _make_app(pool) -> FastAPI:
    app = FastAPI()
    app.include_router(scene.router)
    app.dependency_overrides[get_pool] = lambda: pool
    return app


def _character() -> dict:
    return {
        "name": "Krath",
        "species": "dragonborn",
        "focus": "devoted",
        "background": "soldier",
        "hp": {"current": 76, "max": 100},
        "domains": {
            "power": 45,
            "agility": 35,
            "perception": 35,
            "endurance": 43,
            "intellect": 25,
            "will": 47,
            "presence": 55,
        },
        "knowledge": {"discipline": 2},
        "application": {"sacred_rites": 1},
        "status_effects": ["shaken"],
        "notes": "",
        "identity": {
            "origin": "",
            "motivations": [],
            "quirks": [],
            "bonds": [],
            "flaws": [],
            "wound": "",
            "alignment": {"order": "neutral", "intent": "neutral", "ethos_note": ""},
        },
        "equipment": {"worn": [], "carried": [], "stashed": []},
        "reputation": [],
        "advancement": {
            "points_available": 0,
            "points_spent": 0,
            "points_earned_total": 0,
        },
    }


def _world() -> dict:
    return {
        "location": "test-loc-alpha",
        "threat": "ambush risk",
        "goal": "reach stronghold",
        "turn": 7,
        "companions": [
            {
                "id": "c1",
                "name": "Sorra",
                "species": "halfling",
                "role": "guide",
                "identity": {
                    "origin": "",
                    "motivations": [],
                    "quirks": [],
                    "bonds": [],
                    "flaws": [],
                    "wound": "",
                    "alignment": {"order": "neutral", "intent": "neutral", "ethos_note": ""},
                },
                "hp": {"current": 100, "max": 100},
                "domains": None,
                "knowledge": {},
                "application": {},
                "status": "active",
                "disposition": 0,
                "reputation": [],
            }
        ],
        "economy": {"wealth_tier": "modest", "coin": 1200, "trade_goods": [], "obligations": []},
        "politics": {
            "faction_memberships": [],
            "active_obligations": ["escort debt"],
            "legal_standing": "wanted",
            "known_leverage": ["secret ledger"],
            "active_tensions": ["Guard patrol escalation"],
            "conclave_status": "unknown",
        },
        "time": {
            "day": 1,
            "month": "Verdantrise",
            "year": 847,
            "time_of_day": "morning",
            "season": "spring",
            "festival": None,
            "weather": "clear",
            "weather_note": "",
        },
        "survival": {
            "hunger": "hungry",
            "hydration": "thirsty",
            "fatigue": "tired",
            "load": "burdened",
        },
    }


def _location_data() -> dict:
    return {
        "id": "test-loc-alpha",
        "name": "Ashfield Gate",
        "type": "settlement-edge",
        "description": "A wind-cut gate with watch braziers.",
        "tags": ["settlement", "checkpoint"],
        "connections": ["road-east", "river-ford"],
        "threat_level": 2,
        "known_npcs": ["Gate Warden", "Quartermaster"],
        "discovered": True,
    }


@pytest.mark.regression
def test_scene_context_shape_and_log_truncation() -> None:
    log_entries = [f"turn {i}" for i in range(1, 9)]
    conn = SceneConn(
        state_row={
            "session_id": "abc12345",
            "character": json.dumps(_character()),
            "world": json.dumps(_world()),
            "log": json.dumps(log_entries),
            "updated_at": datetime.now(),
        },
        location_row={"data": json.dumps(_location_data())},
    )
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.get("/scene/abc12345")

    assert r.status_code == 200
    payload = r.json()
    assert payload["session_id"] == "abc12345"
    assert payload["location_summary"]["id"] == "test-loc-alpha"
    assert payload["location_summary"]["name"] == "Ashfield Gate"
    assert payload["recent_log"] == ["turn 4", "turn 5", "turn 6", "turn 7", "turn 8"]
    assert "ambush risk" in " | ".join(payload["active_threats"]).lower()
    assert payload["relevant_character_state"]["survival"]["load"] == "burdened"


@pytest.mark.regression
def test_scene_context_omits_full_world_payload() -> None:
    conn = SceneConn(
        state_row={
            "session_id": "abc12345",
            "character": json.dumps(_character()),
            "world": json.dumps(_world()),
            "log": json.dumps(["one", "two"]),
            "updated_at": datetime.now(),
        },
        location_row={"data": json.dumps(_location_data())},
    )
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.get("/scene/abc12345")

    assert r.status_code == 200
    payload = r.json()
    assert "world" not in payload
    assert "character" not in payload
    assert "politics" not in payload
    assert "economy" not in payload
