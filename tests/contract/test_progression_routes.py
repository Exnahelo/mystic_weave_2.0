"""Contract tests for /progression/scan and /progression/commit (Brief 18)."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import progression
from tests.helpers import zero_advancement


# ---------------------------------------------------------------------------
# Fake asyncpg pool/connection scaffold
# ---------------------------------------------------------------------------

class _AcquireCtx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return None


class _TxCtx:
    """Minimal async context manager standing in for asyncpg's transaction()."""

    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc, tb):
        return None


class FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _AcquireCtx(self._conn)


class ProgressionConn:
    """Stub connection backing scan + commit calls.

    Records the latest character/log on every UPDATE so tests can assert
    post-commit state. Supports SELECT (with or without FOR UPDATE) and
    UPDATE statements.
    """

    def __init__(self, session_id: str | None, character: dict | None, log: list | None = None):
        self.session_id = session_id
        self.character = character
        self.log = log if log is not None else []
        self.updated_at = datetime.now()

    def transaction(self):
        return _TxCtx()

    async def fetchrow(self, query: str, *args):
        if "SELECT character FROM game_states" in query:
            if self.session_id is None or args[0] != self.session_id or self.character is None:
                return None
            return {"character": json.dumps(self.character)}

        if "SELECT character, log FROM game_states" in query:
            if self.session_id is None or args[0] != self.session_id or self.character is None:
                return None
            return {
                "character": json.dumps(self.character),
                "log": json.dumps(self.log),
            }

        return None

    async def execute(self, query: str, *args):
        if "UPDATE game_states" in query and "SET character" in query and "log = $2::jsonb" in query:
            self.character = json.loads(args[0])
            self.log = json.loads(args[1])
            self.updated_at = datetime.now()
            return "UPDATE 1"
        return None


def _make_app(pool) -> FastAPI:
    app = FastAPI()
    app.include_router(progression.router)
    app.dependency_overrides[get_pool] = lambda: pool
    return app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _character_with_tags(
    *,
    knowledge: dict[str, dict] | None = None,
    magic: dict[str, dict] | None = None,
    advancement: dict | None = None,
) -> dict:
    """Build a v5 character record with chosen knowledge/magic blocks."""
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
        "knowledge": knowledge or {},
        "magic": magic or {},
        "status_effects": [],
        "notes": "",
        "identity": {
            "origin": "", "motivations": [], "quirks": [], "bonds": [],
            "flaws": [], "wound": "",
            "alignment": {"order": "neutral", "intent": "neutral", "ethos_note": ""},
        },
        "equipment": {"worn": [], "carried": [], "stashed": []},
        "reputation": [],
        "advancement": advancement or zero_advancement(),
    }


def _druid_character() -> dict:
    """Standard test character: druidry T2 with seedwake T1, athletics T2 with hauling T1."""
    return _character_with_tags(
        knowledge={
            "athletics": {"tier": 2, "applications": {"hauling": 1}},
            "nature": {"tier": 3, "applications": {"ecology": 3}},
        },
        magic={
            "druidry": {"tier": 2, "spells": {"seedwake": 1, "sap_mend": 1}},
        },
    )


# ---------------------------------------------------------------------------
# /progression/scan tests
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_scan_explicit_match() -> None:
    """spell_cast(seedwake, success) -> seedwake explicit, druidry implicit."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/scan",
            json={
                "session_id": "sess1",
                "scene_actions": [{"type": "spell_cast", "spell": "seedwake", "outcome": "success"}],
                "proposed_advances": [],
            },
        )

    assert r.status_code == 200
    body = r.json()
    cands = body["candidates_ranked"]
    by_tag = {c["tag"]: c for c in cands}
    assert by_tag["seedwake"]["fit"]["strength"] == "explicit"
    assert by_tag["seedwake"]["kind"] == "spell"
    assert by_tag["seedwake"]["parent"] == "druidry"
    assert by_tag["druidry"]["fit"]["strength"] == "implicit"
    assert by_tag["druidry"]["kind"] == "magic_field"


@pytest.mark.contract
def test_scan_failure_outcome_implicit() -> None:
    """spell_cast(seedwake, failure) -> seedwake implicit, druidry contextual."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/scan",
            json={
                "session_id": "sess1",
                "scene_actions": [{"type": "spell_cast", "spell": "seedwake", "outcome": "failure"}],
                "proposed_advances": [],
            },
        )

    assert r.status_code == 200
    by_tag = {c["tag"]: c for c in r.json()["candidates_ranked"]}
    assert by_tag["seedwake"]["fit"]["strength"] == "implicit"
    assert by_tag["druidry"]["fit"]["strength"] == "contextual"


@pytest.mark.contract
def test_scan_proposed_match() -> None:
    """A proposed advance that matches the strongest explicit candidate -> proposed_match."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/scan",
            json={
                "session_id": "sess1",
                "scene_actions": [{"type": "spell_cast", "spell": "seedwake", "outcome": "success"}],
                "proposed_advances": [{"tag": "seedwake"}],
            },
        )

    assert r.status_code == 200
    eval_ = r.json()["proposed_evaluation"][0]
    assert eval_["tag"] == "seedwake"
    assert eval_["validation"] == "proposed_match"
    assert eval_["in_candidates"] is True
    assert eval_["eligible"] is True


@pytest.mark.contract
def test_scan_omits_strongest() -> None:
    """Proposing a contextual tag while an explicit candidate exists -> omits_strongest."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/scan",
            json={
                "session_id": "sess1",
                # explicit candidate from spell_cast is seedwake; but we propose hauling
                # (held but unrelated to the scene actions).
                "scene_actions": [{"type": "spell_cast", "spell": "seedwake", "outcome": "success"}],
                "proposed_advances": [{"tag": "hauling"}],
            },
        )

    assert r.status_code == 200
    eval_ = r.json()["proposed_evaluation"][0]
    assert eval_["validation"] == "omits_strongest"
    assert "seedwake" in (eval_["strongest_omitted"] or [])


@pytest.mark.contract
def test_scan_invalid_proposal() -> None:
    """Proposing a tag the character doesn't hold -> validation=invalid."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        # 'climbing' is a real application but the test character doesn't hold it
        r = client.post(
            "/progression/scan",
            json={
                "session_id": "sess1",
                "scene_actions": [],
                "proposed_advances": [{"tag": "climbing"}],
            },
        )

    assert r.status_code == 200
    eval_ = r.json()["proposed_evaluation"][0]
    assert eval_["validation"] == "invalid"
    assert eval_["eligible"] is False


@pytest.mark.contract
def test_scan_unknown_tag() -> None:
    """A proposed tag absent from every registry -> validation=unknown_tag."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/scan",
            json={
                "session_id": "sess1",
                "scene_actions": [],
                "proposed_advances": [{"tag": "made_up_tag"}],
            },
        )

    assert r.status_code == 200
    eval_ = r.json()["proposed_evaluation"][0]
    assert eval_["validation"] == "unknown_tag"


@pytest.mark.contract
def test_scan_parent_cap_violation_marked_ineligible() -> None:
    """Application at parent's tier with no headroom -> eligible=False, parent_cap_ok=False."""
    char = _character_with_tags(
        knowledge={
            # Group at T2, application also at T2 -> next tier (3) would exceed parent (2)
            "athletics": {"tier": 2, "applications": {"hauling": 2}},
        },
    )
    conn = ProgressionConn("sess1", char)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/scan",
            json={
                "session_id": "sess1",
                "scene_actions": [{"type": "generic_roll", "application": "hauling", "outcome": "success"}],
                "proposed_advances": [{"tag": "hauling"}],
            },
        )

    assert r.status_code == 200
    cand = next(c for c in r.json()["candidates_ranked"] if c["tag"] == "hauling")
    assert cand["parent_cap_ok"] is False
    assert cand["eligible"] is False
    eval_ = r.json()["proposed_evaluation"][0]
    assert eval_["validation"] == "invalid"


@pytest.mark.contract
def test_scan_404_unknown_session() -> None:
    """Unknown session_id -> 404."""
    conn = ProgressionConn(None, None)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/scan",
            json={"session_id": "missing", "scene_actions": [], "proposed_advances": []},
        )

    assert r.status_code == 404


@pytest.mark.contract
def test_scan_empty_actions_warning() -> None:
    """Empty scene_actions and proposed_advances -> warnings populated."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/scan",
            json={"session_id": "sess1", "scene_actions": [], "proposed_advances": []},
        )

    assert r.status_code == 200
    warnings = r.json()["warnings"]
    assert "no_scene_actions" in warnings
    assert "no_proposed_advances" in warnings


@pytest.mark.contract
def test_scan_scene_id_echoed_unchanged() -> None:
    """Brief 18 echoes scene_id verbatim; Brief 19 will give it semantics."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/scan",
            json={
                "session_id": "sess1",
                "scene_actions": [],
                "proposed_advances": [],
                "scene_id": "scene-abc-123",
            },
        )

    assert r.status_code == 200
    assert r.json()["scene_id"] == "scene-abc-123"


# ---------------------------------------------------------------------------
# /progression/commit tests
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_commit_application() -> None:
    """Commit a held application; tier increments and counter advances by 1."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/commit",
            json={"session_id": "sess1", "tag": "hauling"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "application"
    assert body["new_tier"] == 2
    assert body["parent_bumped"] is False
    assert body["advancement_after"]["tag_counter"] == 1
    # Persisted character reflects the new tier
    assert conn.character["knowledge"]["athletics"]["applications"]["hauling"] == 2


@pytest.mark.contract
def test_commit_spell() -> None:
    """Commit a held spell; tier increments without parent bump (field tier headroom)."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/commit",
            json={"session_id": "sess1", "tag": "seedwake"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "spell"
    assert body["new_tier"] == 2
    assert body["parent_bumped"] is False
    assert conn.character["magic"]["druidry"]["spells"]["seedwake"] == 2


@pytest.mark.contract
def test_commit_knowledge_group_top_level() -> None:
    """Commit a knowledge group directly; no parent-cap relevance."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/commit",
            json={"session_id": "sess1", "tag": "athletics"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "knowledge_group"
    assert body["new_tier"] == 3
    assert conn.character["knowledge"]["athletics"]["tier"] == 3


@pytest.mark.contract
def test_commit_magic_field_top_level() -> None:
    """Commit a magic field directly; spells under it remain capped."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/commit",
            json={"session_id": "sess1", "tag": "druidry"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["kind"] == "magic_field"
    assert body["new_tier"] == 3
    assert conn.character["magic"]["druidry"]["tier"] == 3


@pytest.mark.contract
def test_commit_parent_bump() -> None:
    """Commit an application at parent's tier; parent gets bumped to match."""
    char = _character_with_tags(
        knowledge={"athletics": {"tier": 2, "applications": {"hauling": 2}}},
    )
    conn = ProgressionConn("sess1", char)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/commit",
            json={"session_id": "sess1", "tag": "hauling"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["new_tier"] == 3
    assert body["parent_bumped"] is True
    assert body["parent_tag"] == "athletics"
    assert conn.character["knowledge"]["athletics"]["tier"] == 3
    assert conn.character["knowledge"]["athletics"]["applications"]["hauling"] == 3


@pytest.mark.contract
def test_commit_counter_rollover() -> None:
    """Three commits roll counter from 0 -> 0 with +1 AP awarded."""
    char = _character_with_tags(
        knowledge={
            "athletics": {"tier": 3, "applications": {"hauling": 1, "climbing": 1, "swimming": 1}},
        },
    )
    conn = ProgressionConn("sess1", char)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        for tag in ("hauling", "climbing", "swimming"):
            r = client.post("/progression/commit", json={"session_id": "sess1", "tag": tag})
            assert r.status_code == 200, r.text

    adv = conn.character["advancement"]
    assert adv["tag_counter"] == 0
    assert adv["points_available"] == 1
    assert adv["points_earned_total"] == 1


@pytest.mark.contract
def test_commit_unknown_tag_422() -> None:
    """A tag not in any registry -> 422 unknown_tag."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post("/progression/commit", json={"session_id": "sess1", "tag": "made_up_tag"})

    assert r.status_code == 422
    assert r.json()["detail"]["error"] == "unknown_tag"


@pytest.mark.contract
def test_commit_tag_not_held_422() -> None:
    """A real application the character doesn't hold -> 422."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        # 'climbing' lives under 'athletics', which the character has, but
        # climbing itself is not in the apps dict.
        r = client.post("/progression/commit", json={"session_id": "sess1", "tag": "climbing"})

    assert r.status_code == 422
    assert r.json()["detail"]["error"] == "tag_not_held"


@pytest.mark.contract
def test_commit_at_max_tier_422() -> None:
    """A tag already at T5 -> 422 at_max_tier."""
    char = _character_with_tags(
        knowledge={"athletics": {"tier": 5, "applications": {"hauling": 5}}},
    )
    conn = ProgressionConn("sess1", char)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post("/progression/commit", json={"session_id": "sess1", "tag": "hauling"})

    assert r.status_code == 422
    assert r.json()["detail"]["error"] == "at_max_tier"


@pytest.mark.contract
def test_commit_log_entry_appended() -> None:
    """Successful commit appends a typed log entry of type=progression."""
    conn = ProgressionConn("sess1", _druid_character())
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post(
            "/progression/commit",
            json={"session_id": "sess1", "tag": "hauling", "rationale": "scene closure"},
        )

    assert r.status_code == 200
    assert len(conn.log) == 1
    entry = conn.log[0]
    assert entry["type"] == "progression"
    assert "hauling" in entry["text"]
    assert "tier 2" in entry["text"]
    assert "scene closure" in entry["text"]


@pytest.mark.contract
def test_commit_atomic_on_validation_error() -> None:
    """Validation failure (e.g., unknown tag) leaves character + log untouched."""
    starting_character = _druid_character()
    starting_log: list[Any] = []
    conn = ProgressionConn("sess1", json.loads(json.dumps(starting_character)), starting_log)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post("/progression/commit", json={"session_id": "sess1", "tag": "made_up_tag"})

    assert r.status_code == 422
    # Stored state must still match the pre-call snapshot exactly.
    assert conn.character == starting_character
    assert conn.log == starting_log


@pytest.mark.contract
def test_commit_404_unknown_session() -> None:
    """Unknown session_id -> 404."""
    conn = ProgressionConn(None, None)
    app = _make_app(FakePool(conn))

    with TestClient(app) as client:
        r = client.post("/progression/commit", json={"session_id": "missing", "tag": "hauling"})

    assert r.status_code == 404
