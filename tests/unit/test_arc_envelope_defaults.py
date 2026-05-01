from __future__ import annotations

from api.game_data import get_arc_type_default_envelope, load_arc_types


EXPECTED_ENVELOPE_KEYS = {
    "ap_award_min",
    "ap_award_max",
    "ap_award_fixed",
    "scene_soft_cap",
    "scene_hard_cap",
    "location_soft_cap",
    "location_hard_cap",
    "reputation_max_positive_delta",
    "reputation_max_negative_delta",
    "economy_coin_cd_max",
    "items_magical_tier_max",
    "items_mundane_tier_max",
    "leverage_obligation_slots_max",
    "leverage_evidence_grade_max",
}

ORDERED_TYPES = [
    "task_local",
    "contract_delicate",
    "mission_multi_leg",
    "undertaking_regional",
    "arc_campaign",
]


def test_each_type_registry_entry_has_all_envelope_fields() -> None:
    for entry in load_arc_types()["types"]:
        assert EXPECTED_ENVELOPE_KEYS <= set(entry)


def test_envelope_defaults_scale_monotonically_with_type() -> None:
    numeric_fields = [
        "reputation_max_positive_delta",
        "reputation_max_negative_delta",
        "economy_coin_cd_max",
        "items_mundane_tier_max",
        "leverage_obligation_slots_max",
        "leverage_evidence_grade_max",
    ]
    for field in numeric_fields:
        values = [get_arc_type_default_envelope(type_id)[field] for type_id in ORDERED_TYPES]
        assert values == sorted(values)

    magical_values = [
        get_arc_type_default_envelope(type_id)["items_magical_tier_max"] or 0
        for type_id in ORDERED_TYPES
    ]
    assert magical_values == sorted(magical_values)


def test_get_arc_type_default_envelope_returns_full_envelope_dict() -> None:
    for type_id in ORDERED_TYPES:
        assert set(get_arc_type_default_envelope(type_id)) == EXPECTED_ENVELOPE_KEYS