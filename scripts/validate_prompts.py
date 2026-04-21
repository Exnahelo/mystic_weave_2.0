#!/usr/bin/env python3
"""Validate required prompt files and lightweight structure constraints."""

from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_PROMPTS = {
    "prompts/engine.md": ["# Mystic Weave", "## Turn Loop", "## API Reference"],
    "prompts/character_creation.md": ["# Mystic Weave", "## Character Creation Flow", "## API Fields for Character Creation"],
    "prompts/world-rules.md": ["#", "##"],
    "prompts/economy-rules.md": ["# Mystic Weave — Economy Rules", "## Coin Economy Rules", "## Barter Economy Rules"],
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
    "# Mystic Weave — The Ptarian Calendar",
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
    