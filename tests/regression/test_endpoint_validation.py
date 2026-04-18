import json
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.models import CharacterModel, WorldModel
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


class FakeConn:
    def __init__(self, *, select_character=None, select_world=None, upsert_row=None):
        self.select_character = select_character
        self.select_world = select_world
        self.upsert_row = upsert_row
        self.execute_calls: list[tuple[str, tuple]] = []

    async def execute(self, query, *args):
        self.execute_calls.append((query, args))
        return "OK"

    async def fetchrow(self, query, *args):
        if "SELECT session_id, character, world, log, updated_at FROM game_states" in query:
            if self.select_character is None or self.select_world is None:
                return None
            return {
                "session_id": args[0],
                "character": json.dumps(self.select_character),
                "world": json.dumps(self.select_world),
                "log": json.dumps([]),
                "updated_at": datetime.now(),
            }

        if "SELECT character, world FROM game_states" in query:
            if self.select_character is None or self.select_world is None:
                return None
            return {
                "character": json.dumps(self.select_character),
                "world": json.dumps(self.select_world),
            }

        if "SELECT character FROM game_states" in query:
            if self.select_character is None:
                return None
            return {"character": json.dumps(self.select_character)}

        if "RETURNING session_id, character, world, log, updated_at" in query:
            if self.upsert_row is not None:
                return self.upsert_row
            return {
                "session_id": args[0],
                "character": args[1],
                "world": args[2],
                "log": args[4],
                "updated_at": datetime.now(),
            }

        return None


class SessionDeltaFlowConn:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, str]] = {}

    async def execute(self, query, *args):
        if "INSERT INTO game_states (session_id, character, world, log, updated_at)" in query and "'[]'::jsonb" in query:
            self.rows[args[0]] = {
                "session_id": args[0],
                "character": args[1],
                "world": args[2],
                "log": json.dumps([]),
            }
        return "OK"

    async def fetchrow(self, query, *args):
        if "SELECT character, world FROM game_states" in query:
            row = self.rows.get(args[0])
            if row is None:
                return None
            return {"character": row["character"], "world": row["world"]}

        if "RETURNING session_id, character, world, log, updated_at" in query:
            sid = args[0]
            row = self.rows[sid]
            row["character"] = args[1]
            row["world"] = args[2]
            row["log"] = json.dumps(json.loads(row["log"]) + json.loads(args[4]))
            return {
                "session_id": sid,
                "character": row["character"],
                "world": row["world"],
                "log": row["log"],
                "updated_at": datetime.now(),
            }

        if "SELECT character FROM game_states" in query:
            row = self.rows.get(args[0])
            if row is None:
                return None
            return {"character": row["character"]}

        return None


def _build_valid_character() -> dict:
    return {
        "name": "Krath",
        "ancestry": "dragonborn",
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
        "knowledge": {"discipline": 2},
        "application": {"sacred_rites": 1},
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
        "advancement": {
            "points_available": 0,
            "points_spent": 0,
            "points_earned_total": 0,
        },
    }


def _build_valid_world() -> dict:
    return {
        "location": "test-loc-alpha",
        "threat": "none",
        "pacing": {
            "tension": 3,
            "last_consequence_weight": "local",
            "turns_since_social_beat": 0,
            "turns_since_discovery": 0,
            "turn_count": 1,
        },
        "goal": "survive",
        "turn": 1,
        "companions": [],
        "economy": {
            "wealth_tier": "modest",
            "coin": 0,
            "trade_goods": [],
            "obligations": [],
        },
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
            "time_of_day": "morning",
            "season": "spring",
            "festival": None,
            "weather": "clear",
            "weather_note": "",
        },
        "survival": {
            "hunger": "sated",
            "hydration": "hydrated",
            "fatigue": "rested",
            "load": "normal",
        },
    }


def _make_app_with_router(router, pool) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_pool] = lambda: pool
    return app


@pytest.mark.regression
def test_session_new_rejects_negative_coin_with_422() -> None:
    app = _make_app_with_router(session.router, FakePool(FakeConn()))

    with TestClient(app) as client:
        r = client.post(
            "/session/new",
            json={
                "character_name": "Broke",
                "ancestry": "human",
                "culture": "drakenvale_city",
                "focus": "champion",
                "background": "soldier",
                "starting_economy": {"wealth_tier": "modest", "coin": -5},
            },
        )

    assert r.status_code == 422


@pytest.mark.regression
def test_session_new_rejects_invalid_wealth_tier_with_422() -> None:
    app = _make_app_with_router(session.router, FakePool(FakeConn()))

    with TestClient(app) as client:
        r = client.post(
            "/session/new",
            json={
                "character_name": "Rich",
                "ancestry": "human",
                "culture": "drakenvale_city",
                "focus": "champion",
                "background": "soldier",
                "starting_economy": {"wealth_tier": "billionaire", "coin": 0},
            },
        )

    assert r.status_code == 422


@pytest.mark.regression
def test_state_save_rejects_invalid_merged_character_from_legacy_extra_key() -> None:
    existing_character = _build_valid_character()
    existing_character["legacy_field"] = "should-not-survive"

    conn = FakeConn(
        select_character=existing_character,
        select_world=_build_valid_world(),
    )

    app = _make_app_with_router(state.router, FakePool(conn))
    save_body = {
        "character": _build_valid_character(),
        "world": _build_valid_world(),
        "log_entry": "entry",
    }

    with TestClient(app) as client:
        r = client.post("/state/abc12345", json=save_body)

    assert r.status_code == 422


@pytest.mark.regression
def test_state_save_rejects_negative_coin_with_422() -> None:
    app = _make_app_with_router(state.router, FakePool(FakeConn()))
    save_body = {
        "character": _build_valid_character(),
        "world": {
            **_build_valid_world(),
            "economy": {
                "wealth_tier": "modest",
                "coin": -1,
                "trade_goods": [],
                "obligations": [],
            },
        },
        "log_entry": "entry",
    }

    with TestClient(app) as client:
        r = client.post("/state/abc12345", json=save_body)

    assert r.status_code == 422


@pytest.mark.regression
def test_state_save_rejects_invalid_time_day_with_422() -> None:
    app = _make_app_with_router(state.router, FakePool(FakeConn()))
    save_body = {
        "character": _build_valid_character(),
        "world": {
            **_build_valid_world(),
            "time": {
                **_build_valid_world()["time"],
                "day": 31,
            },
        },
        "log_entry": "entry",
    }

    with TestClient(app) as client:
        r = client.post("/state/abc12345", json=save_body)

    assert r.status_code == 422


@pytest.mark.regression
def test_state_save_rejects_invalid_time_weather_with_422() -> None:
    app = _make_app_with_router(state.router, FakePool(FakeConn()))
    save_body = {
        "character": _build_valid_character(),
        "world": {
            **_build_valid_world(),
            "time": {
                **_build_valid_world()["time"],
                "weather": "sandstorm",
            },
        },
        "log_entry": "entry",
    }

    with TestClient(app) as client:
        r = client.post("/state/abc12345", json=save_body)

    assert r.status_code == 422


@pytest.mark.regression
def test_state_save_rejects_domain_above_80_with_422() -> None:
    app = _make_app_with_router(state.router, FakePool(FakeConn()))
    save_body = {
        "character": {
            **_build_valid_character(),
            "domains": {
                **_build_valid_character()["domains"],
                "will": 81,
            },
        },
        "world": _build_valid_world(),
        "log_entry": "entry",
    }

    with TestClient(app) as client:
        r = client.post("/state/abc12345", json=save_body)

    assert r.status_code == 422


@pytest.mark.regression
def test_state_save_rejects_negative_advancement_points_with_422() -> None:
    app = _make_app_with_router(state.router, FakePool(FakeConn()))
    save_body = {
        "character": {
            **_build_valid_character(),
            "advancement": {
                "points_available": -1,
                "points_spent": 0,
                "points_earned_total": 0,
            },
        },
        "world": _build_valid_world(),
        "log_entry": "entry",
    }

    with TestClient(app) as client:
        r = client.post("/state/abc12345", json=save_body)

    assert r.status_code == 422


@pytest.mark.regression
def test_state_save_accepts_valid_advancement_block() -> None:
    valid_character = _build_valid_character()
    valid_character["advancement"] = {
        "points_available": 2,
        "points_spent": 1,
        "points_earned_total": 3,
    }

    conn = FakeConn(
        select_character=_build_valid_character(),
        upsert_row={
            "session_id": "abc12345",
            "character": json.dumps(valid_character),
            "world": json.dumps(_build_valid_world()),
            "log": json.dumps(["advancement persisted"]),
            "updated_at": datetime.now(),
        },
    )

    app = _make_app_with_router(state.router, FakePool(conn))
    save_body = {
        "character": valid_character,
        "world": _build_valid_world(),
        "log_entry": "advancement persisted",
    }

    with TestClient(app) as client:
        r = client.post("/state/abc12345", json=save_body)

    assert r.status_code == 200
    payload = r.json()
    assert payload["character"]["advancement"]["points_available"] == 2
    assert payload["character"]["advancement"]["points_spent"] == 1
    assert payload["character"]["advancement"]["points_earned_total"] == 3



@pytest.mark.regression
def test_state_save_preserves_existing_world_structured_blocks_when_legacy_payload_omits_them() -> None:
    existing_world = _build_valid_world()
    existing_world["time"]["weather"] = "mist"
    existing_world["survival"]["fatigue"] = "tired"
    existing_world["pacing"]["tension"] = 6

    conn = FakeConn(
        select_character=_build_valid_character(),
        select_world=existing_world,
    )

    app = _make_app_with_router(state.router, FakePool(conn))
    legacy_world = {
        "location": "test-loc-alpha",
        "threat": "stormfront",
        "goal": "survive",
        "turn": 2,
        "companions": [],
        "economy": _build_valid_world()["economy"],
        "politics": _build_valid_world()["politics"],
    }

    with TestClient(app) as client:
        r = client.post(
            "/state/abc12345",
            json={
                "character": _build_valid_character(),
                "world": legacy_world,
                "log_entry": "legacy world persisted",
            },
        )

    assert r.status_code == 200
    payload = r.json()
    assert payload["world"]["time"]["weather"] == "mist"
    assert payload["world"]["survival"]["fatigue"] == "tired"
    assert payload["world"]["pacing"]["tension"] == 6
    assert payload["world"]["pacing"]["turn_count"] == 2




@pytest.mark.regression
def test_state_delta_rejects_empty_delta_with_422() -> None:
    app = _make_app_with_router(state.router, FakePool(FakeConn()))

    with TestClient(app) as client:
        r = client.post(
            "/state/abc12345/delta",
            json={
                "character": {},
                "world": {},
                "log_entry": "noop",
            },
        )

    assert r.status_code == 422


@pytest.mark.regression
def test_state_delta_rejects_unknown_field_with_422() -> None:
    app = _make_app_with_router(state.router, FakePool(FakeConn()))

    with TestClient(app) as client:
        r = client.post(
            "/state/abc12345/delta",
            json={
                "character": {"unknown_field": "x"},
                "log_entry": "bad",
            },
        )

    assert r.status_code == 422


@pytest.mark.regression
def test_state_delta_returns_404_when_session_not_found() -> None:
    app = _make_app_with_router(state.router, FakePool(FakeConn()))

    with TestClient(app) as client:
        r = client.post(
            "/state/missing/delta",
            json={
                "character": {"notes": "delta note"},
                "log_entry": "entry",
            },
        )

    assert r.status_code == 404



@pytest.mark.regression
def test_session_new_response_session_id_round_trips_into_first_delta_save() -> None:
    app = FastAPI()
    app.include_router(session.router)
    app.include_router(state.router)
    pool = FakePool(SessionDeltaFlowConn())
    app.dependency_overrides[get_pool] = lambda: pool

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

        delta = client.post(
            f"/state/{session_id}/delta",
            json={
                "character": {"notes": "first delta"},
                "log_entry": "first delta",
            },
        )

        assert delta.status_code == 200
        payload = delta.json()
        assert payload["session_id"] == session_id
        assert payload["character"]["notes"] == "first delta"
