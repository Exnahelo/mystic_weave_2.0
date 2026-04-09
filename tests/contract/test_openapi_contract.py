import pytest

from api.main import app


@pytest.mark.contract
def test_openapi_contract_has_expected_core_shapes() -> None:
    # Avoid startup/lifespan side effects (DB pool creation) for pure contract checks.
    spec = app.openapi()
    assert spec["info"]["version"] == "3.0.0"

    new_session_required = spec["components"]["schemas"]["NewSessionRequest"][
        "required"
    ]
    assert new_session_required == ["character_name", "species", "focus", "background"]

    roll_required = spec["components"]["schemas"]["RollRequest"]["required"]
    assert roll_required == ["target"]

    options_schema = spec["paths"]["/options"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert options_schema["$ref"] == "#/components/schemas/OptionsResponse"
