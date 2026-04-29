#!/usr/bin/env python3
"""
Verify production API contract/data footprint against repository expectations.

Checks:
- OpenAPI required fields for NewSessionRequest and RollRequest
- /options ancestry/culture/focus/background counts and index sets
- /options and /tags response key parity
- /version metadata (api_version, fingerprints, and data counts)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.models import OptionsResponse, TagsResponse


def _load_expected_indices(repo_root: Path) -> tuple[set[str], set[str], set[str], set[str]]:
    data_dir = repo_root / "data"

    def load_indices(filename: str) -> set[str]:
        with open(data_dir / filename, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, list):
            return {item["index"] for item in payload}
        return set(payload.keys())

    return (
        load_indices("characters/ancestry.json"),
        load_indices("characters/culture.json"),
        load_indices("characters/focus.json"),
        load_indices("characters/background.json"),
    )


def _load_expected_api_version(repo_root: Path) -> str:
    """Read the expected API version from schemas/openapi.yaml."""
    schema_path = repo_root / "schemas" / "openapi.yaml"
    if not schema_path.exists():
        fail(f"missing OpenAPI schema: {schema_path}")

    in_info = False
    with open(schema_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            stripped = line.strip()
            if stripped == "info:":
                in_info = True
                continue
            if in_info and line and not line.startswith(" "):
                break
            if in_info and stripped.startswith("version:"):
                _, value = stripped.split(":", 1)
                version = value.strip().strip('"\'')
                if version:
                    return version

    fail(f"missing info.version in {schema_path}")


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

    repo_root = REPO_ROOT
    exp_ancestries, exp_cultures, exp_focus, exp_backgrounds = _load_expected_indices(repo_root)
    expected_api_version = _load_expected_api_version(repo_root)
    expected_option_keys = set(OptionsResponse.model_fields)
    expected_tag_keys = set(TagsResponse.model_fields)

    with httpx.Client(base_url=base_url, timeout=20.0) as client:
        openapi = client.get("/openapi.json")
        if openapi.status_code != 200:
            fail(f"GET /openapi.json -> {openapi.status_code}")
        spec = openapi.json()

        new_session_required = spec["components"]["schemas"]["NewSessionRequest"]["required"]
        if new_session_required != ["character_name", "ancestry", "culture", "focus", "background"]:
            fail(f"NewSessionRequest.required mismatch: {new_session_required}")

        roll_required = spec["components"]["schemas"]["RollRequest"]["required"]
        if roll_required != ["target"]:
            fail(f"RollRequest.required mismatch: {roll_required}")

        options = client.get("/options")
        if options.status_code != 200:
            fail(f"GET /options -> {options.status_code}")
        opts = options.json()
        option_keys = set(opts)
        if option_keys != expected_option_keys:
            fail(f"/options keys mismatch. expected={sorted(expected_option_keys)} got={sorted(option_keys)}")
        ancestries = {s["index"] for s in opts.get("ancestries", [])}
        cultures = {c["index"] for c in opts.get("cultures", [])}
        focus = {f["index"] for f in opts.get("focus", [])}
        backgrounds = {b["index"] for b in opts.get("backgrounds", [])}

        if ancestries != exp_ancestries:
            fail(f"Ancestry indices mismatch. expected={sorted(exp_ancestries)} got={sorted(ancestries)}")
        if cultures != exp_cultures:
            fail(f"Culture indices mismatch. expected={sorted(exp_cultures)} got={sorted(cultures)}")
        if focus != exp_focus:
            fail(f"Focus indices mismatch. expected={sorted(exp_focus)} got={sorted(focus)}")
        if backgrounds != exp_backgrounds:
            fail(
                "Background indices mismatch. "
                f"expected={sorted(exp_backgrounds)} got={sorted(backgrounds)}"
            )

        tags = client.get("/tags")
        if tags.status_code != 200:
            fail(f"GET /tags -> {tags.status_code}")
        tag_payload = tags.json()
        tag_keys = set(tag_payload)
        if tag_keys != expected_tag_keys:
            fail(f"/tags keys mismatch. expected={sorted(expected_tag_keys)} got={sorted(tag_keys)}")
        for key in sorted(expected_tag_keys):
            value = tag_payload.get(key)
            if not isinstance(value, list) or not value:
                fail(f"/tags {key} must be a non-empty list")

        version = client.get("/version")
        if version.status_code != 200:
            fail(f"GET /version -> {version.status_code}")
        v = version.json()
        if v.get("api_version") != expected_api_version:
            fail(
                "api_version mismatch in /version: "
                f"expected={expected_api_version} got={v.get('api_version')}"
            )
        if not isinstance(v.get("data_fingerprint"), str) or not v.get("data_fingerprint") or v.get("data_fingerprint") == "unknown":
            fail("/version missing usable data_fingerprint")
        if not isinstance(v.get("combat_rules_fingerprint"), str) or not v.get("combat_rules_fingerprint"):
            fail("/version missing combat_rules_fingerprint")
        if v.get("ancestry_count") != len(exp_ancestries):
            fail(f"/version ancestry_count mismatch: {v.get('ancestry_count')}")
        if v.get("culture_count") != len(exp_cultures):
            fail(f"/version culture_count mismatch: {v.get('culture_count')}")
        if v.get("focus_count") != len(exp_focus):
            fail(f"/version focus_count mismatch: {v.get('focus_count')}")
        if v.get("backgrounds_count") != len(exp_backgrounds):
            fail(f"/version backgrounds_count mismatch: {v.get('backgrounds_count')}")

    print("✅ Production contract verified")


if __name__ == "__main__":
    main()
