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


class FakeConn:
    def __init__(self, *, select_character=None, upsert_row=None):
        self.select_character = select_character
        self.upsert_row = upsert_row
        self.execute_calls: list[tuple[str, tuple]] = []

    async def execute(self, query, *args):
        self.execute_calls.append((query, args))
        return "OK"

    async def fetchrow(self, query, *args):
        if "SELECT character FROM game_states" in query:
            if self.select_character is None:
                return None
            return {"character": json.dumps(self.select_character)}

        if "RETURNING session_id, character, world, log, updated_at" in query:
            return self.upsert_row

        return None


def _build_valid_character() -> dict:
    return {
        "name": "Krath",
        "species": "dragonborn",
        "focus": "devoted",
        "background": "soldier",
        "level": 1,
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
    }


def _build_valid_world() -> dict:
    return {
        "location": "test-loc-alpha",
        "threat": "none",
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
                "species": "human",
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
                "species": "human",
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
        upsert_row={
            "session_id": "abc12345",
            "character": json.dumps(_build_valid_character()),
            "world": json.dumps(_build_valid_world()),
            "log": json.dumps(["entry"]),
            "updated_at": datetime.now(),
        },
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
