import json
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import advancement
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


class _TransactionCtx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


class SpendConn:
    def __init__(self, character: dict | None):
        self.character = character
        self.updated_at = datetime.now()

    def transaction(self):
        return _TransactionCtx()

    async def fetchrow(self, query, *args):
        if "SELECT character FROM game_states" in query:
            if self.character is None:
                return None
            return {"character": json.dumps(self.character)}
        return None

    async def execute(self, query, *args):
        self.character = json.loads(args[0])
        self.updated_at = datetime.now()
        return "UPDATE 1"


def _make_app(pool) -> FastAPI:
    app = FastAPI()
    app.include_router(advancement.router)
    app.dependency_overrides[get_pool] = lambda: pool
    return app


def _character() -> dict:
    advancement_state = zero_advancement()
    advancement_state["points_available"] = 8
    return {
        "name": "Krath",
        "ancestry": "human",
        "culture": "drakenvale_city",
        "focus": "devoted",
        "background": "soldier",
        "hp": {"current": 100, "max": 100},
        "domains": {
            "power": 50,
            "agility": 35,
            "perception": 35,
            "endurance": 43,
            "intellect": 25,
            "will": 47,
            "presence": 59,
        },
        "knowledge": {},
        "application": {},
        "fields": {},
        "status_effects": [],
        "notes": "",
        "identity": {"origin": "", "motivations": [], "quirks": [], "bonds": [], "flaws": [], "wound": "", "alignment": {"order": "neutral", "intent": "neutral", "ethos_note": ""}},
        "equipment": {"worn": [], "carried": [], "stashed": []},
        "reputation": [],
        "advancement": advancement_state,
    }


@pytest.mark.contract
def test_spend_from_fungible_pool_succeeds() -> None:
    app = _make_app(FakePool(SpendConn(_character())))
    with TestClient(app) as client:
        response = client.post(
            "/character/sess1/spend_ap",
            json={"target_domain": "power", "points": 1},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ap_cost_total"] == 1
    assert payload["new_domain_score"] == 51
    assert payload["advancement"]["points_available"] == 7
    assert payload["advancement"]["points_spent"] == 1
    assert "ap_drawn_earned" not in payload
    assert "ap_drawn_awarded" not in payload


@pytest.mark.contract
def test_spend_crossing_bracket_succeeds() -> None:
    app = _make_app(FakePool(SpendConn(_character())))
    with TestClient(app) as client:
        response = client.post(
            "/character/sess1/spend_ap",
            json={"target_domain": "presence", "points": 2},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ap_cost_total"] == 3
    assert payload["new_domain_score"] == 61
    assert payload["advancement"]["points_available"] == 5


@pytest.mark.contract
def test_spend_insufficient_ap_returns_422() -> None:
    character = _character()
    character["advancement"]["points_available"] = 0
    app = _make_app(FakePool(SpendConn(character)))
    with TestClient(app) as client:
        response = client.post(
            "/character/sess1/spend_ap",
            json={"target_domain": "presence", "points": 1},
        )
    assert response.status_code == 422


@pytest.mark.contract
def test_spend_exact_ap_succeeds() -> None:
    character = _character()
    character["advancement"]["points_available"] = 3
    app = _make_app(FakePool(SpendConn(character)))
    with TestClient(app) as client:
        response = client.post(
            "/character/sess1/spend_ap",
            json={"target_domain": "presence", "points": 2},
        )
    assert response.status_code == 200
    assert response.json()["advancement"]["points_available"] == 0


@pytest.mark.contract
def test_spend_unknown_domain_returns_422() -> None:
    app = _make_app(FakePool(SpendConn(_character())))
    with TestClient(app) as client:
        response = client.post(
            "/character/sess1/spend_ap",
            json={"target_domain": "luck", "points": 1},
        )
    assert response.status_code == 422


@pytest.mark.contract
def test_spend_missing_session_returns_404() -> None:
    app = _make_app(FakePool(SpendConn(None)))
    with TestClient(app) as client:
        response = client.post(
            "/character/missing/spend_ap",
            json={"target_domain": "power", "points": 1},
        )
    assert response.status_code == 404


@pytest.mark.contract
def test_spend_above_cap_returns_422() -> None:
    character = _character()
    character["domains"]["power"] = 80
    app = _make_app(FakePool(SpendConn(character)))
    with TestClient(app) as client:
        response = client.post(
            "/character/sess1/spend_ap",
            json={"target_domain": "power", "points": 1},
        )
    assert response.status_code == 422