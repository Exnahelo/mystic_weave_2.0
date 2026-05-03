"""Asserts api/models.py arc Literal types match data/catalog/registries/arc_types.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import get_args

from api.models import ArcOriginType, ArcPrimaryType, ArcStakeScale, ArcState

REPO_ROOT = Path(__file__).resolve().parents[2]
ARC_TYPES_JSON = REPO_ROOT / "data" / "catalog" / "registries" / "arc_types.json"


def _load_registry() -> dict:
    return json.loads(ARC_TYPES_JSON.read_text(encoding="utf-8"))


def test_arc_states_match_registry():
    """ArcState Literal args match registry 'states'."""
    registry = _load_registry()
    code_states = set(get_args(ArcState))
    json_states = set(registry["states"])
    assert code_states == json_states, (
        f"ArcState mismatch.\n  code: {code_states}\n  json: {json_states}"
    )


def test_arc_stake_scales_match_registry():
    """ArcStakeScale Literal args match registry 'stake_scales'."""
    registry = _load_registry()
    code_scales = set(get_args(ArcStakeScale))
    json_scales = set(registry["stake_scales"])
    assert code_scales == json_scales, (
        f"ArcStakeScale mismatch.\n  code: {code_scales}\n  json: {json_scales}"
    )


def test_arc_origin_types_match_registry():
    """ArcOriginType Literal args match registry 'origin_types'."""
    registry = _load_registry()
    code_types = set(get_args(ArcOriginType))
    json_types = set(registry["origin_types"])
    assert code_types == json_types, (
        f"ArcOriginType mismatch.\n  code: {code_types}\n  json: {json_types}"
    )


def test_arc_primary_types_match_registry_type_ids():
    """ArcPrimaryType Literal args match the registry types[].id list.

    The registry stores primary types as objects in the `types` array, each with
    an `id` and per-type caps. The Literal must equal the set of those ids.
    """
    registry = _load_registry()
    code_primaries = set(get_args(ArcPrimaryType))
    json_primary_ids = {t["id"] for t in registry["types"]}
    assert code_primaries == json_primary_ids, (
        f"ArcPrimaryType mismatch.\n  code: {code_primaries}\n  json: {json_primary_ids}"
    )
