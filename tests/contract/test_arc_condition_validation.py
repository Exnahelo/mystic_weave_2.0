"""Validate ArcCondition.type against the registry condition_types list."""
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


def _base_payload() -> dict:
    return {
        "title": "registry-validated arc",
        "summary": "test arc for condition-type validation",
        "primary_type": "task_local",
        "subtype": "investigation",
        "stake_scale": "local",
        "origin_type": "emergent",
    }


@pytest.mark.contract
def test_arc_create_rejects_invalid_closure_condition_type() -> None:
    """Closure conditions with invalid type labels are rejected at create time
    with a clear Pydantic validation error naming the invalid label."""
    conn = ArcTransitionConn()
    payload = {
        **_base_payload(),
        "closure_conditions": {
            "all_of": [{"type": "target_identified", "payload": {}}]
        },
    }
    with TestClient(_app(conn)) as client:
        response = client.post("/arc/sess-cond/create", json=payload)
    assert response.status_code == 422
    assert "target_identified" in response.text


@pytest.mark.contract
def test_arc_create_rejects_invalid_failure_condition_type() -> None:
    """Failure conditions are validated against the same registry."""
    conn = ArcTransitionConn()
    payload = {
        **_base_payload(),
        "failure_conditions": {
            "any_of": [{"type": "totally_made_up_condition", "payload": {}}]
        },
    }
    with TestClient(_app(conn)) as client:
        response = client.post("/arc/sess-cond/create", json=payload)
    assert response.status_code == 422
    assert "totally_made_up_condition" in response.text


@pytest.mark.contract
def test_arc_create_accepts_valid_condition_types() -> None:
    """Closure conditions with registry-valid type labels are accepted."""
    conn = ArcTransitionConn()
    payload = {
        **_base_payload(),
        "closure_conditions": {
            "all_of": [
                {"type": "evidence_chain_complete", "payload": {"flag_id": "complete"}},
                {"type": "report_delivered", "payload": {"flag_id": "report"}},
            ]
        },
        "failure_conditions": {
            "any_of": [{"type": "target_destroyed", "payload": {}}]
        },
    }
    with TestClient(_app(conn)) as client:
        response = client.post("/arc/sess-cond/create", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["state"] == "proposed"
    assert body["closure_conditions"]["all_of"][0]["type"] == "evidence_chain_complete"
