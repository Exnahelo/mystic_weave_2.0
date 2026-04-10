#!/usr/bin/env python3
"""Fail CI when repo OpenAPI contract drifts from FastAPI-generated OpenAPI."""

from __future__ import annotations

import sys
import re
from pathlib import Path

import yaml

from api.main import app

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
IGNORED_PATHS = {"/"}
IGNORED_APP_ONLY_PATHS = {"/version"}
PRIMARY_STATUSES = ("200", "201")


def _normalize_path(path: str) -> str:
    """Normalize path parameter names so {id} and {location_id} compare equal."""
    return re.sub(r"\{[^}]+\}", "{}", path)


def _load_repo_spec() -> dict:
    spec_path = Path(__file__).resolve().parents[1] / "schemas" / "openapi.yaml"
    with open(spec_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _operation_map(spec: dict) -> dict[tuple[str, str], dict]:
    operations: dict[tuple[str, str], dict] = {}
    for path, path_item in spec.get("paths", {}).items():
        if path in IGNORED_PATHS:
            continue
        normalized_path = _normalize_path(path)
        for method, op in path_item.items():
            if method.lower() in HTTP_METHODS:
                operations[(normalized_path, method.lower())] = op
    return operations


def _schema_ref(node: dict | None) -> str | None:
    if not isinstance(node, dict):
        return None
    return (
        node.get("content", {})
        .get("application/json", {})
        .get("schema", {})
        .get("$ref")
    )


def main() -> None:
    repo_spec = _load_repo_spec()
    app_spec = app.openapi()

    issues: list[str] = []

    if repo_spec.get("info", {}).get("version") != app_spec.get("info", {}).get("version"):
        issues.append(
            "info.version mismatch: "
            f"repo={repo_spec.get('info', {}).get('version')} "
            f"app={app_spec.get('info', {}).get('version')}"
        )

    repo_ops = _operation_map(repo_spec)
    app_ops = _operation_map(app_spec)

    missing_in_repo = sorted(
        key for key in (set(app_ops) - set(repo_ops)) if key[0] not in IGNORED_APP_ONLY_PATHS
    )
    missing_in_app = sorted(set(repo_ops) - set(app_ops))
    if missing_in_repo:
        issues.append(f"operations missing in schemas/openapi.yaml: {missing_in_repo}")
    if missing_in_app:
        issues.append(f"operations missing in FastAPI app spec: {missing_in_app}")

    for key in sorted(set(repo_ops) & set(app_ops)):
        repo_op = repo_ops[key]
        app_op = app_ops[key]

        repo_req_ref = _schema_ref(repo_op.get("requestBody"))
        app_req_ref = _schema_ref(app_op.get("requestBody"))
        if repo_req_ref != app_req_ref:
            issues.append(
                f"request schema ref mismatch for {key[1].upper()} {key[0]}: "
                f"repo={repo_req_ref} app={app_req_ref}"
            )

        repo_responses = repo_op.get("responses", {})
        app_responses = app_op.get("responses", {})
        for status in PRIMARY_STATUSES:
            repo_ref = _schema_ref(repo_responses.get(status))
            app_ref = _schema_ref(app_responses.get(status))
            if repo_ref != app_ref:
                issues.append(
                    f"response {status} schema ref mismatch for {key[1].upper()} {key[0]}: "
                    f"repo={repo_ref} app={app_ref}"
                )

    if issues:
        print("❌ OpenAPI drift detected")
        for issue in issues:
            print(f"- {issue}")
        sys.exit(1)

    print("✅ OpenAPI drift check passed")


if __name__ == "__main__":
    main()
