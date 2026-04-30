#!/usr/bin/env python3
"""Regenerate schemas/openapi.json from the live FastAPI app.

Run this whenever models, routes, or response shapes change. The output is
the canonical contract; the drift check verifies CI matches it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.main import app


def main() -> None:
    spec = app.openapi()
    out_path = Path(__file__).resolve().parents[1] / "schemas" / "openapi.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    print(f"✅ Wrote {out_path.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()