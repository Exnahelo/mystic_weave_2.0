import json
from copy import deepcopy
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


class MultiTurnFakeConn:
    def __init__(self, session_id: str, initial_character: dict, initial_world: dict):
        self.session_id = session_id
        self.character = deepcopy(initial_character)
        self.world = deepcopy(initial_world)
        self.log: list[str] = []
        self.updated_at = datetime.now()

    async def fetchrow(self, query, *args):
        if "SELECT session_id, character, world, log, updated_at FROM game_states" in query:
            return {
                "session_id": self.session_id,
                "character": json.dumps(self.character),
                "world": json.dumps(self.world),
                "log": json.dumps(self.log),
                "updated_at": self.updated_at,
            }

        if "SELECT character FROM game_states" in query:
            return {"character": json.dumps(self.character)}

        if "SELECT character, world FROM game_states" in query:
            return {
                "character": json.dumps(self.character),
                "world": json.dumps(self.world),
            }

        if "RETURNING session_id, character, world, log, updated_at" in query:
            # args follow save_state SQL in routes/state.py
            # 0 session_id
            # 1 character json (merged + validated)
            # 2 world json
            # 3 initial log for insert (unused in conflict case)
            # 4 update log append json
            self.character = json.loads(args[1])
            self.world = json.loads(args[2])
            append_entries = json.loads(args[4])
            self.log.extend(append_entries)
            self.updated_at = datetime.now()
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


def _base_character() -> dict:
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
        "knowledge": {"discipline": 2, "courage": 1},
        "application": {"sacred_rites": 1, "shields_armor": 1},
        "status_effects": [],
        "notes": "",
        "identity": {
            "origin": "Exile",
            "motivations": ["Survive"],
            "quirks": ["Counts exits"],
            "bonds": ["Silver Oath"],
            "flaws": ["Distrustful"],
            "wound": "Council scar",
            "alignment": {"order": "lawful", "intent": "good", "ethos_note": ""},
        },
        "equipment": {
            "worn": [{"id": "armor_1", "name": "Mail", "description": "", "tags": ["armor"], "roll_tag": "shields_armor"}],
            "carried": [{"id": "torch_1", "name": "Torch", "description": "", "tags": ["utility"], "roll_tag": None}],
            "stashed": [],
        },
        "reputation": [
            {"faction": "draconic_council", "standing": -25, "note": "exiled", "last_change": "turn 0"}
        ],
        "advancement": {
            "points_available": 0,
            "points_spent": 0,
            "points_earned_total": 0,
        },
    }


def _base_world() -> dict:
    return {
        "location": "test-loc-alpha",
        "threat": "low",
        "goal": "survive",
        "turn": 1,
        "pacing": {
            "tension": 3,
            "last_consequence_weight": "local",
            "turns_since_social_beat": 0,
            "turns_since_discovery": 0,
            "turn_count": 1,
        },
        "companions": [
            {
                "id": "comp_1",
                "tier": "sapient",
                "name": "Sorra",
                "ancestry": "halfling",
                "culture": "riverfolk",
                "background": "scout",
                "focus": "wanderer",
                "identity": {
                    "origin": "",
                    "motivations": ["Stay alive"],
                    "quirks": ["Never sits with back to door"],
                    "bonds": [],
                    "flaws": [],
                    "wound": "",
                    "alignment": {"order": "neutral", "intent": "neutral", "ethos_note": ""},
                },
                "hp": {"current": 100, "max": 100},
                "domains": {
                    "power": 35,
                    "agility": 40,
                    "perception": 45,
                    "endurance": 35,
                    "intellect": 38,
                    "will": 37,
                    "presence": 42,
                },
                "knowledge": {},
                "application": {},
                "equipment": {"worn": [], "carried": [], "stashed": []},
                "bond_links": {"primary": "krath"},
                "reputation": [],
            }
        ],
        "economy": {
            "wealth_tier": "modest",
            "coin": 1200,
            "trade_goods": ["salt"],
            "obligations": ["caravan debt"],
        },
        "politics": {
            "faction_memberships": [],
            "active_obligations": [],
            "legal_standing": "unknown",
            "known_leverage": [],
            "active_tensions": [],
            "conclave_status": "unknown",
        },
    }


@pytest.mark.regression
def test_multi_turn_partial_updates_preserve_nested_identity_and_equipment() -> None:
    session_id = "turnchain1"
    conn = MultiTurnFakeConn(session_id, _base_character(), _base_world())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        # Turn 2: update hp + add status effect, intentionally omit many nested fields
        turn2_character = deepcopy(_base_character())
        turn2_character["hp"]["current"] = 82
        turn2_character["status_effects"] = ["bleeding"]
        # Ensure identity/equipment still present in request model but unchanged

        turn2_world = deepcopy(_base_world())
        turn2_world["turn"] = 2
        turn2_world["threat"] = "medium"

        r2 = client.post(
            f"/state/{session_id}",
            json={"character": turn2_character, "world": turn2_world, "log_entry": "Turn 2 applied."},
        )
        assert r2.status_code == 200

        # Turn 3: mutate a different subset and assert continuity
        turn3_character = deepcopy(r2.json()["character"])
        turn3_character["hp"]["current"] = 70
        turn3_character["notes"] = "Ambushed at the ridge"

        turn3_world = deepcopy(r2.json()["world"])
        turn3_world["turn"] = 3
        turn3_world["goal"] = "reach stronghold"

        r3 = client.post(
            f"/state/{session_id}",
            json={"character": turn3_character, "world": turn3_world, "log_entry": "Turn 3 applied."},
        )
        assert r3.status_code == 200
        body = r3.json()

        assert body["character"]["identity"]["origin"] == "Exile"
        assert body["character"]["equipment"]["worn"][0]["name"] == "Mail"
        assert body["character"]["status_effects"] == ["bleeding"]
        assert body["character"]["notes"] == "Ambushed at the ridge"
        assert body["world"]["turn"] == 3
        assert body["world"]["pacing"]["turn_count"] == 3
        assert body["world"]["goal"] == "reach stronghold"
        assert body["log"] == ["Turn 2 applied.", "Turn 3 applied."]


@pytest.mark.regression
def test_multi_turn_companion_lifecycle_and_political_economy_progression() -> None:
    session_id = "turnchain2"
    conn = MultiTurnFakeConn(session_id, _base_character(), _base_world())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        # Turn 2: companion incapacitated, economy/politics changed
        char2 = deepcopy(_base_character())
        world2 = deepcopy(_base_world())
        world2["turn"] = 2
        world2["companions"][0]["hp"]["current"] = 0
        world2["economy"]["coin"] = 300
        world2["economy"]["obligations"].append("owes healer")
        world2["politics"]["legal_standing"] = "wanted"
        world2["politics"]["active_tensions"] = ["Guard patrol escalation"]

        r2 = client.post(
            f"/state/{session_id}",
            json={"character": char2, "world": world2, "log_entry": "Companion down."},
        )
        assert r2.status_code == 200

        # Turn 3: companion departs, equipment moved, politics evolves
        char3 = deepcopy(r2.json()["character"])
        char3["equipment"]["stashed"].append(char3["equipment"]["carried"][0])
        char3["equipment"]["carried"] = []

        world3 = deepcopy(r2.json()["world"])
        world3["turn"] = 3
        world3["politics"]["known_leverage"] = ["captain bribery ledger"]
        world3["economy"]["wealth_tier"] = "destitute"

        r3 = client.post(
            f"/state/{session_id}",
            json={"character": char3, "world": world3, "log_entry": "Companion departed."},
        )
        assert r3.status_code == 200
        body = r3.json()

        comp = body["world"]["companions"][0]
        assert comp["hp"]["current"] == 0
        assert body["world"]["economy"]["coin"] == 300
        assert body["world"]["economy"]["wealth_tier"] == "destitute"
        assert body["world"]["pacing"]["turn_count"] == 3
        assert "owes healer" in body["world"]["economy"]["obligations"]
        assert body["world"]["politics"]["legal_standing"] == "wanted"
        assert body["world"]["politics"]["known_leverage"] == ["captain bribery ledger"]
        assert body["character"]["equipment"]["carried"] == []
        assert len(body["character"]["equipment"]["stashed"]) == 1
        assert body["log"] == ["Companion down.", "Companion departed."]


@pytest.mark.regression
def test_delta_save_applies_partial_updates_and_preserves_unsent_fields() -> None:
    session_id = "deltachain1"
    conn = MultiTurnFakeConn(session_id, _base_character(), _base_world())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            f"/state/{session_id}/delta",
            json={
                "character": {"notes": "Delta note"},
                "world": {"turn": 2, "threat": "medium"},
                "log_entry": "Delta applied.",
            },
        )

    assert r.status_code == 200
    body = r.json()
    assert body["character"]["notes"] == "Delta note"
    assert body["character"]["identity"]["origin"] == "Exile"
    assert body["world"]["turn"] == 2
    assert body["world"]["threat"] == "medium"
    assert body["world"]["goal"] == "survive"
    assert body["world"]["pacing"]["turn_count"] == 2
    assert body["log"] == ["Delta applied."]


@pytest.mark.regression
def test_delta_save_validation_failure_does_not_commit_state_or_log() -> None:
    session_id = "deltachain2"
    base_character = _base_character()
    base_world = _base_world()
    conn = MultiTurnFakeConn(session_id, base_character, base_world)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            f"/state/{session_id}/delta",
            json={
                "world": {"turn": 0},
                "log_entry": "Should not persist.",
            },
        )

    assert r.status_code == 422
    assert conn.character["notes"] == base_character["notes"]
    assert conn.world["turn"] == base_world["turn"]
    assert conn.log == []



@pytest.mark.regression
def test_delta_save_persists_draconic_traits() -> None:
    session_id = "deltadraconic1"
    conn = MultiTurnFakeConn(session_id, _base_character(), _base_world())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            f"/state/{session_id}/delta",
            json={
                "character": {"draconic_traits": ["dragon_breath", "scaled_hide"]},
                "log_entry": "Draconic traits updated.",
            },
        )

        assert r.status_code == 200
        payload = r.json()
        assert payload["character"]["draconic_traits"] == ["dragon_breath", "scaled_hide"]

        loaded = client.get(f"/state/{session_id}")

    assert loaded.status_code == 200
    assert loaded.json()["character"]["draconic_traits"] == ["dragon_breath", "scaled_hide"]


@pytest.mark.regression
def test_delta_save_updates_coin_without_overwriting_other_economy_fields() -> None:
    session_id = "deltaeconomy1"
    conn = MultiTurnFakeConn(session_id, _base_character(), _base_world())
    app = _make_app(FakePool(conn))

    conn.world["economy"] = {
        "wealth_tier": "wealthy",
        "coin": 1200,
        "trade_goods": ["salt", "silk"],
        "obligations": ["caravan debt", "guild tithe"],
    }

    with TestClient(app) as client:
        r = client.post(
            f"/state/{session_id}/delta",
            json={
                "world": {"economy": {"coin": 300}},
                "log_entry": "Spent coin.",
            },
        )

        assert r.status_code == 200
        payload = r.json()

        assert payload["world"]["economy"]["coin"] == 300
        assert payload["world"]["economy"]["wealth_tier"] == "wealthy"
        assert payload["world"]["economy"]["trade_goods"] == ["salt", "silk"]
        assert payload["world"]["economy"]["obligations"] == ["caravan debt", "guild tithe"]

        loaded = client.get(f"/state/{session_id}")

    assert loaded.status_code == 200
    loaded_economy = loaded.json()["world"]["economy"]
    assert loaded_economy["coin"] == 300
    assert loaded_economy["wealth_tier"] == "wealthy"
    assert loaded_economy["trade_goods"] == ["salt", "silk"]
    assert loaded_economy["obligations"] == ["caravan debt", "guild tithe"]


@pytest.mark.regression
def test_full_save_partial_payload_preserves_knowledge_and_application() -> None:
    session_id = "fullsave1"
    base_character = _base_character()
    base_world = _base_world()
    conn = MultiTurnFakeConn(session_id, base_character, base_world)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            f"/state/{session_id}",
            json={
                "character": {
                    "hp": {"current": 88, "max": 100},
                    "notes": "Partial full-save update.",
                },
                "world": {
                    "turn": 2,
                    "threat": "medium",
                },
                "log_entry": "Partial full save applied.",
            },
        )

    assert r.status_code == 200
    body = r.json()
    assert body["character"]["hp"]["current"] == 88
    assert body["character"]["notes"] == "Partial full-save update."
    assert body["character"]["knowledge"] == base_character["knowledge"]
    assert body["character"]["application"] == base_character["application"]
    assert body["world"]["turn"] == 2
    assert body["world"]["threat"] == "medium"
    assert body["world"]["goal"] == base_world["goal"]
    assert body["world"]["pacing"]["turn_count"] == 2
    assert body["log"] == ["Partial full save applied."]
