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
    # POST /state/{session_id} is the full-record save used by migration
    # scripts and admin tooling. The narrator GPT must use /delta during
    # play so that field-level merge semantics apply; full overwrite would
    # let the GPT clobber state. Excluded from the GPT subset only.
    ("post", "/state/{session_id}"),
    # Brief A (5.7.3): GET /state/{session_id} is retired from the GPT
    # surface. The full-state response (~44 KB observed in 5.7.2 traffic)
    # fails reliably through the OpenAI Actions wrapper despite a healthy
    # 11 ms backend. The narrator now reads via GET /scene/{session_id}
    # and the per-domain endpoints. Direct API access keeps the endpoint
    # in openapi.json for tooling and audit.
    ("get", "/state/{session_id}"),
    # GET /companion/{companion_id} is GPT-redundant: companions are
    # already returned in world.companions on every state load. Excluded
    # from the GPT subset to free a slot.
    ("get", "/companion/{companion_id}"),
    # Brief 19 slot trade: spend_ap is a player-UX flow that the narrator
    # never needs to invoke. Out of GPT subset; remains in openapi.json
    # for admin/UX tooling.
    ("post", "/character/{session_id}/spend_ap"),
    # Brief 19 admin reads: orchestrator/operator only.
    ("get", "/scene/record/{session_id}/{scene_id}"),
    ("get", "/scene/records/{session_id}"),
    # Brief 20 absorbed components: the narrator now calls
    # POST /narrator/scene_resolved which composes these three internally.
    # They remain in openapi.json for direct testing, admin tooling, and
    # the rare edge cases the orchestrator doesn't cover.
    ("post", "/scene/declare_resolution"),
    ("post", "/progression/scan"),
    ("post", "/progression/commit"),
    # Admin-style escape hatch for arcs stuck in non-terminal states
    # (typically authored with invalid closure-condition labels). The
    # narrator should not call this as a routine path — closure is a
    # creative decision and the orchestrator's /declare flow is the
    # supported surface.
    ("post", "/arc/{session_id}/{arc_id}/force_close"),
    # Phase 3 Phase C (5.7.0): /transition and /settle remain in the
    # full spec as deprecated edge-case fallbacks but are hidden from
    # the GPT subset. The narrator's routine arc lifecycle goes through
    # /declare with intent. /spawn stays in the GPT subset since
    # /declare intent=spawn_child is the orchestrated surface but
    # /spawn is a legitimate direct call for non-orchestrated spawns.
    ("post", "/arc/{session_id}/{arc_id}/transition"),
    ("post", "/arc/{session_id}/{arc_id}/settle"),
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