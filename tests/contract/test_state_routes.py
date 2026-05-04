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
        self.log: list = []
        self.updated_at = datetime.now()

    async def fetchrow(self, query, *args):
        if "SELECT character, world FROM game_states" in query:
            if self.session_id is None or args[0] != self.session_id or self.character is None or self.world is None:
                return None
            return {
                "character": self.character,
                "world": self.world,
            }

        if "RETURNING session_id, character, world, log, updated_at" in query:
            self.session_id = args[0]
            self.character = json.loads(args[1])
            self.world = json.loads(args[2])
            if len(args) > 4:
                self.log.extend(json.loads(args[4]))
            elif "log         = game_states.log" not in query:
                self.log = json.loads(args[3])
            self.updated_at = datetime.now()
            return {
                "session_id": self.session_id,
                "character": self.character,
                "world": self.world,
                "log": self.log,
                "updated_at": self.updated_at,
            }

        if "UPDATE game_states" in query and "RETURNING session_id, log, updated_at" in query:
            # GAME_STATE_LOG_APPEND_ONLY — annotation endpoint.
            if self.session_id is None or args[0] != self.session_id:
                return None
            self.log.extend(json.loads(args[1]))
            self.updated_at = datetime.now()
            return {
                "session_id": self.session_id,
                "log": self.log,
                "updated_at": self.updated_at,
            }

        if "SELECT session_id, character, world, log, updated_at FROM game_states" in query:
            if self.session_id is None or args[0] != self.session_id or self.character is None or self.world is None:
                return None
            return {
                "session_id": self.session_id,
                "character": self.character,
                "world": self.world,
                "log": self.log,
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
        "magic": {},
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
    character["knowledge"]["athletics"] = {"tier": 1, "applications": {}}
    conn = StateRouteConn("sess1", character, _world(turn=1, time_of_day="morning"))
    app = _make_app(FakePool(conn))

    incoming_character = _character()
    incoming_character["knowledge"]["athletics"] = {"tier": 2, "applications": {}}

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
    assert payload["character"]["advancement"]["tag_counter"] == 1


@pytest.mark.contract
def test_save_full_state_application_beyond_parent_returns_422() -> None:
    """Parent-cap violations are caught at CharacterModel construction (v5 structural)."""
    character = _character()
    character["knowledge"]["athletics"] = {"tier": 1, "applications": {"hauling": 1}}
    conn = StateRouteConn("sess1", character, _world(turn=1, time_of_day="morning"))
    app = _make_app(FakePool(conn))

    incoming_character = _character()
    # Application 'hauling' at tier 3 with parent group 'athletics' at tier 1 — invalid.
    incoming_character["knowledge"]["athletics"] = {"tier": 1, "applications": {"hauling": 3}}

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
def test_first_save_succeeds() -> None:
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

@pytest.mark.contract
def test_save_advances_time_via_steps() -> None:
    """time_elapsed.steps advances the time-of-day band server-side."""
    stored_world = _world(turn=1, time_of_day="morning")
    conn = StateRouteConn("sess1", _character(), stored_world)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": {"goal": "survive"},
                "log_entry": "Advance two bands.",
                "time_elapsed": {"steps": 2},
            },
        )

    assert response.status_code == 200
    time = response.json()["world"]["time"]
    assert time["day"] == 1
    assert time["month"] == "Verdantrise"
    assert time["time_of_day"] == "afternoon"


@pytest.mark.contract
def test_save_advances_time_via_days() -> None:
    """time_elapsed.days advances the day server-side."""
    stored_world = _world(turn=1, time_of_day="morning")
    conn = StateRouteConn("sess1", _character(), stored_world)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": {"goal": "survive"},
                "log_entry": "Advance one day.",
                "time_elapsed": {"days": 1},
            },
        )

    assert response.status_code == 200
    time = response.json()["world"]["time"]
    assert time["day"] == 2
    assert time["month"] == "Verdantrise"
    assert time["time_of_day"] == "morning"


@pytest.mark.contract
def test_save_advances_time_until_dawn() -> None:
    """time_elapsed.until=dawn advances to the next dawn."""
    stored_world = _world(turn=1, time_of_day="night")
    conn = StateRouteConn("sess1", _character(), stored_world)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": {"goal": "survive"},
                "log_entry": "Advance until dawn.",
                "time_elapsed": {"until": "dawn"},
            },
        )

    assert response.status_code == 200
    time = response.json()["world"]["time"]
    assert time["day"] == 2
    assert time["time_of_day"] == "dawn"


@pytest.mark.contract
def test_save_no_time_elapsed_keeps_time_static() -> None:
    """Default time_elapsed preserves stored time exactly."""
    stored_world = _world(turn=1, time_of_day="midday")
    stored_world["time"]["day"] = 5
    conn = StateRouteConn("sess1", _character(), stored_world)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": {"goal": "survive"},
                "log_entry": "No elapsed time.",
            },
        )

    assert response.status_code == 200
    assert response.json()["world"]["time"] == stored_world["time"]


@pytest.mark.contract
def test_save_ignores_incoming_derived_time_fields() -> None:
    """Incoming world.time.day is silently overridden by server computation."""
    stored_world = _world(turn=1, time_of_day="morning")
    stored_world["time"]["day"] = 5
    conn = StateRouteConn("sess1", _character(), stored_world)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": {"time": {"day": 999}},
                "log_entry": "Derived time write ignored.",
                "time_elapsed": {"steps": 0},
            },
        )

    assert response.status_code == 200
    assert response.json()["world"]["time"]["day"] == 5


@pytest.mark.contract
def test_save_preserves_incoming_weather() -> None:
    """world.time.weather and weather_note remain writable through the save."""
    stored_world = _world(turn=1, time_of_day="morning")
    conn = StateRouteConn("sess1", _character(), stored_world)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": {"time": {"weather": "storm", "weather_note": "hard rain"}},
                "log_entry": "Weather changes.",
            },
        )

    assert response.status_code == 200
    time = response.json()["world"]["time"]
    assert time["weather"] == "storm"
    assert time["weather_note"] == "hard rain"
    assert time["day"] == 1
    assert time["time_of_day"] == "morning"


@pytest.mark.contract
def test_save_state_delta_omitted_log_entry_does_not_append() -> None:
    conn = StateRouteConn("sess1", _character(), _world(turn=1, time_of_day="morning"))
    conn.log = ["Existing legacy entry."]
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/delta",
            json={
                "character": {"notes": "quiet state maintenance"},
                "world": {},
            },
        )

    assert response.status_code == 200
    assert conn.log == ["Existing legacy entry."]
    assert response.json()["log"] == ["Existing legacy entry."]


@pytest.mark.contract
def test_save_state_typed_log_entry_round_trips() -> None:
    conn = StateRouteConn("sess1", _character(), _world(turn=1, time_of_day="morning"))
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": {"goal": "survive"},
                "log_entry": {"type": "narrative_non_arc", "text": "A rare quiet beat."},
            },
        )
        get_response = client.get("/state/sess1")

    assert response.status_code == 200
    assert get_response.status_code == 200
    assert get_response.json()["log"][-1] == {"type": "narrative_non_arc", "text": "A rare quiet beat."}


@pytest.mark.contract
def test_save_state_mixed_legacy_and_typed_log_entries_round_trip() -> None:
    conn = StateRouteConn("sess1", _character(), _world(turn=1, time_of_day="morning"))
    conn.log = ["Existing legacy entry."]
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": {"goal": "survive"},
                "log_entry": {"type": "compression", "text": "Compressed travel beats."},
            },
        )
        get_response = client.get("/state/sess1")

    assert response.status_code == 200
    assert get_response.status_code == 200
    assert get_response.json()["log"] == [
        "Existing legacy entry.",
        {"type": "compression", "text": "Compressed travel beats."},
    ]


@pytest.mark.contract
def test_save_advances_into_festival_day() -> None:
    """Crossing into a festival day populates festival via server lookup."""
    stored_world = _world(turn=1, time_of_day="morning")
    stored_world["time"]["day"] = 30
    stored_world["time"]["month"] = "Deepwarden"
    stored_world["time"]["year"] = 847
    stored_world["time"]["season"] = "autumn"
    conn = StateRouteConn("sess1", _character(), stored_world)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": {"goal": "survive"},
                "log_entry": "Advance into new year.",
                "time_elapsed": {"days": 1},
            },
        )

    assert response.status_code == 200
    time = response.json()["world"]["time"]
    assert time["day"] == 1
    assert time["month"] == "Ashwake"
    assert time["year"] == 848
    assert time["time_of_day"] == "morning"
    assert time["season"] == "winter"
    assert time["festival"] == "New Year's Dawn"


# --- /state/{session_id}/annotation contract -------------------------------

@pytest.mark.contract
def test_annotation_appends_to_log() -> None:
    """Annotation appends an admin_correction TypedLogEntry to the log."""
    conn = StateRouteConn("sess1", _character(), _world())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/annotation",
            json={
                "annotation": "House Vaelaryn was renamed to House Heartwood mid-session.",
                "category": "canon_correction",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "sess1"
    assert body["appended_to_log"] is True
    assert body["log_entry_index"] == 0
    assert isinstance(body["annotation_id"], str) and body["annotation_id"]

    # Log now contains a typed admin_correction entry whose text carries the
    # category prefix and the annotation body.
    assert len(conn.log) == 1
    entry = conn.log[0]
    assert entry["type"] == "admin_correction"
    assert entry["text"].startswith("[canon_correction] ")
    assert "House Heartwood" in entry["text"]


@pytest.mark.contract
def test_annotation_rejects_unknown_session() -> None:
    """Unknown session_id returns 404."""
    conn = StateRouteConn(None, None, None)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/missing/annotation",
            json={"annotation": "test", "category": "canon_correction"},
        )

    assert response.status_code == 404


@pytest.mark.contract
def test_annotation_rejects_empty_string() -> None:
    """Empty annotation string returns 422."""
    conn = StateRouteConn("sess1", _character(), _world())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/annotation",
            json={"annotation": "", "category": "canon_correction"},
        )

    assert response.status_code == 422


@pytest.mark.contract
def test_annotation_rejects_unknown_category() -> None:
    """Category outside the literal set returns 422."""
    conn = StateRouteConn("sess1", _character(), _world())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/annotation",
            json={"annotation": "test", "category": "made_up_category"},
        )

    assert response.status_code == 422


# --- GET /state/{session_id} log_limit + log_total_entries (Brief 24) -------

@pytest.mark.contract
def test_load_state_returns_full_log_when_log_limit_unset() -> None:
    """Without log_limit, response includes the entire log; total matches len."""
    conn = StateRouteConn("sess1", _character(), _world())
    conn.log = [f"entry {i}" for i in range(7)]
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.get("/state/sess1")

    assert response.status_code == 200
    body = response.json()
    assert len(body["log"]) == 7
    assert body["log_total_entries"] == 7


@pytest.mark.contract
def test_load_state_truncates_to_log_limit() -> None:
    """log_limit=N returns only the last N entries; log_total_entries unchanged."""
    conn = StateRouteConn("sess1", _character(), _world())
    conn.log = [f"entry {i}" for i in range(7)]
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.get("/state/sess1?log_limit=2")

    assert response.status_code == 200
    body = response.json()
    assert len(body["log"]) == 2
    assert body["log_total_entries"] == 7


@pytest.mark.contract
def test_load_state_log_limit_returns_tail_not_head() -> None:
    """log_limit returns the *most recent* entries, not the oldest."""
    conn = StateRouteConn("sess1", _character(), _world())
    conn.log = [f"entry {i}" for i in range(5)]
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.get("/state/sess1?log_limit=2")

    body = response.json()
    assert body["log"] == ["entry 3", "entry 4"]


@pytest.mark.contract
def test_load_state_log_limit_larger_than_log_returns_full_log() -> None:
    """log_limit=10000 with a 5-entry log returns 5 entries; no error."""
    conn = StateRouteConn("sess1", _character(), _world())
    conn.log = [f"entry {i}" for i in range(5)]
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.get("/state/sess1?log_limit=10000")

    assert response.status_code == 200
    body = response.json()
    assert len(body["log"]) == 5
    assert body["log_total_entries"] == 5


@pytest.mark.contract
def test_load_state_log_limit_zero_rejected() -> None:
    """log_limit=0 fails Query validation (ge=1)."""
    conn = StateRouteConn("sess1", _character(), _world())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.get("/state/sess1?log_limit=0")

    assert response.status_code == 422


@pytest.mark.contract
def test_load_state_log_limit_above_max_rejected() -> None:
    """log_limit=10001 fails Query validation (le=10000)."""
    conn = StateRouteConn("sess1", _character(), _world())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.get("/state/sess1?log_limit=10001")

    assert response.status_code == 422


@pytest.mark.contract
def test_save_state_response_reports_log_total_entries() -> None:
    """POST /state/{session_id} response also carries log_total_entries."""
    conn = StateRouteConn("sess1", _character(), _world(turn=1, time_of_day="morning"))
    conn.log = ["prior one", "prior two"]
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1",
            json={
                "character": _character(),
                "world": _world(turn=1, time_of_day="morning"),
                "log_entry": "third entry",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["log_total_entries"] == 3
    assert len(body["log"]) == 3


@pytest.mark.contract
def test_annotation_does_not_mutate_character_or_world() -> None:
    """Annotation must touch only the log, never character or world JSONB."""
    starting_character = _character()
    starting_world = _world()
    conn = StateRouteConn("sess1", starting_character, starting_world)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        response = client.post(
            "/state/sess1/annotation",
            json={
                "annotation": "Operational note: token cadence reset.",
                "category": "operational_constraint",
            },
        )

    assert response.status_code == 200
    # Character and world remain bit-identical to what was stored before the call.
    assert conn.character == starting_character
    assert conn.world == starting_world
