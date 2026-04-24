import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import catalog, options


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(options.router)
    app.include_router(catalog.router)
    return app


@pytest.mark.contract
def test_get_options_returns_only_character_creation_fields() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.get("/options")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"ancestries", "cultures", "focus", "backgrounds"}
    assert isinstance(payload["ancestries"], list)
    assert isinstance(payload["cultures"], list)
    assert isinstance(payload["focus"], list)
    assert isinstance(payload["backgrounds"], list)


@pytest.mark.contract
def test_get_catalog_items_returns_expected_groups() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.get("/catalog/items")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"mundane_items", "magical_items", "apparel_items"}

    mundane_ids = {item["id"] for item in payload["mundane_items"]}
    assert {
        "folding-entrenching-tool",
        "animal-bedroll",
        "horse-care-kit",
        "climbing-harness",
        "piton-set-6",
        "rain-dew-catch",
        "small-game-snare",
        "bird-trap",
    }.issubset(mundane_ids)
    assert any(item["name"] in {"Blessed Water", "Holy Water"} for item in payload["magical_items"])
    assert any(item["name"] == "Common Clothes" for item in payload["apparel_items"])


@pytest.mark.contract
def test_get_catalog_items_kind_filter_returns_only_requested_group() -> None:
    app = _make_app()
    with TestClient(app) as client:
        mundane_response = client.get("/catalog/items", params={"kind": "mundane"})
        magical_response = client.get("/catalog/items", params={"kind": "magical"})
        apparel_response = client.get("/catalog/items", params={"kind": "apparel"})

    assert mundane_response.status_code == 200
    assert magical_response.status_code == 200
    assert apparel_response.status_code == 200

    mundane_payload = mundane_response.json()
    assert mundane_payload["mundane_items"]
    assert mundane_payload["magical_items"] == []
    assert mundane_payload["apparel_items"] == []

    magical_payload = magical_response.json()
    assert magical_payload["mundane_items"] == []
    assert magical_payload["magical_items"]
    assert magical_payload["apparel_items"] == []

    apparel_payload = apparel_response.json()
    assert apparel_payload["mundane_items"] == []
    assert apparel_payload["magical_items"] == []
    assert apparel_payload["apparel_items"]


@pytest.mark.contract
def test_get_catalog_creatures_returns_expected_groups() -> None:
    app = _make_app()
    with TestClient(app) as client:
        creatures_response = client.get("/catalog/creatures")

    assert creatures_response.status_code == 200
    creatures_payload = creatures_response.json()
    assert set(creatures_payload.keys()) == {"creature_catalog", "exceptional_catalog"}
    assert any(item.get("subspecies") == "moonthorn_wolf" for item in creatures_payload["creature_catalog"])


@pytest.mark.contract
def test_get_catalog_vocab_returns_expected_groups() -> None:
    app = _make_app()
    with TestClient(app) as client:
        vocab_response = client.get("/catalog/vocab")

    assert vocab_response.status_code == 200
    vocab_payload = vocab_response.json()
    assert set(vocab_payload.keys()) == {
        "natural_abilities",
        "learned_commands",
        "tactical_roles",
        "training_levels",
        "bond_levels",
        "age_categories",
        "creature_sizes",
        "carrying_capacities",
        "movement_modes",
        "natural_weapons",
        "sapience_levels",
        "communication_levels",
        "autonomy_levels",
    }