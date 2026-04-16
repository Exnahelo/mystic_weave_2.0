import pytest

from api.main import app


MAX_ROUTE_DESCRIPTION_LENGTH = 300
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def _iter_operations(spec: dict):
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() in HTTP_METHODS:
                yield path, method.lower(), operation


def _resolve_schema(spec: dict, schema: dict) -> dict:
    schema_ref = schema.get("$ref")
    if not schema_ref:
        return schema
    assert schema_ref.startswith("#/components/schemas/")
    schema_name = schema_ref.split("/")[-1]
    return spec["components"]["schemas"][schema_name]


@pytest.mark.contract
def test_openapi_contract_has_expected_core_shapes() -> None:
    # Avoid startup/lifespan side effects (DB pool creation) for pure contract checks.
    spec = app.openapi()
    assert spec["info"]["version"] == "3.4.0"

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


@pytest.mark.contract
def test_openapi_policy_route_descriptions_respect_max_length() -> None:
    spec = app.openapi()
    for path, method, operation in _iter_operations(spec):
        description = operation.get("description") or ""
        assert len(description) <= MAX_ROUTE_DESCRIPTION_LENGTH, (
            f"{method.upper()} {path} description length {len(description)} exceeds "
            f"max {MAX_ROUTE_DESCRIPTION_LENGTH}"
        )


@pytest.mark.contract
def test_openapi_policy_health_version_root_response_schemas_have_properties() -> None:
    spec = app.openapi()
    for path in ("/", "/health", "/version"):
        schema = spec["paths"][path]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        resolved = _resolve_schema(spec, schema)
        assert resolved.get("type") == "object"
        assert "properties" in resolved
        assert resolved["properties"]


@pytest.mark.contract
def test_openapi_policy_has_top_level_servers_url() -> None:
    spec = app.openapi()
    servers = spec.get("servers")
    assert isinstance(servers, list)
    assert servers
    assert any(isinstance(server.get("url"), str) and server["url"].strip() for server in servers)


@pytest.mark.contract
def test_openapi_contract_has_state_delta_endpoint() -> None:
    spec = app.openapi()
    assert "/state/{session_id}/delta" in spec["paths"]
    delta_post = spec["paths"]["/state/{session_id}/delta"]["post"]
    request_schema = delta_post["requestBody"]["content"]["application/json"]["schema"]
    assert request_schema["$ref"] == "#/components/schemas/ApplyStateDeltaRequest"


@pytest.mark.contract
def test_openapi_contract_has_state_delta_schema_components() -> None:
    spec = app.openapi()
    schemas = spec["components"]["schemas"]
    assert "ApplyStateDeltaRequest" in schemas
    assert "CharacterStateDelta" in schemas
    assert "WorldStateDelta" in schemas
    assert "EquipmentDelta" in schemas


@pytest.mark.contract
def test_openapi_contract_character_delta_includes_magic_and_draconic_fields() -> None:
    spec = app.openapi()
    properties = spec["components"]["schemas"]["CharacterStateDelta"]["properties"]

    assert "magic_fields" in properties
    magic_fields_schema = properties["magic_fields"]
    assert "anyOf" in magic_fields_schema
    array_variant = next(option for option in magic_fields_schema["anyOf"] if option.get("type") == "array")
    assert array_variant["items"]["type"] == "string"

    assert "draconic_traits" in properties
    draconic_traits_schema = properties["draconic_traits"]
    assert "anyOf" in draconic_traits_schema
    array_variant = next(option for option in draconic_traits_schema["anyOf"] if option.get("type") == "array")
    assert array_variant["items"]["type"] == "string"


@pytest.mark.contract
def test_openapi_contract_world_delta_uses_sparse_economy_schema() -> None:
    spec = app.openapi()
    economy_property = spec["components"]["schemas"]["WorldStateDelta"]["properties"]["economy"]
    assert "anyOf" in economy_property
    ref_variant = next(
        option for option in economy_property["anyOf"] if "$ref" in option
    )
    economy_schema = _resolve_schema(spec, ref_variant)

    assert economy_schema["type"] == "object"
    assert economy_schema.get("required") in (None, [])
    assert "coin" in economy_schema["properties"]
    assert "wealth_tier" in economy_schema["properties"]
    assert "trade_goods" in economy_schema["properties"]
    assert "obligations" in economy_schema["properties"]
