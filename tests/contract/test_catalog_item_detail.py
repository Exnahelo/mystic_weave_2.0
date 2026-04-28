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
        response = client.get("/catalog/items/longsword")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "longsword"
    assert "weapon" in payload["modules"]
    assert payload["worldness"]["pricing"]["canonical_value_cp"] == 1500


@pytest.mark.contract
def test_get_catalog_item_flame_tongue_returns_magical_modules() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.get("/catalog/items/flame-tongue-longsword")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "flame-tongue-longsword"
    assert "attunement" in payload["modules"]
    assert payload["modules"]["effects"]


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
        response = client.get("/catalog/items/torch")

    assert response.status_code == 200
    assert response.json()["id"] == "torch"