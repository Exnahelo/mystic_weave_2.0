#!/usr/bin/env python3
"""Pre-deploy API smoke bundle for fast integration confidence."""

from __future__ import annotations

import sys
from typing import Any

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
        "species": "human",
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
        if not all(k in opts for k in ("species", "focus", "backgrounds")):
            fail("GET /options: missing one of species/focus/backgrounds")

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
            "species": "human",
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
