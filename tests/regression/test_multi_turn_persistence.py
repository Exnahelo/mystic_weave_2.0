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
        if "SELECT character FROM game_states" in query:
            return {"character": json.dumps(self.character)}

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
        "species": "dragonborn",
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
        "companions": [
            {
                "id": "comp_1",
                "name": "Sorra",
                "species": "halfling",
                "role": "guide",
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
                "domains": None,
                "knowledge": {},
                "application": {},
                "status": "active",
                "disposition": 25,
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
        world2["companions"][0]["status"] = "incapacitated"
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
        world3["companions"][0]["status"] = "departed"
        world3["politics"]["known_leverage"] = ["captain bribery ledger"]
        world3["economy"]["wealth_tier"] = "destitute"

        r3 = client.post(
            f"/state/{session_id}",
            json={"character": char3, "world": world3, "log_entry": "Companion departed."},
        )
        assert r3.status_code == 200
        body = r3.json()

        comp = body["world"]["companions"][0]
        assert comp["status"] == "departed"
        assert comp["hp"]["current"] == 0
        assert body["world"]["economy"]["coin"] == 300
        assert body["world"]["economy"]["wealth_tier"] == "destitute"
        assert "owes healer" in body["world"]["economy"]["obligations"]
        assert body["world"]["politics"]["legal_standing"] == "wanted"
        assert body["world"]["politics"]["known_leverage"] == ["captain bribery ledger"]
        assert body["character"]["equipment"]["carried"] == []
        assert len(body["character"]["equipment"]["stashed"]) == 1
        assert body["log"] == ["Companion down.", "Companion departed."]
