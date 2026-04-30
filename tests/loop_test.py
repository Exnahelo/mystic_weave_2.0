#!/usr/bin/env python3
"""
loop_test.py — Local API loop test for Mystic Weave 2.0

Tests the full game loop against a running local (or Railway) instance:
  1. Session initialization (options, location seeding, session creation)
  2. State persistence (load, save, log append, new schema fields)
  3. Dice resolution (d100 roll-under, degree of success, criticals)
  4. Location graph (create, retrieve, connections, discovery)
  5. Character re-seeding
  6. Edge cases (invalid ancestry, bad session, hp=0)

Usage:
    # Against local server
    python -m tests.loop_test

    # Against Railway
    python -m tests.loop_test https://mysticweave-production.up.railway.app
"""

from __future__ import annotations

import sys

import httpx

from tests.helpers import zero_advancement

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
    "ancestry": "drakari",
    "culture": "drakenvale_city",
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
        "coin": 1200,
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

def part1(client: httpx.Client) -> str | None:
    """Returns session_id on success, None on failure."""
    section("PART 1 — Session Initialization")
    session_id = None

    subsection("Test 1.1 — GET /options")
    r = client.get("/options")
    check("1.1.a", r.status_code == 200, f"GET /options → {r.status_code}")
    if r.status_code == 200:
        opts = r.json()
        check("1.1.b", len(opts.get("ancestries", [])) == 8, f"ancestries count: {len(opts.get('ancestries', []))}")
        check("1.1.ba", len(opts.get("cultures", [])) >= 1, f"cultures count: {len(opts.get('cultures', []))}")
        check("1.1.c", len(opts.get("focus", [])) == 9, f"focus count: {len(opts.get('focus', []))}")
        check("1.1.d", len(opts.get("backgrounds", [])) == 8, f"backgrounds count: {len(opts.get('backgrounds', []))}")
        check("1.1.da", set(opts.keys()) == {"ancestries", "cultures", "focus", "backgrounds"}, f"/options keys: {sorted(opts.keys())}")
        ancestry_indices = [s["index"] for s in opts.get("ancestries", [])]
        check("1.1.e", "drakari" in ancestry_indices, "'drakari' in ancestries")
        check("1.1.f", "human" in ancestry_indices, "'human' in ancestries")
        culture_indices = [c["index"] for c in opts.get("cultures", [])]
        check("1.1.fa", "drakenvale_city" in culture_indices, "'drakenvale_city' in cultures")
        focus_indices = [f["index"] for f in opts.get("focus", [])]
        check("1.1.g", "devoted" in focus_indices, "'devoted' in focus")
        bg_indices = [b["index"] for b in opts.get("backgrounds", [])]
        check("1.1.h", "soldier" in bg_indices, "'soldier' in backgrounds")

    subsection("Test 1.1b — GET /catalog/items")
    magical_r = client.get("/catalog/items", params={"kind": "magical"})
    check("1.1b.a", magical_r.status_code == 200, f"GET /catalog/items?kind=magical → {magical_r.status_code}")
    apparel_r = client.get("/catalog/items", params={"kind": "apparel"})
    check("1.1b.b", apparel_r.status_code == 200, f"GET /catalog/items?kind=apparel → {apparel_r.status_code}")
    if magical_r.status_code == 200:
        magical_payload = magical_r.json()
        magical_item_names = [item.get("name") for item in magical_payload.get("magical_items", [])]
        check("1.1b.c", ("Blessed Water" in magical_item_names) or ("Holy Water" in magical_item_names), "Blessed Water or Holy Water present in catalog magical")
    if apparel_r.status_code == 200:
        apparel_payload = apparel_r.json()
        apparel_item_names = [item.get("name") for item in apparel_payload.get("apparel_items", [])]
        check("1.1b.d", "Common Clothes" in apparel_item_names, "Common Clothes present in catalog apparel")

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
    check("1.3.c", char["ancestry"] == "drakari", f"ancestry: {char['ancestry']}")
    check("1.3.ca", char["culture"] == "drakenvale_city", f"culture: {char['culture']}")
    check("1.3.d", char["focus"] == "devoted", f"focus: {char['focus']}")
    check("1.3.e", char["background"] == "soldier", f"background: {char['background']}")
    check("1.3.f", char["hp"]["current"] == 100, f"hp: {char['hp']}")
    check("1.3.g", char["hp"]["max"] == 100, f"max hp: {char['hp']['max']}")

    # Domain scores and seeded tags (current ancestry/culture/focus/background stack)
    domains = char["domains"]
    check("1.3.h", domains["presence"] == 53, f"presence: {domains['presence']}")
    check("1.3.i", domains["will"] == 53, f"will: {domains['will']}")
    check("1.3.j", domains["endurance"] == 46, f"endurance: {domains['endurance']}")

    # Competency tags
    knowledge = char.get("knowledge", {})
    application = char.get("application", {})
    check("1.3.k", knowledge.get("discipline") == 2, f"discipline K2: {knowledge.get('discipline')}")
    check("1.3.l", knowledge.get("lore") == 1, f"lore K1: {knowledge.get('lore')}")
    check("1.3.m", knowledge.get("influence") == 1, f"influence K1: {knowledge.get('influence')}")
    check("1.3.n", application.get("command") == 1, f"command A1: {application.get('command')}")
    check("1.3.o", application.get("courage") == 1, f"courage A1: {application.get('courage')}")

    check("1.3.p", char.get("fields", {}).get("sacred") == 1, f"sacred field T1: {char.get('fields', {}).get('sacred')}")
    check("1.3.q", knowledge.get("medium_armor") == 1, f"medium_armor K1: {knowledge.get('medium_armor')}")
    check("1.3.r", knowledge.get("melee") == 1, f"melee K1: {knowledge.get('melee')}")

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
    check("1.3.ac", advancement.get("points_available_earned") == zero_advancement()["points_available_earned"], f"points_available_earned: {advancement.get('points_available_earned')}")
    check("1.3.ad", advancement.get("points_spent") == 0, f"points_spent: {advancement.get('points_spent')}")
    check("1.3.ae", advancement.get("points_earned_total") == 0, f"points_earned_total: {advancement.get('points_earned_total')}")
    check("1.3.af0", advancement.get("points_available_awarded") == 0, f"points_available_awarded: {advancement.get('points_available_awarded')}")
    check("1.3.af1", advancement.get("tag_advance_counters") == zero_advancement()["tag_advance_counters"], f"tag_advance_counters: {advancement.get('tag_advance_counters')}")

    # v3.1.0 — world blocks
    world = data["world"]
    check("1.3.af", world["location"] == "test-loc-alpha", f"location: {world['location']}")
    check("1.3.ag", world["turn"] == 1, f"turn: {world['turn']}")
    check("1.3.ah", isinstance(world.get("companions"), list), "companions list present")
    economy = world.get("economy", {})
    check("1.3.ai", economy.get("wealth_tier") == "modest", f"wealth_tier: {economy.get('wealth_tier')}")
    check("1.3.aj", economy.get("coin") == 1200, f"coin: {economy.get('coin')}")
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

def part2(client: httpx.Client, session_id: str) -> None:
    section("PART 2 — State Persistence")
    companion_id: str | None = None
    second_companion_id: str | None = None
    handler_id = "krath"
    wolf_template: dict | None = None

    subsection("Test 2.1 — GET /state/{session_id}")
    r = client.get(f"/state/{session_id}")
    check("2.1.a", r.status_code == 200, f"GET /state → {r.status_code}")
    if r.status_code == 200:
        state = r.json()
        check("2.1.b", state["session_id"] == session_id, "session_id matches")
        check("2.1.c", state["character"]["name"] == "Krath", "character loaded")
        check("2.1.d", len(state["log"]) == 0, f"log empty: {len(state['log'])}")
        # v3.1.0 — new blocks survive round-trip load
        check("2.1.e", isinstance(state["character"].get("identity"), dict), "identity persisted")
        check("2.1.f", isinstance(state["character"].get("equipment"), dict), "equipment persisted")
        check("2.1.g", isinstance(state["character"].get("reputation"), list), "reputation persisted")
        check("2.1.h", isinstance(state["character"].get("advancement"), dict), "advancement persisted")
        check("2.1.i", isinstance(state["world"].get("companions"), list), "companions persisted")
        check("2.1.j", isinstance(state["world"].get("economy"), dict), "economy persisted")
        check("2.1.k", isinstance(state["world"].get("politics"), dict), "politics persisted")
    subsection("Test 2.1b — Companion lifecycle")
    catalog_resp = client.get("/catalog/creatures")
    check("2.1b.a", catalog_resp.status_code == 200, f"GET /catalog/creatures → {catalog_resp.status_code}")
    if catalog_resp.status_code == 200:
        creature_catalog = catalog_resp.json().get("creature_catalog", [])
        wolf_template = next((c for c in creature_catalog if c.get("subspecies") == "moonthorn_wolf"), None)
        check("2.1b.b", wolf_template is not None, "moonthorn_wolf present in /catalog/creatures")

    if wolf_template is not None:
        base_hp = wolf_template["base_hp"]
        creature_payload = {
            "name": "Shadowmere",
            "species": wolf_template["species"],
            "subtype": wolf_template["subspecies"],
            "size": wolf_template["size"],
            "age_category": wolf_template["age_category"],
            "tactical_roles": wolf_template["tactical_roles_defaults"],
            "training_level": "trained",
            "bond_level": "bonded",
            "natural_abilities": wolf_template["natural_abilities"],
            "learned_commands": ["heel"],
            "command_notes": "Reliable on familiar roads.",
            "movement_modes": wolf_template["movement_modes"],
            "natural_weapons": wolf_template["natural_weapons"],
            "carrying_capacity": wolf_template["carrying_capacity"],
            "hp": base_hp,
            "domains": wolf_template["base_domains"],
            "temperament": wolf_template["temperament"],
            "bond_links": {"primary": handler_id},
        }

        create_resp = client.post(
            "/companion/new",
            json={
                "session_id": session_id,
                "handler_id": handler_id,
                "tier": "creature",
                "companion": creature_payload,
            },
        )
        check("2.1b.c", create_resp.status_code == 201, f"POST /companion/new → {create_resp.status_code}")
        if create_resp.status_code == 201:
            created = create_resp.json()
            companion_id = created["companion_id"]
            check("2.1b.d", companion_id == f"{handler_id}_moonthorn_wolf", f"companion_id format: {companion_id}")

        invalid_handler_resp = client.post(
            "/companion/new",
            json={
                "session_id": session_id,
                "handler_id": "not_krath",
                "tier": "creature",
                "companion": creature_payload,
            },
        )
        check("2.1b.e", invalid_handler_resp.status_code == 409, f"invalid handler_id rejected → {invalid_handler_resp.status_code}")

        second_resp = client.post(
            "/companion/new",
            json={
                "session_id": session_id,
                "handler_id": handler_id,
                "tier": "creature",
                "companion": {**creature_payload, "name": "Shadowmere II"},
            },
        )
        check("2.1b.f", second_resp.status_code == 201, f"second same-subspecies companion → {second_resp.status_code}")
        if second_resp.status_code == 201:
            second_companion_id = second_resp.json()["companion_id"]
            check("2.1b.g", second_companion_id == f"{handler_id}_moonthorn_wolf_2", f"collision suffix id: {second_companion_id}")

        if companion_id is not None:
            get_resp = client.get(f"/companion/{companion_id}", params={"session_id": session_id})
            check("2.1b.h", get_resp.status_code == 200, f"GET /companion/{{id}} → {get_resp.status_code}")
            if get_resp.status_code == 200:
                got = get_resp.json()
                check("2.1b.i", got["companion_id"] == companion_id, f"fetched companion_id matches: {got['companion_id']}")
                check("2.1b.j", got["archived"] is False, "include_archived=false returns active record")

            state_for_delta = client.get(f"/state/{session_id}")
            check("2.1b.k", state_for_delta.status_code == 200, f"GET /state before companion delta → {state_for_delta.status_code}")
            if state_for_delta.status_code == 200:
                state_payload = state_for_delta.json()
                updated_companions = state_payload["world"]["companions"]
                target = next((entry for entry in updated_companions if entry["id"] == companion_id), None)
                if target is not None:
                    target["hp"]["current"] = target["hp"]["current"] - 2
                delta_resp = client.post(
                    f"/state/{session_id}/delta",
                    json={
                        "world": {"companions": updated_companions},
                        "log_entry": "Shadowmere took 2 damage in a scouting mishap.",
                    },
                )
                check("2.1b.l", delta_resp.status_code == 200, f"POST /state/{{session_id}}/delta companion update → {delta_resp.status_code}")
                if delta_resp.status_code == 200:
                    delta_world = delta_resp.json()["world"]
                    updated = next((entry for entry in delta_world["companions"] if entry["id"] == companion_id), None)
                    check("2.1b.m", updated is not None, "updated companion still present after delta")
                    if updated is not None:
                        check("2.1b.n", updated["hp"]["current"] == base_hp["current"] - 2,
                              f"companion hp updated via delta: {updated['hp']['current']}")

            transition_payload = {
                "name": "Shadowmere",
                "species": wolf_template["species"],
                "subtype": wolf_template["subspecies"],
                "size": wolf_template["size"],
                "age_category": wolf_template["age_category"],
                "tactical_roles": wolf_template["tactical_roles_defaults"],
                "training_level": "trained",
                "bond_level": "bonded",
                "natural_abilities": wolf_template["natural_abilities"],
                "learned_commands": ["heel"],
                "command_notes": "Now reacts to strange light.",
                "movement_modes": wolf_template["movement_modes"],
                "natural_weapons": wolf_template["natural_weapons"],
                "carrying_capacity": wolf_template["carrying_capacity"],
                "hp": {"current": base_hp["current"] - 2, "max": base_hp["max"]},
                "domains": wolf_template["base_domains"],
                "temperament": wolf_template["temperament"],
                "bond_links": {"primary": handler_id},
                "exceptional_profile": {
                    "sapience": "partial",
                    "communication": "instinctive",
                    "autonomy": "moderate",
                },
                "motivations": ["Protect Krath"],
                "supernatural_traits": ["heartstone_awakened"],
                "tier_history": [],
            }
            transition_resp = client.post(
                f"/companion/{companion_id}/transition",
                json={
                    "session_id": session_id,
                    "new_companion": transition_payload,
                    "trigger": "Awakened during contact with the Heartstone",
                },
            )
            check("2.1b.o", transition_resp.status_code == 200, f"POST /companion/{{id}}/transition → {transition_resp.status_code}")
            if transition_resp.status_code == 200:
                transitioned = transition_resp.json()
                check("2.1b.p", transitioned["companion_id"] == companion_id, f"transition preserves companion_id: {transitioned['companion_id']}")

            post_transition_get = client.get(f"/companion/{companion_id}", params={"session_id": session_id})
            check("2.1b.q", post_transition_get.status_code == 200, f"GET transitioned companion → {post_transition_get.status_code}")
            if post_transition_get.status_code == 200:
                exceptional = post_transition_get.json()
                tier_history = exceptional["companion"].get("tier_history", [])
                check("2.1b.r", len(tier_history) == 1, f"tier_history entry count: {len(tier_history)}")
                if tier_history:
                    check("2.1b.s", tier_history[0]["from_tier"] == "creature", f"from_tier: {tier_history[0]['from_tier']}")
                    check("2.1b.t", tier_history[0]["to_tier"] == "exceptional", f"to_tier: {tier_history[0]['to_tier']}")
                    check("2.1b.u", bool(tier_history[0].get("trigger")), "transition trigger recorded")

            state_after_transition = client.get(f"/state/{session_id}")
            check("2.1b.v", state_after_transition.status_code == 200, f"GET /state after transition → {state_after_transition.status_code}")
            if state_after_transition.status_code == 200:
                world_after = state_after_transition.json()["world"]
                archive = world_after.get("companion_archive", [])
                check("2.1b.w", len(archive) == 1, f"world.companion_archive count: {len(archive)}")
                if archive:
                    check("2.1b.x", archive[0]["id"] == companion_id, "archived record id matches transitioned companion")

            already_exceptional_resp = client.post(
                f"/companion/{companion_id}/transition",
                json={
                    "session_id": session_id,
                    "new_companion": transition_payload,
                    "trigger": "Second invalid transition",
                },
            )
            check("2.1b.y", already_exceptional_resp.status_code == 422, f"transition on exceptional rejected → {already_exceptional_resp.status_code}")

            missing_transition_resp = client.post(
                "/companion/nonexistent_id/transition",
                json={
                    "session_id": session_id,
                    "new_companion": transition_payload,
                    "trigger": "Missing companion",
                },
            )
            check("2.1b.z", missing_transition_resp.status_code == 404, f"transition nonexistent companion → {missing_transition_resp.status_code}")

    subsection("Test 2.2 — POST /state/{session_id} (save + log)")
    save_body = {
        "character": {
            "name": "Krath",
            "ancestry": "drakari",
            "culture": "drakenvale_city",
            "focus": "devoted",
            "background": "soldier",
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
                "sacred_rites": 1, "shields_armor": 1, "melee": 1,
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
                "points_available_earned": {
                    **zero_advancement()["points_available_earned"],
                    "power": 1,
                },
                "points_available_awarded": 0,
                "points_spent": 0,
                "points_earned_total": 1,
                "tag_advance_counters": zero_advancement()["tag_advance_counters"],
            },
        },
        "world": {
            "location": "test-loc-alpha",
            "threat": "patrol spotted",
            "goal": "test the loop",
            "turn": 2,
            # v3.1.0 fields
                "companions": [],
                "companion_archive": [],
            "economy": {
                "wealth_tier": "modest",
                "coin": 700,
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
            "time": {
                "day": 1,
                "month": "Verdantrise",
                "year": 847,
                "time_of_day": "afternoon",
                "season": "spring",
                "festival": None,
                "weather": "clear",
                "weather_note": "",
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
        check("2.2.c", len(state["log"]) >= 1, f"log has {len(state['log'])} entries")
        check("2.2.d", world["turn"] == 2, f"turn: {world['turn']}")

        # v3.1.0 — identity round-trip
        check("2.2.e", char.get("identity", {}).get("alignment", {}).get("order") == "lawful",
              "alignment.order round-trips")

        # v3.1.0 — equipment round-trip
        worn = char.get("equipment", {}).get("worn", [])
        check("2.2.f", len(worn) == 1, f"worn item count: {len(worn)}")
        check("2.2.g", worn[0]["name"] == "Battered plate armour", f"worn item name: {worn[0]['name']}")
        check("2.2.h", worn[0]["roll_tag"] == "shields_armor", f"roll_tag: {worn[0]['roll_tag']}")

        # v3.1.0 — reputation round-trip
        rep = char.get("reputation", [])
        check("2.2.i", len(rep) == 2, f"reputation entries: {len(rep)}")
        council_rep = next((e for e in rep if e["faction"] == "draconic_council"), None)
        check("2.2.j", council_rep is not None, "draconic_council entry present")
        check("2.2.k", council_rep["standing"] == -40 if council_rep else False,
              f"council standing: {council_rep['standing'] if council_rep else 'missing'}")

        # v3.2.0 — advancement round-trip
        advancement = char.get("advancement", {})
        check("2.2.l", advancement.get("points_available_earned", {}).get("power") == 1,
              f"points_available_earned.power: {advancement.get('points_available_earned', {}).get('power')}")
        check("2.2.m", advancement.get("points_spent") == 0,
              f"points_spent: {advancement.get('points_spent')}")
        check("2.2.n", advancement.get("points_earned_total") == 1,
              f"points_earned_total: {advancement.get('points_earned_total')}")
        check("2.2.na", advancement.get("points_available_awarded") == 0,
              f"points_available_awarded: {advancement.get('points_available_awarded')}")

        # v3.1.0 — companions round-trip
        companions = world.get("companions", [])
        check("2.2.o", len(companions) == 0, f"full save can carry empty companions list: {len(companions)}")
        check("2.2.p", isinstance(world.get("companion_archive"), list), "companion_archive round-trips as a list")

        # v3.1.0 — economy round-trip
        economy = world.get("economy", {})
        check("2.2.s", economy.get("coin") == 700, f"coin: {economy.get('coin')}")
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

def part3(client: httpx.Client) -> None:
    section("PART 3 — Dice Resolution (d100 Roll-Under)")

    subsection("Test 3.1 — Basic d100 roll")
    r = client.post("/roll", json={"target": 65})
    check("3.1.a", r.status_code == 200, f"POST /roll → {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        check("3.1.b", "roll" in result, "'roll' in response")
        check("3.1.c", "target" in result, "'target' in response")
        check("3.1.d", "success" in result, "'success' in response")
        check("3.1.e", "degree" in result, "'degree' in response")
        check("3.1.f", "margin" in result, "'margin' in response")
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
            check("3.3.a", result["degree"] == "critical_success", "roll=1 → critical_success")
            check("3.3.b", result["critical_success"] is True, "critical_success flag True")
        if result["roll"] == 100:
            check("3.3.c", result["degree"] == "critical_failure", "roll=100 → critical_failure")
            check("3.3.d", result["critical_failure"] is True, "critical_failure flag True")


# ---------------------------------------------------------------------------
# Part 4 — Location Graph
# ---------------------------------------------------------------------------

def part4(client: httpx.Client) -> None:
    section("PART 4 — Location Graph")

    subsection("Test 4.1 — GET /location/{location_id}")
    r = client.get("/location/test-loc-alpha")
    check("4.1.a", r.status_code == 200, f"GET /location/test-loc-alpha → {r.status_code}")
    if r.status_code == 200:
        loc = r.json()
        check("4.1.b", loc["name"] == "Test Location Alpha", f"name: {loc['name']}")

    subsection("Test 4.2 — GET /location/{location_id}/connections")
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

def part5(client: httpx.Client, session_id: str) -> None:
    section("PART 5 — Character Re-seeding")

    subsection("Test 5.1 — POST /character/create")
    r = client.post("/character/create", json={
        "session_id": session_id,
        "name": "Thalia",
        "ancestry": "elf",
        "culture": "drakenvale_city",
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
        check("5.1.c", char["ancestry"] == "elf", f"ancestry: {char['ancestry']}")
        check("5.1.ca", char["culture"] == "drakenvale_city", f"culture: {char['culture']}")
        check("5.1.d", char["domains"]["agility"] == 62, f"agility: {char['domains']['agility']}")

        # Stalker + Criminal both grant lockpicking_traps → stacks to T2
        app_tags = char.get("application", {})
        check("5.1.e", app_tags.get("lockpicking_traps") == 2,
              f"lockpicking_traps stacked to T2: {app_tags.get('lockpicking_traps')}")

        # v3.1.0 — identity survives re-seed
        identity = char.get("identity", {})
        check("5.1.f", isinstance(identity, dict), "identity block present after re-seed")
        check("5.1.g", identity.get("alignment", {}).get("order") == "chaotic",
              f"alignment.order: {identity.get('alignment', {}).get('order')}")
        check("5.1.h", len(identity.get("motivations", [])) == 1,
              f"motivations: {identity.get('motivations')}")

        # v3.1.0 — equipment and reputation seeded empty
        check("5.1.i", char.get("equipment") == {"worn": [], "carried": [], "stashed": []},
              "equipment empty on re-seed")
        check("5.1.j", char.get("reputation") == [],
              "reputation empty on re-seed")
        check("5.1.k", char.get("advancement") == zero_advancement(),
              "advancement initialized on re-seed")


# ---------------------------------------------------------------------------
# Part 6 — Edge Cases
# ---------------------------------------------------------------------------

def part6(client: httpx.Client) -> None:
    section("PART 6 — Edge Cases")

    subsection("Test 6.1 — Invalid ancestry")
    r = client.post("/session/new", json={
        "character_name": "Bad",
        "ancestry": "goblin",
        "culture": "drakenvale_city",
        "focus": "devoted",
        "background": "soldier",
    })
    check("6.1.a", r.status_code == 422, f"invalid ancestry → {r.status_code}")

    subsection("Test 6.2 — Invalid focus")
    r = client.post("/session/new", json={
        "character_name": "Bad",
        "ancestry": "human",
        "culture": "drakenvale_city",
        "focus": "wizard",
        "background": "soldier",
    })
    check("6.2.a", r.status_code == 422, f"invalid focus → {r.status_code}")

    subsection("Test 6.3 — Adjustment points exceed total pool")
    r = client.post("/session/new", json={
        "character_name": "Bad",
        "ancestry": "human",
        "culture": "drakenvale_city",
        "focus": "champion",
        "background": "soldier",
        "adjustment_points": {"power": 5, "endurance": 5, "will": 1},
    })
    check("6.3.a", r.status_code == 422, f"excess total adjustment → {r.status_code}")

    subsection("Test 6.4 — Character create for nonexistent session")
    r = client.post("/character/create", json={
        "session_id": "nonexistent",
        "name": "Ghost",
        "ancestry": "human",
        "culture": "drakenvale_city",
        "focus": "champion",
        "background": "soldier",
    })
    check("6.4.a", r.status_code == 404, f"nonexistent session → {r.status_code}")

    subsection("Test 6.5 — Negative coin rejected")
    r = client.post("/session/new", json={
        "character_name": "Broke",
        "ancestry": "human",
        "culture": "drakenvale_city",
        "focus": "champion",
        "background": "soldier",
        "starting_economy": {"wealth_tier": "modest", "coin": -5},
    })
    check("6.5.a", r.status_code == 422, f"negative coin → {r.status_code}")

    subsection("Test 6.6 — Invalid wealth tier rejected")
    r = client.post("/session/new", json={
        "character_name": "Rich",
        "ancestry": "human",
        "culture": "drakenvale_city",
        "focus": "champion",
        "background": "soldier",
        "starting_economy": {"wealth_tier": "billionaire", "coin": 0},
    })
    check("6.6.a", r.status_code == 422, f"invalid wealth_tier → {r.status_code}")


# ---------------------------------------------------------------------------
# Part 7 — Combat Resolution
# ---------------------------------------------------------------------------

def part7(client: httpx.Client) -> None:
    section("PART 7 — Combat Resolution")

    subsection("Test 7.1 — POST /combat/compute_max_hp")
    r = client.post("/combat/compute_max_hp", json={
        "armor_id": "plate",
        "armor_tier": 3,
        "shield_id": "shield",
        "shield_tier": 2,
    })
    check("7.1.a", r.status_code == 200, f"POST /combat/compute_max_hp → {r.status_code}")
    if r.status_code == 200:
        payload = r.json()
        check("7.1.b", "max_hp" in payload and "armor_contribution" in payload and "shield_contribution" in payload, "compute_max_hp response structure present")

    subsection("Test 7.2 — POST /combat/resolve_attack")
    r = client.post("/combat/resolve_attack", json={
        "weapon_id": "sword",
        "weapon_tier": 2,
        "defender_is_unarmored": False,
    })
    check("7.2.a", r.status_code == 200, f"POST /combat/resolve_attack → {r.status_code}")
    if r.status_code == 200:
        payload = r.json()
        check("7.2.b", "roll_1" in payload and "damage" in payload and "events" in payload, "resolve_attack response structure present")

    subsection("Test 7.3 — GET /version includes combat_rules_fingerprint")
    r = client.get("/version")
    check("7.3.a", r.status_code == 200, f"GET /version → {r.status_code}")
    if r.status_code == 200:
        payload = r.json()
        check("7.3.b", "combat_rules_fingerprint" in payload, "combat_rules_fingerprint present")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\nMystic Weave 2.0 — Loop Test")
    print(f"Target: {BASE_URL}\n")

    with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
        r = client.get("/health")
        if r.status_code != 200:
            print(f"FATAL: /health returned {r.status_code}. Is the server running?")
            sys.exit(1)
        print("Health check: OK")

        session_id = part1(client)
        if session_id:
            part2(client, session_id)
        part3(client)
        part4(client)
        if session_id:
            part5(client, session_id)
        part6(client)
        part7(client)

    print(f"\n{'='*60}")
    print(f"RESULTS: {_pass} passed, {_fail} failed, {_pass + _fail} total")
    print(f"{'='*60}\n")
    sys.exit(1 if _fail > 0 else 0)


if __name__ == "__main__":
    main()