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
def test_get_catalog_items_includes_new_gear_items_and_armor() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.get("/catalog/items")

    assert response.status_code == 200
    payload = response.json()
    mundane_ids = {item["id"] for item in payload["mundane"]}
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
    assert any(item["id"] == "weapon_knife_01" for item in payload["weapons"])
    assert any(item["id"] == "armor_unarmored_01" for item in payload["armor"])


@pytest.mark.contract
def test_get_catalog_creatures_and_enums_return_expected_groups() -> None:
    app = _make_app()
    with TestClient(app) as client:
        creatures_response = client.get("/catalog/creatures")
        enums_response = client.get("/catalog/enums")

    assert creatures_response.status_code == 200
    creatures_payload = creatures_response.json()
    assert set(creatures_payload.keys()) == {
        "creatures",
        "exceptional",
        "natural_abilities",
        "learned_commands",
        "tactical_roles",
    }
    assert any(item.get("subspecies") == "moonthorn_wolf" for item in creatures_payload["creatures"])

    assert enums_response.status_code == 200
    enums_payload = enums_response.json()
    assert set(enums_payload.keys()) == {
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