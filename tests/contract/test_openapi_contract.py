import pytest

from api.main import app


@pytest.mark.contract
def test_openapi_contract_has_expected_core_shapes() -> None:
    # Avoid startup/lifespan side effects (DB pool creation) for pure contract checks.
    spec = app.openapi()
    assert spec["info"]["version"] == "3.1.0"

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

    session_new_201 = spec["paths"]["/session/new"]["post"]["responses"]["201"][
        "content"
    ]["application/json"]["schema"]
    assert session_new_201["$ref"] == "#/components/schemas/NewSessionResponse"

    state_get_200 = spec["paths"]["/state/{session_id}"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert state_get_200["$ref"] == "#/components/schemas/GameStateResponse"

    create_character_200 = spec["paths"]["/character/create"]["post"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert create_character_200["$ref"] == "#/components/schemas/CreateCharacterResponse"

    location_post_responses = spec["paths"]["/location"]["post"]["responses"]
    assert "201" in location_post_responses
    assert "200" in location_post_responses

    new_session_props = spec["components"]["schemas"]["NewSessionResponse"]["properties"]
    assert "$ref" in new_session_props["character"]
    assert "$ref" in new_session_props["world"]

    create_character_props = spec["components"]["schemas"]["CreateCharacterResponse"]["properties"]
    assert "$ref" in create_character_props["character"]
