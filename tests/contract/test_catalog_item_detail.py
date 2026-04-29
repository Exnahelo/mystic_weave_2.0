import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import catalog


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(catalog.router)
    return app


@pytest.mark.contract
def test_get_catalog_item_longsword_returns_full_item_shape() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.get("/catalog/items/sword")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "sword"
    assert payload["category"] == "weapon"
    assert payload["base_damage"] is not None
    assert payload["value_cd"] > 0


@pytest.mark.contract
def test_get_catalog_item_flame_tongue_returns_magical_modules() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.get("/catalog/items/heartlight-lantern")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "heartlight-lantern"
    assert payload["category"] == "gear"
    assert payload["tier"] is not None
    assert payload["magic_field"] is not None


@pytest.mark.contract
def test_get_catalog_item_nonexistent_returns_404() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.get("/catalog/items/nonexistent-item")

    assert response.status_code == 404
    assert "item not found" in response.json()["detail"]


@pytest.mark.contract
def test_get_catalog_item_torch_returns_200() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.get("/catalog/items/gear-torch")

    assert response.status_code == 200
    assert response.json()["id"] == "gear-torch"