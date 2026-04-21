import json
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import companion


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


class CompanionRouteConn:
    def __init__(self, session_id: str, character: dict, world: dict):
        self.session_id = session_id
        self.character = character
        self.world = world
        self.log: list[str] = []

    async def fetchrow(self, query, *args):
        if "SELECT character, world FROM game_states" in query:
            if args[0] != self.session_id:
                return None
            return {
                "character": json.dumps(self.character),
                "world": json.dumps(self.world),
            }

        if "INSERT INTO game_states" in query and "RETURNING session_id" in query:
            self.character = json.loads(args[1])
            self.world = json.loads(args[2])
            self.log.extend(json.loads(args[4]))
            return {"session_id": args[0]}

        return None


def _make_app(pool) -> FastAPI:
    app = FastAPI()
    app.include_router(companion.router)
    app.dependency_overrides[get_pool] = lambda: pool
    return app


def _character() -> dict:
    return {
        "name": "Sylvara Heartwood",
        "ancestry": "elf",
        "culture": "feywood_glade",
        "focus": "wanderer",
        "background": "scout",
        "hp": {"current": 100, "max": 100},
        "domains": {
            "power": 35,
            "agility": 45,
            "perception": 50,
            "endurance": 38,
            "intellect": 40,
            "will": 44,
            "presence": 46,
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
            "alignment": {"order": "neutral", "intent": "good", "ethos_note": ""},
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
        "location": "feywood_glade",
        "threat": "none",
        "goal": "explore",
        "turn": 1,
        "companions": [],
        "companion_archive": [],
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
        "pacing": {
            "tension": 3,
            "last_consequence_weight": "local",
            "turns_since_social_beat": 0,
            "turns_since_discovery": 0,
            "turn_count": 1,
        },
    }


def _creature_payload(name: str = "Ash") -> dict:
    return {
        "name": name,
        "species": "wolf",
        "subtype": "moonthorn_wolf",
        "size": "medium",
        "age_category": "adult",
        "tactical_roles": ["hunter", "scout"],
        "training_level": "trained",
        "bond_level": "bonded",
        "natural_abilities": ["keen_senses"],
        "learned_commands": ["heel"],
        "movement_modes": ["walk"],
        "natural_weapons": ["bite"],
        "carrying_capacity": "small",
        "hp": {"current": 10, "max": 10},
        "domains": {"physical": 40, "instinct": 42, "composure": 38},
        "temperament": "Alert",
        "bond_links": {"primary": "sylvara_heartwood"},
    }


def _exceptional_payload() -> dict:
    return {
        "name": "Ash",
        "species": "wolf",
        "subtype": "moonthorn_wolf",
        "size": "medium",
        "age_category": "adult",
        "tactical_roles": ["hunter", "scout"],
        "training_level": "trained",
        "bond_level": "bonded",
        "natural_abilities": ["keen_senses"],
        "learned_commands": ["heel"],
        "movement_modes": ["walk"],
        "natural_weapons": ["bite"],
        "carrying_capacity": "small",
        "hp": {"current": 10, "max": 10},
        "temperament": "Alert",
        "bond_links": {"primary": "sylvara_heartwood"},
        "exceptional_profile": {
            "sapience": "partial",
            "communication": "symbolic",
            "autonomy": "moderate",
        },
        "motivations": ["Protect handler"],
        "domains": {"physical": 40, "instinct": 42, "composure": 38},
    }


@pytest.mark.contract
def test_post_companion_new_valid_creature_returns_generated_id() -> None:
    app = _make_app(FakePool(CompanionRouteConn("sess1", _character(), _world())))
    with TestClient(app) as client:
        response = client.post(
            "/companion/new",
            json={
                "session_id": "sess1",
                "handler_id": "sylvara_heartwood",
                "tier": "creature",
                "companion": _creature_payload(),
            },
        )
    assert response.status_code == 201
    payload = response.json()
    assert payload["companion_id"] == "sylvara_heartwood_moonthorn_wolf"


@pytest.mark.contract
def test_post_companion_new_missing_session_returns_404() -> None:
    app = _make_app(FakePool(CompanionRouteConn("sess1", _character(), _world())))
    with TestClient(app) as client:
        response = client.post(
            "/companion/new",
            json={
                "session_id": "missing",
                "handler_id": "sylvara_heartwood",
                "tier": "creature",
                "companion": _creature_payload(),
            },
        )
    assert response.status_code == 404


@pytest.mark.contract
def test_post_companion_new_invalid_handler_returns_409() -> None:
    app = _make_app(FakePool(CompanionRouteConn("sess1", _character(), _world())))
    with TestClient(app) as client:
        response = client.post(
            "/companion/new",
            json={
                "session_id": "sess1",
                "handler_id": "not_the_character",
                "tier": "creature",
                "companion": _creature_payload(),
            },
        )
    assert response.status_code == 409


@pytest.mark.contract
def test_post_companion_new_second_same_subspecies_gets_suffix() -> None:
    world = _world()
    world["companions"] = [{"id": "sylvara_heartwood_moonthorn_wolf", "companion": _creature_payload()}]
    app = _make_app(FakePool(CompanionRouteConn("sess1", _character(), world)))
    with TestClient(app) as client:
        response = client.post(
            "/companion/new",
            json={
                "session_id": "sess1",
                "handler_id": "sylvara_heartwood",
                "tier": "creature",
                "companion": _creature_payload(name="Birch"),
            },
        )
    assert response.status_code == 201
    assert response.json()["companion_id"] == "sylvara_heartwood_moonthorn_wolf_2"


@pytest.mark.contract
def test_get_companion_returns_envelope() -> None:
    world = _world()
    world["companions"] = [{"id": "sylvara_heartwood_moonthorn_wolf", "companion": _creature_payload()}]
    app = _make_app(FakePool(CompanionRouteConn("sess1", _character(), world)))
    with TestClient(app) as client:
        response = client.get("/companion/sylvara_heartwood_moonthorn_wolf", params={"session_id": "sess1"})
    assert response.status_code == 200
    assert response.json()["companion_id"] == "sylvara_heartwood_moonthorn_wolf"


@pytest.mark.contract
def test_get_companion_nonexistent_returns_404() -> None:
    app = _make_app(FakePool(CompanionRouteConn("sess1", _character(), _world())))
    with TestClient(app) as client:
        response = client.get("/companion/missing_companion", params={"session_id": "sess1"})
    assert response.status_code == 404


@pytest.mark.contract
def test_post_companion_transition_creature_to_exceptional_archives_old_record() -> None:
    world = _world()
    world["companions"] = [{"id": "sylvara_heartwood_moonthorn_wolf", "companion": _creature_payload()}]
    conn = CompanionRouteConn("sess1", _character(), world)
    app = _make_app(FakePool(conn))
    with TestClient(app) as client:
        response = client.post(
            "/companion/sylvara_heartwood_moonthorn_wolf/transition",
            json={
                "session_id": "sess1",
                "new_companion": _exceptional_payload(),
                "trigger": "Awakened in moonlit rite",
            },
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["companion_id"] == "sylvara_heartwood_moonthorn_wolf"
    archived = conn.world["companion_archive"]
    assert len(archived) == 1
    assert archived[0]["id"] == "sylvara_heartwood_moonthorn_wolf"
    tier_history = conn.world["companions"][0]["companion"]["tier_history"]
    assert len(tier_history) == 1
    assert tier_history[0]["from_tier"] == "creature"


@pytest.mark.contract
def test_post_companion_transition_non_creature_returns_422() -> None:
    world = _world()
    world["companions"] = [{"id": "sylvara_heartwood_whisper", "companion": _exceptional_payload()}]
    app = _make_app(FakePool(CompanionRouteConn("sess1", _character(), world)))
    with TestClient(app) as client:
        response = client.post(
            "/companion/sylvara_heartwood_whisper/transition",
            json={
                "session_id": "sess1",
                "new_companion": _exceptional_payload(),
                "trigger": "Invalid second transition",
            },
        )
    assert response.status_code == 422