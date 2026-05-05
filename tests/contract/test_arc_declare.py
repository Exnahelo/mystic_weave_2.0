"""Contract tests for POST /arc/{session_id}/{arc_id}/declare (Brief 3 Phase A).

Covers each declare intent (activate / close / fail / abandon / spawn_child /
scope_check), happy paths, and key rejection paths. Existing endpoint tests
(test_arc_transition_endpoint.py, test_arc_settle_endpoint.py,
test_arc_spawn_endpoint.py) remain in force and serve as the regression
baseline for the legacy /transition, /settle, /spawn paths after the helper
additions in arc_repository / state_repository.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import arc as arc_routes
from tests.contract.test_arc_transition_endpoint import ArcTransitionConn, FakePool


def _app(conn: ArcTransitionConn) -> FastAPI:
    app = FastAPI()
    app.include_router(arc_routes.router)
    app.dependency_overrides[get_pool] = lambda: FakePool(conn)
    return app


def _create_payload(formal: bool = True) -> dict:
    payload: dict = {
        "title": "Declare test arc",
        "summary": "Test arc for declare endpoint validation.",
        "primary_type": "mission_multi_leg",
        "subtype": "investigation",
        "stake_scale": "situational",
        "origin_type": "declared" if formal else "emergent",
        "formal_contract_qualified": formal,
        "closure_conditions": {"all_of": [{"type": "resolved_scene_count_at_least", "payload": {"count": 0}}]},
    }
    if formal:
        payload.update({"patron_npc_id": "npc-test", "explicit_objective": "Do the thing", "expected_return": "Report back"})
    return payload


def _full_settlement(awarded_ap: int = 0) -> dict:
    """A full SettlementEnumeration with all channels populated as explicit empty."""
    return {
        "awarded_ap": awarded_ap,
        "reputation_changes": [],
        "coin_awarded": 0,
        "coin_forfeited": 0,
        "items_awarded": [],
        "leverage_gained": [],
        "obligations": [],
        "world_state_consequences": [],
    }


def _create(client: TestClient, formal: bool = True, session_id: str = "sess-declare") -> dict:
    return client.post(f"/arc/{session_id}/create", json=_create_payload(formal)).json()


# ---------------------------------------------------------------------------
# activate
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_declare_activate_happy_path() -> None:
    """proposed → available → in_progress in a single call."""
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client)
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "activate", "reason": "test activation flow"},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["arc"]["state"] == "in_progress"
    assert body["actions_taken"] == ["transition:proposed->available", "transition:available->in_progress"]


@pytest.mark.contract
def test_declare_activate_rejects_non_proposed() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "first activation"})
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "activate", "reason": "second activation should fail"},
        )
    assert response.status_code == 409
    assert "activate_requires_proposed" in response.text


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_declare_close_requires_settlement() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "close", "reason": "close without settlement"},
        )
    assert response.status_code == 422
    assert "settlement_required" in response.text


@pytest.mark.contract
def test_declare_close_happy_path_records_closure_summary() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=True)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "close", "reason": "close arc cleanly", "settlement": _full_settlement(awarded_ap=1)},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["arc"]["state"] == "complete"
    assert body["arc"]["settlement"]["awarded_ap"] == 1
    closure_entries = [e for e in conn.log if e.get("type") == "closure_summary"]
    assert len(closure_entries) == 1
    payload = closure_entries[0]["payload"]
    assert payload["via"] == "declare"
    assert payload["outcome"] == "complete"


@pytest.mark.contract
def test_declare_close_rejects_emergent_arc_awarded_ap() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=False)  # emergent
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "close", "reason": "close emergent with AP", "settlement": _full_settlement(awarded_ap=1)},
        )
    assert response.status_code == 422
    assert "emergent_arc_no_ap" in response.text


@pytest.mark.contract
def test_declare_close_rejects_ap_outside_envelope() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=True)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        # mission_multi_leg envelope max is 2; ask for 99
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "close", "reason": "ap blowout", "settlement": _full_settlement(awarded_ap=99)},
        )
    assert response.status_code == 422
    assert "ap_outside_envelope" in response.text


# ---------------------------------------------------------------------------
# fail
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_declare_fail_happy_path() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=True)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "fail", "reason": "investigation collapsed", "settlement": _full_settlement(awarded_ap=0)},
        )
    assert response.status_code == 200, response.text
    assert response.json()["arc"]["state"] == "failed"


@pytest.mark.contract
def test_declare_fail_rejects_awarded_ap() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=True)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "fail", "reason": "fail with ap", "settlement": _full_settlement(awarded_ap=1)},
        )
    assert response.status_code == 422
    assert "ap_on_failure_not_allowed" in response.text


# ---------------------------------------------------------------------------
# abandon
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_declare_abandon_from_in_progress() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=True)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "abandon", "reason": "player disengaged completely"},
        )
    assert response.status_code == 200, response.text
    assert response.json()["arc"]["state"] == "abandoned"


# ---------------------------------------------------------------------------
# spawn_child
# ---------------------------------------------------------------------------

def _child_payload() -> dict:
    return {
        "child_title": "Child arc",
        "child_summary": "Child for spawn test",
        "child_primary_type": "task_local",
        "child_subtype": "investigation",
        "child_stake_scale": "local",
        "ap_ownership": "none",
        "reason": "child for spawn test path",
    }


@pytest.mark.contract
def test_declare_spawn_child_happy_path_continue() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=True)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={
                "intent": "spawn_child",
                "reason": "scope expanded; spawning sub-investigation",
                "child_arc": _child_payload(),
                "parent_action_after_spawn": "continue",
            },
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["child_arc"] is not None
    assert body["child_arc"]["state"] == "proposed"
    assert body["arc"]["state"] == "in_progress"  # parent unchanged
    assert body["child_arc"]["id"] in body["arc"]["spawned_arc_ids"]


@pytest.mark.contract
def test_declare_spawn_child_merge_into_child_replaces_parent() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=True)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={
                "intent": "spawn_child",
                "reason": "successor takes over the work",
                "child_arc": _child_payload(),
                "parent_action_after_spawn": "merge_into_child",
            },
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["arc"]["state"] == "replaced_by_successor"


@pytest.mark.contract
def test_declare_spawn_child_requires_child_arc_body() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=True)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "spawn_child", "reason": "missing child body field on this request"},
        )
    assert response.status_code == 422
    assert "child_arc_required" in response.text


# ---------------------------------------------------------------------------
# scope_check
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_declare_scope_check_returns_envelope_status() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=True)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "scope_check", "reason": "checking scope after recent scenes"},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["actions_taken"] == []
    assert body["envelope_status"] is not None
    assert "phase_shift_candidate" in body["envelope_status"]
    assert body["arc"]["state"] == "in_progress"  # unchanged


@pytest.mark.contract
def test_declare_scope_check_recommends_spawn_when_phase_shift_candidate() -> None:
    """An emergent arc past its soft cap should get a spawn_child recommendation."""
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=False)  # emergent
        # Fast-forward consumption past soft cap by direct fake mutation.
        for row in conn.rows:
            if row["id"] == arc["id"]:
                row["data"]["consumption"]["resolved_scenes_used"] = (
                    row["data"]["budget"]["resolved_scene_soft_cap"] + 1
                )
                row["data"]["state"] = "in_progress"
                row["state"] = "in_progress"
                break
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "scope_check", "reason": "post phase_shift_candidate audit"},
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["envelope_status"]["phase_shift_candidate"] is True
    suggestions = body["suggestions"]
    assert any(s["suggested_intent"] == "spawn_child" for s in suggestions)


@pytest.mark.contract
def test_declare_scope_check_rejects_terminal_arc() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=True)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "abandon", "reason": "abandon to reach terminal state"},
        )
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "scope_check", "reason": "scope check on terminal arc"},
        )
    assert response.status_code == 409
    assert "arc_terminal" in response.text


# ---------------------------------------------------------------------------
# Schema enforcement: settlement enumeration as forcing function
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_settlement_enumeration_rejects_omitted_channel() -> None:
    """The forcing function — every channel must be present in the request."""
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=True)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        # settlement missing world_state_consequences and obligations
        broken_settlement = {
            "awarded_ap": 0,
            "reputation_changes": [],
            "coin_awarded": 0,
            "coin_forfeited": 0,
            "items_awarded": [],
            "leverage_gained": [],
            # obligations omitted
            # world_state_consequences omitted
        }
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "close", "reason": "close with incomplete settlement", "settlement": broken_settlement},
        )
    assert response.status_code == 422
    text = response.text
    assert "obligations" in text or "world_state_consequences" in text


@pytest.mark.contract
def test_settlement_enumeration_accepts_explicit_empty_channels() -> None:
    """Empty list is the explicit no-change marker; populated request validates."""
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=True)
        client.post(f"/arc/sess-declare/{arc['id']}/declare", json={"intent": "activate", "reason": "activate the arc"})
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={
                "intent": "close",
                "reason": "close with all empties",
                "settlement": _full_settlement(awarded_ap=0),
            },
        )
    assert response.status_code == 200, response.text


# ---------------------------------------------------------------------------
# Reason validation
# ---------------------------------------------------------------------------

@pytest.mark.contract
def test_declare_rejects_short_reason() -> None:
    conn = ArcTransitionConn()
    with TestClient(_app(conn)) as client:
        arc = _create(client, formal=True)
        response = client.post(
            f"/arc/sess-declare/{arc['id']}/declare",
            json={"intent": "activate", "reason": "short"},
        )
    assert response.status_code == 422
