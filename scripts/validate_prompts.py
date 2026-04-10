#!/usr/bin/env python3
"""Validate required prompt files and lightweight structure constraints."""

from __future__ import annotations

import sys
from pathlib import Path


REQUIRED_PROMPTS = {
    "prompts/engine.md": ["# Mystic Weave", "## Turn Loop", "## API Reference"],
    "prompts/character_creation.md": ["# Mystic Weave", "## Character Creation Flow", "## API Fields for Character Creation"],
    "prompts/world_rules.md": ["#", "##"],
}


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    failures: list[str] = []

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

    world_dir = repo_root / "prompts" / "world"
    world_files = sorted(world_dir.glob("*.md")) if world_dir.exists() else []
    if len(world_files) == 0:
        failures.append("prompts/world has no location markdown files")

    if failures:
        print("❌ Prompt validation failed")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)

    print("✅ Prompt validation passed")


if __name__ == "__main__":
    main()
