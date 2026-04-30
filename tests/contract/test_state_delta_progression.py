import json
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import state
from tests.helpers import zero_advancement


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


class DeltaConn:
    def __init__(self, character: dict, world: dict):
        self.session_id = "sess1"
        self.character = character
        self.world = world
        self.log: list[str] = []
        self.updated_at = datetime.now()

    async def fetchrow(self, query, *args):
        if "SELECT character, world FROM game_states" in query:
            if args[0] != self.session_id:
                return None
            return {"character": json.dumps(self.character), "world": json.dumps(self.world)}

        if "RETURNING session_id, character, world, log, updated_at" in query:
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
        "domains": {"power": 45, "agility": 35, "perception": 35, "endurance": 43, "intellect": 25, "will": 47, "presence": 55},
        "knowledge": {"athletics": 1},
        "application": {"hauling": 1},
        "fields": {},
        "status_effects": [],
        "notes": "",
        "identity": {"origin": "", "motivations": [], "quirks": [], "bonds": [], "flaws": [], "wound": "", "alignment": {"order": "neutral", "intent": "neutral", "ethos_note": ""}},
        "equipment": {"worn": [], "carried": [], "stashed": []},
        "reputation": [],
        "advancement": zero_advancement(),
    }


def _world() -> dict:
    return {
        "location": "test-loc-alpha",
        "threat": "none",
        "goal": "survive",
        "turn": 1,
        "companions": [],
        "companion_archive": [],
        "economy": {"wealth_tier": "modest", "coin": 0, "trade_goods": [], "obligations": []},
        "politics": {"faction_memberships": [], "active_obligations": [], "legal_standing": "unknown", "known_leverage": [], "active_tensions": [], "conclave_status": "unknown"},
        "time": {"day": 1, "month": "Verdantrise", "year": 847, "time_of_day": "morning", "season": "spring", "festival": None, "weather": "clear", "weather_note": ""},
        "survival": {"hunger": "sated", "hydration": "hydrated", "fatigue": "rested", "load": "normal"},
        "pacing": {"tension": 3, "last_consequence_weight": "local", "turns_since_social_beat": 0, "turns_since_discovery": 0, "turn_count": 1},
    }


@pytest.mark.contract
def test_state_delta_tag_advance_increments_counter() -> None:
    app = _make_app(FakePool(DeltaConn(_character(), _world())))
    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/delta",
            json={"character": {"knowledge": {"athletics": 2}}, "log_entry": "advance"},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["character"]["advancement"]["tag_advance_counters"]["power"] == 1


@pytest.mark.contract
def test_state_delta_three_advances_convert_to_earned_ap() -> None:
    conn = DeltaConn(_character(), _world())
    app = _make_app(FakePool(conn))
    with TestClient(app) as client:
        client.post("/state/sess1/delta", json={"character": {"knowledge": {"athletics": 2}}, "log_entry": "advance1"})
        client.post("/state/sess1/delta", json={"character": {"application": {"hauling": 2}}, "log_entry": "advance2"})
        client.post("/state/sess1/delta", json={"character": {"knowledge": {"athletics": 3}}, "log_entry": "advance3"})
        response = client.get("/state/sess1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["character"]["advancement"]["points_available_earned"]["power"] == 1
    assert payload["character"]["advancement"]["tag_advance_counters"]["power"] == 0


@pytest.mark.contract
def test_state_delta_application_beyond_parent_returns_422() -> None:
    character = _character()
    character["knowledge"]["athletics"] = 1
    character["application"]["hauling"] = 1
    app = _make_app(FakePool(DeltaConn(character, _world())))
    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/delta",
            json={"character": {"application": {"hauling": 2}}, "log_entry": "bad advance"},
        )
    assert response.status_code == 422


@pytest.mark.contract
def test_state_delta_seeded_above_application_cannot_advance_further() -> None:
    character = _character()
    character["knowledge"]["athletics"] = 1
    character["application"]["hauling"] = 2
    app = _make_app(FakePool(DeltaConn(character, _world())))
    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/delta",
            json={"character": {"application": {"hauling": 3}}, "log_entry": "bad seeded advance"},
        )
    assert response.status_code == 422

@pytest.mark.contract
def test_state_delta_advances_time_via_steps() -> None:
    """Delta time_elapsed.steps advances server-computed time."""
    world = _world()
    world["time"]["time_of_day"] = "morning"
    app = _make_app(FakePool(DeltaConn(_character(), world)))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/delta",
            json={"world": {"goal": "survive"}, "time_elapsed": {"steps": 2}, "log_entry": "advance time"},
        )

    assert response.status_code == 200
    time = response.json()["world"]["time"]
    assert time["day"] == 1
    assert time["time_of_day"] == "afternoon"


@pytest.mark.contract
def test_state_delta_ignores_incoming_derived_time_fields() -> None:
    """Delta world.time.day is ignored in favor of server-computed time."""
    world = _world()
    world["time"]["day"] = 4
    app = _make_app(FakePool(DeltaConn(_character(), world)))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/delta",
            json={"world": {"time": {"day": 999}}, "log_entry": "ignore derived"},
        )

    assert response.status_code == 200
    time = response.json()["world"]["time"]
    assert time["day"] == 4
    assert time["time_of_day"] == "morning"


@pytest.mark.contract
def test_state_delta_preserves_incoming_weather() -> None:
    """Delta world.time.weather and weather_note remain writable."""
    app = _make_app(FakePool(DeltaConn(_character(), _world())))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/delta",
            json={
                "world": {"time": {"weather": "mist", "weather_note": "river fog"}},
                "log_entry": "weather change",
            },
        )

    assert response.status_code == 200
    time = response.json()["world"]["time"]
    assert time["weather"] == "mist"
    assert time["weather_note"] == "river fog"
    assert time["day"] == 1
    assert time["time_of_day"] == "morning"

