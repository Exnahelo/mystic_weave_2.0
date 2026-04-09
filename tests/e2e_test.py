"""
tests/e2e_test.py — End-to-end production test for the Mystic Weave API.

Simulates the full GPT game loop against the production (or local) API.
Tests the exact sequence of calls the GPT makes: options → session creation →
location load → connections check → roll → state save → session resume.

Covers all items from the end-to-end loop test checklist:
  - New session creation (species + subspecies + background + class)
  - Turn loop (location load → connections → roll → save)
  - Session resume (simulated new conversation)
  - Edge cases: hp=0, invalid class/species/background

Prerequisites:
  pip install httpx

Usage:
  python3 tests/e2e_test.py                                          # → Railway production
  python3 tests/e2e_test.py --base-url http://localhost:8000         # → local
  python3 tests/e2e_test.py --verbose                                # → print response bodies
  python3 tests/e2e_test.py --base-url http://localhost:8000 --verbose
"""

from __future__ import annotations

import argparse
import math
import sys
from typing import Any

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

results: list[tuple[str, str, str]] = []
_verbose = False


def check(test_id: str, condition: bool, note: str = "") -> bool:
    status = PASS if condition else FAIL
    results.append((test_id, status, note))
    icon = "✓" if condition else "✗"
    print(f"  {icon} [{test_id}] {note}")
    return condition


def vprint(label: str, data: Any) -> None:
    if _verbose:
        import json
        print(f"    {label}: {json.dumps(data, indent=2, default=str)[:500]}")


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def subsection(title: str) -> None:
    print(f"\n  --- {title} ---")


# ---------------------------------------------------------------------------
# Test data — Drakenvale locations
# ---------------------------------------------------------------------------

# Primary character: Human Ranger, Soldier background
# Base scores (pre-background): STR 13, DEX 15, CON 12, INT 10, WIS 14, CHA 8
# Soldier background scores: STR, DEX, CON
# No primary_score → default +1 to all three background scores
# Final: STR 14, DEX 16, CON 13, INT 10, WIS 14, CHA 8
# HP: d10 max (10) + CON mod (+1) = 11
# Languages: Common (auto) + dwarvish, elvish (2 choices required for human)
PRIMARY_CHARACTER = {
    "character_name": "Aldric",
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
    "language_choices": ["dwarvish", "elvish"],
    "starting_location": "alpine-pass",
    "goal": "Reach the hidden sanctuary of Drakenvale",
    "threat": "Ice drakes patrol the mountain pass",
}
PRIMARY_EXPECTED_SCORES = {"STR": 14, "DEX": 16, "CON": 13, "INT": 10, "WIS": 14, "CHA": 8}
PRIMARY_EXPECTED_HP = 11

# Secondary character: Elf Wizard, High Elf subspecies, no background
# Tests subspecies path + no-background edge case
# Base scores: STR 8, DEX 14, CON 12, INT 16, WIS 13, CHA 10
# No background bonuses applied
# Languages: Common, Elvish (auto) + draconic (1 choice required for elf)
SECONDARY_CHARACTER = {
    "character_name": "Sylvara",
    "class": "wizard",
    "species": "elf",
    "subspecies": "elven-lineage-high-elf",
    "ability_scores": {
        "STR": 8,
        "DEX": 14,
        "CON": 12,
        "INT": 16,
        "WIS": 13,
        "CHA": 10,
    },
    "skill_choices": ["arcana", "history"],
    "language_choices": ["draconic"],
    "starting_location": "alpine-pass",
    "goal": "Study the ancient wards protecting Drakenvale",
    "threat": "Frost wyverns in the peaks",
}
SECONDARY_EXPECTED_SCORES = {"STR": 8, "DEX": 14, "CON": 12, "INT": 16, "WIS": 13, "CHA": 10}
# Wizard HP: d6 max (6) + CON mod (+1) = 7
SECONDARY_EXPECTED_HP = 7

# Test location: Alpine Pass — starting location, outer mountain ring
ALPINE_PASS = {
    "id": "alpine-pass",
    "name": "Alpine Pass",
    "type": "wilderness",
    "description": "A high mountain pass through the outer ring of peaks surrounding Drakenvale. Glacial crystals embedded in the rock glint with ice magic. The air is thin and bitterly cold. Ice drakes and frost wyverns patrol the skies as territorial creatures.",
    "tags": ["alpine", "high-altitude", "entry-point"],
    "connections": ["glacial-stream-crossing"],
    "threat_level": 3,
    "known_npcs": [],
    "discovered": True,
}

# Test location: Glacial Stream Crossing — connects pass to lower slopes
GLACIAL_STREAM_CROSSING = {
    "id": "glacial-stream-crossing",
    "name": "Glacial Stream Crossing",
    "type": "wilderness",
    "description": "A stream fed by the peaks above, bridged by weathered stone. The water is clear and painfully cold, carrying faint traces of latent magic. A natural rest point on the descent into the valley.",
    "tags": ["alpine", "water", "transition"],
    "connections": ["alpine-pass"],
    "threat_level": 2,
    "known_npcs": [],
    "discovered": False,
}


# ---------------------------------------------------------------------------
# Part 1 — Setup
# ---------------------------------------------------------------------------

def test_part1_setup(client: httpx.Client) -> bool:
    section("PART 1 — Setup & Health Check")

    subsection("Test 1.1 — Health check")
    r = client.get("/health")
    ok = check("1.1.a", r.status_code == 200, f"GET /health → {r.status_code}")
    if ok:
        vprint("health", r.json())
        check("1.1.b", r.json().get("status") == "ok", f"status=ok: {r.json()}")

    subsection("Test 1.2 — GET /options")
    r = client.get("/options")
    check("1.2.a", r.status_code == 200, f"GET /options → {r.status_code}")
    if r.status_code != 200:
        return False

    opts = r.json()
    vprint("options summary", {
        "classes": len(opts.get("classes", [])),
        "species": len(opts.get("species", [])),
        "subspecies": len(opts.get("subspecies", [])),
        "backgrounds": len(opts.get("backgrounds", [])),
    })
    check("1.2.b", len(opts.get("classes", [])) >= 12, f"classes: {len(opts.get('classes', []))}")
    check("1.2.c", len(opts.get("species", [])) >= 9, f"species: {len(opts.get('species', []))}")
    check("1.2.d", len(opts.get("backgrounds", [])) >= 4, f"backgrounds: {len(opts.get('backgrounds', []))}")

    class_indices = [c["index"] for c in opts.get("classes", [])]
    species_indices = [s["index"] for s in opts.get("species", [])]
    subspecies_indices = [s["index"] for s in opts.get("subspecies", [])]
    bg_indices = [b["index"] for b in opts.get("backgrounds", [])]

    check("1.2.e", "ranger" in class_indices, f"'ranger' in classes")
    check("1.2.f", "wizard" in class_indices, f"'wizard' in classes")
    check("1.2.g", "human" in species_indices, f"'human' in species")
    check("1.2.h", "elf" in species_indices, f"'elf' in species")
    check("1.2.i", "elven-lineage-high-elf" in subspecies_indices, f"'elven-lineage-high-elf' in subspecies")
    check("1.2.j", "soldier" in bg_indices, f"'soldier' in backgrounds")

    subsection("Test 1.3 — Seed test locations")
    # Seed glacial-stream-crossing first (no connections to alpine-pass yet)
    r = client.post("/location", json=GLACIAL_STREAM_CROSSING)
    check("1.3.a", r.status_code == 201, f"POST /location (glacial-stream-crossing) → {r.status_code}")

    # Seed alpine-pass with connection to glacial-stream-crossing
    r = client.post("/location", json=ALPINE_PASS)
    check("1.3.b", r.status_code == 201, f"POST /location (alpine-pass) → {r.status_code}")

    # Verify alpine-pass loads
    r = client.get("/location/alpine-pass")
    check("1.3.c", r.status_code == 200, f"GET /location/alpine-pass → {r.status_code}")
    if r.status_code == 200:
        loc = r.json()
        vprint("alpine-pass", loc)
        check("1.3.d", loc.get("name") == "Alpine Pass", f"name: {loc.get('name')!r}")

    # Verify connections
    r = client.get("/location/alpine-pass/connections")
    check("1.3.e", r.status_code == 200, f"GET /location/alpine-pass/connections → {r.status_code}")
    if r.status_code == 200:
        conn_data = r.json()
        to_ids = [c["to_id"] for c in conn_data.get("connections", [])]
        check("1.3.f", "glacial-stream-crossing" in to_ids, f"alpine-pass → glacial-stream-crossing: {to_ids}")

    return True


# ---------------------------------------------------------------------------
# Part 2 — Primary Session Creation (Human Ranger, Soldier background)
# ---------------------------------------------------------------------------

def test_part2_primary_session(client: httpx.Client) -> str | None:
    section("PART 2 — Primary Session Creation (Human Ranger, Soldier)")

    subsection("Test 2.1 — POST /session/new")
    r = client.post("/session/new", json=PRIMARY_CHARACTER)
    check("2.1.a", r.status_code == 201, f"POST /session/new → {r.status_code} {r.text[:200]}")
    if r.status_code != 201:
        return None

    session = r.json()
    session_id = session.get("session_id")
    vprint("session", session)
    check("2.1.b", bool(session_id), f"session_id: {session_id!r}")

    char = session.get("character", {})
    scores = char.get("ability_scores", {})
    hp = char.get("hp", {})

    check("2.1.c", scores == PRIMARY_EXPECTED_SCORES,
          f"ability scores: {scores} (expected {PRIMARY_EXPECTED_SCORES})")
    check("2.1.d", hp.get("current") == PRIMARY_EXPECTED_HP and hp.get("max") == PRIMARY_EXPECTED_HP,
          f"HP: {hp} (expected {PRIMARY_EXPECTED_HP})")
    check("2.1.e", char.get("class") == "ranger", f"class: {char.get('class')!r}")
    check("2.1.f", char.get("species") == "human", f"species: {char.get('species')!r}")
    check("2.1.g", char.get("background") == "soldier", f"background: {char.get('background')!r}")
    check("2.1.h", char.get("feat") is not None, f"feat from background: {char.get('feat')!r}")

    profs = char.get("proficiencies", [])
    check("2.1.i", len(profs) > 0, f"proficiencies: {profs[:4]}...")
    # Ranger should have light-armor, medium-armor, shields, simple-weapons, martial-weapons
    for expected_prof in ["light-armor", "medium-armor", "shields", "simple-weapons", "martial-weapons"]:
        check(f"2.1.prof.{expected_prof}", expected_prof in profs, f"'{expected_prof}' in proficiencies")

    skills = char.get("skills", [])
    check("2.1.j", "perception" in skills, f"'perception' in skills: {skills}")
    check("2.1.k", "stealth" in skills, f"'stealth' in skills: {skills}")
    # Soldier background gives athletics + intimidation
    check("2.1.l", "athletics" in skills, f"'athletics' (soldier) in skills: {skills}")
    check("2.1.m", "intimidation" in skills, f"'intimidation' (soldier) in skills: {skills}")

    world = session.get("world", {})
    check("2.1.n", world.get("turn") == 1, f"turn: {world.get('turn')}")
    check("2.1.o", world.get("location") == "alpine-pass", f"location: {world.get('location')!r}")

    subsection("Test 2.2 — GET /state/{session_id} (verify persistence)")
    r = client.get(f"/state/{session_id}")
    check("2.2.a", r.status_code == 200, f"GET /state/{session_id} → {r.status_code}")
    if r.status_code == 200:
        state = r.json()
        check("2.2.b", state.get("session_id") == session_id, "session_id matches")
        check("2.2.c", len(state.get("log", [])) == 0, f"log starts empty: {state.get('log')}")
        check("2.2.d", state.get("character", {}).get("class") == "ranger", "class persisted")

    subsection("Test 2.3 — GET /location/alpine-pass (GPT loads location before describing)")
    r = client.get("/location/alpine-pass")
    check("2.3.a", r.status_code == 200, f"GET /location/alpine-pass → {r.status_code}")
    if r.status_code == 200:
        loc = r.json()
        check("2.3.b", loc.get("id") == "alpine-pass", f"id: {loc.get('id')!r}")

    return session_id


# ---------------------------------------------------------------------------
# Part 3 — Secondary Session Creation (Elf Wizard, subspecies, no background)
# ---------------------------------------------------------------------------

def test_part3_secondary_session(client: httpx.Client) -> str | None:
    section("PART 3 — Secondary Session (Elf Wizard, subspecies, no background)")

    subsection("Test 3.1 — POST /session/new (elf + subspecies, no background)")
    r = client.post("/session/new", json=SECONDARY_CHARACTER)
    check("3.1.a", r.status_code == 201, f"POST /session/new → {r.status_code} {r.text[:200]}")
    if r.status_code != 201:
        return None

    session = r.json()
    session_id = session.get("session_id")
    char = session.get("character", {})
    vprint("secondary character", char)

    scores = char.get("ability_scores", {})
    hp = char.get("hp", {})

    check("3.1.b", scores == SECONDARY_EXPECTED_SCORES,
          f"ability scores (no background bonuses): {scores}")
    check("3.1.c", hp.get("current") == SECONDARY_EXPECTED_HP and hp.get("max") == SECONDARY_EXPECTED_HP,
          f"HP: {hp} (expected {SECONDARY_EXPECTED_HP})")
    check("3.1.d", char.get("class") == "wizard", f"class: {char.get('class')!r}")
    check("3.1.e", char.get("species") == "elf", f"species: {char.get('species')!r}")
    check("3.1.f", char.get("subspecies") == "elven-lineage-high-elf",
          f"subspecies: {char.get('subspecies')!r}")
    check("3.1.g", char.get("background") is None, f"background is None (no background): {char.get('background')!r}")
    check("3.1.h", char.get("feat") is None, f"feat is None (no background): {char.get('feat')!r}")

    skills = char.get("skills", [])
    check("3.1.i", "arcana" in skills, f"'arcana' in skills: {skills}")
    check("3.1.j", "history" in skills, f"'history' in skills: {skills}")

    return session_id


# ---------------------------------------------------------------------------
# Part 4 — Turn Loop (10 turns, realistic GPT flow)
# ---------------------------------------------------------------------------

def test_part4_turn_loop(client: httpx.Client, session_id: str) -> None:
    section("PART 4 — Turn Loop (10 turns, realistic GPT flow)")

    # Load initial state
    r = client.get(f"/state/{session_id}")
    if r.status_code != 200:
        check("4.setup", False, f"Could not load state: {r.status_code}")
        return

    state = r.json()
    character = state["character"]
    world = state["world"]
    current_hp = character["hp"]["current"]
    max_hp = character["hp"]["max"]
    current_location = world["location"]

    turn_failures = []

    for turn in range(1, 11):
        # Step A: Load location before describing (GPT requirement)
        r_loc = client.get(f"/location/{current_location}")
        if r_loc.status_code != 200:
            turn_failures.append(f"Turn {turn}: GET /location/{current_location} → {r_loc.status_code}")
            continue

        # Step B: Check connections (GPT checks valid movement options)
        r_conn = client.get(f"/location/{current_location}/connections")
        if r_conn.status_code != 200:
            turn_failures.append(f"Turn {turn}: GET /location/{current_location}/connections → {r_conn.status_code}")
            continue

        # Step C: Roll a contested action (DEX check, varying DC)
        dc = 10 + (turn % 6)  # DC cycles 11–16
        r_roll = client.post("/roll", json={
            "dice": "1d20",
            "ability": "DEX",
            "score": PRIMARY_EXPECTED_SCORES["DEX"],
            "proficient": True,
            "dc": dc,
        })
        if r_roll.status_code != 200:
            turn_failures.append(f"Turn {turn}: POST /roll → {r_roll.status_code}")
            continue

        roll_result = r_roll.json()
        success = roll_result["success"]

        # Apply HP delta based on roll
        if roll_result.get("critical_failure"):
            current_hp = max(0, current_hp - 2)
        elif not success:
            current_hp = max(0, current_hp - 1)

        # Step D: Save state with updated turn, HP, and log entry
        updated_character = dict(character)
        updated_character["hp"] = {"current": current_hp, "max": max_hp}

        updated_world = dict(world)
        updated_world["turn"] = turn + 1

        outcome = "critical success" if roll_result.get("critical_success") else \
                  "critical failure" if roll_result.get("critical_failure") else \
                  "success" if success else "failure"
        log_entry = (
            f"Turn {turn}: Aldric attempted a DEX check (DC {dc}) — "
            f"{outcome} (rolled {roll_result['roll']}, total {roll_result['total']}). "
            f"HP: {current_hp}/{max_hp}."
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

        # Verify turn incremented
        saved_turn = saved.get("world", {}).get("turn")
        if saved_turn != turn + 1:
            turn_failures.append(f"Turn {turn}: expected world.turn={turn+1}, got {saved_turn}")

        # Verify log length
        saved_log = saved.get("log", [])
        if len(saved_log) != turn:
            turn_failures.append(f"Turn {turn}: expected {turn} log entries, got {len(saved_log)}")

        # Update local state
        character = saved["character"]
        world = saved["world"]
        current_hp = character["hp"]["current"]

    check("4.loop", len(turn_failures) == 0,
          "All 10 turns completed cleanly" if not turn_failures else f"{len(turn_failures)} turn failures")
    if turn_failures:
        for f in turn_failures[:5]:
            print(f"    → {f}")
        if len(turn_failures) > 5:
            print(f"    → ... and {len(turn_failures) - 5} more")

    # Final state verification
    r = client.get(f"/state/{session_id}")
    check("4.final_state", r.status_code == 200, f"GET /state after 10 turns → {r.status_code}")
    if r.status_code == 200:
        final = r.json()
        final_log = final.get("log", [])
        check("4.log_count", len(final_log) == 10, f"log has {len(final_log)} entries (expected 10)")
        final_turn = final.get("world", {}).get("turn")
        check("4.final_turn", final_turn == 11, f"world.turn = {final_turn} (expected 11)")
        final_hp = final.get("character", {}).get("hp", {})
        check("4.hp_valid", 0 <= final_hp.get("current", -1) <= max_hp,
              f"HP {final_hp.get('current')}/{max_hp} is valid")


# ---------------------------------------------------------------------------
# Part 5 — Session Resume (simulated new conversation)
# ---------------------------------------------------------------------------

def test_part5_session_resume(client: httpx.Client, session_id: str) -> None:
    section("PART 5 — Session Resume (simulated new conversation)")

    subsection("Test 5.1 — Fresh state load")
    r = client.get(f"/state/{session_id}")
    check("5.1.a", r.status_code == 200, f"GET /state/{session_id} → {r.status_code}")
    if r.status_code != 200:
        return

    state = r.json()
    vprint("resumed state", {
        "session_id": state.get("session_id"),
        "turn": state.get("world", {}).get("turn"),
        "log_count": len(state.get("log", [])),
        "hp": state.get("character", {}).get("hp"),
    })

    check("5.1.b", state.get("session_id") == session_id, "session_id matches")
    check("5.1.c", state.get("world", {}).get("turn") == 11, f"turn = {state.get('world', {}).get('turn')} (expected 11)")
    check("5.1.d", len(state.get("log", [])) == 10, f"log has {len(state.get('log', []))} entries (expected 10)")
    check("5.1.e", state.get("character", {}).get("class") == "ranger", "class persisted")
    check("5.1.f", state.get("character", {}).get("background") == "soldier", "background persisted")

    subsection("Test 5.2 — Load location from resumed state")
    current_location = state.get("world", {}).get("location", "alpine-pass")
    r = client.get(f"/location/{current_location}")
    check("5.2.a", r.status_code == 200, f"GET /location/{current_location} → {r.status_code}")
    if r.status_code == 200:
        loc = r.json()
        check("5.2.b", loc.get("id") == current_location, f"location id matches: {loc.get('id')!r}")

    subsection("Test 5.3 — Run one more turn after resume")
    character = state["character"]
    world = state["world"]
    current_hp = character["hp"]["current"]
    max_hp = character["hp"]["max"]

    r_roll = client.post("/roll", json={
        "dice": "1d20",
        "ability": "WIS",
        "score": PRIMARY_EXPECTED_SCORES["WIS"],
        "proficient": False,
        "dc": 12,
    })
    check("5.3.a", r_roll.status_code == 200, f"POST /roll (resume turn) → {r_roll.status_code}")
    if r_roll.status_code != 200:
        return

    roll_result = r_roll.json()
    updated_world = dict(world)
    updated_world["turn"] = 12

    r_save = client.post(f"/state/{session_id}", json={
        "character": character,
        "world": updated_world,
        "log_entry": f"Turn 11 (resumed): Aldric made a WIS check — {'success' if roll_result['success'] else 'failure'}.",
    })
    check("5.3.b", r_save.status_code == 200, f"POST /state (resume turn) → {r_save.status_code}")
    if r_save.status_code == 200:
        saved = r_save.json()
        check("5.3.c", saved.get("world", {}).get("turn") == 12, f"turn = {saved.get('world', {}).get('turn')} (expected 12)")
        check("5.3.d", len(saved.get("log", [])) == 11, f"log has {len(saved.get('log', []))} entries (expected 11)")


# ---------------------------------------------------------------------------
# Part 6 — Edge Cases
# ---------------------------------------------------------------------------

def test_part6_edge_cases(client: httpx.Client) -> None:
    section("PART 6 — Edge Cases")

    subsection("Test 6.1 — HP=0 is accepted (incapacitation)")
    r = client.post("/session/new", json=PRIMARY_CHARACTER)
    if r.status_code == 201:
        sid = r.json()["session_id"]
        char = r.json()["character"]
        char["hp"]["current"] = 0
        r2 = client.post(f"/state/{sid}", json={
            "character": char,
            "world": {"location": "alpine-pass", "threat": "ice drakes", "goal": "survive", "turn": 2},
            "log_entry": "Aldric was struck down by an ice drake and fell unconscious.",
        })
        check("6.1.a", r2.status_code == 200, f"POST /state with hp.current=0 → {r2.status_code} (expected 200)")
        if r2.status_code == 200:
            saved_hp = r2.json().get("character", {}).get("hp", {})
            check("6.1.b", saved_hp.get("current") == 0, f"hp.current=0 persisted: {saved_hp}")
    else:
        results.append(("6.1.a", SKIP, "Could not create session for HP=0 test"))
        print(f"  - [6.1.a] SKIP: Could not create session")

    subsection("Test 6.2 — HP=-1 is rejected (422)")
    r = client.post("/session/new", json=PRIMARY_CHARACTER)
    if r.status_code == 201:
        sid = r.json()["session_id"]
        char = r.json()["character"]
        char["hp"]["current"] = -1
        r2 = client.post(f"/state/{sid}", json={
            "character": char,
            "world": {"location": "alpine-pass", "threat": "none", "goal": "test", "turn": 1},
            "log_entry": "test",
        })
        check("6.2.a", r2.status_code == 422, f"POST /state with hp.current=-1 → {r2.status_code} (expected 422)")
    else:
        results.append(("6.2.a", SKIP, "Could not create session for HP=-1 test"))
        print(f"  - [6.2.a] SKIP: Could not create session")

    subsection("Test 6.3 — Invalid class → 422")
    bad = dict(PRIMARY_CHARACTER)
    bad["class"] = "dragonlord"
    r = client.post("/session/new", json=bad)
    check("6.3.a", r.status_code == 422, f"POST /session/new (bad class) → {r.status_code} (expected 422)")

    subsection("Test 6.4 — Invalid species → 422")
    bad = dict(PRIMARY_CHARACTER)
    bad["species"] = "dragonborn-supreme"
    r = client.post("/session/new", json=bad)
    check("6.4.a", r.status_code == 422, f"POST /session/new (bad species) → {r.status_code} (expected 422)")

    subsection("Test 6.5 — Invalid background → 422")
    bad = dict(PRIMARY_CHARACTER)
    bad["background"] = "nonexistent-background"
    r = client.post("/session/new", json=bad)
    check("6.5.a", r.status_code == 422, f"POST /session/new (bad background) → {r.status_code} (expected 422)")

    subsection("Test 6.6 — Invalid session ID → 404")
    r = client.get("/state/NONEXISTENT_SESSION_XYZ")
    check("6.6.a", r.status_code == 404, f"GET /state/NONEXISTENT → {r.status_code} (expected 404)")

    subsection("Test 6.7 — Invalid location → 404")
    r = client.get("/location/nonexistent-location-xyz")
    check("6.7.a", r.status_code == 404, f"GET /location/nonexistent → {r.status_code} (expected 404)")

    subsection("Test 6.8 — Movement to unconnected location (connections check)")
    # alpine-pass only connects to glacial-stream-crossing — not to a stronghold
    r = client.get("/location/alpine-pass/connections")
    check("6.8.a", r.status_code == 200, f"GET /location/alpine-pass/connections → {r.status_code}")
    if r.status_code == 200:
        conn_data = r.json()
        to_ids = [c["to_id"] for c in conn_data.get("connections", [])]
        check("6.8.b", "stronghold-gates" not in to_ids,
              f"'stronghold-gates' not in alpine-pass connections (correct): {to_ids}")
        check("6.8.c", "glacial-stream-crossing" in to_ids,
              f"'glacial-stream-crossing' in alpine-pass connections: {to_ids}")

    subsection("Test 6.9 — Invalid ability in roll → 422")
    r = client.post("/roll", json={
        "dice": "1d20",
        "ability": "LUCK",
        "score": 15,
        "proficient": False,
        "dc": 10,
    })
    check("6.9.a", r.status_code == 422, f"POST /roll (bad ability) → {r.status_code} (expected 422)")


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
        print(f"\n  FAILED CHECKS:")
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
    global _verbose

    parser = argparse.ArgumentParser(description="Mystic Weave end-to-end test")
    parser.add_argument(
        "--base-url",
        default="https://mysticweave-production.up.railway.app",
        help="API base URL (default: Railway production)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print response bodies for debugging",
    )
    args = parser.parse_args()
    _verbose = args.verbose

    print(f"\nMystic Weave End-to-End Test")
    print(f"Target: {args.base_url}")

    with httpx.Client(base_url=args.base_url, timeout=30.0) as client:
        # Health check
        try:
            r = client.get("/health")
            if r.status_code != 200:
                print(f"\nERROR: API health check failed ({r.status_code}). Is the server running?")
                return 1
            print(f"API is up: {r.json()}")
        except httpx.ConnectError:
            print(f"\nERROR: Cannot connect to {args.base_url}.")
            if "localhost" not in args.base_url:
                print("  Is Railway deployed and running?")
            else:
                print("  Start it with: uvicorn api.main:app --port 8000")
            return 1

        # Run all parts
        setup_ok = test_part1_setup(client)
        if not setup_ok:
            print("\n  FATAL: Setup failed. Aborting.")
            return print_summary()

        primary_session_id = test_part2_primary_session(client)
        test_part3_secondary_session(client)

        if primary_session_id:
            test_part4_turn_loop(client, primary_session_id)
            test_part5_session_resume(client, primary_session_id)
        else:
            print("\n  FATAL: Primary session creation failed. Skipping Parts 4 and 5.")

        test_part6_edge_cases(client)

    return print_summary()


if __name__ == "__main__":
    sys.exit(main())