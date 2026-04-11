#!/usr/bin/env python3
"""Validate required prompt files and lightweight structure constraints."""

from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_PROMPTS = {
    "prompts/engine.md": ["# Mystic Weave", "## Turn Loop", "## API Reference"],
    "prompts/character_creation.md": ["# Mystic Weave", "## Character Creation Flow", "## API Fields for Character Creation"],
    "prompts/world_rules.md": ["#", "##"],
    "prompts/economy_currency_reference.md": ["# Mystic Weave — Economy & Currency Reference", "## Currency — The Drake System", "## Economy Rules for the GPT (Non-Negotiable)"],
}

ENGINE_REQUIRED_SECTIONS = [
    "### Runtime Safety Checkpoint (Await + Validate)",
    "### Time/Weather/Moon Runtime Checkpoint",
    "### Economy Runtime Checkpoint",
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
    "economy_consistency": [
        ("prompts/drakenvale_world.md", "barter in enchanted artifacts, knowledge, and services. Coin use exists but is secondary"),
        ("prompts/drakenvale_factions.md", "Barter in enchanted artifacts, knowledge, and services is primary"),
    ],
    "arcane_conservatory_access_consistency": [
        ("prompts/drakenvale_factions.md", "Open to all residents for standard materials"),
        ("prompts/drakenvale_organizations.md", "Open to all residents. Restricted sections require Council approval"),
    ],
    "crisis_protocol_maturity_baseline": [
        ("prompts/drakenvale_factions.md", "## Crisis Protocols (Baseline)"),
        ("prompts/drakenvale_factions.md", "baseline operating norms, not a fully codified wartime charter"),
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

    world_dir = repo_root / "prompts" / "world"
    world_files = sorted(world_dir.glob("*.md")) if world_dir.exists() else []
    if len(world_files) == 0:
        failures.append("prompts/world has no location markdown files")

    # Soft checks: ensure known contradiction-pair markers remain present.
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
