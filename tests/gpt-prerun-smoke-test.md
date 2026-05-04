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
- Status code and key response fields (or status + error body if failed)
- PASS or FAIL based on the criteria stated for that step

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
    PASS: 200, response includes a session_id (16-char hex).
    Record the session_id; use it for all subsequent calls.

1.2 GET /state/{session_id}
    PASS: 200, response includes character, world, log fields. Character name is "smoke_test_runner".

1.3 GET /options
    PASS: 200, response includes ancestries, cultures, focuses, backgrounds.

PHASE 2 — REFERENCE DATA

2.1 GET /catalog/items
    PASS: 200, response is non-empty list or paginated structure.

2.2 GET /catalog/items/{some_item_id} for an item from 2.1
    PASS: 200, response includes the item details.

2.3 GET /registry/{name} — try "tags", "applications", or another known registry
    PASS: 200 with populated result, OR clean 404 with structured error if name doesn't exist.

2.4 GET /npcs
    PASS: 200.

PHASE 3 — WORLD/LOCATION

3.1 GET /location/vaelmere
    PASS: 200, response includes location data.

3.2 GET /location/vaelmere/connections
    PASS: 200, response includes connections list.

PHASE 4 — CORE GAMEPLAY LOOP

4.1 POST /roll with {"sides": 20}
    PASS: 200, response includes a roll result in [1, 20].

4.2 POST /narrator/scene_resolved with this body:
    {
      "session_id": "<session_id>",
      "scene_summary": "smoke_test: character surveys surroundings.",
      "scene_actions": [],
      "world_changes": {},
      "character_changes": {},
      "time_elapsed": {"steps": 1}
    }
    PASS: 200. state_after.world.time advanced by one band. changes_applied includes "scene_recorded" and "time_advanced".

4.3 POST /state/{session_id}/delta with this body:
    {
      "world": {"pacing": {"tension": 4}},
      "log_entry": {"type": "narrative_non_arc", "text": "smoke_test: pacing tension nudged"},
      "time_elapsed": {}
    }
    PASS: 200. Response state shows world.pacing.tension == 4. Verify with a follow-up GET /state/{session_id} that this persisted.

4.4 POST /state/{session_id}/annotation with:
    {"category": "operational", "text": "smoke_test: annotation probe"}
    PASS: 200. Verify the annotation appears in /state/{session_id} log.

4.5 GET /scene/{session_id}
    PASS: 200, response includes recent_log without validation errors. (This endpoint had a known list[str] vs typed-log shape issue — flag if it returns 500 or a Pydantic validation error.)

PHASE 5 — ARCS

5.1 GET /arc/{session_id}
    PASS: 200, returns list (likely empty for a fresh session).

5.2 POST /arc/{session_id}/create with this minimal payload:
    {
      "title": "smoke_test arc",
      "summary": "smoke_test arc for endpoint verification",
      "primary_type": "task_local",
      "subtype": "investigation",
      "stake_scale": "local",
      "origin_type": "emergent"
    }
    PASS: 200, response includes new arc with id and state.
    Record the arc_id.

5.3 GET /arc/{session_id}/{arc_id}
    PASS: 200, returns the arc.

5.4 GET /arc/{session_id}/active
    PASS: 200, includes the new arc.

5.5 POST /arc/{session_id}/{arc_id}/progress with a minimal progress event
    (use the OpenAPI schema for the request body — typically a beat description and small envelope cost).
    PASS: 200.

5.6 POST /arc/{session_id}/{arc_id}/transition with a valid state transition
    (consult OpenAPI for valid target states from "in_progress").
    PASS: 200.

5.7 POST /arc/{session_id}/{arc_id}/settle with a valid settlement payload.
    PASS: 200, arc state becomes "settled" or terminal equivalent.

5.8 POST /arc/{session_id}/{arc_id}/spawn — try spawning a child arc from the now-settled parent
    OR from a separate active parent if 5.7 closed the only arc. (Skip with note if no eligible parent.)
    PASS: 200 if attempted, with new child arc returned.

PHASE 6 — COMBAT

6.1 POST /combat/compute_max_hp with the test character's identity
    (use what you have from /state/{session_id}).
    PASS: 200, response includes a numeric max_hp.

6.2 POST /combat/resolve_attack with a minimal attacker/defender setup using the test character
    (use any reasonable target — generic creature or NPC reference).
    PASS: 200, response includes resolved attack outcome with hit/miss and damage if hit.

PHASE 7 — COMPANIONS

7.1 POST /companion/new with a minimal companion payload tied to the test session.
    PASS: 200, response includes companion_id.
    Record the companion_id.

7.2 POST /companion/{companion_id}/transition with a valid transition (consult OpenAPI for valid target states).
    PASS: 200.

PHASE 8 — NEGATIVE TESTS (error contracts)

These verify that error paths return correct status codes and structured bodies. A negative test FAILS if the call unexpectedly succeeds (silent bug) or returns the wrong error shape.

8.1 GET /state/intentionally_nonexistent_session_xyz
    PASS: 404 with structured error body. FAIL if 200 (silent bug) or 500.

8.2 POST /state/{session_id}/delta with empty payload:
    {"character": {}, "world": {}, "time_elapsed": {}}
    PASS: 422 with error indicating delta requires changes.

8.3 POST /state/{session_id}/delta with conflicting time_elapsed:
    {"world": {"pacing": {"tension": 5}}, "time_elapsed": {"until": "dawn", "steps": 3}}
    PASS: 422 with error about until being mutually exclusive with steps/days.

8.4 POST /state/{session_id}/delta with empty log_entry text:
    {"world": {"pacing": {"tension": 5}}, "log_entry": {"type": "narrative_non_arc", "text": ""}, "time_elapsed": {}}
    PASS: 422 with error about empty text (or schema rejection at the platform layer).

8.5 POST /narrator/scene_resolved with a parent-cap violation:
    The test character starts with all knowledge groups at tier 1 and applications at tier 1. Submit a scene_actions entry that would advance an application past parent. For example:
    {
      "session_id": "<session_id>",
      "scene_summary": "smoke_test: parent-cap negative test",
      "scene_actions": [{"type": "social_roll", "application": "etiquette", "outcome": "success"}],
      "world_changes": {},
      "character_changes": {},
      "time_elapsed": {}
    }
    PASS: 200. candidates_ranked shows etiquette with parent_cap_ok: false, eligible: false. The endpoint MUST NOT 500 — it should return the structured rejection.

FINAL REPORT

After all phases, produce in this order:

PHASE RESULTS TABLE
- Per phase: PASS count / FAIL count / skipped count.
- Each FAIL: which step, what failed, response status and body fragment.

CRITICAL FAILURES (non-empty list, or "none")
- Any 500.
- Any unexpected error shape (missing body, non-JSON, malformed status).
- Any negative test that incorrectly passed (false success — these are silent bugs).
- Any contract drift: response shape differs from the OpenAPI schema you used.

CONTRACT DRIFT INDICATORS
- Per call where actual response shape differed from the OpenAPI schema: which call, which field, what was different.

BOTTOM LINE
- One sentence: did the system pass enough to start a real session?
- One sentence: which phase, if any, blocks production play, and what would need fixing.

Tone: clinical, specific, evidence-based. No retrospective polishing. If you couldn't complete a phase because a prior call failed, say so plainly — don't fabricate downstream data.