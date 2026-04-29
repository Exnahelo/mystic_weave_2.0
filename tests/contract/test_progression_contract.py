import pytest

from api.main import app


@pytest.mark.contract
def test_progression_endpoints_present() -> None:
    spec = app.openapi()
    for path, method in {
        "/progression/{session_id}": "get",
        "/progression/{session_id}/tag-advance": "post",
        "/progression/{session_id}/ap-award": "post",
        "/progression/{session_id}/spend": "post",
        "/progression/{session_id}/propose-tag": "post",
        "/progression/{session_id}/confirm-tag": "post",
    }.items():
        assert path in spec["paths"]
        assert method in spec["paths"][path]


@pytest.mark.contract
def test_progression_models_present_and_advancement_shape() -> None:
    schemas = app.openapi()["components"]["schemas"]
    for name in (
        "AdvancementState",
        "TagAdvanceRequest",
        "TagAdvanceResponse",
        "APAwardRequest",
        "APAwardResponse",
        "APSpendRequest",
        "APSpendResponse",
        "TagProposalRequest",
        "TagProposalResponse",
        "TagConfirmRequest",
        "TagConfirmResponse",
    ):
        assert name in schemas

    props = schemas["AdvancementState"]["properties"]
    assert set(props) == {"points_available", "points_spent", "points_earned_total", "tag_counter"}
    assert props["tag_counter"]["maximum"] == 2


@pytest.mark.contract
def test_progression_version_is_4_2_0() -> None:
    assert app.openapi()["info"]["version"] == "4.2.0"