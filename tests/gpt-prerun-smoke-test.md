# Mystic Weave — Pre-Run Smoke Test

Pre-run baseline test. Paste verbatim into the narrator GPT after a deploy
or any change to the backend, schemas, or knowledge files. The GPT runs
through the test sequence end-to-end and reports phase-by-phase results.

Use BEFORE starting a real play session. The output confirms the system
works end-to-end and surfaces broken contracts before they corrupt canon.

The test creates a fresh session with "smoke_test" in the character name
so test sessions are easy to identify. The DB is wiped weekly; test
sessions accumulating is fine.

---

Smoke test. Step out of narrator role. No fiction, no in-character framing. Run the sequence below in order, REPORTING PHASE BY PHASE as you go. Do not hold results to assemble a polished summary at the end — engineering needs to see failures the moment they happen.

For each call, report:
- Endpoint and operationId
- Whether the call succeeded (2xx response with expected fields) or failed
- For successes: the key response fields verifying the criterion
- For failures: the response body or error fragment you received
- PASS or FAIL based on the criteria stated for that step

NOTE on negative tests: the OpenAI Actions wrapper does not always surface HTTP status codes. For negative tests, PASS means a non-success response with an error message containing the expected fragment. Do not fail a negative test solely because the status code wasn't visible — match on the error message content instead.

If any call fails, do not stop the test — note the failure and continue. The point is to exercise the whole surface and surface ALL broken endpoints in one run. The only exception: if Phase 1 (session setup) fails, stop — subsequent phases need a session_id.

PHASE 1 — SESSION SETUP

1.1 POST /session/new with this body:
    {
      "character_name": "smoke_test_runner",
      "ancestry": "elf",
      "culture": "feywood_wilds",
      "focus": "warden",
      "background": "outlander"
    }
    PASS: 2xx, response includes a session_id (16-char hex).
    Record the session_id; use it for all subsequent calls.

1.2 GET /state/{session_id}
    PASS: 2xx, response includes character, world, log fields. Character name is "smoke_test_runner".

1.3 GET /options
    PASS: 2xx, response includes ancestries, cultures, focuses, backgrounds keys.

PHASE 2 — REFERENCE DATA

2.1 GET /catalog/items?kind=mundane
    PASS: 2xx, response is a structured catalog (bucketed by item type — mundane_items, etc.).
    (Valid kind values: mundane, magical, apparel, weapon, armor, ammunition.)

2.2 GET /catalog/items/{some_item_id} for any item_id from 2.1's response
    PASS: 2xx, response includes the item details.

2.3 GET /registry/ecology
    PASS: 2xx, response is a registry entry. (The /registry endpoint is single-entry lookup, not enumeration.)

2.4 GET /npcs
    PASS: 2xx.

PHASE 3 — WORLD/LOCATION

3.1 GET /location/vaelmere
    PASS: 2xx, response includes location data.

3.2 GET /location/vaelmere/connections
    PASS: 2xx, response includes connections list.

PHASE 4 — CORE GAMEPLAY LOOP

4.1 POST /roll with {"target": 10, "reason": "smoke_test probe"}
    PASS: 2xx, response includes fields: roll, target, success, margin, degree.
    (The /roll endpoint resolves d100 rolls against a target. roll is in [1, 100], degree is one of the standard outcome bands.)

4.2 POST /narrator/scene_resolved with this body — sets a real location for later /scene tests:
    {
      "session_id": "<session_id>",
      "scene_summary": "smoke_test: character arrives at vaelmere.",
      "scene_actions": [],
      "world_changes": {"location": "vaelmere"},
      "character_changes": {},
      "time_elapsed": {"steps": 1}
    }
    PASS: 2xx. state_after.world.location == "vaelmere". changes_applied includes "scene_recorded", "world.location", and "time_advanced".

4.3 POST /state/{session_id}/delta with this body:
    {
      "world": {"pacing": {"tension": 4}},
      "log_entry": {"type": "narrative_non_arc", "text": "smoke_test: pacing tension nudged"},
      "time_elapsed": {}
    }
    PASS: 2xx. Response state shows world.pacing.tension == 4. Verify with a follow-up GET /state/{session_id} that this persisted.

4.4 POST /state/{session_id}/annotation with:
    {"annotation": "smoke_test: annotation probe", "category": "operational_constraint"}
    PASS: 2xx.
    (Body field is `annotation`, not `text`. Valid categories: canon_correction, operational_constraint, rule_clarification, narrator_correction.)

4.5 GET /scene/{session_id}
    PASS: 2xx, response includes location_summary, recent_log, relevant_character_state.
    location_summary.id should be "vaelmere" (from 4.2).

4.6 GET /scene on a fresh session — degraded location handling.
    Create a SECOND session via POST /session/new (same body shape as 1.1, character_name "smoke_test_runner_2"). Immediately call GET /scene/{new_session_id} BEFORE setting any location.
    PASS: 2xx. location_summary.id is "unknown" or location_summary.name indicates no location is set. Empty visible_entities and available_opportunities are expected.
    (If this returns 404 with "current location not found: unknown", the /scene degradation fix has not landed — flag as FAIL.)

PHASE 5 — ARCS

5.1 GET /arc/{session_id}
    PASS: 2xx, returns list (likely empty for a fresh session).

5.2 POST /arc/{session_id}/create with this minimal payload:
    {
      "title": "smoke_test arc",
      "summary": "smoke_test arc for endpoint verification",
      "primary_type": "task_local",
      "subtype": "investigation",
      "stake_scale": "local",
      "origin_type": "emergent"
    }
    PASS: 2xx, response includes new arc with id and state.
    Record the arc_id. The new arc starts in state "proposed".

5.3 GET /arc/{session_id}/{arc_id}
    PASS: 2xx, returns the arc.

5.4 GET /arc/{session_id}/active
    PASS: 2xx. Note: a freshly-created arc is in state "proposed" and will NOT appear in /active until transitioned. Empty list here is expected at this point.

5.5 POST /arc/{session_id}/{arc_id}/transition to move the arc to in_progress:
    {"from_state": "proposed", "to_state": "in_progress", "reason": "smoke_test transition"}
    PASS: 2xx, arc state becomes "in_progress".

5.6 GET /arc/{session_id}/active again
    PASS: 2xx, list now includes the arc.

5.7 POST /arc/{session_id}/{arc_id}/progress
    {"resolved_scene_occurred": true, "notes": "smoke_test progress"}
    PASS: 2xx.

5.8 POST /arc/{session_id}/{arc_id}/spawn — spawn a child arc:
    {
      "child_title": "smoke_test child arc",
      "child_summary": "smoke_test child for spawn verification",
      "child_primary_type": "task_local",
      "child_subtype": "investigation",
      "child_stake_scale": "local",
      "ap_ownership": "child",
      "reason": "smoke_test spawn"
    }
    PASS: 2xx, new child arc returned.

5.9 POST /arc/{session_id}/{arc_id}/settle
    {"outcome": "complete", "notes": "smoke_test settle"}
    PASS: 2xx, parent arc state becomes "settled" or terminal equivalent.

PHASE 6 — COMBAT

6.1 POST /combat/compute_max_hp with a minimal valid payload:
    {"armor_id": "studded-leather-feywood-ranger", "armor_tier": 1}
    PASS: 2xx, response includes a numeric max_hp.

6.2 POST /combat/resolve_attack with a minimal valid payload:
    {"weapon_id": "moonthorn-hunting-knife", "weapon_tier": 1, "defender_is_unarmored": true}
    PASS: 2xx, response includes resolved attack outcome (hit/miss, damage if hit).

PHASE 7 — COMPANIONS

7.1 POST /companion/new with a minimal payload. The companion sub-object schema is non-trivial; consult the OpenAPI schema for the `tier` chosen and construct accordingly. Suggested tier="creature" with a minimal valid companion object.
    PASS: 2xx, response includes companion_id. Record the companion_id.
    SKIP this step (and 7.2) with a clear reason if the companion sub-schema is too complex to construct without further investigation. Do NOT attempt with an invented or incomplete payload.

7.2 POST /companion/{companion_id}/transition with a valid TransitionCompanionRequest payload (session_id, new_companion, trigger).
    PASS: 2xx.
    SKIPPED if 7.1 was skipped.

PHASE 8 — NEGATIVE TESTS (error contracts)

These verify that error paths return the correct error MESSAGES. PASS = non-success response with an error message containing the expected fragment. The wrapper may not surface status codes; match on message content.

A negative test FAILS if the call unexpectedly succeeds (silent bug — a real problem) or returns an error message that doesn't match the expected validation.

8.1 GET /state/intentionally_nonexistent_session_xyz
    PASS: error response with "session not found" or equivalent. FAIL if 2xx (silent bug) or if error message is missing/unrelated.

8.2 POST /state/{session_id}/delta with empty payload:
    {"character": {}, "world": {}, "time_elapsed": {}}
    PASS: error response with message containing "must include at least one character or world change" (or close paraphrase).

8.3 POST /state/{session_id}/delta with conflicting time_elapsed:
    {"world": {"pacing": {"tension": 5}}, "time_elapsed": {"until": "dawn", "steps": 3}}
    PASS: error response with message about "until" being mutually exclusive with steps/days.

8.4 POST /state/{session_id}/delta with empty log_entry text:
    {"world": {"pacing": {"tension": 5}}, "log_entry": {"type": "narrative_non_arc", "text": ""}, "time_elapsed": {}}
    PASS: error response indicating empty/too-short text is invalid.

8.5 POST /narrator/scene_resolved with a parent-cap violation:
    The test character starts with all knowledge groups at tier 1 and applications at tier 1. Submit:
    {
      "session_id": "<session_id>",
      "scene_summary": "smoke_test: parent-cap negative test",
      "scene_actions": [{"type": "social_roll", "application": "etiquette", "outcome": "success"}],
      "world_changes": {},
      "character_changes": {},
      "time_elapsed": {}
    }
    PASS: 2xx response. candidates_ranked includes etiquette with parent_cap_ok: false, eligible: false. The endpoint MUST NOT return an error — it should return the structured rejection in candidates_ranked.
    FAIL if 5xx (this is the bug we're guarding against), or if etiquette is marked eligible in candidates_ranked (silent parent-cap violation).

FINAL REPORT

After all phases, produce in this order:

PHASE RESULTS TABLE
- Per phase: PASS count / FAIL count / SKIPPED count.
- Each FAIL: which step, what failed, response body fragment.

CRITICAL FAILURES (non-empty list, or "none")
- Any 5xx confirmed in response.
- Any negative test that incorrectly passed (false success — silent bug).
- Any contract drift you found that's NOT already noted in the test (i.e., a response shape that didn't match what this test expected, beyond what the test description warned about).

CONTRACT DRIFT INDICATORS
- Per call where actual response shape differed from this test's expectations: which call, which field, what was different. (This helps maintain the smoke test itself — if the schema has shifted, the test needs updating.)

BOTTOM LINE
- One sentence: did the system pass enough to start a real session?
- One sentence: which phase, if any, blocks production play, and what would need fixing.

Tone: clinical, specific, evidence-based. No retrospective polishing. If you couldn't complete a phase because a prior call failed, say so plainly — don't fabricate downstream data. If you couldn't construct a payload because the schema is too complex (e.g., 7.1 companion), mark SKIPPED with a clear reason rather than attempting and failing.