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
from typing import Any, Callable

from api.items import Item, derive_indexes
from api.models import DOMAIN_KEYS
from core.dice_roller import roll

_DATA_DIR = Path(__file__).parent.parent / "data"
_DATA_FILES = (
    "characters/ancestry.json",
    "characters/culture.json",
    "characters/focus.json",
    "characters/background.json",
)
_TAG_REGISTRY_FILES = (
    "tags/knowledge_groups.json",
    "tags/magic_fields.json",
    "tags/applications.json",
)
_ITEM_DATA_FILES = (
    "items/gear.json",
    "items/magical_item.json",
    "items/apparel.json",
    "items/armor.json",
    "items/weapon.json",
    "items/ammunition.json",
)
_SPELL_DATA_FILES = (
    "magic/alchemy.json",
    "magic/binding.json",
    "magic/druidry.json",
    "magic/elemental.json",
    "magic/illusion.json",
    "magic/necromancy.json",
    "magic/runecraft.json",
    "magic/sacred.json",
    "magic/warding.json",
)
_BEAST_DATA_FILES = (
    "beasts/creatures.json",
    "beasts/exceptional.json",
    "beasts/natural_abilities.json",
    "beasts/learned_commands.json",
    "beasts/tactical_roles.json",
)
_CATALOG_ITEMS_DIR = _DATA_DIR / "catalog" / "items"
_NPC_DATA_DIR = _DATA_DIR / "npcs"
_MAGIC_DIR = _DATA_DIR / "magic"
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


_WEAPON_TIER_TARGETS = {
    0: 45,
    1: 55,
    2: 65,
    3: 75,
    4: 85,
    5: 95,
}


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


@lru_cache(maxsize=1)
def load_catalog_items() -> list[dict[str, Any]]:
    """
    Load every item under data/catalog/items/**/*.json.

    Each item is validated through the Item Pydantic model at load time;
    validation errors raise immediately so a broken catalog fails fast at
    startup rather than at request time.

    Returns a list of dicts in stable order (sorted by ID). Each dict has
    an extra `_subdir` key (the immediate parent directory under
    catalog/items/, e.g. "weapons", "armor", "gear") for downstream
    category routing. The `_subdir` key is the only field added; all other
    fields are exactly as authored.
    """
    if not _CATALOG_ITEMS_DIR.is_dir():
        return []

    out: list[dict[str, Any]] = []
    for path in sorted(_CATALOG_ITEMS_DIR.rglob("*.json")):
        # Skip template files (starts with underscore) defensively, though
        # data/catalog/items/ should not contain any.
        if path.name.startswith("_"):
            continue
        raw = json.loads(path.read_text())
        # Validate. Raises pydantic.ValidationError on failure.
        Item.model_validate(raw)
        # Tag with subdir for category routing.
        subdir = path.parent.name
        raw["_subdir"] = subdir
        out.append(raw)

    out.sort(key=lambda d: d["id"])
    return out


def project_catalog_to_item_option(item: dict[str, Any]) -> dict[str, Any]:
    """
    Project a catalog Item dict into the ItemOption shape consumed by the
    legacy /catalog/items?kind=... endpoint.

    Mapping:
      - id, name, description, tags: copied
      - category: derived from the item's _subdir
                  (e.g. "weapons" -> "weapon", "armor" -> "armor",
                   "ammunition" -> "ammunition", "gear" -> "gear")
      - roll_tag: None (no direct equivalent in new schema; the first
                  tool.roll_tags entry is NOT surfaced here to keep the
                  projection lossless and unambiguous)

    The Item model has no apparel module yet; apparel-shaped catalog items
    do not exist in this batch. The projection is best-effort and stable:
    extra fields beyond ItemOption's defined fields are not added (the
    ItemOption model has extra="allow", but we avoid relying on it).
    """
    subdir_to_category = {
        "weapons": "weapon",
        "armor": "armor",
        "ammunition": "ammunition",
        "gear": "gear",
        "wondrous": "wondrous",
    }
    return {
        "id": item["id"],
        "name": item["name"],
        "category": subdir_to_category.get(item.get("_subdir", ""), "gear"),
        "description": item.get("description", ""),
        "tags": list(item.get("tags", [])),
        "roll_tag": None,
    }


def filter_catalog_by_kind(kind: str) -> list[dict[str, Any]]:
    """
    Return catalog items projected to ItemOption shape, filtered by the
    legacy `kind` query parameter values.

    Filter rules (using derive_indexes):
      - "magical":    is_magical == True
      - "weapon":     is_weapon == True AND is_magical == False
      - "armor":      is_armor == True AND is_magical == False
      - "ammunition": is_ammunition == True
      - "mundane":    not (is_weapon or is_armor or is_ammunition or is_magical)
      - "apparel":    [] (no apparel module in current schema)

    The "magical" bucket overrides weapon/armor for items that are both,
    matching the legacy convention where magical longswords appeared in
    magical_item.json, not weapon.json.

    Unknown kind values return an empty list rather than raising; route
    layer handles input validation.
    """
    if kind == "apparel":
        return []

    out: list[dict[str, Any]] = []
    for item in load_catalog_items():
        idx = derive_indexes(
            Item.model_validate({k: v for k, v in item.items() if k != "_subdir"})
        )

        if kind == "magical":
            include = idx["is_magical"]
        elif kind == "weapon":
            include = idx["is_weapon"] and not idx["is_magical"]
        elif kind == "armor":
            include = idx["is_armor"] and not idx["is_magical"]
        elif kind == "ammunition":
            include = idx["is_ammunition"]
        elif kind == "mundane":
            include = not (
                idx["is_weapon"]
                or idx["is_armor"]
                or idx["is_ammunition"]
                or idx["is_magical"]
            )
        else:
            include = False

        if include:
            out.append(project_catalog_to_item_option(item))

    return out


# ---------------------------------------------------------------------------
# Ancestries
# ---------------------------------------------------------------------------

def get_ancestry(index: str) -> dict[str, Any]:
    """Return ancestry data for the given index (e.g. 'human', 'drakari')."""
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
    data = _load_json("characters/background.json")
    if index not in data:
        raise ValueError(f"Unknown background: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


def list_backgrounds() -> list[dict[str, Any]]:
    """Return all backgrounds as a list of summary dicts."""
    data = _load_json("characters/background.json")
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

def list_knowledge_groups() -> list[dict[str, Any]]:
    """Return all mundane knowledge group entries."""
    data = _load_json("tags/knowledge_groups.json")
    if not isinstance(data, dict):
        return []
    return list(data.values())


def get_knowledge_group(index: str) -> dict[str, Any]:
    """Return a specific knowledge group by index."""
    data = _load_json("tags/knowledge_groups.json")
    if index not in data:
        raise ValueError(f"Unknown knowledge group: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


def list_magic_fields() -> list[dict[str, Any]]:
    """Return all magic field entries."""
    data = _load_json("tags/magic_fields.json")
    if not isinstance(data, dict):
        return []
    return list(data.values())


def get_magic_field(index: str) -> dict[str, Any]:
    """Return a specific magic field by index."""
    data = _load_json("tags/magic_fields.json")
    if index not in data:
        raise ValueError(f"Unknown magic field: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


def list_applications() -> list[dict[str, Any]]:
    """Return all application entries."""
    data = _load_json("tags/applications.json")
    if not isinstance(data, dict):
        return []
    return list(data.values())


def get_application(index: str) -> dict[str, Any]:
    """Return a specific application by index."""
    data = _load_json("tags/applications.json")
    if index not in data:
        raise ValueError(f"Unknown application: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


def get_application_group(app_index: str) -> str | None:
    """Return the parent group/field index for an application, or None."""
    data = _load_json("tags/applications.json")
    if app_index not in data:
        return None
    return data[app_index].get("group")


def get_tag_primary_domain(tag_index: str, tag_kind: str) -> str | None:
    """
    Return the primary_domain of a tag by its index and kind.

    tag_kind: 'knowledge' | 'application' | 'field'

    For applications, primary_domain comes directly from the application entry.
    For knowledge groups and magic fields, it comes from the group/field entry.

    Returns None if the tag is not found in the registry. Callers should
    treat None as "skip counter increment for this tag" — defensive, not fatal.
    """
    if tag_kind == "knowledge":
        data = _load_json("tags/knowledge_groups.json")
    elif tag_kind == "application":
        data = _load_json("tags/applications.json")
    elif tag_kind == "field":
        data = _load_json("tags/magic_fields.json")
    else:
        return None

    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict) and entry.get("index") == tag_index:
                return entry.get("primary_domain")
        return None

    if isinstance(data, dict):
        entry = data.get(tag_index)
        if isinstance(entry, dict):
            return entry.get("primary_domain")
        return None

    return None


def validate_application_parent_cap(
    character: dict[str, Any],
    delta_application: dict[str, int],
) -> None:
    """
    Enforce: an application tag may not exceed the tier of its parent knowledge group.

    Exception: if the application is already above its parent (seeded above at creation),
    it does not regress, but cannot advance further until the parent catches up.

    Raises ValueError with a descriptive message on violation.
    """
    knowledge = character.get("knowledge") or {}
    existing_application = character.get("application") or {}

    for app_index, new_tier in delta_application.items():
        if not isinstance(new_tier, int):
            continue

        parent_group = get_application_group(app_index)
        if parent_group is None:
            continue

        parent_tier = knowledge.get(parent_group, 0) or 0
        old_tier = existing_application.get(app_index, 0) or 0

        if old_tier > parent_tier:
            if new_tier > old_tier:
                raise ValueError(
                    f"application {app_index!r} is at T{old_tier} (seeded above "
                    f"parent {parent_group!r} at T{parent_tier}); cannot advance "
                    f"to T{new_tier} until parent catches up"
                )
            continue

        if new_tier > parent_tier:
            raise ValueError(
                f"application {app_index!r} cannot advance to T{new_tier}: "
                f"parent knowledge group {parent_group!r} is at T{parent_tier}"
            )

def list_mundane_items() -> list[dict[str, Any]]:
    """Return all mundane catalog items."""
    data = _load_json("items/gear.json")
    if not isinstance(data, list):
        return []
    return data


def list_weapons() -> list[dict[str, Any]]:
    """Return all weapon catalog items."""
    data = _load_json("items/weapon.json")
    if not isinstance(data, list):
        return []
    return data


def list_armor() -> list[dict[str, Any]]:
    """Return all armor catalog items."""
    data = _load_json("items/armor.json")
    if not isinstance(data, list):
        return []
    return data


def list_ammunition() -> list[dict[str, Any]]:
    """Return all ammunition catalog items."""
    data = _load_json("items/ammunition.json")
    if not isinstance(data, list):
        return []
    return data


def list_magical_items() -> list[dict[str, Any]]:
    """Return all magical catalog items."""
    data = _load_json("items/magical_item.json")
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
    """Return concatenated runtime item catalogs."""
    return (
        list_mundane_items()
        + list_magical_items()
        + list_apparel_items()
        + list_weapons()
        + list_armor()
        + list_ammunition()
    )


def get_weapon(weapon_id: str) -> dict[str, Any]:
    """Return a weapon catalog entry by ID."""
    data = _load_json("items/weapon.json")
    if not isinstance(data, list):
        raise ValueError("weapon catalog unavailable")
    for item in data:
        if item.get("id") == weapon_id:
            if item.get("category") != "weapon":
                raise ValueError(f"Invalid weapon entry: {weapon_id!r}")
            return item
    raise ValueError(f"Unknown weapon: {weapon_id!r}")


def get_armor(armor_id: str) -> dict[str, Any]:
    """Return an armor catalog entry by ID."""
    data = _load_json("items/armor.json")
    if not isinstance(data, list):
        raise ValueError("armor catalog unavailable")
    for item in data:
        if item.get("id") == armor_id:
            if item.get("category") != "armor":
                raise ValueError(f"Invalid armor entry: {armor_id!r}")
            return item
    raise ValueError(f"Unknown armor: {armor_id!r}")


def get_shield(shield_id: str) -> dict[str, Any]:
    """Return a shield catalog entry by ID."""
    data = _load_json("items/armor.json")
    if not isinstance(data, list):
        raise ValueError("shield catalog unavailable")
    for item in data:
        if item.get("id") == shield_id:
            if item.get("category") != "shield":
                raise ValueError(f"Invalid shield entry: {shield_id!r}")
            return item
    raise ValueError(f"Unknown shield: {shield_id!r}")


def get_ammunition(ammo_id: str) -> dict[str, Any]:
    """Return an ammunition catalog entry by ID."""
    data = _load_json("items/ammunition.json")
    if not isinstance(data, list):
        raise ValueError("ammunition catalog unavailable")
    for item in data:
        if item.get("id") == ammo_id:
            if item.get("category") != "ammunition":
                raise ValueError(f"Invalid ammunition entry: {ammo_id!r}")
            return item
    raise ValueError(f"Unknown ammunition: {ammo_id!r}")


def compute_max_hp(
    armor_entry: dict[str, Any],
    armor_tier: int,
    shield_entry: dict[str, Any] | None,
    shield_tier: int,
) -> dict[str, int]:
    """Compute pre-combat max HP from armor and shield contributions."""
    base = 100
    armor_floor = int(armor_entry["armor_floor"])
    armor_ceiling = int(armor_entry["armor_ceiling"])
    armor_contribution = int(
        armor_floor + (armor_ceiling - armor_floor) * (armor_tier / 5)
    )

    shield_contribution = 0
    if shield_entry is not None:
        shield_floor = int(shield_entry["armor_floor"])
        shield_ceiling = int(shield_entry["armor_ceiling"])
        shield_contribution = int(
            shield_floor + (shield_ceiling - shield_floor) * (shield_tier / 5)
        )

    return {
        "max_hp": base + armor_contribution + shield_contribution,
        "base": base,
        "armor_contribution": armor_contribution,
        "shield_contribution": shield_contribution,
    }


def resolve_attack(
    *,
    weapon_id: str,
    weapon_tier: int,
    ammo_id: str | None = None,
    use_off_hand: bool = False,
    defender_is_unarmored: bool,
    defender_unarmored_tier: int = 0,
    defender_agility_tier: int = 0,
    dice: Callable[[str], int] = roll,
) -> dict[str, Any]:
    """Resolve a single combat attack using Combat v1.0 rules."""
    weapon_entry = get_weapon(weapon_id)
    if "base_damage" not in weapon_entry:
        raise ValueError(f"Weapon missing base_damage: {weapon_id!r}")
    weapon_base = int(weapon_entry["base_damage"])

    ammo_modifier = 0
    if ammo_id is not None:
        ammo_entry = get_ammunition(ammo_id)
        if "damage_modifier" not in ammo_entry:
            raise ValueError(f"Ammunition missing damage_modifier: {ammo_id!r}")
        ammo_modifier = int(ammo_entry["damage_modifier"])

    if weapon_tier not in _WEAPON_TIER_TARGETS:
        raise ValueError("weapon_tier must be between 0 and 5")
    if not 0 <= defender_unarmored_tier <= 5:
        raise ValueError("defender_unarmored_tier must be between 0 and 5")
    if not 0 <= defender_agility_tier <= 5:
        raise ValueError("defender_agility_tier must be between 0 and 5")

    effective_base = weapon_base // 2 if use_off_hand else weapon_base
    base_target = _WEAPON_TIER_TARGETS[weapon_tier]
    target = base_target
    if defender_is_unarmored:
        target = max(1, base_target - (defender_unarmored_tier * 5))

    agility_reduction_multiplier = 1 - (defender_agility_tier * 0.10)
    roll_1_value = dice("1d100")
    events = ["roll_1"]

    damage = {
        "weapon_base": weapon_base,
        "effective_base": effective_base,
        "ammo_modifier": ammo_modifier,
        "margin_multiplier": 0.0,
        "agility_reduction_multiplier": agility_reduction_multiplier,
        "pre_reduction": 0,
        "final": 0,
    }

    result: dict[str, Any] = {
        "hit": False,
        "critical_hit": False,
        "fumble": False,
        "tied": False,
        "roll_1": {
            "value": roll_1_value,
            "target": target,
            "base_target": base_target,
        },
        "roll_2": None,
        "damage": damage,
        "rebound": None,
        "events": events,
    }

    if roll_1_value == 1:
        pre_reduction = (effective_base * 3) + ammo_modifier
        final = max(0, int(pre_reduction * agility_reduction_multiplier))
        damage.update(
            {
                "margin_multiplier": 3.0,
                "pre_reduction": pre_reduction,
                "final": final,
            }
        )
        events.extend(["critical_hit", "damage_computed", "agility_reduction"])
        result["hit"] = True
        result["critical_hit"] = True
        return result

    if roll_1_value == 100:
        rebound_damage = dice("1d6") + 4
        events.append("fumble")
        result["fumble"] = True
        result["rebound"] = {"attacker_damage": rebound_damage}
        return result

    if roll_1_value > target:
        events.append("miss")
        return result

    events.append("hit")
    attacker_r2 = dice("1d100")
    defender_r2 = dice("1d100")
    margin = attacker_r2 - defender_r2
    result["roll_2"] = {
        "attacker": attacker_r2,
        "defender": defender_r2,
        "margin": margin,
    }
    events.append("roll_2")

    if margin == 0:
        result["tied"] = True
        events.append("tied")
        return result

    margin_multiplier = 1 + (margin / 100)
    pre_reduction = max(0, int(effective_base * margin_multiplier)) + ammo_modifier
    final = max(0, int(pre_reduction * agility_reduction_multiplier))
    damage.update(
        {
            "margin_multiplier": margin_multiplier,
            "pre_reduction": pre_reduction,
            "final": final,
        }
    )
    events.extend(["damage_computed", "agility_reduction"])
    result["hit"] = final > 0
    return result


def combat_rules_fingerprint() -> str:
    """Stable SHA256 fingerprint of prompts/combat-rules.md."""
    hasher = hashlib.sha256()
    with open(_PROMPTS_DIR / "combat-rules.md", "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# Companion / beast catalogs
# ---------------------------------------------------------------------------

def list_creature_catalog() -> list[dict[str, Any]]:
    """Return all starter creature entries."""
    data = _load_json("beasts/creatures.json")
    if not isinstance(data, list):
        return []
    return data


def get_creature(subspecies: str) -> dict[str, Any]:
    """Return a specific creature entry by subspecies ID."""
    for entry in list_creature_catalog():
        if entry.get("subspecies") == subspecies:
            return entry
    raise ValueError(f"Unknown creature subspecies: {subspecies!r}")


def list_exceptional_catalog() -> list[dict[str, Any]]:
    """Return all starter exceptional companion entries (may be empty)."""
    data = _load_json("beasts/exceptional.json")
    if not isinstance(data, list):
        return []
    return data


def list_natural_abilities() -> list[dict[str, Any]]:
    data = _load_json("beasts/natural_abilities.json")
    return data if isinstance(data, list) else []


def list_learned_commands() -> list[dict[str, Any]]:
    data = _load_json("beasts/learned_commands.json")
    return data if isinstance(data, list) else []


def list_tactical_roles() -> list[dict[str, Any]]:
    data = _load_json("beasts/tactical_roles.json")
    return data if isinstance(data, list) else []


# ---------------------------------------------------------------------------
# NPC registry
# ---------------------------------------------------------------------------

def _discover_npc_files() -> list[Path]:
    """Return all NPC JSON files under data/npcs/, recursively, excluding _ prefixed."""
    if not _NPC_DATA_DIR.exists():
        return []
    return sorted(
        p for p in _NPC_DATA_DIR.rglob("*.json")
        if not p.name.startswith("_")
    )


@lru_cache(maxsize=None)
def _load_npc_catalogs() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Load all NPC files recursively, partitioned by file stem.

    Returns (named, roles) tuple:
      - named: entries from any file stemmed 'named.json' (tier 1-2 individuals)
      - roles: entries from any file stemmed 'roles.json' (tier 3 role templates)

    Files whose stem is neither 'named' nor 'roles' are silently skipped.
    Entries with ids starting with '_' are excluded (scaffold/template rows).
    """
    named: list[dict[str, Any]] = []
    roles: list[dict[str, Any]] = []
    for path in _discover_npc_files():
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if not isinstance(payload, list):
            continue
        entries = [
            e for e in payload
            if isinstance(e, dict) and not str(e.get("id", "")).startswith("_")
        ]
        if path.stem == "named":
            named.extend(entries)
        elif path.stem == "roles":
            roles.extend(entries)
    return named, roles


def list_npcs_named() -> list[dict[str, Any]]:
    """Return all tier 1-2 named NPC entries across all regions."""
    return list(_load_npc_catalogs()[0])


def list_npc_roles() -> list[dict[str, Any]]:
    """Return all tier 3 generative role template entries across all regions."""
    return list(_load_npc_catalogs()[1])


def list_npcs() -> list[dict[str, Any]]:
    """Return all NPC entries (named + roles) as a single flat list."""
    named, roles = _load_npc_catalogs()
    return named + roles


def get_npc(npc_id: str) -> dict[str, Any]:
    """Return a specific NPC entry by id, searching both named and role catalogs."""
    for entry in list_npcs():
        if entry.get("id") == npc_id:
            return entry
    raise ValueError(f"Unknown npc: {npc_id!r}")


def data_fingerprint() -> str:
    """
    Stable SHA256 fingerprint of core game data files used by /options and seeding.

    Exposed by GET /version for deployment/contract sanity checks.
    """
    hasher = hashlib.sha256()
    for filename in (*_DATA_FILES, *_ITEM_DATA_FILES, *_BEAST_DATA_FILES):
        path = _DATA_DIR / filename
        if not path.exists():
            continue
        with open(path, "rb") as f:
            hasher.update(f.read())

    for filename in _TAG_REGISTRY_FILES:
        path = _DATA_DIR / filename
        if not path.exists():
            continue
        with open(path, "rb") as f:
            hasher.update(f.read())

    for filename in _SPELL_DATA_FILES:
        path = _DATA_DIR / filename
        if not path.exists():
            continue
        with open(path, "rb") as f:
            hasher.update(f.read())

    for path in _discover_npc_files():
        if not path.exists():
            continue
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
            "points_available_earned": {d: 0 for d in DOMAIN_KEYS},
            "points_available_awarded": 0,
            "points_spent": 0,
            "points_earned_total": 0,
            "tag_advance_counters": {d: 0 for d in DOMAIN_KEYS},
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