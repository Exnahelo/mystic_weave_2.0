"""Contract tests for /registry/{name}."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import registry


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(registry.router)
    return app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(_make_app())


@pytest.mark.contract
def test_lookup_application(client: TestClient) -> None:
    """An application name returns kind=application with full record."""
    r = client.get("/registry/shortsword")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "shortsword"
    assert body["kind"] == "application"
    assert body["data"]["group"] == "close_combat"
    assert body["data"]["primary_domain"] == "agility"


@pytest.mark.contract
def test_lookup_knowledge_group(client: TestClient) -> None:
    """A knowledge group name returns kind=knowledge_group."""
    r = client.get("/registry/athletics")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "athletics"
    assert body["kind"] == "knowledge_group"
    assert "primary_domain" in body["data"]


@pytest.mark.contract
def test_lookup_magic_field(client: TestClient) -> None:
    """A magic field name returns kind=magic_field."""
    r = client.get("/registry/druidry")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "druidry"
    assert body["kind"] == "magic_field"


@pytest.mark.contract
def test_lookup_spell(client: TestClient) -> None:
    """A spell name returns kind=spell with field reference."""
    r = client.get("/registry/seedwake")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "seedwake"
    assert body["kind"] == "spell"
    assert body["data"]["field"] == "druidry"
    assert "tier" in body["data"]


@pytest.mark.contract
def test_lookup_unknown_returns_404_with_suggestions(client: TestClient) -> None:
    """An unknown name returns 404 with closest-match suggestions."""
    r = client.get("/registry/wraithbinding")
    assert r.status_code == 404
    detail = r.json()["detail"]
    assert detail["error"] == "unknown_registry_name"
    assert detail["name"] == "wraithbinding"
    assert "suggestions" in detail
    assert isinstance(detail["suggestions"], list)
    assert detail["registries_searched"] == [
        "applications",
        "knowledge_groups",
        "magic_fields",
        "spells",
    ]


@pytest.mark.contract
def test_lookup_unknown_with_no_close_matches(client: TestClient) -> None:
    """An unknown name with no close matches returns an empty suggestion list."""
    r = client.get("/registry/zzzzzzzzzzz")
    assert r.status_code == 404
    detail = r.json()["detail"]
    assert detail["suggestions"] == []


@pytest.mark.contract
def test_lookup_case_sensitive(client: TestClient) -> None:
    """Registry lookups are case-sensitive (per kebab-case convention)."""
    r_correct = client.get("/registry/shortsword")
    r_mixed = client.get("/registry/Shortsword")
    assert r_correct.status_code == 200
    assert r_mixed.status_code == 404
