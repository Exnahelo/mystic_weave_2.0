#!/usr/bin/env python3
"""
loop_test.py — Local API loop test for Mystic Weave 2.0

Tests the full game loop against a running local (or Railway) instance:
  1. Session initialization (options, location seeding, session creation)
  2. State persistence (load, save, log append, deep merge)
  3. Dice resolution (d100 roll-under, degree of success, criticals)
  4. Location graph (create, retrieve, connections, discovery)
  5. Character re-seeding
  6. Edge cases (invalid species, bad session, hp=0)

Usage:
    # Against local server
    python tests/loop_test.py

    # Against Railway
    python tests/loop_test.py https://mysticweave-production.up.railway.app
"""

from __future__ import annotations

import sys

import httpx

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

_pass = 0
_fail = 0


def check(tag: str, condition: bool, detail: str = "") -> None:
    global _pass, _fail
    if condition:
        _pass += 1
        print(f"  ✅ {tag}: {detail}")
    else:
        _fail += 1
        print(f"  ❌ {tag}: {detail}")


def section(title: str) -> None:
    print(f"\n{'='*60}\n{title}\n{'='*60}")


def subsection(title: str) -> None:
    print(f"\n  --- {title} ---")


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

TEST_CHARACTER = {
    "character_name": "Krath",
    "species": "dragonborn",
    "focus": "devoted",
    "background": "soldier",
    "adjustment_points": {
        "will": 2,
        "endurance": 3,
    },
    "starting_location": "test-loc-alpha",
    "goal": "test the loop",
    "threat": "bugs",
}

TEST_LOC_ALPHA = {
    "id": "test-loc-alpha",
    "name": "Test Location Alpha",
    "type": "settlement",
    "description": "A test location for the loop test.",
    "tags": ["test"],
    "connections": ["test-loc-beta"],
    "threat_level": 0,
    "known_npcs": [],
    "discovered": True,
}

TEST_LOC_BETA = {
    "id": "test-loc-beta",
    "name": "Test Location Beta",
    "type": "wilderness",
    "description": "A second test location for the loop test.",
    "tags": ["test"],
    "connections": ["test-loc-alpha"],
    "threat_level": 1,
    "known_npcs": [],
    "discovered": False,
}


# ---------------------------------------------------------------------------
# Part 1 — Session Initialization
# ---------------------------------------------------------------------------

def test_part1(client: httpx.Client) -> str | None:
    """Returns session_id on success, None on failure."""
    section("PART 1 — Session Initialization")
    session_id = None

    subsection("Test 1.1 — GET /options")
    r = client.get("/options")
    check("1.1.a", r.status_code == 200, f"GET /options → {r.status_code}")
    if r.status_code == 200:
        opts = r.json()
        check("1.1.b", len(opts.get("species", [])) == 8, f"species count: {len(opts.get('species', []))}")
        check("1.1.c", len(opts.get("focus", [])) == 7, f"focus count: {len(opts.get('focus', []))}")
        check("1.1.d", len(opts.get("backgrounds", [])) == 8, f"backgrounds count: {len(opts.get('backgrounds', []))}")
        species_indices = [s["index"] for s in opts.get("species", [])]
        check("1.1.e", "dragonborn" in species_indices, f"'dragonborn' in species")
        check("1.1.f", "human" in species_indices, f"'human' in species")
        focus_indices = [f["index"] for f in opts.get("focus", [])]
        check("1.1.g", "devoted" in focus_indices, f"'devoted' in focus")
        bg_indices = [b["index"] for b in opts.get("backgrounds", [])]
        check("1.1.h", "soldier" in bg_indices, f"'soldier' in backgrounds")

    subsection("Test 1.2 — Seed test locations")
    r = client.post("/location", json=TEST_LOC_ALPHA)
    check("1.2.a", r.status_code in (201, 200), f"POST /location (alpha) → {r.status_code}")
    r = client.post("/location", json=TEST_LOC_BETA)
    check("1.2.b", r.status_code in (201, 200), f"POST /location (beta) → {r.status_code}")

    subsection("Test 1.3 — POST /session/new")
    r = client.post("/session/new", json=TEST_CHARACTER)
    check("1.3.a", r.status_code == 201, f"POST /session/new → {r.status_code} {r.text[:200]}")
    if r.status_code != 201:
        print("  FATAL: Cannot continue without a session.")
        return None
    data = r.json()
    session_id = data["session_id"]
    char = data["character"]
    check("1.3.b", char["name"] == "Krath", f"name: {char['name']}")
    check("1.3.c", char["species"] == "dragonborn", f"species: {char['species']}")
    check("1.3.d", char["focus"] == "devoted", f"focus: {char['focus']}")
    check("1.3.e", char["background"] == "soldier", f"background: {char['background']}")
    check("1.3.f", char["hp"]["current"] == 100, f"hp: {char['hp']}")
    check("1.3.g", char["hp"]["max"] == 100, f"max hp: {char['hp']['max']}")

    # Verify domain scores (dragonborn base + adjustment)
    domains = char["domains"]
    check("1.3.h", domains["presence"] == 55, f"presence: {domains['presence']} (dragonborn primary)")
    check("1.3.i", domains["will"] == 47, f"will: {domains['will']} (45 base + 2 adj)")
    check("1.3.j", domains["endurance"] == 43, f"endurance: {domains['endurance']} (40 base + 3 adj)")

    # Verify tags
    knowledge = char.get("knowledge", {})
    check("1.3.k", knowledge.get("discipline") == 2, f"discipline K2: {knowledge.get('discipline')}")
    check("1.3.l", knowledge.get("courage") == 1, f"courage K1: {knowledge.get('courage')}")
    check("1.3.m", knowledge.get("command") == 1, f"command K1: {knowledge.get('command')}")
    check("1.3.n", knowledge.get("intimidation") == 1, f"intimidation K1: {knowledge.get('intimidation')}")
    check("1.3.o", knowledge.get("exertion") == 1, f"exertion K1: {knowledge.get('exertion')}")

    application = char.get("application", {})
    check("1.3.p", application.get("sacred_rites") == 1, f"sacred_rites A1: {application.get('sacred_rites')}")
    check("1.3.q", application.get("shields_armor") == 1, f"shields_armor A1: {application.get('shields_armor')}")
    check("1.3.r", application.get("heavy_weapons") == 1, f"heavy_weapons A1: {application.get('heavy_weapons')}")

    world = data["world"]
    check("1.3.s", world["location"] == "test-loc-alpha", f"location: {world['location']}")
    check("1.3.t", world["turn"] == 1, f"turn: {world['turn']}")

    return session_id


# ---------------------------------------------------------------------------
# Part 2 — State Persistence
# ---------------------------------------------------------------------------

def test_part2(client: httpx.Client, session_id: str) -> None:
    section("PART 2 — State Persistence")

    subsection("Test 2.1 — GET /state/{session_id}")
    r = client.get(f"/state/{session_id}")
    check("2.1.a", r.status_code == 200, f"GET /state → {r.status_code}")
    if r.status_code == 200:
        state = r.json()
        check("2.1.b", state["session_id"] == session_id, f"session_id matches")
        check("2.1.c", state["character"]["name"] == "Krath", f"character loaded")
        check("2.1.d", len(state["log"]) == 0, f"log empty: {len(state['log'])}")

    subsection("Test 2.2 — POST /state/{session_id} (save + log)")
    save_body = {
        "character": {
            "name": "Krath",
            "species": "dragonborn",
            "focus": "devoted",
            "background": "soldier",
            "level": 1,
            "hp": {"current": 85, "max": 100},
            "domains": {
                "power": 45, "agility": 35, "perception": 35,
                "endurance": 43, "intellect": 25, "will": 47, "presence": 55,
            },
            "knowledge": {"discipline": 2, "courage": 1, "command": 1, "intimidation": 1, "exertion": 1},
            "application": {"sacred_rites": 1, "shields_armor": 1, "heavy_weapons": 1},
            "status_effects": [],
            "notes": "",
        },
        "world": {
            "location": "test-loc-alpha",
            "threat": "bugs",
            "goal": "test the loop",
            "turn": 2,
        },
        "log_entry": "Krath took 15 damage from a test bug.",
    }
    r = client.post(f"/state/{session_id}", json=save_body)
    check("2.2.a", r.status_code == 200, f"POST /state → {r.status_code}")
    if r.status_code == 200:
        state = r.json()
        check("2.2.b", state["character"]["hp"]["current"] == 85, f"hp saved: {state['character']['hp']['current']}")
        check("2.2.c", len(state["log"]) == 1, f"log has 1 entry")
        check("2.2.d", state["world"]["turn"] == 2, f"turn: {state['world']['turn']}")

    subsection("Test 2.3 — 404 for invalid session")
    r = client.get("/state/nonexistent")
    check("2.3.a", r.status_code == 404, f"GET /state/nonexistent → {r.status_code}")


# ---------------------------------------------------------------------------
# Part 3 — Dice Resolution
# ---------------------------------------------------------------------------

def test_part3(client: httpx.Client) -> None:
    section("PART 3 — Dice Resolution (d100 Roll-Under)")

    subsection("Test 3.1 — Basic d100 roll")
    r = client.post("/roll", json={"target": 65})
    check("3.1.a", r.status_code == 200, f"POST /roll → {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        check("3.1.b", "roll" in result, f"'roll' in response")
        check("3.1.c", "target" in result, f"'target' in response")
        check("3.1.d", "success" in result, f"'success' in response")
        check("3.1.e", "degree" in result, f"'degree' in response")
        check("3.1.f", "margin" in result, f"'margin' in response")
        check("3.1.g", 1 <= result["roll"] <= 100, f"roll={result['roll']} in [1,100]")
        check("3.1.h", result["target"] == 65, f"target echoed: {result['target']}")
        # Verify margin calculation
        expected_margin = 65 - result["roll"]
        check("3.1.i", result["margin"] == expected_margin,
              f"margin={result['margin']} == 65 - {result['roll']} = {expected_margin}")

    subsection("Test 3.2 — Target clamping")
    r = client.post("/roll", json={"target": 150})
    check("3.2.a", r.status_code == 200, f"POST /roll (target=150) → {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        check("3.2.b", result["target"] == 99, f"target clamped to 99: {result['target']}")

    r = client.post("/roll", json={"target": -5})
    check("3.2.c", r.status_code == 200, f"POST /roll (target=-5) → {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        check("3.2.d", result["target"] == 1, f"target clamped to 1: {result['target']}")

    subsection("Test 3.3 — Degree of success bands (sample 50 rolls)")
    degrees_seen: set[str] = set()
    valid_degrees = {"critical_success", "strong_success", "success", "partial_failure", "failure", "critical_failure"}
    for _ in range(50):
        r = client.post("/roll", json={"target": 50})
        if r.status_code == 200:
            result = r.json()
            degrees_seen.add(result["degree"])
            check_degree = result["degree"] in valid_degrees
            if not check_degree:
                check("3.3.x", False, f"invalid degree: {result['degree']}")
    check("3.3.a", len(degrees_seen) >= 3, f"saw {len(degrees_seen)} distinct degrees: {degrees_seen}")

    subsection("Test 3.4 — Critical rules (sample 200 rolls)")
    crit_success_seen = False
    crit_failure_seen = False
    for _ in range(200):
        r = client.post("/roll", json={"target": 50})
        if r.status_code != 200:
            continue
        result = r.json()
        if result["roll"] == 1:
            crit_success_seen = True
            check("3.4.a", result["critical_success"] is True, f"roll=1 → critical_success=True")
            check("3.4.b", result["success"] is True, f"roll=1 → success=True")
            check("3.4.c", result["degree"] == "critical_success", f"roll=1 → degree=critical_success")
        if result["roll"] == 100:
            crit_failure_seen = True
            check("3.4.d", result["critical_failure"] is True, f"roll=100 → critical_failure=True")
            check("3.4.e", result["success"] is False, f"roll=100 → success=False")
            check("3.4.f", result["degree"] == "critical_failure", f"roll=100 → degree=critical_failure")
    if not crit_success_seen:
        print("  ⚠️  3.4: No natural 1 seen in 200 rolls (unlucky, not a bug)")
    if not crit_failure_seen:
        print("  ⚠️  3.4: No natural 100 seen in 200 rolls (unlucky, not a bug)")


# ---------------------------------------------------------------------------
# Part 4 — Location Graph
# ---------------------------------------------------------------------------

def test_part4(client: httpx.Client) -> None:
    section("PART 4 — Location Graph")

    subsection("Test 4.1 — GET /location/{id}")
    r = client.get("/location/test-loc-alpha")
    check("4.1.a", r.status_code == 200, f"GET /location/test-loc-alpha → {r.status_code}")
    if r.status_code == 200:
        loc = r.json()
        check("4.1.b", loc["name"] == "Test Location Alpha", f"name: {loc['name']}")

    subsection("Test 4.2 — GET /location/{id}/connections")
    r = client.get("/location/test-loc-alpha/connections")
    check("4.2.a", r.status_code == 200, f"GET connections → {r.status_code}")
    if r.status_code == 200:
        conns = r.json()
        to_ids = [c["to_id"] for c in conns.get("connections", [])]
        check("4.2.b", "test-loc-beta" in to_ids, f"connected to beta: {to_ids}")

    subsection("Test 4.3 — 404 for unknown location")
    r = client.get("/location/nonexistent")
    check("4.3.a", r.status_code == 404, f"GET /location/nonexistent → {r.status_code}")


# ---------------------------------------------------------------------------
# Part 5 — Character Re-seeding
# ---------------------------------------------------------------------------

def test_part5(client: httpx.Client, session_id: str) -> None:
    section("PART 5 — Character Re-seeding")

    subsection("Test 5.1 — POST /character/create")
    r = client.post("/character/create", json={
        "session_id": session_id,
        "name": "Thalia",
        "species": "elf",
        "focus": "stalker",
        "background": "criminal",
        "adjustment_points": {"agility": 3, "perception": 2},
    })
    check("5.1.a", r.status_code == 200, f"POST /character/create → {r.status_code}")
    if r.status_code == 200:
        char = r.json()["character"]
        check("5.1.b", char["name"] == "Thalia", f"name: {char['name']}")
        check("5.1.c", char["species"] == "elf", f"species: {char['species']}")
        check("5.1.d", char["domains"]["agility"] == 58, f"agility: {char['domains']['agility']} (55+3)")
        # Stalker + Criminal both grant lockpicking_traps → should stack to T2
        app_tags = char.get("application", {})
        check("5.1.e", app_tags.get("lockpicking_traps") == 2,
              f"lockpicking_traps stacked to T2: {app_tags.get('lockpicking_traps')}")


# ---------------------------------------------------------------------------
# Part 6 — Edge Cases
# ---------------------------------------------------------------------------

def test_part6(client: httpx.Client) -> None:
    section("PART 6 — Edge Cases")

    subsection("Test 6.1 — Invalid species")
    r = client.post("/session/new", json={
        "character_name": "Bad",
        "species": "goblin",
        "focus": "devoted",
        "background": "soldier",
    })
    check("6.1.a", r.status_code == 422, f"invalid species → {r.status_code}")

    subsection("Test 6.2 — Invalid focus")
    r = client.post("/session/new", json={
        "character_name": "Bad",
        "species": "human",
        "focus": "wizard",
        "background": "soldier",
    })
    check("6.2.a", r.status_code == 422, f"invalid focus → {r.status_code}")

    subsection("Test 6.3 — Adjustment points exceed 5")
    r = client.post("/session/new", json={
        "character_name": "Bad",
        "species": "human",
        "focus": "champion",
        "background": "soldier",
        "adjustment_points": {"power": 3, "endurance": 3},
    })
    check("6.3.a", r.status_code == 422, f"excess adjustment → {r.status_code}")

    subsection("Test 6.4 — Character create for nonexistent session")
    r = client.post("/character/create", json={
        "session_id": "nonexistent",
        "name": "Ghost",
        "species": "human",
        "focus": "champion",
        "background": "soldier",
    })
    check("6.4.a", r.status_code == 404, f"nonexistent session → {r.status_code}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"\nMystic Weave 2.0 — Loop Test")
    print(f"Target: {BASE_URL}\n")

    with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
        # Health check
        r = client.get("/health")
        if r.status_code != 200:
            print(f"FATAL: /health returned {r.status_code}. Is the server running?")
            sys.exit(1)
        print(f"Health check: OK")

        session_id = test_part1(client)
        if session_id:
            test_part2(client, session_id)
        test_part3(client)
        test_part4(client)
        if session_id:
            test_part5(client, session_id)
        test_part6(client)

    print(f"\n{'='*60}")
    print(f"RESULTS: {_pass} passed, {_fail} failed, {_pass + _fail} total")
    print(f"{'='*60}\n")
    sys.exit(1 if _fail > 0 else 0)


if __name__ == "__main__":
    main()
