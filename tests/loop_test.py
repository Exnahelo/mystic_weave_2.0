#!/usr/bin/env python3
"""
loop_test.py — Local API loop test for Mystic Weave 2.0

Tests the full game loop against a running local (or Railway) instance:
  1. Session initialization (options, location seeding, session creation)
  2. State persistence (load, save, log append, new schema fields)
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
    "identity": {
        "origin": "Exiled from Drakenvale after a failed oath",
        "motivations": ["Restore family honour", "Find who ordered the exile"],
        "quirks": ["Speaks in clipped sentences under stress"],
        "bonds": ["The Platinum Flame"],
        "flaws": ["Distrusts mercy in others"],
        "wound": "Watched the exile decree read aloud in the Draconic Hall",
        "alignment": {
            "order": "lawful",
            "intent": "good",
            "ethos_note": "Honour before comfort, but never honour before life",
        },
    },
    "starting_economy": {
        "wealth_tier": "modest",
        "coin": 12,
        "trade_goods": [],
        "obligations": ["Owes a debt to the caravan master who smuggled them out"],
    },
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

    # Core identity fields
    check("1.3.b", char["name"] == "Krath", f"name: {char['name']}")
    check("1.3.c", char["species"] == "dragonborn", f"species: {char['species']}")
    check("1.3.d", char["focus"] == "devoted", f"focus: {char['focus']}")
    check("1.3.e", char["background"] == "soldier", f"background: {char['background']}")
    check("1.3.f", char["hp"]["current"] == 100, f"hp: {char['hp']}")
    check("1.3.g", char["hp"]["max"] == 100, f"max hp: {char['hp']['max']}")

    # Domain scores (dragonborn base + adjustments)
    domains = char["domains"]
    check("1.3.h", domains["presence"] == 55, f"presence: {domains['presence']} (dragonborn primary)")
    check("1.3.i", domains["will"] == 47, f"will: {domains['will']} (45 base + 2 adj)")
    check("1.3.j", domains["endurance"] == 43, f"endurance: {domains['endurance']} (40 base + 3 adj)")

    # Competency tags
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

    # v3.1.0 — identity block
    identity = char.get("identity", {})
    check("1.3.s", isinstance(identity, dict), f"identity block present: {type(identity)}")
    check("1.3.t", identity.get("origin") == "Exiled from Drakenvale after a failed oath",
          f"origin: {identity.get('origin')!r}")
    check("1.3.u", len(identity.get("motivations", [])) == 2,
          f"motivations count: {len(identity.get('motivations', []))}")
    check("1.3.v", len(identity.get("quirks", [])) == 1,
          f"quirks count: {len(identity.get('quirks', []))}")
    alignment = identity.get("alignment", {})
    check("1.3.w", alignment.get("order") == "lawful", f"alignment.order: {alignment.get('order')}")
    check("1.3.x", alignment.get("intent") == "good", f"alignment.intent: {alignment.get('intent')}")

    # v3.1.0 — equipment block
    equipment = char.get("equipment", {})
    check("1.3.y", isinstance(equipment, dict), f"equipment block present: {type(equipment)}")
    check("1.3.z", "worn" in equipment and "carried" in equipment and "stashed" in equipment,
          f"equipment slots: {list(equipment.keys())}")

    # v3.1.0 — reputation block
    reputation = char.get("reputation", [])
    check("1.3.aa", isinstance(reputation, list), f"reputation list present: {type(reputation)}")

    # v3.2.0 — advancement block
    advancement = char.get("advancement", {})
    check("1.3.ab", isinstance(advancement, dict), f"advancement block present: {type(advancement)}")
    check("1.3.ac", advancement.get("points_available") == 0, f"points_available: {advancement.get('points_available')}")
    check("1.3.ad", advancement.get("points_spent") == 0, f"points_spent: {advancement.get('points_spent')}")
    check("1.3.ae", advancement.get("points_earned_total") == 0, f"points_earned_total: {advancement.get('points_earned_total')}")

    # v3.1.0 — world blocks
    world = data["world"]
    check("1.3.af", world["location"] == "test-loc-alpha", f"location: {world['location']}")
    check("1.3.ag", world["turn"] == 1, f"turn: {world['turn']}")
    check("1.3.ah", isinstance(world.get("companions"), list), f"companions list present")
    economy = world.get("economy", {})
    check("1.3.ai", economy.get("wealth_tier") == "modest", f"wealth_tier: {economy.get('wealth_tier')}")
    check("1.3.aj", economy.get("coin") == 12, f"coin: {economy.get('coin')}")
    check("1.3.ak", len(economy.get("obligations", [])) == 1,
          f"obligations: {len(economy.get('obligations', []))}")
    politics = world.get("politics", {})
    check("1.3.al", isinstance(politics, dict), f"politics block present: {type(politics)}")
    check("1.3.am", politics.get("legal_standing") == "unknown",
          f"legal_standing: {politics.get('legal_standing')}")

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
        # v3.1.0 — new blocks survive round-trip load
        check("2.1.e", isinstance(state["character"].get("identity"), dict), f"identity persisted")
        check("2.1.f", isinstance(state["character"].get("equipment"), dict), f"equipment persisted")
        check("2.1.g", isinstance(state["character"].get("reputation"), list), f"reputation persisted")
        check("2.1.h", isinstance(state["character"].get("advancement"), dict), f"advancement persisted")
        check("2.1.i", isinstance(state["world"].get("companions"), list), f"companions persisted")
        check("2.1.j", isinstance(state["world"].get("economy"), dict), f"economy persisted")
        check("2.1.k", isinstance(state["world"].get("politics"), dict), f"politics persisted")

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
            "knowledge": {
                "discipline": 2, "courage": 1, "command": 1,
                "intimidation": 1, "exertion": 1,
            },
            "application": {
                "sacred_rites": 1, "shields_armor": 1, "heavy_weapons": 1,
            },
            "status_effects": [],
            "notes": "",
            # v3.1.0 fields
            "identity": {
                "origin": "Exiled from Drakenvale after a failed oath",
                "motivations": ["Restore family honour", "Find who ordered the exile"],
                "quirks": ["Speaks in clipped sentences under stress"],
                "bonds": ["The Platinum Flame"],
                "flaws": ["Distrusts mercy in others"],
                "wound": "Watched the exile decree read aloud in the Draconic Hall",
                "alignment": {
                    "order": "lawful",
                    "intent": "good",
                    "ethos_note": "Honour before comfort, but never honour before life",
                },
            },
            "equipment": {
                "worn": [
                    {
                        "id": "item_001",
                        "name": "Battered plate armour",
                        "description": "Dented but functional. Bears the mark of the Dragon Guard.",
                        "tags": ["armor"],
                        "roll_tag": "shields_armor",
                    }
                ],
                "carried": [],
                "stashed": [],
            },
            "reputation": [
                {
                    "faction": "draconic_council",
                    "standing": -40,
                    "note": "Exiled by Council decree",
                    "last_change": "Exile ordered at turn 0",
                },
                {
                    "faction": "dragon_guard",
                    "standing": -20,
                    "note": "Former member, left under a cloud",
                    "last_change": "Departed at exile",
                },
            ],
            "advancement": {
                "points_available": 1,
                "points_spent": 0,
                "points_earned_total": 1,
            },
        },
        "world": {
            "location": "test-loc-alpha",
            "threat": "patrol spotted",
            "goal": "test the loop",
            "turn": 2,
            # v3.1.0 fields
            "companions": [
                {
                    "id": "companion_001",
                    "name": "Sorra",
                    "species": "halfling",
                    "role": "guide",
                    "identity": {
                        "origin": "",
                        "motivations": ["Stay alive"],
                        "quirks": ["Never walks in straight lines"],
                        "bonds": [],
                        "flaws": [],
                        "wound": "",
                        "alignment": {
                            "order": "neutral",
                            "intent": "neutral",
                            "ethos_note": "",
                        },
                    },
                    "hp": {"current": 100, "max": 100},
                    "domains": None,
                    "knowledge": {},
                    "application": {},
                    "status": "active",
                    "disposition": 30,
                    "reputation": [],
                }
            ],
            "economy": {
                "wealth_tier": "modest",
                "coin": 7,
                "trade_goods": [],
                "obligations": ["Owes a debt to the caravan master who smuggled them out"],
            },
            "politics": {
                "faction_memberships": [],
                "active_obligations": [],
                "legal_standing": "exile",
                "known_leverage": [],
                "active_tensions": ["Dragon Guard patrol active in the region"],
                "conclave_status": "unknown",
            },
        },
        "log_entry": "Krath took 15 damage from a patrol ambush and spotted a Dragon Guard patrol.",
    }
    r = client.post(f"/state/{session_id}", json=save_body)
    check("2.2.a", r.status_code == 200, f"POST /state → {r.status_code}")
    if r.status_code == 200:
        state = r.json()
        char = state["character"]
        world = state["world"]

        # Core fields
        check("2.2.b", char["hp"]["current"] == 85, f"hp saved: {char['hp']['current']}")
        check("2.2.c", len(state["log"]) == 1, f"log has 1 entry")
        check("2.2.d", world["turn"] == 2, f"turn: {world['turn']}")

        # v3.1.0 — identity round-trip
        check("2.2.e", char.get("identity", {}).get("alignment", {}).get("order") == "lawful",
              f"alignment.order round-trips")

        # v3.1.0 — equipment round-trip
        worn = char.get("equipment", {}).get("worn", [])
        check("2.2.f", len(worn) == 1, f"worn item count: {len(worn)}")
        check("2.2.g", worn[0]["name"] == "Battered plate armour", f"worn item name: {worn[0]['name']}")
        check("2.2.h", worn[0]["roll_tag"] == "shields_armor", f"roll_tag: {worn[0]['roll_tag']}")

        # v3.1.0 — reputation round-trip
        rep = char.get("reputation", [])
        check("2.2.i", len(rep) == 2, f"reputation entries: {len(rep)}")
        council_rep = next((e for e in rep if e["faction"] == "draconic_council"), None)
        check("2.2.j", council_rep is not None, f"draconic_council entry present")
        check("2.2.k", council_rep["standing"] == -40 if council_rep else False,
              f"council standing: {council_rep['standing'] if council_rep else 'missing'}")

        # v3.2.0 — advancement round-trip
        advancement = char.get("advancement", {})
        check("2.2.l", advancement.get("points_available") == 1,
              f"points_available: {advancement.get('points_available')}")
        check("2.2.m", advancement.get("points_spent") == 0,
              f"points_spent: {advancement.get('points_spent')}")
        check("2.2.n", advancement.get("points_earned_total") == 1,
              f"points_earned_total: {advancement.get('points_earned_total')}")

        # v3.1.0 — companions round-trip
        companions = world.get("companions", [])
        check("2.2.o", len(companions) == 1, f"companion count: {len(companions)}")
        sorra = companions[0]
        check("2.2.p", sorra["name"] == "Sorra", f"companion name: {sorra['name']}")
        check("2.2.q", sorra["status"] == "active", f"companion status: {sorra['status']}")
        check("2.2.r", sorra["disposition"] == 30, f"companion disposition: {sorra['disposition']}")

        # v3.1.0 — economy round-trip
        economy = world.get("economy", {})
        check("2.2.s", economy.get("coin") == 7, f"coin: {economy.get('coin')}")
        check("2.2.t", economy.get("wealth_tier") == "modest", f"wealth_tier: {economy.get('wealth_tier')}")

        # v3.1.0 — politics round-trip
        politics = world.get("politics", {})
        check("2.2.u", politics.get("legal_standing") == "exile",
              f"legal_standing: {politics.get('legal_standing')}")
        check("2.2.v", len(politics.get("active_tensions", [])) == 1,
              f"active_tensions: {len(politics.get('active_tensions', []))}")

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
        expected_margin = 65 - result["roll"]
        check("3.1.i", result["margin"] == expected_margin,
              f"margin={result['margin']} == 65 - {result['roll']} = {expected_margin}")

    subsection("Test 3.2 — Target clamping")
    r = client.post("/roll", json={"target": 150})
    check("3.2.a", r.status_code == 200, f"POST /roll (target=150) → {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        check("3.2.b", result["target"] == 99, f"target clamped to 99: {result['target']}")

    r = client.post("/roll", json={"target": 0})
    check("3.2.c", r.status_code == 200, f"POST /roll (target=0) → {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        check("3.2.d", result["target"] == 1, f"target clamped to 1: {result['target']}")

    subsection("Test 3.3 — Degree of success bands")
    # Roll 1 must be critical success
    r = client.post("/roll", json={"target": 50})
    if r.status_code == 200:
        result = r.json()
        if result["roll"] == 1:
            check("3.3.a", result["degree"] == "critical_success", f"roll=1 → critical_success")
            check("3.3.b", result["critical_success"] is True, f"critical_success flag True")
        if result["roll"] == 100:
            check("3.3.c", result["degree"] == "critical_failure", f"roll=100 → critical_failure")
            check("3.3.d", result["critical_failure"] is True, f"critical_failure flag True")


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
        "identity": {
            "origin": "Grew up picking pockets in the harbour district",
            "motivations": ["Buy her brother's freedom"],
            "quirks": ["Counts exits before sitting down"],
            "bonds": [],
            "flaws": ["Lies reflexively"],
            "wound": "",
            "alignment": {
                "order": "chaotic",
                "intent": "neutral",
                "ethos_note": "",
            },
        },
    })
    check("5.1.a", r.status_code == 200, f"POST /character/create → {r.status_code}")
    if r.status_code == 200:
        char = r.json()["character"]
        check("5.1.b", char["name"] == "Thalia", f"name: {char['name']}")
        check("5.1.c", char["species"] == "elf", f"species: {char['species']}")
        check("5.1.d", char["domains"]["agility"] == 58, f"agility: {char['domains']['agility']} (55+3)")

        # Stalker + Criminal both grant lockpicking_traps → stacks to T2
        app_tags = char.get("application", {})
        check("5.1.e", app_tags.get("lockpicking_traps") == 2,
              f"lockpicking_traps stacked to T2: {app_tags.get('lockpicking_traps')}")

        # v3.1.0 — identity survives re-seed
        identity = char.get("identity", {})
        check("5.1.f", isinstance(identity, dict), f"identity block present after re-seed")
        check("5.1.g", identity.get("alignment", {}).get("order") == "chaotic",
              f"alignment.order: {identity.get('alignment', {}).get('order')}")
        check("5.1.h", len(identity.get("motivations", [])) == 1,
              f"motivations: {identity.get('motivations')}")

        # v3.1.0 — equipment and reputation seeded empty
        check("5.1.i", char.get("equipment") == {"worn": [], "carried": [], "stashed": []},
              f"equipment empty on re-seed")
        check("5.1.j", char.get("reputation") == [],
              f"reputation empty on re-seed")
        check("5.1.k", char.get("advancement") == {"points_available": 0, "points_spent": 0, "points_earned_total": 0},
              f"advancement initialized on re-seed")


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

    subsection("Test 6.5 — Negative coin rejected")
    r = client.post("/session/new", json={
        "character_name": "Broke",
        "species": "human",
        "focus": "champion",
        "background": "soldier",
        "starting_economy": {"wealth_tier": "modest", "coin": -5},
    })
    check("6.5.a", r.status_code == 422, f"negative coin → {r.status_code}")

    subsection("Test 6.6 — Invalid wealth tier rejected")
    r = client.post("/session/new", json={
        "character_name": "Rich",
        "species": "human",
        "focus": "champion",
        "background": "soldier",
        "starting_economy": {"wealth_tier": "billionaire", "coin": 0},
    })
    check("6.6.a", r.status_code == 422, f"invalid wealth_tier → {r.status_code}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"\nMystic Weave 2.0 — Loop Test")
    print(f"Target: {BASE_URL}\n")

    with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
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