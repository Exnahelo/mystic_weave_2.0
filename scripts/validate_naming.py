#!/usr/bin/env python3
"""Validate repository naming conventions for tracked files."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


DOCUMENTED_EXCEPTIONS = {
    "README.md",
    "LICENSE",
    "LICENSE.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "SUPPORT.md",
    "Makefile",
}

SNAKE = re.compile(r"^[a-z_][a-z0-9_]*$")
ALEMBIC_SNAKE = re.compile(r"^[a-z0-9_]+$")
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ENV_KEY = re.compile(r"^[A-Z][A-Z0-9_]*=")
SAFE_ENV_SUFFIXES = (".example", ".template", ".sample", ".dist")
DATA_SCHEMA_DIRS = {"schemas"}


def _tracked_files(repo_root: Path) -> list[Path]:
    output = subprocess.check_output(["git", "ls-files"], cwd=repo_root, text=True)
    return [repo_root / rel for rel in output.splitlines() if rel]


def _parse_documented_exceptions(conventions_path: Path) -> set[str]:
    text = conventions_path.read_text(encoding="utf-8")
    parsed: set[str] = set()

    repo_match = re.search(
        r"## Repository root files\n\n### Use exact conventional names for tooling-sensitive files\n\n(.*?)\n\nDo not rename these",
        text,
        re.DOTALL,
    )
    if repo_match:
        for item in re.findall(r"- `([^`]+)`", repo_match.group(1)):
            if item == "LICENSE":
                parsed.update({"LICENSE", "LICENSE.md"})
            else:
                parsed.add(item)

    docs_match = re.search(
        r"## Documentation\n\n### Tooling-sensitive docs\n\nUse exact conventional names:\n\n(.*?)\n\n### General docs",
        text,
        re.DOTALL,
    )
    if docs_match:
        for item in re.findall(r"- `([^`]+)`", docs_match.group(1)):
            if item == "LICENSE":
                parsed.update({"LICENSE", "LICENSE.md"})
            else:
                parsed.add(item)

    return parsed


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    tracked = _tracked_files(repo_root)
    violations: list[str] = []

    parsed_exceptions = _parse_documented_exceptions(repo_root / "docs" / "conventions.md")
    if parsed_exceptions != DOCUMENTED_EXCEPTIONS:
        print("❌ Naming validation failed")
        print(
            "- documented exceptions drift: "
            f"validator={sorted(DOCUMENTED_EXCEPTIONS)} docs={sorted(parsed_exceptions)}"
        )
        sys.exit(1)

    for path in tracked:
        rel = path.relative_to(repo_root)
        rel_str = rel.as_posix()
        name = path.name
        stem = path.stem

        if not path.exists():
            continue

        if " " in rel_str:
            violations.append(f"NAMING VIOLATION  {rel_str}  expected=no-spaces  got={name}")

        if name.startswith(".") and not name.startswith(".env"):
            continue

        if rel.parent == Path(".") and (name == ".env" or name.startswith(".env.")):
            is_safe_template = any(name.endswith(suffix) for suffix in SAFE_ENV_SUFFIXES)
            if name == ".env" or not is_safe_template:
                violations.append(
                    f"NAMING VIOLATION  {rel_str}  env file tracked in git — must be gitignored"
                )
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if "=" not in stripped:
                    violations.append(f"NAMING VIOLATION  {rel_str}  malformed line: {stripped}")
                    continue
                key = stripped.split("=", 1)[0]
                if not re.match(r"^[A-Z][A-Z0-9_]*$", key):
                    violations.append(
                        f"NAMING VIOLATION  {rel_str}  env key not UPPER_SNAKE_CASE: {key}"
                    )
            continue

        if path.suffix == ".py":
            pattern = ALEMBIC_SNAKE if rel.parts[:2] == ("alembic", "versions") else SNAKE
            if not pattern.fullmatch(stem):
                violations.append(f"NAMING VIOLATION  {rel_str}  expected=snake_case  got={stem}")
            continue

        if path.suffix == ".sh":
            if not SNAKE.fullmatch(stem):
                violations.append(f"NAMING VIOLATION  {rel_str}  expected=snake_case  got={stem}")
            continue

        if (
            rel.parts
            and rel.parts[0] == "data"
            and path.suffix in (".json", ".yaml")
        ):
            if path.name.startswith("_"):
                continue
            if any(part in DATA_SCHEMA_DIRS for part in rel.parts):
                continue
            if not SNAKE.match(path.stem):
                violations.append(
                    f"NAMING VIOLATION  {rel_str}  data file stem not snake_case: {path.stem}"
                )
            continue

        if path.suffix in {".yaml", ".yml"}:
            if not SNAKE.fullmatch(stem):
                violations.append(f"NAMING VIOLATION  {rel_str}  expected=snake_case  got={stem}")
            continue

        if path.suffix == ".md":
            if len(rel.parts) >= 2 and rel.parts[0] == "prompts" and rel.parts[1] == "world_vault":
                if name == "README.md":
                    continue
                if not SNAKE.fullmatch(stem):
                    violations.append(f"NAMING VIOLATION  {rel_str}  expected=snake_case  got={stem}")
                continue

            if rel.parts and rel.parts[0] == "prompts":
                if not KEBAB.fullmatch(stem):
                    violations.append(f"NAMING VIOLATION  {rel_str}  expected=kebab-case  got={stem}")
                continue

            if name in DOCUMENTED_EXCEPTIONS:
                continue

            if not KEBAB.fullmatch(stem):
                violations.append(f"NAMING VIOLATION  {rel_str}  expected=kebab-case  got={stem}")

    if violations:
        print("❌ Naming validation failed")
        for violation in violations:
            print(violation)
        sys.exit(1)

    print("Clean.")


if __name__ == "__main__":
    main()