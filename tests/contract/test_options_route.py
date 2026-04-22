import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import options


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(options.router)
    return app


@pytest.mark.contract
def test_get_options_includes_weapons_and_armor() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.get("/options")

    assert response.status_code == 200
    payload = response.json()
    assert "weapons" in payload
    assert "armor" in payload
    assert isinstance(payload["weapons"], list)
    assert isinstance(payload["armor"], list)
    assert any(item["id"] == "weapon_knife_01" for item in payload["weapons"])
    assert any(item["id"] == "armor_unarmored_01" for item in payload["armor"])


@pytest.mark.contract
def test_get_options_includes_new_gear_items_in_mundane_items() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.get("/options")

    assert response.status_code == 200
    mundane_ids = {item["id"] for item in response.json()["mundane_items"]}
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