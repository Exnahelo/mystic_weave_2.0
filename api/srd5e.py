"""
srd5e.py — Load unified SRD JSON snapshots and expose helper functions.

Data lives in /data/srd/ (merged 2014+2024, 2024 takes priority).
The SRD source files are never called at runtime — only during the
initial merge script (scripts/merge_srd.py).

All JSON files are arrays of objects with an 'index' field.
The loader converts arrays → dicts keyed by index for O(1) lookup.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

# Resolve path relative to this file so it works regardless of cwd
_SRD_DIR = Path(__file__).parent.parent / "data" / "srd"

# Ability score index → uppercase abbreviation mapping
_ABILITY_MAP = {
    "str": "STR",
    "dex": "DEX",
    "con": "CON",
    "int": "INT",
    "wis": "WIS",
    "cha": "CHA",
    "strength": "STR",
    "dexterity": "DEX",
    "constitution": "CON",
    "intelligence": "INT",
    "wisdom": "WIS",
    "charisma": "CHA",
}


@lru_cache(maxsize=None)
def _load_indexed(filename: str) -> dict[str, Any]:
    """Load a JSON array file and return a dict keyed by 'index'."""
    path = _SRD_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {item["index"]: item for item in data}
    # Already a dict (shouldn't happen with merged files, but handle gracefully)
    return data


# ---------------------------------------------------------------------------
# Classes (2014 format — array of class objects)
# ---------------------------------------------------------------------------

def get_class(index: str) -> dict[str, Any]:
    """Return full SRD class data for the given index (e.g. 'ranger')."""
    data = _load_indexed("classes.json")
    if index not in data:
        raise ValueError(f"Unknown class: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


def list_classes() -> list[dict[str, str]]:
    """Return all supported classes as a list of {index, name, hit_die} dicts."""
    data = _load_indexed("classes.json")
    return [
        {"index": k, "name": v["name"], "hit_die": f"d{v['hit_die']}"}
        for k, v in data.items()
    ]


# ---------------------------------------------------------------------------
# Species (2024 — replaces Races)
# ---------------------------------------------------------------------------

def get_species(index: str) -> dict[str, Any]:
    """Return full SRD species data for the given index (e.g. 'human')."""
    data = _load_indexed("species.json")
    if index not in data:
        raise ValueError(f"Unknown species: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


def list_species() -> list[dict[str, Any]]:
    """Return all supported species as a list of summary dicts."""
    data = _load_indexed("species.json")
    return [
        {
            "index": k,
            "name": v["name"],
            "speed": str(v.get("speed", 30)),
            "size": v.get("size", "Medium"),
            "subspecies": [
                {"index": s["index"], "name": s["name"]}
                for s in v.get("subspecies", [])
            ],
        }
        for k, v in data.items()
    ]


# ---------------------------------------------------------------------------
# Subspecies (2024 — replaces Subraces)
# ---------------------------------------------------------------------------

def get_subspecies(index: str) -> dict[str, Any]:
    """Return full SRD subspecies data for the given index."""
    data = _load_indexed("subspecies.json")
    if index not in data:
        raise ValueError(f"Unknown subspecies: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


def list_subspecies(species_index: str | None = None) -> list[dict[str, Any]]:
    """
    Return all subspecies, optionally filtered by species index.
    Each entry: {index, name, species_index}.
    """
    data = _load_indexed("subspecies.json")
    result = []
    for k, v in data.items():
        sp_idx = v.get("species", {}).get("index", "")
        if species_index is None or sp_idx == species_index:
            result.append({
                "index": k,
                "name": v["name"],
                "species_index": sp_idx,
            })
    return result


# ---------------------------------------------------------------------------
# Subclasses (2014 + 2024 merged)
# ---------------------------------------------------------------------------

def get_subclass(index: str) -> dict[str, Any]:
    """Return full SRD subclass data for the given index (e.g. 'hunter')."""
    data = _load_indexed("subclasses.json")
    if index not in data:
        raise ValueError(f"Unknown subclass: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


def list_subclasses(class_index: str | None = None) -> list[dict[str, Any]]:
    """
    Return all subclasses, optionally filtered by class index.
    Each entry: {index, name, class_index, description}.
    Prefers 2024 entries (url contains '2024') when both exist for a class.
    """
    data = _load_indexed("subclasses.json")
    result = []
    for k, v in data.items():
        cls_idx = v.get("class", {}).get("index", "")
        if class_index is not None and cls_idx != class_index:
            continue
        # Build description: 2024 entries have 'summary', 2014 have 'desc' list
        description = v.get("summary") or v.get("subclass_flavor") or ""
        if not description and v.get("desc"):
            desc_list = v["desc"]
            description = desc_list[0] if isinstance(desc_list, list) else str(desc_list)
        result.append({
            "index": k,
            "name": v["name"],
            "class_index": cls_idx,
            "description": description,
        })
    return result


def list_subclasses_for_class(class_index: str) -> list[dict[str, Any]]:
    """Return all subclasses for a given class index."""
    return list_subclasses(class_index=class_index)


# ---------------------------------------------------------------------------
# Backgrounds (2024)
# ---------------------------------------------------------------------------

def get_background(index: str) -> dict[str, Any]:
    """Return full SRD background data for the given index (e.g. 'soldier')."""
    data = _load_indexed("backgrounds.json")
    if index not in data:
        raise ValueError(f"Unknown background: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


def list_backgrounds() -> list[dict[str, Any]]:
    """Return all supported backgrounds as a list of summary dicts."""
    data = _load_indexed("backgrounds.json")
    result = []
    for k, v in data.items():
        ability_scores = [
            _ABILITY_MAP.get(a["index"].lower(), a["index"].upper())
            for a in v.get("ability_scores", [])
        ]
        skill_profs = [
            p["index"].replace("skill-", "")
            for p in v.get("proficiencies", [])
            if p["index"].startswith("skill-")
        ]
        tool_profs = [
            p["index"].replace("tool-", "")
            for p in v.get("proficiencies", [])
            if p["index"].startswith("tool-")
        ]
        # Extract tool proficiency choices from proficiency_choices (e.g. "Choose one Gaming Set")
        tool_prof_choices: list[str] = []
        for pc in v.get("proficiency_choices", []):
            if pc.get("type") == "proficiencies":
                desc = pc.get("desc", "")
                if desc:
                    tool_prof_choices.append(desc)
        feat = v.get("feat", {}).get("index", "")
        # Build human-readable ability score bonus description
        scores_str = ", ".join(ability_scores)
        ability_score_bonuses = f"(+2 and +1) or (+1/+1/+1) across {scores_str}"
        result.append({
            "index": k,
            "name": v["name"],
            "description": v.get("description", ""),
            "lifestyle": v.get("lifestyle", "modest"),
            "ability_scores": ability_scores,
            "ability_score_bonuses": ability_score_bonuses,
            "feat": feat,
            "skill_proficiencies": skill_profs,
            "tool_proficiencies": tool_profs,
            "tool_proficiency_choices": tool_prof_choices,
        })
    return result


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

def get_skills() -> list[str]:
    """Return the list of all valid skill index strings."""
    data = _load_indexed("skills.json")
    return sorted(data.keys())


def get_skill(index: str) -> dict[str, Any]:
    """Return full SRD skill data for the given index."""
    data = _load_indexed("skills.json")
    if index not in data:
        raise ValueError(f"Unknown skill: {index!r}")
    return data[index]


# ---------------------------------------------------------------------------
# Languages
# ---------------------------------------------------------------------------

def list_languages() -> list[dict[str, Any]]:
    """Return all supported languages as a list of summary dicts."""
    data = _load_indexed("languages.json")
    return [
        {
            "index": k,
            "name": v["name"],
            "is_rare": v.get("is_rare", False),
            "note": v.get("note", ""),
        }
        for k, v in data.items()
    ]


def get_language(index: str) -> dict[str, Any]:
    """Return full SRD language data for the given index (e.g. 'elvish')."""
    data = _load_indexed("languages.json")
    if index not in data:
        raise ValueError(f"Unknown language: {index!r}. Valid: {sorted(data.keys())}")
    return data[index]


# ---------------------------------------------------------------------------
# Conditions, Ability Scores
# ---------------------------------------------------------------------------

def get_conditions() -> dict[str, Any]:
    """Return all conditions keyed by index."""
    return _load_indexed("conditions.json")


def get_ability_scores() -> dict[str, Any]:
    """Return all ability score descriptions keyed by index."""
    return _load_indexed("ability-scores.json")


# ---------------------------------------------------------------------------
# Character seeding helpers
# ---------------------------------------------------------------------------

def ability_modifier(score: int) -> int:
    """Standard 5e ability modifier: floor((score - 10) / 2)."""
    return math.floor((score - 10) / 2)


def proficiency_bonus(level: int = 1) -> int:
    """Standard 5e proficiency bonus by level (level 1–4 = +2)."""
    return math.ceil(level / 4) + 1


def starting_hp(hit_die_str: str, con_score: int) -> int:
    """
    Level 1 HP = hit die max + CON modifier.
    hit_die_str is e.g. 'd10' or '10'.
    """
    die_size = int(str(hit_die_str).lstrip("d"))
    return die_size + ability_modifier(con_score)


def _apply_background_bonuses(
    background_index: str,
    ability_scores: dict[str, int],
    primary_score: str | None = None,
    secondary_score: str | None = None,
) -> tuple[dict[str, int], str | None, list[str], list[str], str]:
    """
    Apply 2024-rule background ability score bonuses and extract background data.

    Bonus rules (2024 PHB):
    - (+2 and +1): primary_score gets +2, secondary_score gets +1, third gets +0.
      Both primary_score and secondary_score must be provided and must be different
      scores from the background's three ability scores.
    - (+1/+1/+1): if primary_score is None, all three background scores get +1 each.

    Returns (final_scores, background_feat, background_skill_profs, background_tool_profs, lifestyle).
    """
    final_scores = dict(ability_scores)
    background_feat: str | None = None
    background_skill_profs: list[str] = []
    background_tool_profs: list[str] = []
    lifestyle: str = "modest"
    try:
        bg = get_background(background_index)
        bg_ability_scores = [
            _ABILITY_MAP.get(a["index"].lower(), a["index"].upper())
            for a in bg.get("ability_scores", [])
        ]
        lifestyle = bg.get("lifestyle", "modest")

        if primary_score is not None:
            # Player chose (+2 and +1): primary gets +2, secondary gets +1, third gets +0
            primary_upper = primary_score.upper()
            if primary_upper not in bg_ability_scores:
                raise ValueError(
                    f"primary_score '{primary_score}' is not one of the background's ability scores: {bg_ability_scores}."
                )
            if secondary_score is None:
                raise ValueError(
                    f"secondary_score is required when primary_score is provided. "
                    f"Choose one of the remaining background scores: "
                    f"{[s for s in bg_ability_scores if s != primary_upper]}."
                )
            secondary_upper = secondary_score.upper()
            if secondary_upper not in bg_ability_scores:
                raise ValueError(
                    f"secondary_score '{secondary_score}' is not one of the background's ability scores: {bg_ability_scores}."
                )
            if secondary_upper == primary_upper:
                raise ValueError(
                    f"secondary_score must be different from primary_score (both are '{primary_upper}')."
                )
            if primary_upper in final_scores:
                final_scores[primary_upper] = final_scores[primary_upper] + 2
            if secondary_upper in final_scores:
                final_scores[secondary_upper] = final_scores[secondary_upper] + 1
            # Third score gets +0 (no change)
        else:
            # Default: +1 to all three
            for ab in bg_ability_scores[:3]:
                if ab in final_scores:
                    final_scores[ab] = final_scores[ab] + 1

        background_feat = bg.get("feat", {}).get("index")
        background_skill_profs = [
            p["index"].replace("skill-", "")
            for p in bg.get("proficiencies", [])
            if p["index"].startswith("skill-")
        ]
        background_tool_profs = [
            p["index"].replace("tool-", "")
            for p in bg.get("proficiencies", [])
            if p["index"].startswith("tool-")
        ]
    except ValueError as e:
        if "Unknown background" in str(e) or "primary_score" in str(e):
            raise
        raise ValueError(f"Unknown background index: '{background_index}'. Call GET /options for valid backgrounds.")
    return final_scores, background_feat, background_skill_profs, background_tool_profs, lifestyle


def _build_skill_list(
    background_skill_profs: list[str],
    skill_choices: list[str] | None,
) -> tuple[list[str], list[str]]:
    """
    Merge background skill proficiencies with player skill choices.

    Returns (merged_skill_list, conflicts).
    conflicts is a list of skill indices that were in skill_choices but were
    already granted by the background — the GPT should prompt the player to
    choose a replacement for each conflict.
    """
    all_skills = get_skills()
    chosen: list[str] = list(background_skill_profs)
    conflicts: list[str] = []
    for s in (skill_choices or []):
        if s in all_skills:
            if s in chosen:
                conflicts.append(s)
            else:
                chosen.append(s)
    return chosen, conflicts


# ---------------------------------------------------------------------------
# Ability score method validation
# ---------------------------------------------------------------------------

# Point buy cost table: score → point cost
_POINT_BUY_COSTS: dict[int, int] = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
_STANDARD_ARRAY: list[int] = sorted([15, 14, 13, 12, 10, 8])


def validate_ability_scores(
    scores: dict[str, int],
    method: str = "manual",
) -> None:
    """
    Validate ability scores against the chosen method.

    method:
    - "manual"         — no validation beyond the 1–30 range check in AbilityScores model
    - "point-buy"      — 27 points, scores 8–15, costs per PHB table
    - "standard-array" — must be exactly [15, 14, 13, 12, 10, 8] in any order

    Raises ValueError if validation fails.
    """
    if method == "manual":
        return  # AbilityScores model already validates 1–30 range

    if method == "point-buy":
        total_cost = 0
        for ability, score in scores.items():
            if score < 8 or score > 15:
                raise ValueError(
                    f"Point buy scores must be between 8 and 15 before background bonuses. "
                    f"Got {ability}={score}."
                )
            if score not in _POINT_BUY_COSTS:
                raise ValueError(f"Invalid score {score} for {ability} in point buy.")
            total_cost += _POINT_BUY_COSTS[score]
        if total_cost != 27:
            raise ValueError(
                f"Point buy total must be exactly 27 points. Got {total_cost} points."
            )
        return

    if method == "standard-array":
        values = sorted(scores.values())
        if values != _STANDARD_ARRAY:
            raise ValueError(
                f"Standard array must use exactly [15, 14, 13, 12, 10, 8] assigned to any abilities. "
                f"Got {sorted(scores.values())}."
            )
        return

    raise ValueError(f"Unknown ability_score_method: {method!r}. Use 'manual', 'point-buy', or 'standard-array'.")


def _resolve_starting_equipment(
    cls: dict[str, Any],
    background_index: str | None,
    equipment_choice: str,
) -> tuple[list[str], int]:
    """
    Resolve starting equipment and gold from class + background SRD data.

    equipment_choice:
    - "equipment" — take the itemized starting equipment package (option A)
    - "gold"      — take starting gold instead (option B)

    Returns (equipment_list, gold_gp).

    The equipment list contains item indices from the class's `starting_equipment`
    plus the first concrete items from the background's equipment option A.
    Open-ended choices (e.g. "any martial weapon") are represented as descriptive
    strings so the GPT can present them to the player.
    """
    equipment_list: list[str] = []
    gold_gp: int = 0

    if equipment_choice == "gold":
        # Try background option B (gold) first, then class gold
        if background_index:
            try:
                bg = get_background(background_index)
                bg_opts = bg.get("equipment_options", [])
                if bg_opts:
                    options = bg_opts[0].get("from", {}).get("options", [])
                    # Option B is typically the last option and is a money entry
                    for opt in reversed(options):
                        if opt.get("option_type") == "money":
                            gold_gp += opt.get("count", 0)
                            break
            except ValueError:
                pass
        return equipment_list, gold_gp

    # equipment_choice == "equipment": take class fixed items + background option A items
    # Class fixed starting equipment
    for entry in cls.get("starting_equipment", []):
        eq = entry.get("equipment", {})
        idx = eq.get("index")
        qty = entry.get("quantity", 1)
        if idx:
            if qty > 1:
                equipment_list.append(f"{idx} (x{qty})")
            else:
                equipment_list.append(idx)

    # Background equipment option A (first option in the options array)
    if background_index:
        try:
            bg = get_background(background_index)
            bg_opts = bg.get("equipment_options", [])
            if bg_opts:
                options = bg_opts[0].get("from", {}).get("options", [])
                # Option A is the first entry (option_type: "multiple")
                option_a = next(
                    (o for o in options if o.get("option_type") == "multiple"), None
                )
                if option_a:
                    for item in option_a.get("items", []):
                        otype = item.get("option_type")
                        if otype == "counted_reference":
                            idx = item.get("of", {}).get("index")
                            count = item.get("count", 1)
                            if idx:
                                if count > 1:
                                    equipment_list.append(f"{idx} (x{count})")
                                else:
                                    equipment_list.append(idx)
                        elif otype == "money":
                            gold_gp += item.get("count", 0)
                        elif otype == "choice":
                            # Open-ended choice — record the description for the GPT
                            choice_desc = item.get("choice", {}).get("desc", "player-choice")
                            equipment_list.append(f"[choice: {choice_desc}]")
        except ValueError:
            pass

    return equipment_list, gold_gp


def seed_character_from_srd(
    name: str,
    class_index: str,
    species_index: str,
    ability_scores: dict[str, int],
    background_index: str | None = None,
    subspecies_index: str | None = None,
    subclass_index: str | None = None,
    skill_choices: list[str] | None = None,
    primary_score: str | None = None,
    secondary_score: str | None = None,
    language_choices: list[str] | None = None,
    species_choices: dict[str, Any] | None = None,
    equipment_choice: str = "equipment",
    alignment: str | None = None,
    faith: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """
    Build a full character dict from SRD data + player inputs.

    In 2024 rules, backgrounds (not species) determine ability score bonuses.
    The player assigns their base scores, then the background adds bonuses:
    - (+2 and +1): primary_score gets +2, secondary_score gets +1, third gets +0
    - (+1/+1/+1): all three get +1 if primary_score is None

    Returns (character_dict, skill_conflicts).
    character_dict matches the CharacterModel shape (using 'class' key, not 'class_').
    skill_conflicts is a list of skill indices that duplicated background grants.
    """
    cls = get_class(class_index)
    sp = get_species(species_index)

    hit_die_str = f"d{cls['hit_die']}"
    proficiencies: list[str] = [p["index"] for p in cls.get("proficiencies", [])]

    # Validate subclass if provided
    if subclass_index:
        sub = get_subclass(subclass_index)  # raises ValueError if invalid
        sub_class_idx = sub.get("class", {}).get("index", "")
        if sub_class_idx != class_index:
            raise ValueError(
                f"Subclass {subclass_index!r} belongs to {sub_class_idx!r}, not {class_index!r}."
            )

    # Background ability score bonuses (2024 rule)
    final_scores = dict(ability_scores)
    background_feat: str | None = None
    background_skill_profs: list[str] = []
    background_tool_profs: list[str] = []
    bg_lifestyle: str = "modest"

    if background_index:
        final_scores, background_feat, background_skill_profs, background_tool_profs, bg_lifestyle = (
            _apply_background_bonuses(background_index, final_scores, primary_score, secondary_score)
        )

    con_score = final_scores.get("CON", 10)
    max_hp = starting_hp(hit_die_str, con_score)
    chosen_skills, skill_conflicts = _build_skill_list(background_skill_profs, skill_choices)

    # Determine size (some species have size_options)
    sc = species_choices or {}
    size = sc.get("size", sp.get("size", "Medium") or "Medium")

    # Build language list from species automatic languages + validated player choices
    all_lang_indexes = {lang["index"] for lang in list_languages()}
    automatic_languages: list[str] = sp.get("automatic_languages", ["common"])
    choice_count: int = sp.get("language_choice_count", 0)

    # Validate player language choices
    chosen_extra: list[str] = []
    for lang in (language_choices or []):
        if lang not in all_lang_indexes:
            raise ValueError(
                f"Unknown language: {lang!r}. Call GET /options for valid languages."
            )
        if lang in automatic_languages:
            raise ValueError(
                f"Language {lang!r} is already granted automatically by your species. "
                f"Choose a different language."
            )
        if lang not in chosen_extra:
            chosen_extra.append(lang)

    if len(chosen_extra) != choice_count:
        raise ValueError(
            f"Species {species_index!r} requires exactly {choice_count} language choice(s). "
            f"Got {len(chosen_extra)}: {chosen_extra}."
        )

    languages: list[str] = list(automatic_languages) + chosen_extra

    # Resolve starting equipment from class + background SRD data
    equipment_list, starting_gold = _resolve_starting_equipment(
        cls, background_index, equipment_choice
    )

    result: dict[str, Any] = {
        "name": name,
        "class": class_index,
        "species": species_index,
        "level": 1,
        "hp": {"current": max_hp, "max": max_hp},
        "hit_die": hit_die_str,
        "ability_scores": final_scores,
        "proficiencies": proficiencies,
        "tool_proficiencies": background_tool_profs,
        "skills": chosen_skills,
        "languages": languages,
        "size": size,
        "lifestyle": bg_lifestyle if background_index else None,
        "equipment": equipment_list,
        "gold": starting_gold,
        "feat_choices": {},
        "biography": {},
    }

    if subspecies_index:
        result["subspecies"] = subspecies_index
    if subclass_index:
        result["subclass"] = subclass_index
    if background_index:
        result["background"] = background_index
    if background_feat:
        result["feat"] = background_feat
    if alignment:
        result["alignment"] = alignment
    if faith:
        result["faith"] = faith

    return result, skill_conflicts
