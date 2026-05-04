# Mystic Weave — Mid-Session Audit

Mid-session write-side audit. Paste verbatim into the narrator GPT
mid-session to spot-check whether tool calls and state writes match the
prose. The GPT audits the most recent turns while context is still warm.

Use when:
- Something feels off but nothing has obviously broken.
- ~10 turns have passed since last audit and you want a checkpoint.
- A turn just had complex state changes (new gear, location changes,
  multiple reputation shifts) and you want to verify they actually persisted.

Mid-session audits catch silent fabrication and dropped deltas. End-of-session
debriefs cannot — by then the context is compressed and the narrator can no
longer distinguish what it actually did from what it remembers narrating.

---

Mid-session audit. Step out of narrator role. No fiction, no in-character framing, no apologies. Audit the LAST 10 TURNS (or fewer if the session is shorter). Engineering audience. Clinical and specific.

Cover the two sections below for those turns, in order.

1. TOOL-USE COMPLIANCE

For each of the last 10 turns, list:
   - Turn description (one phrase: "investigation at trade office", "ride to town", etc.)
   - State changes you NARRATED in prose: location, time, inventory, HP, reputation, NPC presence, arc movement, currency, etc.
   - Tool calls you ACTUALLY MADE on that turn: endpoint and operationId
   - FABRICATED: any narrated state change with no matching tool call.
   - SILENT FAILURE: any tool call that returned an error where you continued narrating as if it had succeeded.

If you cannot reliably reconstruct what tool calls happened on a given turn (context truncated, you don't remember), say so explicitly. Do not invent tool calls to make the record look complete. Confessing gaps is what the engineer needs.

For each FABRICATED change, state:
   - What state the player believes is canon.
   - What state the backend actually has — call /state/{session_id} now to verify; quote the relevant field.
   - Whether the backend can be brought into alignment via a /state/{session_id}/delta call (forward), or whether a /state/{session_id}/annotation correction is needed (backward record of the divergence).

2. NARRATIVE-TO-STRUCTURE EXTRACTION

For each turn that resulted in a /narrator/scene_resolved or /state/{session_id}/delta call, compare:
   - The prose outcome you narrated (one-line summary of what happened in fiction).
   - The delta payload you submitted (specific fields changed).

Flag each mismatch:
   - PROSE > DELTA: you narrated a state change that wasn't in the delta payload. Lost write.
   - DELTA > PROSE: the delta included a change the prose didn't mention. Suspicious; may be reasonable but should be checked.
   - VALUE MISMATCH: the value saved doesn't match the narration (e.g., narrated reputation +3, saved +1; narrated three days passed, saved one step).

For each flag: which turn (number or scene_summary first phrase), and what the discrepancy is.

BOTTOM LINE

After both sections:
   - Count of fabrications detected.
   - Count of extraction mismatches detected.
   - Single-sentence judgment: is current backend state aligned with current player understanding, or is there drift that needs correction before play continues?
   - If drift exists, what specific call (or sequence of calls) would restore alignment.

Tone: clinical, evidence-based. Confessing fabrication is the goal — do not soften. If you genuinely cannot audit a turn because context is gone, say so plainly. A short audit reporting "I can't reliably audit turns 1–4 because context is compressed; here's what I can verify on 5–10" is more useful than a full report stuffed with reconstructions.