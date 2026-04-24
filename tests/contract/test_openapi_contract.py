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
    assert spec["info"]["version"] == "4.2.0"

    new_session_required = spec["components"]["schemas"]["NewSessionRequest"][
        "required"
    ]
    assert new_session_required == ["character_name", "ancestry", "culture", "focus", "background"]

    roll_required = spec["components"]["schemas"]["RollRequest"]["required"]
    assert roll_required == ["target"]

    options_schema = spec["paths"]["/options"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert options_schema["$ref"] == "#/components/schemas/OptionsResponse"

    options_props = spec["components"]["schemas"]["OptionsResponse"]["properties"]
    assert sorted(options_props) == ["ancestries", "backgrounds", "cultures", "focus"]

    item_catalog_schema = spec["paths"]["/catalog/items"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert item_catalog_schema["$ref"] == "#/components/schemas/ItemCatalogResponse"

    creature_catalog_schema = spec["paths"]["/catalog/creatures"]["get"]["responses"][
        "200"
    ]["content"]["application/json"]["schema"]
    assert creature_catalog_schema["$ref"] == "#/components/schemas/CreatureCatalogResponse"

    vocab_schema = spec["paths"]["/catalog/vocab"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert vocab_schema["$ref"] == "#/components/schemas/CompanionVocabResponse"

    item_catalog_props = spec["components"]["schemas"]["ItemCatalogResponse"]["properties"]
    assert sorted(item_catalog_props) == ["apparel_items", "magical_items", "mundane_items"]

    creature_catalog_props = spec["components"]["schemas"]["CreatureCatalogResponse"]["properties"]
    assert sorted(creature_catalog_props) == ["creature_catalog", "exceptional_catalog"]

    vocab_props = spec["components"]["schemas"]["CompanionVocabResponse"]["properties"]
    assert sorted(vocab_props) == [
        "age_categories",
        "autonomy_levels",
        "bond_levels",
        "carrying_capacities",
        "communication_levels",
        "creature_sizes",
        "learned_commands",
        "movement_modes",
        "natural_abilities",
        "natural_weapons",
        "sapience_levels",
        "tactical_roles",
        "training_levels",
    ]

    npcs_schema = spec["paths"]["/npcs"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert npcs_schema["$ref"] == "#/components/schemas/NpcRegistryResponse"

    npcs_response_props = spec["components"]["schemas"]["NpcRegistryResponse"]["properties"]
    assert "entries" in npcs_response_props
    assert "count" in npcs_response_props

    npcs_entry_props = spec["components"]["schemas"]["NpcRegistryEntry"]["properties"]
    assert "id" in npcs_entry_props
    assert "name" in npcs_entry_props

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

    assert spec["paths"]["/combat/compute_max_hp"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ComputeMaxHpResponse"
    assert spec["paths"]["/combat/resolve_attack"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ResolveAttackResponse"
    assert "combat_rules_fingerprint" in spec["components"]["schemas"]["VersionResponse"]["properties"]


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
def test_openapi_contract_character_delta_includes_fields_dict() -> None:
    spec = app.openapi()
    properties = spec["components"]["schemas"]["CharacterStateDelta"]["properties"]

    assert "fields" in properties
    fields_schema = properties["fields"]
    assert "anyOf" in fields_schema
    object_variant = next(option for option in fields_schema["anyOf"] if option.get("type") == "object")
    assert object_variant["additionalProperties"]["type"] == "integer"


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


@pytest.mark.contract
def test_openapi_contract_roll_response_uses_roll_response_schema() -> None:
    spec = app.openapi()
    schema = spec["paths"]["/roll"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert schema["$ref"] == "#/components/schemas/RollResponse"


@pytest.mark.contract
def test_openapi_contract_location_get_response_uses_location_response_schema() -> None:
    spec = app.openapi()
    schema = spec["paths"]["/location/{location_id}"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert schema["$ref"] == "#/components/schemas/LocationResponse"


@pytest.mark.contract
def test_openapi_contract_location_connections_response_uses_connections_response_schema() -> None:
    spec = app.openapi()
    schema = spec["paths"]["/location/{location_id}/connections"]["get"]["responses"][
        "200"
    ]["content"]["application/json"]["schema"]
    assert schema["$ref"] == "#/components/schemas/ConnectionsResponse"


@pytest.mark.contract
def test_openapi_contract_location_post_responses_use_location_response_schema() -> None:
    spec = app.openapi()
    responses = spec["paths"]["/location"]["post"]["responses"]
    created_schema = responses["201"]["content"]["application/json"]["schema"]
    updated_schema = responses["200"]["content"]["application/json"]["schema"]
    assert created_schema["$ref"] == "#/components/schemas/LocationResponse"
    assert updated_schema["$ref"] == "#/components/schemas/LocationResponse"


@pytest.mark.contract
def test_openapi_contract_scene_response_uses_scene_context_schema() -> None:
    spec = app.openapi()
    schema = spec["paths"]["/scene/{session_id}"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert schema["$ref"] == "#/components/schemas/SceneContext"


@pytest.mark.contract
def test_openapi_contract_state_delta_response_uses_game_state_response_schema() -> None:
    spec = app.openapi()
    schema = spec["paths"]["/state/{session_id}/delta"]["post"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]
    assert schema["$ref"] == "#/components/schemas/GameStateResponse"


@pytest.mark.contract
def test_openapi_contract_tags_response_uses_tags_response_schema() -> None:
    spec = app.openapi()
    schema = spec["paths"]["/tags"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert schema["$ref"] == "#/components/schemas/TagsResponse"
