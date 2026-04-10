#!/usr/bin/env python3
"""
Verify production API contract/data footprint against repository expectations.

Checks:
- OpenAPI required fields for NewSessionRequest and RollRequest
- /options species/focus/background counts and index sets
- /version metadata (api_version + data counts)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx


def _load_expected_indices(repo_root: Path) -> tuple[set[str], set[str], set[str]]:
    data_dir = repo_root / "data"

    def load_indices(filename: str) -> set[str]:
        with open(data_dir / filename, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, list):
            return {item["index"] for item in payload}
        return set(payload.keys())

    return (
        load_indices("species.json"),
        load_indices("focus.json"),
        load_indices("backgrounds.json"),
    )


def fail(msg: str) -> None:
    print(f"❌ {msg}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "base_url",
        nargs="?",
        default="https://mysticweave-production.up.railway.app",
        help="API base URL",
    )
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    repo_root = Path(__file__).resolve().parents[1]
    exp_species, exp_focus, exp_backgrounds = _load_expected_indices(repo_root)

    with httpx.Client(base_url=base_url, timeout=20.0) as client:
        openapi = client.get("/openapi.json")
        if openapi.status_code != 200:
            fail(f"GET /openapi.json -> {openapi.status_code}")
        spec = openapi.json()

        new_session_required = spec["components"]["schemas"]["NewSessionRequest"]["required"]
        if new_session_required != ["character_name", "species", "focus", "background"]:
            fail(f"NewSessionRequest.required mismatch: {new_session_required}")

        roll_required = spec["components"]["schemas"]["RollRequest"]["required"]
        if roll_required != ["target"]:
            fail(f"RollRequest.required mismatch: {roll_required}")

        options = client.get("/options")
        if options.status_code != 200:
            fail(f"GET /options -> {options.status_code}")
        opts = options.json()
        species = {s["index"] for s in opts.get("species", [])}
        focus = {f["index"] for f in opts.get("focus", [])}
        backgrounds = {b["index"] for b in opts.get("backgrounds", [])}

        if species != exp_species:
            fail(f"Species indices mismatch. expected={sorted(exp_species)} got={sorted(species)}")
        if focus != exp_focus:
            fail(f"Focus indices mismatch. expected={sorted(exp_focus)} got={sorted(focus)}")
        if backgrounds != exp_backgrounds:
            fail(
                "Background indices mismatch. "
                f"expected={sorted(exp_backgrounds)} got={sorted(backgrounds)}"
            )

        version = client.get("/version")
        if version.status_code != 200:
            fail(f"GET /version -> {version.status_code}")
        v = version.json()
        if v.get("api_version") != "3.1.0":
            fail(f"api_version mismatch in /version: {v.get('api_version')}")
        if v.get("species_count") != len(exp_species):
            fail(f"/version species_count mismatch: {v.get('species_count')}")
        if v.get("focus_count") != len(exp_focus):
            fail(f"/version focus_count mismatch: {v.get('focus_count')}")
        if v.get("backgrounds_count") != len(exp_backgrounds):
            fail(f"/version backgrounds_count mismatch: {v.get('backgrounds_count')}")

    print("✅ Production contract/options/version checks passed")


if __name__ == "__main__":
    main()
