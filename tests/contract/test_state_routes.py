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
        "advancement": zero_advancement(),
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
def test_save_full_state_tag_advance_increments_counter() -> None:
    character = _character()
    character["knowledge"]["athletics"] = 1
    conn = StateRouteConn("sess1", character, _world(turn=1, time_of_day="morning"))
    app = _make_app(FakePool(conn))

    incoming_character = _character()
    incoming_character["knowledge"]["athletics"] = 2

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": incoming_character,
                "world": _world(turn=1, time_of_day="morning"),
                "log_entry": "Full save advances athletics.",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["character"]["advancement"]["tag_advance_counters"]["power"] == 1


@pytest.mark.contract
def test_save_full_state_application_beyond_parent_returns_422() -> None:
    character = _character()
    character["knowledge"]["athletics"] = 1
    character["application"]["hauling"] = 1
    conn = StateRouteConn("sess1", character, _world(turn=1, time_of_day="morning"))
    app = _make_app(FakePool(conn))

    incoming_character = _character()
    incoming_character["knowledge"]["athletics"] = 1
    incoming_character["application"]["hauling"] = 3

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": incoming_character,
                "world": _world(turn=1, time_of_day="morning"),
                "log_entry": "Full save violates parent cap.",
            },
        )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["message"] == "parent-cap violation"


@pytest.mark.contract
def test_save_rejects_when_turn_advances_without_time() -> None:
    """Turn advanced + no world.time field in body → 422 (enforced acknowledgment)."""
    conn = StateRouteConn("sess1", _character(), _world(turn=1, time_of_day="morning"))
    app = _make_app(FakePool(conn))

    # Build a body that sends turn=2 but omits the time block entirely.
    world_no_time = _world(turn=2, time_of_day="morning")
    world_no_time.pop("time")

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": world_no_time,
                "log_entry": "Turn advanced without time.",
            },
        )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["error"] == "time_acknowledgment_required"
    assert body["detail"]["previous_turn"] == 1
    assert body["detail"]["current_turn"] == 2


@pytest.mark.contract
def test_save_accepts_when_turn_advances_with_time_echoed() -> None:
    """Turn advanced + time block present (even echoing prior values) → 200 (acknowledgment)."""
    conn = StateRouteConn("sess1", _character(), _world(turn=1, time_of_day="morning"))
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": _world(turn=2, time_of_day="morning"),  # time block present, same time_of_day
                "log_entry": "Deliberate no-advance turn.",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    # Drift warning still informative, but save succeeds because acknowledgment was given.
    assert payload["time_drift_warning"] is not None


@pytest.mark.contract
def test_save_state_accepts_time_elapsed_field() -> None:
    """time_elapsed is accepted but not yet consumed by the save route."""
    stored_world = _world(turn=1, time_of_day="morning")
    conn = StateRouteConn("sess1", _character(), stored_world)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": _world(turn=1, time_of_day="morning"),
                "log_entry": "Save accepts time elapsed shape.",
                "time_elapsed": {"steps": 2},
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["world"]["time"] == stored_world["time"]


@pytest.mark.contract
def test_save_state_rejects_invalid_time_elapsed() -> None:
    """time_elapsed validates per its model. steps > 12 should 422."""
    conn = StateRouteConn("sess1", _character(), _world(turn=1, time_of_day="morning"))
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": _world(turn=1, time_of_day="morning"),
                "log_entry": "Invalid time elapsed shape.",
                "time_elapsed": {"steps": 13},
            },
        )

    assert response.status_code == 422


@pytest.mark.contract
def test_save_rejects_time_regression() -> None:
    """The actual GPT bug: time block sent with day=1 (regenerated default) over stored day=4 → 422."""
    # Existing state is already at day 4 of Verdantrise, afternoon.
    stored_world = _world(turn=10, time_of_day="afternoon")
    stored_world["time"]["day"] = 4
    conn = StateRouteConn("sess1", _character(), stored_world)
    app = _make_app(FakePool(conn))

    # Incoming save sends a full time block but with day=1 (default regeneration).
    incoming_world = _world(turn=11, time_of_day="afternoon")
    incoming_world["time"]["day"] = 1  # regression!

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": incoming_world,
                "log_entry": "Save layer regenerates day=1 over stored day=4.",
            },
        )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["error"] == "time_regression_rejected"
    assert body["detail"]["previous_time"]["day"] == 4
    assert body["detail"]["incoming_time"]["day"] == 1


@pytest.mark.contract
def test_save_accepts_legitimate_month_wrap() -> None:
    """day=1 of next month over day=30 of prev month → 200 (forward in time)."""
    stored_world = _world(turn=10, time_of_day="night")
    stored_world["time"]["day"] = 30
    stored_world["time"]["month"] = "Verdantrise"
    conn = StateRouteConn("sess1", _character(), stored_world)
    app = _make_app(FakePool(conn))

    incoming_world = _world(turn=11, time_of_day="dawn")
    incoming_world["time"]["day"] = 1
    incoming_world["time"]["month"] = "Clearwater"  # next month

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": incoming_world,
                "log_entry": "Crossed midnight from day 30 Verdantrise to day 1 Clearwater.",
            },
        )

    assert response.status_code == 200


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
def test_delta_rejects_when_turn_advances_without_time() -> None:
    """Delta: turn advanced + body.world.time None → 422."""
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

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["error"] == "time_acknowledgment_required"
    assert body["detail"]["current_turn"] == 2


@pytest.mark.contract
def test_delta_accepts_when_turn_advances_with_time_echoed() -> None:
    """Delta: turn advanced + body.world.time present (echo) → 200."""
    conn = StateRouteConn("sess1", _character(), _world(turn=1, time_of_day="morning"))
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/delta",
            json={
                "world": {
                    "turn": 2,
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
                },
                "log_entry": "Delta acknowledging no-advance turn.",
            },
        )

    assert response.status_code == 200


@pytest.mark.contract
def test_delta_accepts_time_elapsed_field() -> None:
    """time_elapsed is accepted but not yet consumed by the delta route."""
    stored_world = _world(turn=1, time_of_day="morning")
    conn = StateRouteConn("sess1", _character(), stored_world)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/delta",
            json={
                "world": {"goal": "survive"},
                "log_entry": "Delta accepts time elapsed shape.",
                "time_elapsed": {"steps": 2},
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["world"]["time"] == stored_world["time"]