"""
Deterministic pricing resolver and currency narration for Mystic Weave 2.0.

Pure functions. No I/O at call time -- caller passes loaded price_rules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.items import PricingInputs


# ---------- rules loading ----------

def load_price_rules(path: Path) -> dict[str, Any]:
    """Load and validate price_rules.json. Raises ValueError on shape errors."""
    with path.open() as f:
        rules = json.load(f)

    if rules.get("schema_version") != 1:
        raise ValueError(
            f"price_rules.json: unsupported schema_version "
            f"{rules.get('schema_version')}"
        )

    if rules.get("regional_modifiers") is not None:
        raise ValueError(
            "price_rules.json: regional_modifiers must be null in v1 "
            "(regional pricing deferred)"
        )

    components = rules.get("components", [])
    if not components:
        raise ValueError("price_rules.json: components must be non-empty")

    seen_ids: set[str] = set()
    for c in components:
        cid = c.get("id")
        if cid in seen_ids:
            raise ValueError(f"price_rules.json: duplicate component id '{cid}'")
        seen_ids.add(cid)

        kind = c.get("kind")
        if kind == "lookup":
            table = c.get("table")
            if not isinstance(table, dict) or not table:
                raise ValueError(
                    f"price_rules.json: component '{cid}' lookup requires "
                    f"non-empty table"
                )
            for k, v in table.items():
                if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                    raise ValueError(
                        f"price_rules.json: component '{cid}' table['{k}'] "
                        f"must be non-negative int"
                    )
        elif kind == "flat":
            v = c.get("value_cp")
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                raise ValueError(
                    f"price_rules.json: component '{cid}' flat requires "
                    f"non-negative int value_cp"
                )
        else:
            raise ValueError(
                f"price_rules.json: component '{cid}' has unknown kind '{kind}'"
            )

    return rules


# ---------- resolution ----------

def resolve_price_cp(inputs: PricingInputs, rules: dict[str, Any]) -> int:
    """
    Sum component contributions into a canonical cp value.

    Raises ValueError on:
      - unknown component id referenced from inputs
      - lookup component referenced without a key
      - lookup key not in component's table
      - flat component referenced with a key (rejected to keep inputs honest)
    """
    by_id = {c["id"]: c for c in rules["components"]}
    total = 0

    for ref in inputs.components:
        comp = by_id.get(ref.id)
        if comp is None:
            raise ValueError(f"unknown pricing component '{ref.id}'")

        kind = comp["kind"]
        if kind == "lookup":
            if ref.key is None:
                raise ValueError(f"component '{ref.id}' is lookup; requires key")
            if ref.key not in comp["table"]:
                raise ValueError(
                    f"component '{ref.id}' has no entry for key '{ref.key}'"
                )
            total += comp["table"][ref.key]
        elif kind == "flat":
            if ref.key is not None:
                raise ValueError(f"component '{ref.id}' is flat; must not have key")
            total += comp["value_cp"]

    return total


# ---------- currency narration ----------

# Authoritative ordering, descending by value_cp.
# Mirrors data/catalog/economy/currencies.json. Hardcoded here for resolver
# determinism; tests enforce parity with the JSON file.
_DENOMINATIONS = [
    ("pp", 1000),
    ("gp", 100),
    ("ep", 50),
    ("sp", 10),
    ("cp", 1),
]


def cp_to_denominations(value_cp: int, *, use_electrum: bool = False) -> dict[str, int]:
    """
    Decompose a cp value into greedy denominations.

    Default skips electrum (5e convention: ep is rare in practice).
    Returns {} for value_cp == 0. Negative values raise ValueError.
    """
    if value_cp < 0:
        raise ValueError(f"cp_to_denominations: negative value {value_cp}")

    denoms = (
        _DENOMINATIONS
        if use_electrum
        else [d for d in _DENOMINATIONS if d[0] not in {"ep", "pp"}]
    )
    out: dict[str, int] = {}
    remaining = value_cp
    for name, val in denoms:
        if remaining >= val:
            out[name] = remaining // val
            remaining %= val
    return out


def narrate_price(value_cp: int, *, use_electrum: bool = False) -> str:
    """
    Render cp value as natural narration. Examples:
      0     -> "nothing"
      7     -> "7 cp"
      150   -> "1 gp 5 sp"
      1547  -> "15 gp 4 sp 7 cp"
    """
    if value_cp == 0:
        return "nothing"
    parts = cp_to_denominations(value_cp, use_electrum=use_electrum)
    return " ".join(f"{count} {name}" for name, count in parts.items())