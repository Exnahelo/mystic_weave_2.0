import pytest

from api.companions import generate_companion_id


@pytest.mark.unit
def test_generate_companion_id_no_collision() -> None:
    assert generate_companion_id("sylvara_heartwood", "moonthorn_wolf", set()) == "sylvara_heartwood_moonthorn_wolf"


@pytest.mark.unit
def test_generate_companion_id_first_collision() -> None:
    existing = {"sylvara_heartwood_moonthorn_wolf"}
    assert generate_companion_id("sylvara_heartwood", "moonthorn_wolf", existing) == "sylvara_heartwood_moonthorn_wolf_2"


@pytest.mark.unit
def test_generate_companion_id_multiple_collisions() -> None:
    existing = {
        "sylvara_heartwood_moonthorn_wolf",
        "sylvara_heartwood_moonthorn_wolf_2",
        "sylvara_heartwood_moonthorn_wolf_3",
    }
    assert generate_companion_id("sylvara_heartwood", "moonthorn_wolf", existing) == "sylvara_heartwood_moonthorn_wolf_4"