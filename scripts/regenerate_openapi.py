#!/usr/bin/env python3
"""Regenerate OpenAPI contracts from the live FastAPI app.

Run this whenever models, routes, or response shapes change. The output is
the canonical contract; the drift check verifies CI matches it.

This script also writes a trimmed GPT Actions spec. GPT Builder caps a single
Actions spec at 30 operations, so schemas/openapi.gpt.json removes only
infrastructure/static-reference endpoints that the GPT should not call at
runtime. The API and canonical full spec remain unchanged.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.main import app

HTTP_OPERATION_METHODS = {"get", "post", "put", "delete", "patch"}
GPT_ACTIONS_OPERATION_CAP = 30
GPT_SPEC_EXCLUSIONS = [
    ("get", "/"),
    ("get", "/health"),
    ("get", "/version"),
    ("get", "/catalog/vocab"),
    ("get", "/catalog/creatures"),
    ("get", "/tags"),
]


def operation_count(spec: dict) -> int:
    """Count GPT Builder-relevant HTTP operations in an OpenAPI spec."""
    return sum(
        1
        for path_methods in spec.get("paths", {}).values()
        for method in path_methods
        if method.lower() in HTTP_OPERATION_METHODS
    )


def generate_gpt_spec(full_spec: dict) -> dict:
    """
    Generate the GPT-facing spec by removing operations that should not be
    exposed to the GPT Actions surface.

    The GPT spec is functionally identical to the full spec for retained
    operations. Schema definitions are not pruned even if they become unused in
    the trimmed spec; keeping schemas consistent avoids contract drift between
    the full API spec and the GPT Actions spec.
    """
    gpt_spec = copy.deepcopy(full_spec)
    paths = gpt_spec.get("paths", {})

    for method, path in GPT_SPEC_EXCLUSIONS:
        method = method.lower()
        if path in paths and method in paths[path]:
            del paths[path][method]
            if not paths[path]:
                del paths[path]

    info = gpt_spec.get("info", {})
    title = info.get("title", "Mystic Weave API")
    if not title.endswith(" (GPT Actions)"):
        info["title"] = f"{title} (GPT Actions)"

    return gpt_spec


def write_spec(spec: dict, out_path: Path) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    print(f"✅ Wrote {out_path.relative_to(Path.cwd())}")


def main() -> None:
    full_spec = app.openapi()
    repo_root = Path(__file__).resolve().parents[1]
    schemas_dir = repo_root / "schemas"

    full_out_path = schemas_dir / "openapi.json"
    write_spec(full_spec, full_out_path)

    gpt_spec = generate_gpt_spec(full_spec)
    gpt_op_count = operation_count(gpt_spec)
    if gpt_op_count > GPT_ACTIONS_OPERATION_CAP:
        raise RuntimeError(
            "GPT spec exceeds "
            f"{GPT_ACTIONS_OPERATION_CAP}-operation cap: {gpt_op_count}"
        )

    gpt_out_path = schemas_dir / "openapi.gpt.json"
    write_spec(gpt_spec, gpt_out_path)
    print(f"GPT spec operation count: {gpt_op_count}/{GPT_ACTIONS_OPERATION_CAP}")


if __name__ == "__main__":
    main()