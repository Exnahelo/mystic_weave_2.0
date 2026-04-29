import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import combat


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(combat.router)
    return app


@pytest.mark.contract
def test_compute_max_hp_happy_path_returns_expected_math() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.post(
            "/combat/compute_max_hp",
            json={
                "armor_id": "plate",
                "armor_tier": 3,
                "shield_id": "shield",
                "shield_tier": 2,
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "max_hp": 183,
        "base": 100,
        "armor_contribution": 68,
        "shield_contribution": 15,
        "armor_id": "plate",
        "armor_tier": 3,
        "shield_id": "shield",
        "shield_tier": 2,
    }


@pytest.mark.contract
def test_compute_max_hp_rejects_tier_out_of_range() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.post(
            "/combat/compute_max_hp",
            json={"armor_id": "plate", "armor_tier": 6},
        )

    assert response.status_code == 422


@pytest.mark.contract
def test_compute_max_hp_rejects_non_armor_set() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.post(
            "/combat/compute_max_hp",
            json={"armor_id": "bracers", "armor_tier": 1},
        )

    assert response.status_code == 422


@pytest.mark.contract
def test_compute_max_hp_rejects_unknown_armor() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.post(
            "/combat/compute_max_hp",
            json={"armor_id": "missing_armor", "armor_tier": 1},
        )

    assert response.status_code == 422


@pytest.mark.contract
def test_resolve_attack_minimum_valid_input_returns_well_formed_response() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.post(
            "/combat/resolve_attack",
            json={
                "weapon_id": "sword",
                "weapon_tier": 0,
                "defender_is_unarmored": False,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert sorted(payload.keys()) == [
        "critical_hit",
        "damage",
        "events",
        "fumble",
        "hit",
        "rebound",
        "roll_1",
        "roll_2",
        "tied",
    ]
    assert sorted(payload["roll_1"].keys()) == ["base_target", "target", "value"]
    assert sorted(payload["damage"].keys()) == [
        "agility_reduction_multiplier",
        "ammo_modifier",
        "effective_base",
        "final",
        "margin_multiplier",
        "pre_reduction",
        "weapon_base",
    ]


@pytest.mark.contract
def test_resolve_attack_rejects_unknown_weapon() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.post(
            "/combat/resolve_attack",
            json={
                "weapon_id": "missing_weapon",
                "weapon_tier": 0,
                "defender_is_unarmored": False,
            },
        )

    assert response.status_code == 422


@pytest.mark.contract
def test_resolve_attack_rejects_unknown_ammo() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.post(
            "/combat/resolve_attack",
            json={
                "weapon_id": "sword",
                "weapon_tier": 0,
                "ammo_id": "missing_ammo",
                "defender_is_unarmored": False,
            },
        )

    assert response.status_code == 422


@pytest.mark.contract
def test_resolve_attack_rejects_weapon_tier_out_of_range() -> None:
    app = _make_app()
    with TestClient(app) as client:
        response = client.post(
            "/combat/resolve_attack",
            json={
                "weapon_id": "sword",
                "weapon_tier": 6,
                "defender_is_unarmored": False,
            },
        )

    assert response.status_code == 422
