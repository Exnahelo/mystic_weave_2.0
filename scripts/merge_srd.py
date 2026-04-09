#!/usr/bin/env python3
"""
merge_srd.py — Merge 2014 and 2024 SRD JSON files into a unified data/srd/ directory.

Rules:
- 2024 takes priority when the same index exists in both editions
- 2014-only entries are added (e.g., Grappler feat, extra equipment)
- Races → Species (2024 wins), Subraces → Subspecies (2024 wins)
- Classes come from 2014 only (no 2024 equivalent)
- Features, Levels, Monsters, Spells come from 2014 only
- Rules/Rule-Sections are dropped (not used)
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC_2014 = ROOT / "src" / "2014"
SRC_2024 = ROOT / "src" / "2024"
OUT_DIR = ROOT / "data" / "srd"


def load_json(path: Path) -> list | dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: list | dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  ✓ {path.relative_to(ROOT)}")


def merge_arrays(arr_2014: list, arr_2024: list) -> list:
    """
    Merge two arrays of objects keyed by 'index'.
    2024 takes priority on conflicts. 2014-only entries are appended.
    """
    merged: dict[str, dict] = {}
    # Load 2014 first (lower priority)
    for item in arr_2014:
        idx = item.get("index", "")
        merged[idx] = item
    # Overlay 2024 (higher priority)
    for item in arr_2024:
        idx = item.get("index", "")
        merged[idx] = item
    return list(merged.values())


def copy_only(src: Path, out_name: str) -> None:
    """Copy a single file as-is to the output directory."""
    data = load_json(src)
    save_json(data, OUT_DIR / out_name)


def merge_and_save(file_2014: str, file_2024: str, out_name: str) -> None:
    """Merge two edition files and save to output."""
    path_2014 = SRC_2014 / file_2014
    path_2024 = SRC_2024 / file_2024

    arr_2014 = load_json(path_2014) if path_2014.exists() else []
    arr_2024 = load_json(path_2024) if path_2024.exists() else []

    # Ensure both are lists
    if isinstance(arr_2014, dict):
        arr_2014 = list(arr_2014.values())
    if isinstance(arr_2024, dict):
        arr_2024 = list(arr_2024.values())

    merged = merge_arrays(arr_2014, arr_2024)
    save_json(merged, OUT_DIR / out_name)
    print(f"    (2014: {len(arr_2014)} items, 2024: {len(arr_2024)} items → merged: {len(merged)} items)")


def main() -> None:
    print(f"\n{'='*60}")
    print("Merging SRD data into data/srd/")
    print(f"{'='*60}\n")

    # Clean output directory
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    # -----------------------------------------------------------------------
    # 2024-only files (no 2014 equivalent, or 2024 fully supersedes 2014)
    # -----------------------------------------------------------------------
    print("→ 2024-only files:")
    copy_only(SRC_2024 / "5e-SRD-Species.json", "species.json")
    copy_only(SRC_2024 / "5e-SRD-Subspecies.json", "subspecies.json")
    copy_only(SRC_2024 / "5e-SRD-Ability-Scores.json", "ability-scores.json")
    copy_only(SRC_2024 / "5e-SRD-Alignments.json", "alignments.json")
    copy_only(SRC_2024 / "5e-SRD-Conditions.json", "conditions.json")
    copy_only(SRC_2024 / "5e-SRD-Damage-Types.json", "damage-types.json")
    copy_only(SRC_2024 / "5e-SRD-Equipment-Categories.json", "equipment-categories.json")
    copy_only(SRC_2024 / "5e-SRD-Languages.json", "languages.json")
    copy_only(SRC_2024 / "5e-SRD-Magic-Schools.json", "magic-schools.json")
    copy_only(SRC_2024 / "5e-SRD-Skills.json", "skills.json")
    copy_only(SRC_2024 / "5e-SRD-Traits.json", "traits.json")
    copy_only(SRC_2024 / "5e-SRD-Weapon-Properties.json", "weapon-properties.json")
    copy_only(SRC_2024 / "5e-SRD-Weapon-Mastery-Properties.json", "weapon-mastery-properties.json")

    # -----------------------------------------------------------------------
    # 2014-only files (no 2024 equivalent)
    # -----------------------------------------------------------------------
    print("\n→ 2014-only files:")
    copy_only(SRC_2014 / "5e-SRD-Classes.json", "classes.json")
    copy_only(SRC_2014 / "5e-SRD-Features.json", "features.json")
    copy_only(SRC_2014 / "5e-SRD-Levels.json", "levels.json")
    copy_only(SRC_2014 / "5e-SRD-Monsters.json", "monsters.json")
    copy_only(SRC_2014 / "5e-SRD-Spells.json", "spells.json")

    # -----------------------------------------------------------------------
    # Merged files (both editions, 2024 takes priority on conflicts)
    # -----------------------------------------------------------------------
    print("\n→ Merged files (2024 priority):")
    merge_and_save(
        "5e-SRD-Backgrounds.json", "5e-SRD-Backgrounds.json", "backgrounds.json"
    )
    merge_and_save(
        "5e-SRD-Subclasses.json", "5e-SRD-Subclasses.json", "subclasses.json"
    )
    merge_and_save(
        "5e-SRD-Feats.json", "5e-SRD-Feats.json", "feats.json"
    )
    merge_and_save(
        "5e-SRD-Equipment.json", "5e-SRD-Equipment.json", "equipment.json"
    )
    merge_and_save(
        "5e-SRD-Magic-Items.json", "5e-SRD-Magic-Items.json", "magic-items.json"
    )
    merge_and_save(
        "5e-SRD-Proficiencies.json", "5e-SRD-Proficiencies.json", "proficiencies.json"
    )

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    files = sorted(OUT_DIR.glob("*.json"))
    print(f"\n{'='*60}")
    print(f"Done! {len(files)} files written to data/srd/:")
    for f in files:
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name:<45} {size_kb:>7.1f} KB")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
