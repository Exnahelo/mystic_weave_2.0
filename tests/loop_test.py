"""
tests/loop_test.py — Local loop test for the Mystic Weave API.

Drives the full game loop against a locally running API instance without
requiring the GPT. Covers all test cases from gpt_test_template.md.

Prerequisites:
  1. Local Postgres running with DATABASE_URL set in .env
  2. API running: uvicorn api.main:app --port 8000
  3. httpx installed: pip install httpx

Usage:
  python tests/loop_test.py
  python tests/loop_test.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import sys

try:
    import httpx
except ImportError:
    print("ERROR: httpx is required. Run: pip install httpx")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"

results: list[tuple[str, str, str]] = []  # (test_id, status, note)


def check(test_id: str, condition: bool, note: str = "") -> bool:
    status = PASS if condition else FAIL
    results.append((test_id, status, note))
    icon = "✓" if condition else "✗"
    print(f"  {icon} [{test_id}] {note}")
    return condition


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def subsection(title: str) -> None:
    print(f"\n  --- {title} ---")


# ---------------------------------------------------------------------------
# Test character data
# ---------------------------------------------------------------------------

# Human Ranger, Soldier background
# Base scores (pre-background): STR 13, DEX 15, CON 12, INT 10, WIS 14, CHA 8
# Soldier bonuses: STR +2, DEX +1, CON +1
# Final: STR 15, DEX 16, CON 13, INT 10, WIS 14, CHA 8
# HP: d10 max (10) + CON mod (+1) = 11
TEST_CHARACTER = {
    "character_name": "Soren",
    "class": "ranger",
    "species": "human",
    "background": "soldier",
    "ability_scores": {
        "STR": 13,
        "DEX": 15,
        "CON": 12,
        "INT": 10,
        "WIS": 14,
        "CHA": 8,
    },
    "skill_choices": ["perception", "stealth"],
    "starting_location": "test-loc-alpha",
    "goal": "Gain an audience with the Draconic Council",
    "threat": "Suspicion from the Dragon Guard",
}

EXPECTED_FINAL_SCORES = {"STR": 15, "DEX": 16, "CON": 13, "INT": 10, "WIS": 14, "CHA": 8}
EXPECTED_HP = 11  # d10 + CON mod (+1)

# Test locations — ephemeral, test-scoped only
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
        check("1.1.b", len(opts.get("classes", [])) > 0, f"classes returned: {len(opts.get('classes', []))}")
        check("1.1.c", len(opts.get("species", [])) > 0, f"species returned: {len(opts.get('species', []))}")
        check("1.1.d", len(opts.get("backgrounds", [])) > 0, f"backgrounds returned: {len(opts.get('backgrounds', []))}")
        class_indices = [c["index"] for c in opts.get("classes", [])]
        check("1.1.e", "ranger" in class_indices, f"'ranger' in classes: {class_indices[:5]}...")
        species_indices = [s["index"] for s in opts.get("species", [])]
        check("1.1.f", "human" in species_indices, f"'human' in species: {species_indices[:5]}...")
        bg_indices = [b["index"] for b in opts.get("backgrounds", [])]
        check("1.1.g", "soldier" in bg_indices, f"'soldier' in backgrounds: {bg_indices[:5]}...")

    subsection("Test 1.2 — Seed test locations")
    r = client.post("/location", json=TEST_LOC_ALPHA)
    check("1.2.a", r.status_code in (201, 200), f"POST /location (test-loc-alpha) → {r.status_code}")
    r = client.post("/location", json=TEST_LOC_BETA)
    check("1.2.b", r.status_code in (201, 200), f"POST /location (test-loc-beta) → {r.status_code}")

    subsection("Test 1.3 — POST /session/new")
    r = client.post("/session/new", json=TEST_CHARACTER)
    check("1.3.a", r.status_code == 201, f"POST /session/new → {r.status_code} {r.text[:200]}")
    if r.status_code != 201:
        print("  FATAL: Cannot continue without a session. Aborting Part 1.")
        return None

    session = r.json()
    session_id = session.get("session_id")
    check("1.3.b", bool(session_id), f"session_id present: {session_id!r}")

    char = session.get("character", {})
    scores = char.get("ability_scores", {})
    check("1.3.c", scores == EXPECTED_FINAL_SCORES,
          f"ability scores after background bonuses: {scores} (expected {EXPECTED_FINAL_SCORES})")

    hp = char.get("hp", {})
    check("1.3.d", hp.get("current") == EXPECTED_HP and hp.get("max") == EXPECTED_HP,
          f"HP: {hp} (expected current={EXPECTED_HP}, max={EXPECTED_HP})")

    check("1.3.e", char.get("class") == "ranger", f"class: {char.get('class')!r}")
    check("1.3.f", char.get("species") == "human", f"species: {char.get('species')!r}")
    check("1.3.g", char.get("background") == "soldier", f"background: {char.get('background')!r}")

    skills = char.get("skills", [])
    check("1.3.h", "perception" in skills, f"'perception' in skills: {skills}")
    check("1.3.i", "stealth" in skills, f"'stealth' in skills: {skills}")

    world = session.get("world", {})
    check("1.3.j", world.get("turn") == 1, f"turn: {world.get('turn')}")
    check("1.3.k", world.get("location") == "test-loc-alpha",
          f"location: {world.get('location')!r}")

    subsection("Test 1.4 — GET /state/{session_id}")
    r = client.get(f"/state/{session_id}")
    check("1.4.a", r.status_code == 200, f"GET /state/{session_id} → {r.status_code}")
    if r.status_code == 200:
        state = r.json()
        check("1.4.b", state.get("session_id") == session_id, "session_id matches")
        check("1.4.c", isinstance(state.get("log"), list), f"log is a list: {type(state.get('log'))}")
        check("1.4.d", len(state.get("log", [])) == 0, f"log starts empty: {state.get('log')}")

    return session_id


# ---------------------------------------------------------------------------
# Part 2 — 20-Turn Loop
# ---------------------------------------------------------------------------

def test_part2(client: httpx.Client, session_id: str, initial_character: dict) -> None:
    section("PART 2 — 20-Turn Loop")

    r = client.get(f"/state/{session_id}")
    if r.status_code != 200:
        check("2.setup", False, f"Could not load state to begin loop: {r.status_code}")
        return

    state = r.json()
    character = state["character"]
    world = state["world"]
    current_hp = character["hp"]["current"]
    max_hp = character["hp"]["max"]

    turn_failures = []

    for turn in range(1, 21):
        dc = 10 + (turn % 5)  # DC cycles 11–15
        roll_payload = {
            "dice": "1d20",
            "ability": "DEX",
            "score": EXPECTED_FINAL_SCORES["DEX"],
            "proficient": True,
            "dc": dc,
        }
        r_roll = client.post("/roll", json=roll_payload)
        if r_roll.status_code != 200:
            turn_failures.append(f"Turn {turn}: POST /roll failed ({r_roll.status_code})")
            continue

        roll_result = r_roll.json()
        success = roll_result["success"]

        if not success and not roll_result.get("critical_failure"):
            current_hp = max(0, current_hp - 1)
        elif roll_result.get("critical_failure"):
            current_hp = max(0, current_hp - 2)

        updated_character = dict(character)
        updated_character["hp"] = {"current": current_hp, "max": max_hp}

        updated_world = dict(world)
        updated_world["turn"] = turn + 1

        log_entry = (
            f"Turn {turn}: Soren {'succeeded' if success else 'failed'} a DEX check "
            f"(rolled {roll_result['roll']}, total {roll_result['total']} vs DC {dc})."
        )

        r_save = client.post(f"/state/{session_id}", json={
            "character": updated_character,
            "world": updated_world,
            "log_entry": log_entry,
        })
        if r_save.status_code != 200:
            turn_failures.append(
                f"Turn {turn}: POST /state → {r_save.status_code}: {r_save.text[:200]}"
            )
            continue

        saved = r_save.json()
        saved_turn = saved.get("world", {}).get("turn")
        if saved_turn != turn + 1:
            turn_failures.append(f"Turn {turn}: expected world.turn={turn + 1}, got {saved_turn}")

        saved_log = saved.get("log", [])
        if len(saved_log) != turn:
            turn_failures.append(f"Turn {turn}: expected {turn} log entries, got {len(saved_log)}")

        character = saved["character"]
        world = saved["world"]
        current_hp = character["hp"]["current"]

    check("2.loop", len(turn_failures) == 0,
          "All 20 turns completed cleanly" if not turn_failures else f"{len(turn_failures)} turn failures")
    if turn_failures:
        for f in turn_failures[:5]:
            print(f"    → {f}")
        if len(turn_failures) > 5:
            print(f"    → ... and {len(turn_failures) - 5} more")

    r = client.get(f"/state/{session_id}")
    check("2.final_state", r.status_code == 200, f"GET /state after 20 turns → {r.status_code}")
    if r.status_code == 200:
        final = r.json()
        check("2.final_turn", final.get("world", {}).get("turn") == 21,
              f"world.turn = {final.get('world', {}).get('turn')} (expected 21)")
        check("2.final_log", len(final.get("log", [])) == 20,
              f"log has {len(final.get('log', []))} entries (expected 20)")
        final_hp = final.get("character", {}).get("hp", {})
        check("2.final_hp", 0 <= final_hp.get("current", -1) <= max_hp,
              f"HP {final_hp.get('current')}/{max_hp} is valid")


# ---------------------------------------------------------------------------
# Part 3 — Dice Resolution
# ---------------------------------------------------------------------------

def test_part3(client: httpx.Client) -> None:
    section("PART 3 — Dice Resolution")

    subsection("Test 3.1 — Basic d20 roll")
    r = client.post("/roll", json={
        "dice": "1d20",
        "ability": "STR",
        "score": 16,
        "proficient": False,
        "dc": 12,
    })
    check("3.1.a", r.status_code == 200, f"POST /roll → {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        check("3.1.b", "roll" in result, f"'roll' in response: {list(result.keys())}")
        check("3.1.c", "total" in result, f"'total' in response")
        check("3.1.d", "success" in result, f"'success' in response")
        check("3.1.e", 1 <= result["roll"] <= 20, f"roll={result['roll']} in range [1,20]")
        # STR 16 → mod +3; no proficiency; expected total = roll + 3
        expected_total = result["roll"] + 3
        check("3.1.f", result["total"] == expected_total,
              f"total={result['total']} == roll({result['roll']}) + mod(3) = {expected_total}")

    subsection("Test 3.2 — Proficiency bonus applied")
    r = client.post("/roll", json={
        "dice": "1d20",
        "ability": "DEX",
        "score": 16,
        "proficient": True,
        "dc": 12,
    })
    check("3.2.a", r.status_code == 200, f"POST /roll (proficient) → {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        # DEX 16 → mod +3; level 1 proficiency bonus = +2; expected total = roll + 5
        expected_total = result["roll"] + 5
        check("3.2.b", result["total"] == expected_total,
              f"total={result['total']} == roll({result['roll']}) + mod(3) + prof(2) = {expected_total}")

    subsection("Test 3.3 — Critical rules (sample 20 rolls)")
    nat20_seen = False
    nat1_seen = False
    for i in range(20):
        r = client.post("/roll", json={
            "dice": "1d20",
            "ability": "WIS",
            "score": 10,
            "proficient": False,
            "dc": 10,
        })
        if r.status_code != 200:
            continue
        result = r.json()
        if result["roll"] == 20:
            nat20_seen = True
            check("3.3.a", result.get("critical_success") is True,
                  f"nat 20 → critical_success=True: {result.get('critical_success')}")
            check("3.3.b", result.get("success") is True,
                  "nat 20 → success=True")
        if result["roll"] == 1:
            nat1_seen = True
            check("3.3.c", result.get("critical_failure") is True,
                  f"nat 1 → critical_failure=True: {result.get('critical_failure')}")
            check("3.3.d", result.get("success") is False,
                  "nat 1 → success=False")
        if not result.get("critical_success") and not result.get("critical_failure"):
            expected_success = result["total"] >= 10
            check("3.3.e", result["success"] == expected_success,
                  f"success={result['success']} matches total({result['total']}) >= dc(10): {expected_success}")

    subsection("Test 3.4 — Non-d20 roll (no critical flags)")
    r = client.post("/roll", json={
        "dice": "2d6",
        "ability": "STR",
        "score": 15,
        "proficient": False,
        "dc": 8,
    })
    check("3.4.a", r.status_code == 200, f"POST /roll (2d6) → {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        check("3.4.b", result.get("critical_success") is False,
              f"2d6: critical_success={result.get('critical_success')} (expected False)")
        check("3.4.c", result.get("critical_failure") is False,
              f"2d6: critical_failure={result.get('critical_failure')} (expected False)")


# ---------------------------------------------------------------------------
# Part 4 — Location Graph
# ---------------------------------------------------------------------------

def test_part4(client: httpx.Client) -> None:
    section("PART 4 — Location Graph")

    subsection("Test 4.1 — Retrieve test-loc-alpha (seeded in Part 1)")
    r = client.get("/location/test-loc-alpha")
    check("4.1.a", r.status_code == 200, f"GET /location/test-loc-alpha → {r.status_code}")
    if r.status_code == 200:
        loc = r.json()
        check("4.1.b", loc.get("id") == "test-loc-alpha", f"id: {loc.get('id')!r}")
        check("4.1.c", loc.get("name") == "Test Location Alpha", f"name: {loc.get('name')!r}")

    subsection("Test 4.2 — Retrieve test-loc-beta (seeded in Part 1)")
    r = client.get("/location/test-loc-beta")
    check("4.2.a", r.status_code == 200, f"GET /location/test-loc-beta → {r.status_code}")
    if r.status_code == 200:
        loc = r.json()
        check("4.2.b", loc.get("id") == "test-loc-beta", f"id: {loc.get('id')!r}")

    subsection("Test 4.3 — Connections from test-loc-alpha")
    r = client.get("/location/test-loc-alpha/connections")
    check("4.3.a", r.status_code == 200, f"GET /location/test-loc-alpha/connections → {r.status_code}")
    if r.status_code == 200:
        conn_data = r.json()
        to_ids = [c["to_id"] for c in conn_data.get("connections", [])]
        check("4.3.b", "test-loc-beta" in to_ids,
              f"test-loc-alpha → test-loc-beta: {to_ids}")

    subsection("Test 4.4 — Upsert (overwrite) existing location")
    updated = dict(TEST_LOC_ALPHA)
    updated["threat_level"] = 2
    r = client.post("/location", json=updated)
    check("4.4.a", r.status_code in (200, 201), f"POST /location (upsert) → {r.status_code}")
    r = client.get("/location/test-loc-alpha")
    if r.status_code == 200:
        check("4.4.b", r.json().get("data", {}).get("threat_level") == 2,
              f"threat_level after upsert: {r.json().get('data', {}).get('threat_level')}")


# ---------------------------------------------------------------------------
# Part 5 — Edge Cases
# ---------------------------------------------------------------------------

def test_part5(client: httpx.Client) -> None:
    section("PART 5 — Edge Cases")

    subsection("Test 5.1 — GET /state for unknown session → 404")
    r = client.get("/state/NONEXISTENT_SESSION_XYZ")
    check("5.1.a", r.status_code == 404, f"GET /state/NONEXISTENT → {r.status_code} (expected 404)")

    subsection("Test 5.2 — Invalid class → 422")
    bad = dict(TEST_CHARACTER)
    bad["class"] = "dragonlord"
    r = client.post("/session/new", json=bad)
    check("5.2.a", r.status_code == 422, f"POST /session/new (bad class) → {r.status_code} (expected 422)")

    subsection("Test 5.3 — Invalid species → 422")
    bad = dict(TEST_CHARACTER)
    bad["species"] = "dragonborn-supreme"
    r = client.post("/session/new", json=bad)
    check("5.3.a", r.status_code == 422, f"POST /session/new (bad species) → {r.status_code} (expected 422)")

    subsection("Test 5.4 — Invalid background → 422")
    bad = dict(TEST_CHARACTER)
    bad["background"] = "nonexistent-background"
    r = client.post("/session/new", json=bad)
    check("5.4.a", r.status_code == 422, f"POST /session/new (bad background) → {r.status_code} (expected 422)")

    subsection("Test 5.5 — GET unknown location → 404")
    r = client.get("/location/nonexistent-location-xyz")
    check("5.5.a", r.status_code == 404, f"GET /location/nonexistent → {r.status_code} (expected 404)")

    subsection("Test 5.6 — GET connections for unknown location → 404")
    r = client.get("/location/nonexistent-location-xyz/connections")
    check("5.6.a", r.status_code == 404,
          f"GET /location/nonexistent/connections → {r.status_code} (expected 404)")

    subsection("Test 5.7 — Invalid ability in roll → 422")
    r = client.post("/roll", json={
        "dice": "1d20",
        "ability": "LUCK",
        "score": 15,
        "proficient": False,
        "dc": 10,
    })
    check("5.7.a", r.status_code == 422, f"POST /roll (bad ability) → {r.status_code} (expected 422)")

    subsection("Test 5.8 — HP cannot go negative (model validation)")
    r = client.post("/session/new", json=TEST_CHARACTER)
    if r.status_code == 201:
        sid = r.json()["session_id"]
        char = r.json()["character"]
        char["hp"]["current"] = -5
        r2 = client.post(f"/state/{sid}", json={
            "character": char,
            "world": {"location": "test-loc-alpha", "threat": "none", "goal": "test", "turn": 1},
            "log_entry": "test",
        })
        check("5.8.a", r2.status_code == 422,
              f"POST /state with hp.current=-5 → {r2.status_code} (expected 422)")
    else:
        results.append(("5.8.a", SKIP, "Could not create session for HP validation test"))
        print("  - [5.8.a] SKIP: Could not create session for HP validation test")


# ---------------------------------------------------------------------------
# Part 6 — Session Resume
# ---------------------------------------------------------------------------

def test_part6(client: httpx.Client, session_id: str) -> None:
    section("PART 6 — Session Resume")

    subsection("Test 6.1 — Resume session by ID")
    r = client.get(f"/state/{session_id}")
    check("6.1.a", r.status_code == 200, f"GET /state/{session_id} → {r.status_code}")
    if r.status_code == 200:
        state = r.json()
        check("6.1.b", state.get("session_id") == session_id, "session_id matches")
        check("6.1.c", isinstance(state.get("log"), list), "log is a list")
        check("6.1.d", len(state.get("log", [])) == 20,
              f"log has 20 entries: {len(state.get('log', []))}")
        check("6.1.e", state.get("world", {}).get("turn") == 21,
              f"turn = {state.get('world', {}).get('turn')} (expected 21)")
        check("6.1.f", state.get("character", {}).get("class") == "ranger",
              f"class = {state.get('character', {}).get('class')!r}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary() -> int:
    section("TEST SUMMARY")
    passed = sum(1 for _, s, _ in results if s == PASS)
    failed = sum(1 for _, s, _ in results if s == FAIL)
    skipped = sum(1 for _, s, _ in results if s == SKIP)
    total = len(results)

    print(f"\n  Total:   {total}")
    print(f"  Passed:  {passed}")
    print(f"  Failed:  {failed}")
    print(f"  Skipped: {skipped}")

    if failed > 0:
        print("\n  FAILED CHECKS:")
        for test_id, status, note in results:
            if status == FAIL:
                print(f"    ✗ [{test_id}] {note}")

    overall = "PASS" if failed == 0 else "FAIL"
    print(f"\n  Overall: {overall}\n")
    return 0 if failed == 0 else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Mystic Weave local loop test")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()

    print(f"\nMystic Weave Loop Test")
    print(f"Target: {args.base_url}")

    with httpx.Client(base_url=args.base_url, timeout=30.0) as client:
        try:
            r = client.get("/health")
            if r.status_code != 200:
                print(f"\nERROR: API health check failed ({r.status_code}). Is the server running?")
                return 1
            print(f"API is up: {r.json()}")
        except httpx.ConnectError:
            print(f"\nERROR: Cannot connect to {args.base_url}. Is the server running?")
            print("  Start it with: uvicorn api.main:app --port 8000")
            return 1

        session_id = test_part1(client)
        if session_id:
            test_part2(client, session_id, {})
            test_part6(client, session_id)
        else:
            print("\n  FATAL: Part 1 failed to create a session. Skipping Parts 2 and 6.")

        test_part3(client)
        test_part4(client)
        test_part5(client)

    return print_summary()


if __name__ == "__main__":
    sys.exit(main())
