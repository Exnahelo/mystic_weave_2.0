import json
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import state


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


class StateRouteConn:
    def __init__(self, session_id: str | None, character: dict | None, world: dict | None):
        self.session_id = session_id
        self.character = character
        self.world = world
        self.log: list[str] = []
        self.updated_at = datetime.now()

    async def fetchrow(self, query, *args):
        if "SELECT character, world FROM game_states" in query:
            if self.session_id is None or args[0] != self.session_id or self.character is None or self.world is None:
                return None
            return {
                "character": json.dumps(self.character),
                "world": json.dumps(self.world),
            }

        if "RETURNING session_id, character, world, log, updated_at" in query:
            self.session_id = args[0]
            self.character = json.loads(args[1])
            self.world = json.loads(args[2])
            self.log.extend(json.loads(args[4]))
            self.updated_at = datetime.now()
            return {
                "session_id": self.session_id,
                "character": json.dumps(self.character),
                "world": json.dumps(self.world),
                "log": json.dumps(self.log),
                "updated_at": self.updated_at,
            }

        if "SELECT session_id, character, world, log, updated_at FROM game_states" in query:
            if self.session_id is None or args[0] != self.session_id or self.character is None or self.world is None:
                return None
            return {
                "session_id": self.session_id,
                "character": json.dumps(self.character),
                "world": json.dumps(self.world),
                "log": json.dumps(self.log),
                "updated_at": self.updated_at,
            }

        return None


def _make_app(pool) -> FastAPI:
    app = FastAPI()
    app.include_router(state.router)
    app.dependency_overrides[get_pool] = lambda: pool
    return app


def _character() -> dict:
    return {
        "name": "Krath",
        "ancestry": "human",
        "culture": "drakenvale_city",
        "focus": "devoted",
        "background": "soldier",
        "hp": {"current": 100, "max": 100},
        "domains": {
            "power": 45,
            "agility": 35,
            "perception": 35,
            "endurance": 43,
            "intellect": 25,
            "will": 47,
            "presence": 55,
        },
        "knowledge": {},
        "application": {},
        "fields": {},
        "status_effects": [],
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
        "advancement": {"points_available": 0, "points_spent": 0, "points_earned_total": 0},
    }


def _world(turn: int = 1, time_of_day: str = "morning") -> dict:
    return {
        "location": "test-loc-alpha",
        "threat": "none",
        "goal": "survive",
        "turn": turn,
        "companions": [],
        "companion_archive": [],
        "economy": {"wealth_tier": "modest", "coin": 0, "trade_goods": [], "obligations": []},
        "politics": {
            "faction_memberships": [],
            "active_obligations": [],
            "legal_standing": "unknown",
            "known_leverage": [],
            "active_tensions": [],
            "conclave_status": "unknown",
        },
        "time": {
            "day": 1,
            "month": "Verdantrise",
            "year": 847,
            "time_of_day": time_of_day,
            "season": "spring",
            "festival": None,
            "weather": "clear",
            "weather_note": "",
        },
        "survival": {"hunger": "sated", "hydration": "hydrated", "fatigue": "rested", "load": "normal"},
        "pacing": {
            "tension": 3,
            "last_consequence_weight": "local",
            "turns_since_social_beat": 0,
            "turns_since_discovery": 0,
            "turn_count": turn,
        },
    }


@pytest.mark.contract
def test_save_returns_drift_warning_when_time_stale() -> None:
    conn = StateRouteConn("sess1", _character(), _world(turn=1, time_of_day="morning"))
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": _world(turn=2, time_of_day="morning"),
                "log_entry": "Turn advanced without time.",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["time_drift_warning"] is not None
    assert payload["time_drift_warning"]["previous_turn"] == 1
    assert payload["time_drift_warning"]["current_turn"] == 2


@pytest.mark.contract
def test_save_without_drift_returns_null_warning() -> None:
    conn = StateRouteConn("sess1", _character(), _world(turn=1, time_of_day="morning"))
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": _world(turn=2, time_of_day="afternoon"),
                "log_entry": "Turn advanced with time.",
            },
        )

    assert response.status_code == 200
    assert response.json()["time_drift_warning"] is None


@pytest.mark.contract
def test_first_save_returns_null_warning() -> None:
    conn = StateRouteConn(None, None, None)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": _world(turn=1, time_of_day="morning"),
                "log_entry": "First save.",
            },
        )

    assert response.status_code == 200
    assert response.json()["time_drift_warning"] is None


@pytest.mark.contract
def test_delta_returns_drift_warning_when_turn_advances_without_time_change() -> None:
    conn = StateRouteConn("sess1", _character(), _world(turn=1, time_of_day="morning"))
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/delta",
            json={
                "world": {"turn": 2},
                "log_entry": "Delta turn only.",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["time_drift_warning"] is not None
    assert payload["time_drift_warning"]["current_turn"] == 2