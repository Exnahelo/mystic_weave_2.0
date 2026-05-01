from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.database import get_pool
from api.routes import arc as arc_routes


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


class ArcRouteConn:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    async def execute(self, query, *args):
        if "INSERT INTO arcs" in query:
            self.rows.append(
                {
                    "id": args[0],
                    "session_id": args[1],
                    "primary_type": args[2],
                    "state": args[3],
                    "parent_arc_id": args[4],
                    "data": args[5],
                    "created_at": args[6],
                }
            )
        return "INSERT 0 1"

    async def fetchrow(self, query, *args):
        if "WHERE session_id = $1 AND id = $2" in query:
            for row in self.rows:
                if row["session_id"] == args[0] and row["id"] == args[1]:
                    return {"data": row["data"]}
        return None

    async def fetch(self, query, *args):
        if "state IN ('in_progress', 'at_scope_cap')" in query:
            return [
                {"data": row["data"]}
                for row in self.rows
                if row["session_id"] == args[0] and row["state"] in {"in_progress", "at_scope_cap"}
            ]
        if "WHERE session_id = $1" in query:
            return [
                {"data": row["data"]}
                for row in self.rows
                if row["session_id"] == args[0]
            ]
        return []


def _make_app(conn: ArcRouteConn) -> FastAPI:
    app = FastAPI()
    app.include_router(arc_routes.router)
    app.dependency_overrides[get_pool] = lambda: FakePool(conn)
    return app


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Find the missing scouts",
        "summary": "Investigate the disappearance near the old watch road.",
        "primary_type": "mission_multi_leg",
        "subtype": "investigation",
        "stake_scale": "situational",
        "origin_type": "emergent",
        "formal_contract_qualified": False,
    }
    payload.update(overrides)
    return payload


def _post(payload: dict[str, object], session_id: str = "sess-arc"):
    conn = ArcRouteConn()
    app = _make_app(conn)
    with TestClient(app) as client:
        response = client.post(f"/arc/{session_id}/create", json=payload)
    return response, conn


@pytest.mark.contract
def test_create_emergent_arc_happy_path_zero_ap() -> None:
    response, _ = _post(_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "proposed"
    assert body["rewards"]["ap_award"] == {"min": 0, "max": 0, "fixed": False}
    assert body["flags"]["formal_contract_qualified"] is False


@pytest.mark.contract
def test_create_formal_contract_happy_path_awards_default_ap() -> None:
    response, _ = _post(
        _payload(
            formal_contract_qualified=True,
            patron_npc_id="npc-arden",
            explicit_objective="Recover the missing charter.",
            expected_return="Return the charter to Arden.",
        )
    )

    assert response.status_code == 200
    body = response.json()
    assert body["rewards"]["ap_award"] == {"min": 1, "max": 2, "fixed": False}
    assert body["flags"]["formal_contract_qualified"] is True
    assert body["flags"]["ap_ownership"] == "parent"


@pytest.mark.contract
def test_create_formal_contract_rejects_no_patron() -> None:
    response, _ = _post(
        _payload(
            formal_contract_qualified=True,
            explicit_objective="Recover the missing charter.",
            expected_return="Return the charter.",
        )
    )

    assert response.status_code == 422
    assert "patron_npc_id or patron_faction" in response.json()["detail"]["missing_fields"]


@pytest.mark.contract
def test_create_formal_contract_rejects_no_objective() -> None:
    response, _ = _post(
        _payload(
            formal_contract_qualified=True,
            patron_faction="council",
            expected_return="Report back.",
        )
    )

    assert response.status_code == 422
    assert "explicit_objective" in response.json()["detail"]["missing_fields"]


@pytest.mark.contract
def test_create_formal_contract_rejects_no_expected_return() -> None:
    response, _ = _post(
        _payload(
            formal_contract_qualified=True,
            patron_faction="council",
            explicit_objective="Find proof.",
        )
    )

    assert response.status_code == 422
    assert "expected_return" in response.json()["detail"]["missing_fields"]


@pytest.mark.contract
def test_create_formal_contract_rejects_empty_string_objective() -> None:
    response, _ = _post(
        _payload(
            formal_contract_qualified=True,
            patron_faction="council",
            explicit_objective="  ",
            expected_return="Report back.",
        )
    )

    assert response.status_code == 422
    assert "explicit_objective" in response.json()["detail"]["missing_fields"]


@pytest.mark.contract
def test_create_formal_contract_reports_multiple_missing_fields() -> None:
    response, _ = _post(
        _payload(
            formal_contract_qualified=True,
            patron_faction="council",
        )
    )

    assert response.status_code == 422
    missing = response.json()["detail"]["missing_fields"]
    assert "explicit_objective" in missing
    assert "expected_return" in missing


@pytest.mark.contract
def test_create_rejects_invalid_primary_type() -> None:
    response, _ = _post(_payload(primary_type="made_up_type"))

    assert response.status_code == 422


@pytest.mark.contract
def test_create_rejects_invalid_subtype() -> None:
    response, _ = _post(_payload(subtype="made_up_subtype"))

    assert response.status_code == 422


@pytest.mark.contract
def test_create_rejects_invalid_stake_scale() -> None:
    response, _ = _post(_payload(stake_scale="galactic"))

    assert response.status_code == 422


@pytest.mark.contract
def test_create_applies_mission_multi_leg_calibrated_defaults() -> None:
    response, _ = _post(_payload(primary_type="mission_multi_leg"))

    assert response.status_code == 200
    assert response.json()["budget"] == {
        "resolved_scene_soft_cap": 6,
        "resolved_scene_hard_cap": 10,
        "location_soft_cap": 3,
        "location_hard_cap": 5,
        "encounter_density_hint": None,
        "expected_duration_turns": None,
    }


@pytest.mark.contract
def test_create_initial_state_is_proposed() -> None:
    response, _ = _post(_payload())

    assert response.status_code == 200
    assert response.json()["state"] == "proposed"


@pytest.mark.contract
def test_create_initial_consumption_is_zero() -> None:
    response, _ = _post(_payload())

    assert response.status_code == 200
    consumption = response.json()["consumption"]
    assert consumption["resolved_scenes_used"] == 0
    assert consumption["locations_visited"] == []


@pytest.mark.contract
def test_create_initial_timestamps_set_correctly() -> None:
    before = datetime.now(timezone.utc)
    response, _ = _post(_payload())
    after = datetime.now(timezone.utc)

    assert response.status_code == 200
    timestamps = response.json()["timestamps"]
    created_at = datetime.fromisoformat(timestamps["created_at"])
    assert before <= created_at <= after
    assert timestamps["accepted_at"] is None
    assert timestamps["last_progressed_at"] is None
    assert timestamps["closed_at"] is None