"""
game_data.py — Load game system JSON data and expose helper functions.

Replaces srd5e.py. Data lives in /data/ as JSON files for ancestry,
culture, focus archetypes, backgrounds, knowledge skills, and application
categories.
"""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).parent.parent / "data"
_DATA_FILES = (
    "characters/ancestry.json",
    "characters/culture.json",
    "characters/focus.json",
    "characters/backgrounds.json",
)
_ITEM_DATA_FILES = (
    "items/gear.json",
    "items/magical.json",
    "items/apparel.json",
    "items/armor.json",
    "items/weapons.json",
    "items/ammunition.json",
    "items/notable.json",
)
_SPELL_DATA_FILES = ("magic-spells.json",)
_MAGIC_DIR = _DATA_DIR / "magic"


@lru_cache(maxsize=None)
def _load_json(filename: str) -> dict[str, Any] | list[Any]:
    """Load a JSON file from the data directory."""
    path = _DATA_DIR / filename
    if path.name.startswith("_"):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if not str(k).startswith("_")}
    if isinstance(data, list):
        filtered = []
        for item in data:
            if isinstance(item, dict) and str(item.get("index", "")).startswith("_"):
                continue
            filtered.append(item)
        data = filtered
    # If it's a list of objects with 'index' keys, convert to dict
    if isinstance(data, list) and data and "index" in data[0]:
        return {item["index"]: item for item in data}
    return data


# ---------------------------------------------------------------------------
# Ancestries
# ---------------------------------------------------------------------------

def get_ancestry(index: str) -> dict[str, Any]:
    """Return ancestry data for the given index (e.g. 'human', 'dragonborn')."""
    data = _load_json("characters/ancestry.json")
    if index not in data:
        raise ValueError(f"Unknown ancestry: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


def list_ancestries() -> list[dict[str, Any]]:
    data = _load_json("characters/ancestry.json")
    return [
        {
            "index": k,
            "name": v["name"],
            "description": v.get("description", ""),
            "primary_domain": v.get("primary_domain"),
            "domains": v["domains"],
            "traits": v.get("traits", []),
        }
        for k, v in data.items()
    ]


# ---------------------------------------------------------------------------
# Cultures
# ---------------------------------------------------------------------------

def get_culture(index: str) -> dict[str, Any]:
    """Return culture data for the given index."""
    data = _load_json("characters/culture.json")
    if index not in data:
        raise ValueError(f"Unknown culture: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


def list_cultures() -> list[dict[str, Any]]:
    """Return all cultures as a list of summary dicts."""
    data = _load_json("characters/culture.json")
    return [
        {
            "index": k,
            "name": v["name"],
            "description": v.get("description", ""),
            "domain_bonuses": v.get("domain_bonuses", {}),
            "knowledge_tags": v.get("knowledge_tags", {}),
            "application_tags": v.get("application_tags", {}),
            "field_tags": v.get("field_tags", {}),
        }
        for k, v in data.items()
    ]


# ---------------------------------------------------------------------------
# Focus Archetypes
# ---------------------------------------------------------------------------

def get_focus(index: str) -> dict[str, Any]:
    """Return focus archetype data for the given index (e.g. 'devoted')."""
    data = _load_json("characters/focus.json")
    if index not in data:
        raise ValueError(f"Unknown focus: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


def list_focus() -> list[dict[str, Any]]:
    """Return all focus archetypes as a list of summary dicts."""
    data = _load_json("characters/focus.json")
    return [
        {
            "index": k,
            "name": v["name"],
            "description": v.get("description", ""),
            "signature_tag": v.get("signature_tag"),
            "knowledge_tags": v.get("knowledge_tags", {}),
            "application_tags": v.get("application_tags", {}),
            "field_tags": v.get("field_tags", {}),
        }
        for k, v in data.items()
    ]


# ---------------------------------------------------------------------------
# Backgrounds
# ---------------------------------------------------------------------------

def get_background(index: str) -> dict[str, Any]:
    """Return background data for the given index (e.g. 'soldier')."""
    data = _load_json("characters/backgrounds.json")
    if index not in data:
        raise ValueError(f"Unknown background: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


def list_backgrounds() -> list[dict[str, Any]]:
    """Return all backgrounds as a list of summary dicts."""
    data = _load_json("characters/backgrounds.json")
    return [
        {
            "index": k,
            "name": v["name"],
            "description": v.get("description", ""),
            "domain_bonuses": v.get("domain_bonuses", {}),
            "knowledge_tags": v.get("knowledge_tags", {}),
            "application_tags": v.get("application_tags", {}),
            "field_tags": v.get("field_tags", {}),
        }
        for k, v in data.items()
    ]


# ---------------------------------------------------------------------------
# Item catalogs
# ---------------------------------------------------------------------------

def list_mundane_items() -> list[dict[str, Any]]:
    """Return all mundane catalog items."""
    data = _load_json("items/gear.json")
    if not isinstance(data, list):
        return []
    return data


def list_magical_items() -> list[dict[str, Any]]:
    """Return all magical catalog items."""
    data = _load_json("items/magical.json")
    if not isinstance(data, list):
        return []
    return data


def list_apparel_items() -> list[dict[str, Any]]:
    """Return all apparel catalog items."""
    data = _load_json("items/apparel.json")
    if not isinstance(data, list):
        return []
    return data


def list_all_items() -> list[dict[str, Any]]:
    """Return concatenated mundane + magical + apparel item catalogs."""
    return list_mundane_items() + list_magical_items() + list_apparel_items()


def data_fingerprint() -> str:
    """
    Stable SHA256 fingerprint of core game data files used by /options and seeding.

    Exposed by GET /version for deployment/contract sanity checks.
    """
    hasher = hashlib.sha256()
    for filename in (*_DATA_FILES, *_ITEM_DATA_FILES, *_SPELL_DATA_FILES):
        path = _DATA_DIR / filename
        with open(path, "rb") as f:
            hasher.update(f.read())

    if _MAGIC_DIR.exists():
        for path in sorted(_MAGIC_DIR.glob("*.json")):
            with open(path, "rb") as f:
                hasher.update(f.read())
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# Character seeding
# ---------------------------------------------------------------------------

def seed_character(
    name: str,
    ancestry_index: str,
    culture_index: str,
    focus_index: str,
    background_index: str,
    adjustment_points: dict[str, int] | None = None,
    identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a complete character dict from ancestry + culture + focus + background.

    Applies:
    - Ancestry base domain scores
    - Culture and background domain bonuses
    - Player adjustment points (+10 total, max +5 per domain)
    - Knowledge, application, and field tag stacking across all four layers
    - Ancestry trait application tags at T1 when present

    Optional identity dict is passed through verbatim — it is validated
    upstream by the Identity Pydantic model before reaching here.

    Returns the character dict ready for JSONB storage.
    """
    ancestry   = get_ancestry(ancestry_index)
    culture    = get_culture(culture_index)
    focus      = get_focus(focus_index)
    background = get_background(background_index)

    # --- Domain scores ---
    domains = dict(ancestry["domains"])

    for layer in (culture, background):
        for domain, bonus in layer.get("domain_bonuses", {}).items():
            if domain not in domains:
                raise ValueError(f"Invalid domain: {domain!r}")
            domains[domain] += bonus

    adj       = adjustment_points or {}
    total_adj = sum(adj.values())
    if total_adj > 10:
        raise ValueError(f"Adjustment pool is 10 points max. Got {total_adj}.")
    for domain, points in adj.items():
        if domain not in domains:
            raise ValueError(f"Invalid domain: {domain!r}")
        if points > 5:
            raise ValueError(f"Max +5 per domain. {domain} got +{points}.")
        domains[domain] += points
        if domains[domain] > 80:
            raise ValueError(f"Domain {domain!r} cannot exceed 80. Got {domains[domain]}.")

    for domain, score in domains.items():
        if score > 80:
            raise ValueError(f"Domain {domain!r} cannot exceed 80. Got {score}.")

    # --- Competency and field tags ---
    knowledge: dict[str, int] = {}
    application: dict[str, int] = {}
    fields: dict[str, int] = {}

    def _stack_tags(target: dict[str, int], source: dict[str, int]) -> None:
        for tag, tier in source.items():
            if tag in target:
                target[tag] = min(target[tag] + 1, 5)
            else:
                target[tag] = tier

    for trait in ancestry.get("traits", []):
        application_tag = trait.get("application_tag")
        if application_tag and application_tag not in application:
            application[application_tag] = 1

    for layer in (culture, background, focus):
        _stack_tags(knowledge, layer.get("knowledge_tags", {}))
        _stack_tags(application, layer.get("application_tags", {}))
        _stack_tags(fields, layer.get("field_tags", {}))

    # --- Assemble character dict ---
    character: dict[str, Any] = {
        "name":           name,
        "ancestry":       ancestry_index,
        "culture":        culture_index,
        "focus":          focus_index,
        "background":     background_index,
        "hp":             {"current": 100, "max": 100},
        "domains":        domains,
        "knowledge":      knowledge,
        "application":    application,
        "fields":         fields,
        "status_effects": [],
        "notes":          "",
        # v3.1.0 narrative and inventory blocks
        "identity":       _default_identity(identity),
        "equipment":      {"worn": [], "carried": [], "stashed": []},
        "reputation":     [],
        "advancement": {
            "points_available": 0,
            "points_spent": 0,
            "points_earned_total": 0,
        },
    }

    return character


# ---------------------------------------------------------------------------
# Identity helpers
# ---------------------------------------------------------------------------

_IDENTITY_DEFAULTS: dict[str, Any] = {
    "origin":      "",
    "motivations": [],
    "quirks":      [],
    "bonds":       [],
    "flaws":       [],
    "wound":       "",
    "alignment": {
        "order":      "neutral",
        "intent":     "neutral",
        "ethos_note": "",
    },
}


def _default_identity(identity: dict[str, Any] | None) -> dict[str, Any]:
    """
    Merge a caller-supplied identity dict onto the default identity shape.

    Ensures the stored JSONB always has all keys present, even when the
    player skips optional fields at character creation.
    """
    if not identity:
        return dict(_IDENTITY_DEFAULTS)

    merged = dict(_IDENTITY_DEFAULTS)
    merged.update(identity)

    # Ensure alignment sub-keys are always present
    incoming_alignment = identity.get("alignment", {})
    merged["alignment"] = {**_IDENTITY_DEFAULTS["alignment"], **incoming_alignment}

    return merged