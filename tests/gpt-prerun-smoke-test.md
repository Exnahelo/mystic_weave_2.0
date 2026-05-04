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

NOTE on negative tests and wrapper observability: the OpenAI Actions wrapper does not always surface HTTP status codes. For negative tests, PASS means the call returned a non-success result with an error indication consistent with the expected validation. If the wrapper returns only `ClientResponseError` with no body, that is sufficient to confirm the endpoint rejected the call — record it as PASS and move on. Do not fail a negative test solely because the status code or error message wasn't visible.

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
    NOTE: if this returns ClientResponseError (wrapper-hidden failure) but a retry succeeds within 30 seconds, mark PASS with a note. Cold-start hiccups are acceptable; reproducible failures are not.

1.3 GET /options
    PASS: 2xx, response includes ancestries, cultures, focus, backgrounds keys.
    (Field name is `focus` singular, not `focuses`. Other categories are plural. Do not flag this as drift.)

PHASE 2 — REFERENCE DATA

2.1 GET /catalog/items?kind=mundane
    PASS: 2xx, response is a structured catalog (bucketed by item type).
    (Valid kind values: mundane, magical, apparel, weapon, armor, ammunition.)

2.2 GET /catalog/items/{item_id} for any item_id from 2.1's response
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
    (The /roll endpoint resolves d100 rolls against a target. roll is in [1, 100].)

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
    PASS: 2xx. Response state shows world.pacing.tension == 4.
    Verification: follow up with GET /state/{session_id} and confirm world.pacing.tension == 4.
    NOTE: if the follow-up GET returns ClientResponseError with retry success, mark PASS with a note.

4.4 POST /state/{session_id}/annotation with:
    {"annotation": "smoke_test: annotation probe", "category": "operational_constraint"}
    PASS: 2xx.
    (Body field is `annotation`, not `text`. Valid categories: canon_correction, operational_constraint, rule_clarification, narrator_correction.)

4.5 GET /scene/{session_id}
    PASS: 2xx, response includes location_summary, recent_log, relevant_character_state.
    location_summary.id should be "vaelmere" (from 4.2).
    NOTE: if this returns 500, the typed-log fix may not have landed. Flag as FAIL with the response status.

4.6 GET /scene on a fresh session — degraded location handling.
    Create a SECOND session via POST /session/new (same body shape as 1.1, character_name "smoke_test_runner_2"). Immediately call GET /scene/{new_session_id} BEFORE setting any location.
    PASS: 2xx. location_summary.id is "unknown" or location_summary.name indicates no location is set. Empty visible_entities and available_opportunities are expected.

PHASE 5 — ARCS

The arc lifecycle is: `proposed → available → in_progress → ready_to_close → settle`. New arcs start in `proposed`. Each transition is a separate /transition call.

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
    PASS: 2xx, response includes new arc with id and state="proposed".
    Record the arc_id.

5.3 GET /arc/{session_id}/{arc_id}
    PASS: 2xx, returns the arc with state="proposed".

5.4 GET /arc/{session_id}/active
    PASS: 2xx. Empty list expected (arc is "proposed", not yet active).

5.5 POST /arc/{session_id}/{arc_id}/transition — proposed → available:
    {"from_state": "proposed", "to_state": "available", "reason": "smoke_test: ready for player acceptance"}
    PASS: 2xx, arc state becomes "available".

5.6 POST /arc/{session_id}/{arc_id}/transition — available → in_progress:
    {"from_state": "available", "to_state": "in_progress", "reason": "smoke_test: player accepted"}
    PASS: 2xx, arc state becomes "in_progress".

5.7 GET /arc/{session_id}/active
    PASS: 2xx, list now includes the arc.

5.8 POST /arc/{session_id}/{arc_id}/progress
    {"resolved_scene_occurred": true, "notes": "smoke_test progress"}
    PASS: 2xx.

5.9 POST /arc/{session_id}/{arc_id}/spawn — spawn a child arc:
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

5.10 POST /arc/{session_id}/{arc_id}/transition — in_progress → ready_to_close:
    {"from_state": "in_progress", "to_state": "ready_to_close", "reason": "smoke_test: closure"}
    PASS: 2xx, arc state becomes "ready_to_close".

5.11 POST /arc/{session_id}/{arc_id}/settle
    {"outcome": "complete", "notes": "smoke_test settle"}
    PASS: 2xx, arc state becomes "complete" or terminal equivalent.

PHASE 6 — COMBAT

6.1 POST /combat/compute_max_hp with a real catalog armor:
    {"armor_id": "leather", "armor_tier": 1}
    PASS: 2xx, response includes a numeric max_hp.

6.2 POST /combat/resolve_attack with a real catalog weapon:
    {"weapon_id": "dagger", "weapon_tier": 1, "defender_is_unarmored": true}
    PASS: 2xx, response includes resolved attack outcome (hit/miss, damage if hit).

PHASE 7 — COMPANIONS

7.1 POST /companion/new with a minimal payload. The companion sub-object schema is non-trivial; consult the OpenAPI schema for the `tier` chosen and construct accordingly. Suggested tier="creature" with a minimal valid companion object.
    PASS: 2xx, response includes companion_id. Record the companion_id.
    NOTE: do NOT include an `id` field in the inner companion object; backend rejects client-supplied ids as `extra_forbidden`. The backend generates the id.
    SKIP this step (and 7.2) with a clear reason if the companion sub-schema is too complex to construct without further investigation. Do NOT attempt with an invented or incomplete payload.

7.2 POST /companion/{companion_id}/transition with a valid TransitionCompanionRequest payload (session_id, new_companion, trigger).
    PASS: 2xx.
    SKIPPED if 7.1 was skipped.

PHASE 8 — NEGATIVE TESTS (error contracts)

These verify that error paths return non-2xx for invalid inputs. PASS = call returned non-success (2xx absent). The wrapper may obscure status codes and bodies; that's fine — what matters is the call did not silently succeed.

A negative test FAILS if the call unexpectedly succeeds (silent bug — a real problem).

8.1 GET /state/intentionally_nonexistent_session_xyz
    PASS: any non-2xx response (404, 500-with-not-found, ClientResponseError). FAIL if 2xx with valid state body.

8.2 POST /state/{session_id}/delta with empty payload:
    {"character": {}, "world": {}, "time_elapsed": {}}
    PASS: any non-2xx response.

8.3 POST /state/{session_id}/delta with conflicting time_elapsed:
    {"world": {"pacing": {"tension": 5}}, "time_elapsed": {"until": "dawn", "steps": 3}}
    PASS: any non-2xx response.

8.4 POST /state/{session_id}/delta with empty log_entry text:
    {"world": {"pacing": {"tension": 5}}, "log_entry": {"type": "narrative_non_arc", "text": ""}, "time_elapsed": {}}
    PASS: any non-2xx response.

8.5 POST /narrator/scene_resolved verifying parent-cap rejection mechanism is engaged.
    The smoke test character is a warden, which starts with knowledge: nature=2, tracking=1, ranged=1, application: ecology=1, command=1.
    Submit a scene action proposing advancement on `command`:
    {
      "session_id": "<session_id>",
      "scene_summary": "smoke_test: parent-cap evaluation probe",
      "scene_actions": [{"type": "social_roll", "application": "command", "outcome": "success"}],
      "world_changes": {},
      "character_changes": {},
      "time_elapsed": {}
    }
    PASS: 2xx response. candidates_ranked is present and non-empty. The endpoint MUST NOT 5xx.
    Note for engineering: do NOT assert on specific eligibility flags. Different characters trigger different rejection paths. The contract being tested is "endpoint does not 5xx on advancement evaluation." Any structured candidate response is acceptable.
    FAIL if 5xx (the actual concern), or if response is missing candidates_ranked entirely.

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
