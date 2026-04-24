#!/usr/bin/env python3
"""Pre-deploy API smoke bundle for fast integration confidence."""

from __future__ import annotations

import sys
from typing import Any
import re

import httpx


def fail(message: str) -> None:
    print(f"❌ {message}")
    raise SystemExit(1)


def expect_status(resp: httpx.Response, expected: int | tuple[int, ...], step: str) -> None:
    expected_set = expected if isinstance(expected, tuple) else (expected,)
    if resp.status_code not in expected_set:
        fail(f"{step}: expected {expected_set}, got {resp.status_code} :: {resp.text[:300]}")


def main() -> None:
    base_url = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    print(f"Running pre-deploy smoke bundle against: {base_url}")

    alpha_id = "smoke-loc-alpha"
    beta_id = "smoke-loc-beta"

    new_session_payload: dict[str, Any] = {
        "character_name": "SmokeRunner",
        "ancestry": "human",
        "culture": "drakenvale_city",
        "focus": "champion",
        "background": "soldier",
        "adjustment_points": {"power": 2, "endurance": 2, "will": 1},
        "starting_location": alpha_id,
        "goal": "verify deployment candidate",
        "threat": "pipeline drift",
        "identity": {
            "origin": "Pipeline proving grounds",
            "motivations": ["Pass verification"],
            "quirks": ["Counts every step"],
            "bonds": ["Release quality"],
            "flaws": ["Over-cautious"],
            "wound": "Failed once in staging",
            "alignment": {"order": "lawful", "intent": "good", "ethos_note": "Ship only when proven"},
        },
        "starting_economy": {
            "wealth_tier": "modest",
            "coin": 500,
            "trade_goods": ["inspection-kit"],
            "obligations": [],
        },
    }

    with httpx.Client(base_url=base_url, timeout=20.0) as client:
        # Core health and contract shape hints
        expect_status(client.get("/health"), 200, "GET /health")
        version = client.get("/version")
        expect_status(version, 200, "GET /version")
        if "api_version" not in version.json():
            fail("GET /version: missing api_version")

        options = client.get("/options")
        expect_status(options, 200, "GET /options")
        opts = options.json()
        expected_option_keys = {"ancestries", "cultures", "focus", "backgrounds"}
        if set(opts.keys()) != expected_option_keys:
            fail(f"GET /options: unexpected key set {sorted(opts.keys())}")

        creatures = client.get("/catalog/creatures")
        expect_status(creatures, 200, "GET /catalog/creatures")
        catalog = creatures.json()
        wolf_template = next(
            (c for c in catalog.get("creature_catalog", []) if c.get("subspecies") == "moonthorn_wolf"),
            None,
        )
        if wolf_template is None:
            fail("GET /catalog/creatures: moonthorn_wolf missing from creature_catalog")

        items = client.get("/catalog/items")
        expect_status(items, 200, "GET /catalog/items")
        item_keys = set(items.json().keys())
        if item_keys != {"mundane_items", "magical_items", "apparel_items"}:
            fail(f"GET /catalog/items: unexpected key set {sorted(item_keys)}")

        vocab = client.get("/catalog/vocab")
        expect_status(vocab, 200, "GET /catalog/vocab")

        # Location create/update semantics
        alpha = {
            "id": alpha_id,
            "name": "Smoke Alpha",
            "type": "settlement",
            "description": "predeploy smoke alpha",
            "tags": ["smoke"],
            "connections": [beta_id],
            "threat_level": 0,
            "known_npcs": [],
            "discovered": True,
        }
        beta = {
            "id": beta_id,
            "name": "Smoke Beta",
            "type": "wilderness",
            "description": "predeploy smoke beta",
            "tags": ["smoke"],
            "connections": [alpha_id],
            "threat_level": 1,
            "known_npcs": [],
            "discovered": True,
        }

        expect_status(client.post("/location", json=alpha), (200, 201), "POST /location alpha (create)")
        expect_status(client.post("/location", json=beta), (200, 201), "POST /location beta (create)")

        alpha["description"] = "predeploy smoke alpha updated"
        alpha_update = client.post("/location", json=alpha)
        expect_status(alpha_update, 200, "POST /location alpha (update)")

        expect_status(client.get(f"/location/{alpha_id}"), 200, "GET /location/{location_id}")
        conn_resp = client.get(f"/location/{alpha_id}/connections")
        expect_status(conn_resp, 200, "GET /location/{location_id}/connections")
        conns = {c["to_id"] for c in conn_resp.json().get("connections", [])}
        if beta_id not in conns:
            fail("connections endpoint missing expected beta target")

        # Session/state lifecycle
        session_resp = client.post("/session/new", json=new_session_payload)
        expect_status(session_resp, 201, "POST /session/new")
        session_data = session_resp.json()
        session_id = session_data["session_id"]
        character = session_data["character"]
        world = session_data["world"]

        state_get = client.get(f"/state/{session_id}")
        expect_status(state_get, 200, "GET /state/{session_id}")

        companion_payload = {
            "name": "Smokefang",
            "species": wolf_template["species"],
            "subtype": wolf_template["subspecies"],
            "size": wolf_template["size"],
            "age_category": wolf_template["age_category"],
            "tactical_roles": wolf_template["tactical_roles_defaults"],
            "training_level": "trained",
            "bond_level": "bonded",
            "natural_abilities": wolf_template["natural_abilities"],
            "learned_commands": ["heel"],
            "command_notes": "Smoke sanity companion",
            "movement_modes": wolf_template["movement_modes"],
            "natural_weapons": wolf_template["natural_weapons"],
            "carrying_capacity": wolf_template["carrying_capacity"],
            "hp": {"current": wolf_template["base_hp"], "max": wolf_template["base_hp"]},
            "domains": wolf_template["base_domains"],
            "temperament": wolf_template["temperament"],
            "bond_links": {"primary": "smokerunner"},
        }
        companion_create = client.post(
            "/companion/new",
            json={
                "session_id": session_id,
                "handler_id": "smokerunner",
                "tier": "creature",
                "companion": companion_payload,
            },
        )
        expect_status(companion_create, 201, "POST /companion/new")
        companion_id = companion_create.json()["companion_id"]
        if not re.fullmatch(r"smokerunner_moonthorn_wolf(?:_\d+)?", companion_id):
            fail(f"companion_id format unexpected: {companion_id}")

        companion_get = client.get(f"/companion/{companion_id}", params={"session_id": session_id})
        expect_status(companion_get, 200, "GET /companion/{id}")
        companion_data = companion_get.json()
        if companion_data.get("companion_id") != companion_id:
            fail("GET /companion/{id}: returned companion_id mismatch")
        if companion_data.get("companion", {}).get("name") != "Smokefang":
            fail("GET /companion/{id}: returned wrong companion payload")

        world["turn"] = int(world.get("turn", 1)) + 1
        world["threat"] = "smoke-check-in-progress"
        save_payload = {
            "character": character,
            "world": world,
            "log_entry": "Smoke bundle advanced one turn.",
        }
        save_resp = client.post(f"/state/{session_id}", json=save_payload)
        expect_status(save_resp, 200, "POST /state/{session_id}")

        # Character reseed endpoint
        char_create_payload = {
            "session_id": session_id,
            "name": "SmokeRunner",
            "ancestry": "human",
            "culture": "drakenvale_city",
            "focus": "champion",
            "background": "soldier",
            "adjustment_points": {"power": 1},
            "identity": {"origin": "Reseed check"},
        }
        expect_status(client.post("/character/create", json=char_create_payload), 200, "POST /character/create")

        # Roll endpoint
        roll_resp = client.post("/roll", json={"target": 64})
        expect_status(roll_resp, 200, "POST /roll")
        roll_data = roll_resp.json()
        if "roll" not in roll_data or "degree" not in roll_data:
            fail("POST /roll response missing roll/degree")

    print("✅ Pre-deploy smoke bundle passed")


if __name__ == "__main__":
    main()
