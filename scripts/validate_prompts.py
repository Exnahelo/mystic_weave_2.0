#!/usr/bin/env python3
"""Validate required prompt files and lightweight structure constraints."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


REQUIRED_PROMPTS = {
    "prompts/engine.md": ["# Mystic Weave", "## Turn Loop", "## API Reference"],
    "prompts/character-creation.md": ["# Mystic Weave", "## Character Creation Flow", "## API Fields for Character Creation"],
    "prompts/character-rules.md": ["#", "##"],
    "prompts/economy-rules.md": ["# Mystic Weave — Economy Rules", "## Coin Economy Rules", "## Barter Economy Rules"],
    "prompts/arc-rules.md": ["# Mystic Weave — Arc Rules", "## Arc Types", "## Required Backend Calls"],
    "prompts/world.md": ["# Drakenvale", "## Governance", "## Reference Files"],
    "prompts/geography.md": ["# Drakenvale — Geography", "## Formation", "## Major Regions"],
    "prompts/history.md": ["#", "##"],
    "prompts/groups.md": ["# Drakenvale — Groups", "## Purpose", "## Civic and State Institutions"],
    "prompts/npcs.md": ["#", "##"],
}

ENGINE_REQUIRED_SECTIONS = [
    "### Runtime Safety Checkpoint (Await + Validate)",
    "### Time/Weather/Moon Runtime Checkpoint",
    "### Economy Runtime Checkpoint",
    "### Progression Runtime Checkpoint",
    "### Irreversible Action Confirmation Gate",
    "## Canon Precedence (Conflict Resolution Order)",
]

CALENDAR_REQUIRED_MARKERS = [
    "# Mystic Weave — The Oath Calendar",
    "## Weather",
    "## Time of Day Progression",
    "## GPT Time Rules (Non-Negotiable)",
]

KNOWN_CONTRADICTION_WARNING_MARKERS = {
    "economy_structure": [
        ("prompts/world.md", "## Economy"),
        ("prompts/economy-rules.md", "## Barter Economy Rules"),
    ],
    "group_canon_merge": [
        ("prompts/world.md", "Drakenvale is sustained by a small number of major institutions whose detailed structure belongs in `groups.md`."),
        ("prompts/groups.md", 'It replaces any prior split between "organizations" and "factions."'),
    ],
    "arcane_conservatory_presence": [
        ("prompts/world.md", "- **Arcane Conservatory** — elite advanced magical study and arcane refinement"),
        ("prompts/groups.md", "### Arcane Conservatory"),
    ],
}

KEBAB_CASE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WORLD_META_TAGS = {"canonical", "canonical-realm", "placeholder", "TODO", "draft"}
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
TAG_SECTION_RE = re.compile(r"^## Tags\n\n((?:- .+\n)+)", re.MULTILINE)

ENGINE_BYTE_CEILING = 8000
MIRROR_IGNORE_STEMS = {Path("README")}


def _check_engine_byte_ceiling(repo_root: Path) -> list[str]:
    """Assert prompts/engine.md is at or under the GPT Builder upload ceiling."""
    engine_path = repo_root / "prompts" / "engine.md"
    if not engine_path.exists():
        return [f"engine.md not found at {engine_path}"]
    size = engine_path.stat().st_size
    if size > ENGINE_BYTE_CEILING:
        return [
            f"prompts/engine.md is {size} bytes; ceiling is {ENGINE_BYTE_CEILING}. "
            "GPT Builder upload will fail."
        ]
    return []


def _check_data_vault_mirror(repo_root: Path) -> list[str]:
    """Assert data/world/**/*.json and prompts/world_vault/**/*.md are paired."""
    data_root = repo_root / "data" / "world"
    vault_root = repo_root / "prompts" / "world_vault"
    if not data_root.exists() or not vault_root.exists():
        return [
            f"mirror check skipped: data_root={data_root.exists()}, "
            f"vault_root={vault_root.exists()}"
        ]

    data_stems = {
        p.relative_to(data_root).with_suffix("")
        for p in data_root.rglob("*.json")
    } - MIRROR_IGNORE_STEMS
    vault_stems = {
        p.relative_to(vault_root).with_suffix("")
        for p in vault_root.rglob("*.md")
    } - MIRROR_IGNORE_STEMS

    only_in_data = sorted(data_stems - vault_stems)
    only_in_vault = sorted(vault_stems - data_stems)

    failures = []
    if only_in_data:
        failures.append(
            "data/world/ files without prompts/world_vault/ pair: "
            f"{[str(p) for p in only_in_data]}"
        )
    if only_in_vault:
        failures.append(
            "prompts/world_vault/ files without data/world/ pair: "
            f"{[str(p) for p in only_in_vault]}"
        )
    return failures


def _validate_vault_markdown(repo_root: Path, failures: list[str]) -> None:
    vault_root = repo_root / "prompts" / "world_vault"
    for path in sorted(vault_root.rglob("*.md")):
        if path.name.startswith("_"):
            continue
        rel_path = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8")
        frontmatter_match = FRONTMATTER_RE.search(text)
        if not frontmatter_match:
            continue

        frontmatter_text = frontmatter_match.group(1)
        try:
            frontmatter = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError as exc:
            first_line = str(exc).splitlines()[0]
            failures.append(f"{rel_path} frontmatter YAML error: {first_line}")
            continue

        if not isinstance(frontmatter, dict):
            failures.append(f"{rel_path} frontmatter must parse to mapping")
            continue

        world_id = frontmatter.get("id")
        if world_id is None:
            continue
        if not isinstance(world_id, str) or not world_id:
            failures.append(f"{rel_path} frontmatter id must be non-empty string")
            continue

        expected_stem = world_id.replace("-", "_")
        if path.stem != expected_stem:
            failures.append(f"{rel_path} stem/id mismatch stem={path.stem} id={world_id}")

        frontmatter_tags = frontmatter.get("tags", [])
        if not isinstance(frontmatter_tags, list):
            failures.append(f"{rel_path} frontmatter tags must be a list")
            frontmatter_tags = []

        body_match = TAG_SECTION_RE.search(text)
        body_tags = [line[2:].strip() for line in body_match.group(1).splitlines()] if body_match else []

        for source_name, tags in (("frontmatter", frontmatter_tags), ("## Tags", body_tags)):
            seen: set[str] = set()
            for index, tag in enumerate(tags):
                if not isinstance(tag, str):
                    failures.append(f"{rel_path} {source_name}[{index}] tag must be string")
                    continue
                if not KEBAB_CASE_RE.fullmatch(tag):
                    failures.append(f"{rel_path} {source_name}[{index}] must be kebab-case (got {tag})")
                if tag in WORLD_META_TAGS:
                    failures.append(f"{rel_path} {source_name}[{index}] forbidden meta tag {tag}")
                if tag in seen:
                    failures.append(f"{rel_path} {source_name}[{index}] duplicate tag {tag}")
                seen.add(tag)

        if set(frontmatter_tags) != set(body_tags):
            failures.append(f"{rel_path} frontmatter/body tag sets differ")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    failures: list[str] = []
    warnings: list[str] = []

    for rel_path, required_markers in REQUIRED_PROMPTS.items():
        prompt_path = repo_root / rel_path
        if not prompt_path.exists():
            failures.append(f"missing required prompt file: {rel_path}")
            continue

        content = prompt_path.read_text(encoding="utf-8")
        if not content.strip():
            failures.append(f"{rel_path} is empty")
            continue

        if len(content.strip()) < 300:
            failures.append(f"{rel_path} appears too short (<300 chars)")

        for marker in required_markers:
            if marker not in content:
                failures.append(f"{rel_path} missing required marker: {marker}")

        if rel_path == "prompts/engine.md":
            for section in ENGINE_REQUIRED_SECTIONS:
                if section not in content:
                    failures.append(f"{rel_path} missing required runtime safety section: {section}")

    calendar_path = repo_root / "prompts" / "calendar.md"
    if not calendar_path.exists():
        failures.append("missing required prompt file: prompts/calendar.md")
    else:
        calendar_content = calendar_path.read_text(encoding="utf-8")
        for marker in CALENDAR_REQUIRED_MARKERS:
            if marker not in calendar_content:
                failures.append(f"prompts/calendar.md missing required marker: {marker}")

    # Soft checks: ensure known cross-file markers remain present.
    # These emit warnings (non-fatal) so maintainers can detect drift early
    # without blocking unrelated prompt edits.
    for check_name, markers in KNOWN_CONTRADICTION_WARNING_MARKERS.items():
        for rel_path, marker in markers:
            target = repo_root / rel_path
            if not target.exists():
                warnings.append(f"[{check_name}] missing file: {rel_path}")
                continue
            content = target.read_text(encoding="utf-8")
            if marker not in content:
                warnings.append(
                    f"[{check_name}] missing marker in {rel_path}: {marker}"
                )

    _validate_vault_markdown(repo_root, failures)
    failures.extend(_check_engine_byte_ceiling(repo_root))
    failures.extend(_check_data_vault_mirror(repo_root))

    if failures:
        print("❌ Prompt validation failed")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)

    if warnings:
        print("⚠️ Prompt validation warnings")
        for warning in warnings:
            print(f"- {warning}")

    print("✅ Prompt validation passed")


if __name__ == "__main__":
    main()
    