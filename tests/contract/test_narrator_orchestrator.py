"""Contract tests for POST /narrator/scene_resolved (Brief 20)."""
from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import narrator as narrator_routes
from tests.helpers import zero_advancement


# ---------------------------------------------------------------------------
# Async-context scaffolding
# ---------------------------------------------------------------------------

class _AcquireCtx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return None


class _TxCtx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        # Snapshot the conn's mutable state so we can rollback on exception.
        self._conn._snapshot()
        return None

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self._conn._rollback()
        return False


class FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _AcquireCtx(self._conn)


# ---------------------------------------------------------------------------
# Comprehensive fake conn supporting orchestrator + scene_records + commit SQL
# ---------------------------------------------------------------------------

class NarratorConn:
    """Stub connection covering every SQL the orchestrator and its helpers issue."""

    def __init__(self, session_id: str, character: dict, world: dict, log: list | None = None):
        self.session_id = session_id
        self.character: dict = character
        self.world: dict = world
        self.log: list = log if log is not None else []
        self.updated_at: datetime | None = datetime(2026, 5, 3, tzinfo=timezone.utc)
        self.arcs: dict[str, dict[str, Any]] = {}  # arc_id -> {session_id, state, data}
        self.scene_records: dict[str, dict[str, Any]] = {}  # scene_id -> row
        self._monotonic = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)
        # For transactional rollback of in-memory state
        self._snapshot_state: tuple | None = None

    def _snapshot(self) -> None:
        self._snapshot_state = (
            copy.deepcopy(self.character),
            copy.deepcopy(self.world),
            copy.deepcopy(self.log),
            copy.deepcopy(self.scene_records),
            self.updated_at,
        )

    def _rollback(self) -> None:
        if self._snapshot_state is None:
            return
        self.character, self.world, self.log, self.scene_records, self.updated_at = self._snapshot_state

    def _next_ts(self) -> datetime:
        self._monotonic += timedelta(seconds=1)
        return self._monotonic

    def add_arc(self, arc_id: str, *, state: str = "in_progress", data: dict | None = None) -> None:
        if data is None:
            data = {
                "title": arc_id,
                "state": state,
                "budget": {
                    "resolved_scene_soft_cap": 4,
                    "resolved_scene_hard_cap": 6,
                    "location_soft_cap": 3,
                    "location_hard_cap": 5,
                },
            }
        self.arcs[arc_id] = {"session_id": self.session_id, "state": state, "data": data}

    def transaction(self):
        return _TxCtx(self)

    async def fetchrow(self, query: str, *args):
        # Orchestrator's initial lock-and-load
        if "SELECT character, world, log FROM game_states" in query and "FOR UPDATE" in query:
            if args[0] != self.session_id:
                return None
            return {"character": self.character, "world": self.world, "log": self.log}

        # Orchestrator's final state read (after mutations)
        if "SELECT character, world, log, updated_at" in query and "FROM game_states" in query:
            if args[0] != self.session_id:
                return None
            return {
                "character": self.character,
                "world": self.world,
                "log": self.log,
                "updated_at": self.updated_at,
            }

        # Re-read character after commit
        if "SELECT character FROM game_states" in query:
            if args[0] != self.session_id:
                return None
            return {"character": self.character}

        # declare_scene_in_transaction's world load
        if "SELECT world FROM game_states" in query:
            if args[0] != self.session_id:
                return None
            return {"world": self.world}

        # commit's character + log lock-and-load
        if "SELECT character, log FROM game_states" in query and "FOR UPDATE" in query:
            if args[0] != self.session_id:
                return None
            return {"character": self.character, "log": self.log}

        # Brief 19: scene_records lock for one-tag-per-scene check
        if "SELECT tag_advance_committed FROM scene_records" in query:
            scene_id, session_id = args[0], args[1]
            row = self.scene_records.get(scene_id)
            if row is None or row["session_id"] != session_id:
                return None
            return {"tag_advance_committed": row.get("tag_advance_committed")}

        # Scene insert readback
        if "SELECT resolved_at FROM scene_records" in query:
            row = self.scene_records.get(args[0])
            return {"resolved_at": row["resolved_at"]} if row else None

        # Envelope status: scene + location count for one arc_id
        if "SELECT COUNT(*)" in query and "arc_progressed_ids @>" in query:
            session_id = args[0]
            target_arc_ids = json.loads(args[1])
            scene_count = 0
            distinct_locs: set[str] = set()
            for r in self.scene_records.values():
                if r["session_id"] != session_id:
                    continue
                if all(aid in (r.get("arc_progressed_ids") or []) for aid in target_arc_ids):
                    scene_count += 1
                    if r.get("location_id"):
                        distinct_locs.add(r["location_id"])
            return {"scene_count": scene_count, "loc_count": len(distinct_locs)}

        return None

    async def fetch(self, query: str, *args):
        if "SELECT id FROM arcs" in query and "ANY($2::text[])" in query:
            ids = list(args[1])
            return [
                {"id": aid}
                for aid, info in self.arcs.items()
                if info["session_id"] == args[0] and aid in ids
            ]
        if "SELECT id, data FROM arcs" in query and "state = 'in_progress'" in query:
            return [
                {"id": aid, "data": info["data"]}
                for aid, info in self.arcs.items()
                if info["session_id"] == args[0] and info["state"] == "in_progress"
            ]
        return []

    async def execute(self, query: str, *args):
        # Scene record insert
        if "INSERT INTO scene_records" in query:
            self.scene_records[args[0]] = {
                "scene_id": args[0],
                "session_id": args[1],
                "scene_summary": args[2],
                "scene_actions": json.loads(args[3]),
                "arc_progressed_ids": json.loads(args[4]),
                "location_id": args[5],
                "turn_at_resolution": args[6],
                "time_at_resolution": (json.loads(args[7]) if args[7] else None),
                "tag_advance_committed": None,
                "resolved_at": self._next_ts(),
            }
            return "INSERT 0 1"

        # commit's character + log update
        if "UPDATE game_states" in query and "SET character" in query and "log = $2::jsonb" in query:
            self.character = json.loads(args[0])
            self.log = json.loads(args[1])
            self.updated_at = self._next_ts()
            return "UPDATE 1"

        # orchestrator's character + world update
        if "UPDATE game_states" in query and "SET character" in query and "world = $2::jsonb" in query:
            self.character = args[0] if isinstance(args[0], dict) else json.loads(args[0])
            self.world = args[1] if isinstance(args[1], dict) else json.loads(args[1])
            self.updated_at = self._next_ts()
            return "UPDATE 1"

        # scene_records stamp (on commit)
        if "UPDATE scene_records SET tag_advance_committed" in query:
            tag, scene_id = args[0], args[1]
            row = self.scene_records.get(scene_id)
            if row is not None:
                row["tag_advance_committed"] = tag
            return "UPDATE 1"

        return None


def _make_app(conn: NarratorConn) -> FastAPI:
    app = FastAPI()
    app.include_router(narrator_routes.router)
    app.dependency_overrides[get_pool] = lambda: FakePool(conn)
    return app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _world(*, location: str = "feywood-river-bend", turn: int = 4) -> dict[str, Any]:
    return {
        "location": location,
        "threat": "low",
        "goal": "patrol the bend",
        "turn": turn,
        "time": {
            "day": 1, "month": "Verdantrise", "year": 847,
            "time_of_day": "afternoon", "season": "spring",
            "festival": None, "weather": "clear", "weather_note": "",
        },
        "companions": [],
        "companion_archive": [],
        "economy": {"wealth_tier": "modest", "coin": 0, "trade_goods": [], "obligations": []},
        "politics": {
            "faction_memberships": [], "active_obligations": [],
            "legal_standing": "unknown", "known_leverage": [],
            "active_tensions": [], "conclave_status": "unknown",
        },
        "survival": {"hunger": "sated", "hydration": "hydrated", "fatigue": "rested", "load": "normal"},
        "pacing": {
            "tension": 3, "last_consequence_weight": "local",
            "turns_since_social_beat": 0, "turns_since_discovery": 0, "turn_count": turn,
        },
    }


def _druid_character() -> dict[str, Any]:
    return {
        "name": "Sylvara",
        "ancestry": "elf",
        "culture": "feywood_wilds",
        "focus": "warden",
        "background": "outlander",
        "hp": {"current": 100, "max": 100},
        "domains": {
            "power": 35, "agility": 45, "perception": 50,
            "endurance": 35, "intellect": 35, "will": 40, "presence": 35,
        },
        "knowledge": {
            "athletics": {"tier": 2, "applications": {"hauling": 1}},
            "nature": {"tier": 3, "applications": {"ecology": 3}},
        },
        "magic": {
            "druidry": {"tier": 2, "spells": {"seedwake": 1, "sap_mend": 1}},
        },
        "status_effects": [],
        "notes": "",
        "identity": {
            "origin": "", "motivations": [], "quirks": [], "bonds": [],
            "flaws": [], "wound": "",
            "alignment": {"order": "neutral", "intent": "neutral", "ethos_note": ""},
        },
        "equipment": {"worn": [], "carried": [], "stashed": []},
        "reputation": [],
        "advancement": zero_advancement(),
    }


def _new_conn(**overrides: Any) -> NarratorConn:
    return NarratorConn(
        session_id=overrides.get("session_id", "sess-narr"),
        character=overrides.get("character", _druid_character()),
        world=overrides.get("world", _world()),
        log=overrides.get("log", []),
    )


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_orchestrator_records_scene_only() -> None:
    """Minimal payload: scene boundary recorded, no advance, no state changes."""
    conn = _new_conn()
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/narrator/scene_resolved",
            json={"session_id": "sess-narr"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["scene_id"]
    assert body["advance_committed"] is None
    assert body["proposed_evaluation"] is None
    assert body["candidates_ranked"] == []
    assert "scene_recorded" in body["changes_applied"]
    # Scene was persisted in fake store
    assert body["scene_id"] in conn.scene_records


@pytest.mark.contract
def test_orchestrator_full_flow_with_advance() -> None:
    """Spell cast scene + matching proposed_advance: scene recorded, advance committed."""
    conn = _new_conn()
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/narrator/scene_resolved",
            json={
                "session_id": "sess-narr",
                "scene_summary": "Vine snare contains the brookside intruder.",
                "scene_actions": [
                    {"type": "spell_cast", "spell": "seedwake", "outcome": "success"},
                ],
                "proposed_advance": {"tag": "seedwake"},
            },
        )

    assert r.status_code == 200
    body = r.json()
    assert body["advance_committed"] is not None
    assert body["advance_committed"]["tag"] == "seedwake"
    assert body["advance_committed"]["new_tier"] == 2
    assert body["proposed_evaluation"]["validation"] == "proposed_match"
    # Candidates ranked: explicit seedwake first, druidry implicit second
    cand_tags = [c["tag"] for c in body["candidates_ranked"]]
    assert cand_tags[0] == "seedwake"
    assert "druidry" in cand_tags
    assert any(c.startswith("advance_committed:") for c in body["changes_applied"])
    # State_after reflects the advance
    assert body["state_after"]["character"]["magic"]["druidry"]["spells"]["seedwake"] == 2


@pytest.mark.contract
def test_orchestrator_advance_with_state_changes() -> None:
    """proposed_advance + character_changes + time_elapsed all applied atomically."""
    conn = _new_conn()
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/narrator/scene_resolved",
            json={
                "session_id": "sess-narr",
                "scene_actions": [
                    {"type": "spell_cast", "spell": "seedwake", "outcome": "success"},
                ],
                "proposed_advance": {"tag": "seedwake"},
                "character_changes": {"hp": {"current": 88, "max": 100}},
                "time_elapsed": {"steps": 1},
            },
        )

    assert r.status_code == 200
    body = r.json()
    # Advance landed
    assert body["advance_committed"]["new_tier"] == 2
    # HP applied
    assert body["state_after"]["character"]["hp"]["current"] == 88
    # Time advanced (afternoon -> dusk)
    assert body["state_after"]["world"]["time"]["time_of_day"] == "dusk"
    # Turn incremented on time advance
    assert body["state_after"]["world"]["turn"] == 5
    # Changes_applied lists each step
    applied = body["changes_applied"]
    assert "scene_recorded" in applied
    assert "advance_committed:seedwake" in applied
    assert "character.hp" in applied
    assert "time_advanced" in applied


@pytest.mark.contract
def test_orchestrator_returns_full_state_after() -> None:
    """state_after has character + world + log + updated_at."""
    conn = _new_conn()
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post("/narrator/scene_resolved", json={"session_id": "sess-narr"})

    assert r.status_code == 200
    state = r.json()["state_after"]
    assert set(state.keys()) == {"character", "world", "log", "updated_at"}
    assert isinstance(state["character"], dict)
    assert isinstance(state["world"], dict)
    assert isinstance(state["log"], list)


@pytest.mark.contract
def test_orchestrator_changes_applied_lists_steps_in_order() -> None:
    """changes_applied entries reflect what actually landed."""
    conn = _new_conn()
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/narrator/scene_resolved",
            json={
                "session_id": "sess-narr",
                "world_changes": {"threat": "rising"},
            },
        )

    body = r.json()
    assert body["changes_applied"][0] == "scene_recorded"
    assert "world.threat" in body["changes_applied"]


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_orchestrator_404_unknown_session() -> None:
    conn = _new_conn(session_id="other")
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post("/narrator/scene_resolved", json={"session_id": "missing"})

    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "session_not_found"


@pytest.mark.contract
def test_orchestrator_unknown_tag_records_scene_no_commit() -> None:
    """Unknown tag in proposed_advance: scene record persists, evaluation flags issue, no commit."""
    conn = _new_conn()
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/narrator/scene_resolved",
            json={
                "session_id": "sess-narr",
                "scene_actions": [],
                "proposed_advance": {"tag": "made_up_tag"},
            },
        )

    assert r.status_code == 200
    body = r.json()
    assert body["scene_id"]
    assert body["advance_committed"] is None
    assert body["proposed_evaluation"]["validation"] == "unknown_tag"
    assert body["proposed_evaluation"]["eligible"] is False
    # Scene still recorded
    assert body["scene_id"] in conn.scene_records


@pytest.mark.contract
def test_orchestrator_422_invalid_arc_id_rolls_back() -> None:
    """Invalid arc_progressed_ids: 422 + entire transaction rolls back."""
    conn = _new_conn()
    starting_records = dict(conn.scene_records)
    starting_character = copy.deepcopy(conn.character)
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/narrator/scene_resolved",
            json={
                "session_id": "sess-narr",
                "arc_progressed_ids": ["arc-not-real"],
                "scene_actions": [{"type": "spell_cast", "spell": "seedwake", "outcome": "success"}],
                "proposed_advance": {"tag": "seedwake"},
                "character_changes": {"hp": {"current": 50}},
            },
        )

    assert r.status_code == 422
    assert r.json()["detail"]["error"] == "unknown_arc_ids"
    # Rollback verified: no scene_records, character unchanged
    assert conn.scene_records == starting_records
    assert conn.character == starting_character


@pytest.mark.contract
def test_orchestrator_proposed_evaluation_omits_strongest() -> None:
    """Eligible weaker proposal alongside an explicit candidate: commit lands, omits_strongest flagged."""
    conn = _new_conn()
    app = _make_app(conn)

    with TestClient(app) as client:
        # Explicit candidate from spell_cast is seedwake; we propose hauling instead.
        r = client.post(
            "/narrator/scene_resolved",
            json={
                "session_id": "sess-narr",
                "scene_actions": [
                    {"type": "spell_cast", "spell": "seedwake", "outcome": "success"},
                ],
                "proposed_advance": {"tag": "hauling"},
            },
        )

    assert r.status_code == 200
    body = r.json()
    assert body["proposed_evaluation"]["validation"] == "omits_strongest"
    assert "seedwake" in (body["proposed_evaluation"]["strongest_omitted"] or [])
    # The narrator's choice still stands: commit landed.
    assert body["advance_committed"]["tag"] == "hauling"
    assert body["advance_committed"]["new_tier"] == 2


@pytest.mark.contract
def test_orchestrator_invalid_proposal_skips_commit_records_scene() -> None:
    """Tag character doesn't hold: validation=invalid, no commit, scene still recorded."""
    conn = _new_conn()
    app = _make_app(conn)

    with TestClient(app) as client:
        # 'climbing' is a real application but Sylvara doesn't hold it.
        r = client.post(
            "/narrator/scene_resolved",
            json={
                "session_id": "sess-narr",
                "scene_actions": [],
                "proposed_advance": {"tag": "climbing"},
            },
        )

    assert r.status_code == 200
    body = r.json()
    assert body["proposed_evaluation"]["validation"] == "invalid"
    assert body["advance_committed"] is None
    assert body["scene_id"] in conn.scene_records


# ---------------------------------------------------------------------------
# State integration tests
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_orchestrator_advances_world_time_via_steps() -> None:
    conn = _new_conn(world=_world(turn=4))  # afternoon
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/narrator/scene_resolved",
            json={"session_id": "sess-narr", "time_elapsed": {"steps": 2}},
        )

    body = r.json()
    assert body["state_after"]["world"]["time"]["time_of_day"] == "night"
    assert body["state_after"]["world"]["turn"] == 5  # +1 on time advance


@pytest.mark.contract
def test_orchestrator_does_not_advance_turn_without_time_elapsed() -> None:
    conn = _new_conn(world=_world(turn=4))
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/narrator/scene_resolved",
            json={
                "session_id": "sess-narr",
                "world_changes": {"threat": "rising"},
            },
        )

    body = r.json()
    assert body["state_after"]["world"]["turn"] == 4
    assert body["state_after"]["world"]["threat"] == "rising"


@pytest.mark.contract
def test_orchestrator_uses_world_location_when_omitted() -> None:
    conn = _new_conn(world=_world(location="feywood-vault"))
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post("/narrator/scene_resolved", json={"session_id": "sess-narr"})

    body = r.json()
    assert body["location_id"] == "feywood-vault"
    assert body["turn_at_resolution"] == 4


@pytest.mark.contract
def test_orchestrator_overrides_location_when_provided() -> None:
    conn = _new_conn(world=_world(location="feywood-vault"))
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/narrator/scene_resolved",
            json={"session_id": "sess-narr", "location_id": "feywood-overlook"},
        )

    body = r.json()
    assert body["location_id"] == "feywood-overlook"


@pytest.mark.contract
def test_orchestrator_envelope_status_includes_active_arcs() -> None:
    """arc_envelope_status reports per-arc scene counts and cap flags."""
    conn = _new_conn()
    conn.add_arc("arc-A")
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/narrator/scene_resolved",
            json={
                "session_id": "sess-narr",
                "arc_progressed_ids": ["arc-A"],
            },
        )

    body = r.json()
    arc_a = next(s for s in body["arc_envelope_status"] if s["arc_id"] == "arc-A")
    assert arc_a["resolved_scenes_used"] == 1
    assert arc_a["soft_cap_approaching"] is False


@pytest.mark.contract
def test_orchestrator_failed_advance_recoverable_via_direct_commit() -> None:
    """Unknown tag leaves the scene record un-stamped; future direct commit can succeed.

    After the orchestrator records the scene with no advance (because the
    proposed tag was unknown), the scene_record's `tag_advance_committed`
    is None. Brief 19's enforcement allows a subsequent commit to that
    same scene_id via the direct endpoint. This documents that recovery
    path; no pre/post state assertion is made here beyond shape.
    """
    conn = _new_conn()
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/narrator/scene_resolved",
            json={
                "session_id": "sess-narr",
                "proposed_advance": {"tag": "made_up_tag"},
            },
        )

    body = r.json()
    scene_id = body["scene_id"]
    # The scene is still un-stamped — recovery via /progression/commit is open.
    assert conn.scene_records[scene_id]["tag_advance_committed"] is None


@pytest.mark.contract
def test_orchestrator_no_commit_skips_state_save_when_no_other_changes() -> None:
    """Scene-only call doesn't issue a redundant character/world UPDATE."""
    conn = _new_conn()
    starting_character = copy.deepcopy(conn.character)
    starting_world = copy.deepcopy(conn.world)
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post("/narrator/scene_resolved", json={"session_id": "sess-narr"})

    assert r.status_code == 200
    # Character and world are bit-identical to before the call.
    assert conn.character == starting_character
    assert conn.world == starting_world


@pytest.mark.contract
def test_orchestrator_surfaces_phase_shift_for_emergent_arc_at_soft_cap() -> None:
    """Brief 21: orchestrator passes phase_shift_candidate + suggestion through.

    Emergent arc with soft_cap=2; pre-seed 1 scene; the orchestrator's
    declare adds the second, hitting soft cap. arc_envelope_status entry
    should be phase_shift_candidate=True; suggestions should include the
    phase-shift entry.
    """
    conn = _new_conn()
    conn.add_arc(
        "arc-willowglass",
        data={
            "title": "Willowglass thread",
            "state": "in_progress",
            "origin_type": "emergent",
            "budget": {
                "resolved_scene_soft_cap": 2,
                "resolved_scene_hard_cap": 4,
                "location_soft_cap": 3,
                "location_hard_cap": 5,
            },
        },
    )
    # Pre-seed one prior scene contributing to arc-willowglass.
    conn.scene_records["prior-1"] = {
        "scene_id": "prior-1",
        "session_id": "sess-narr",
        "scene_summary": None,
        "scene_actions": [],
        "arc_progressed_ids": ["arc-willowglass"],
        "location_id": "feywood-river-bend",
        "turn_at_resolution": 4,
        "time_at_resolution": None,
        "tag_advance_committed": None,
        "resolved_at": conn._next_ts(),
    }
    app = _make_app(conn)

    with TestClient(app) as client:
        r = client.post(
            "/narrator/scene_resolved",
            json={
                "session_id": "sess-narr",
                "arc_progressed_ids": ["arc-willowglass"],
            },
        )

    assert r.status_code == 200
    body = r.json()
    arc_status = next(
        s for s in body["arc_envelope_status"] if s["arc_id"] == "arc-willowglass"
    )
    assert arc_status["phase_shift_candidate"] is True
    phase_shift_suggestions = [s for s in body["suggestions"] if "Phase Change Indicators" in s]
    assert len(phase_shift_suggestions) >= 1
