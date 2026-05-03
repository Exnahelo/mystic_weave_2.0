"""Asserts prompts/calendar.md and api/time_advance.py agree on calendar canon."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from api.time_advance import MONTHS, SEASON_BY_MONTH, FESTIVALS

REPO_ROOT = Path(__file__).resolve().parents[2]
CALENDAR_MD = REPO_ROOT / "prompts" / "calendar.md"


def _parse_months_table() -> list[tuple[str, str]]:
    """Parse the ## Months table. Returns [(month_name, season_label), ...]."""
    text = CALENDAR_MD.read_text(encoding="utf-8")
    match = re.search(r"## Months\s*\n(.*?)\n##", text, re.DOTALL)
    if not match:
        pytest.fail("Could not locate ## Months section in calendar.md")
    rows = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0] in ("#", "---") or cells[0].startswith("---"):
            continue
        name = cells[1].strip("* ").strip()
        season = cells[2].strip().lower()
        rows.append((name, season))
    return rows


def _parse_festivals_table() -> list[tuple[str, str, int]]:
    """Parse the ## Festival Days table. Returns [(festival_name, month, day), ...]."""
    text = CALENDAR_MD.read_text(encoding="utf-8")
    match = re.search(
        r"## Festival Days\s*\n.*?\n(\| Name.*?)\n\n",
        text,
        re.DOTALL,
    )
    if not match:
        pytest.fail("Could not locate ## Festival Days table in calendar.md")
    rows = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or cells[0].startswith("Name") or cells[0].startswith("---"):
            continue
        name = cells[0].strip("* ").strip()
        calendar_day = cells[1].strip()
        day_match = re.match(r"^(\w+)\s+(\d+)$", calendar_day)
        if not day_match:
            continue
        rows.append((name, day_match.group(1), int(day_match.group(2))))
    return rows


def test_months_match_code_canon():
    """Month names in calendar.md match MONTHS in time_advance.py, in order."""
    md_rows = _parse_months_table()
    md_names = [name for name, _season in md_rows]
    assert md_names == list(MONTHS), (
        f"Month names disagree.\n"
        f"  calendar.md: {md_names}\n"
        f"  time_advance.py: {list(MONTHS)}"
    )


def test_seasons_match_code_canon():
    """Season-by-month mapping in calendar.md matches SEASON_BY_MONTH.

    calendar.md uses transitional labels (e.g. "Winter → Spring") for some months;
    we accept either pure or transitional labels as long as the primary season
    matches the code canon.
    """
    md_rows = _parse_months_table()
    for name, md_season in md_rows:
        md_primary = md_season.split("→")[0].strip()
        code_season = SEASON_BY_MONTH.get(name)
        assert code_season is not None, f"Month {name} missing from SEASON_BY_MONTH"
        assert md_primary == code_season, (
            f"Season mismatch for {name}: calendar.md={md_primary}, code={code_season}"
        )


def test_festivals_match_code_canon():
    """Festival (month, day) tuples in calendar.md match FESTIVALS in time_advance.py."""
    md_rows = _parse_festivals_table()
    md_set = {(month, day): name for name, month, day in md_rows}
    code_set = {(month, day): name for (month, day), name in FESTIVALS.items()}
    assert md_set == code_set, (
        f"Festival mappings disagree.\n  calendar.md: {md_set}\n  time_advance.py: {code_set}"
    )
