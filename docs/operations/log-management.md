# Log Management Strategy

## Authority and durability

The `game_states.log` array is part of the authoritative game state. Like character and world data, it is durable. The log captures narrative beats, decisions, escalations, NPC conversations, closures — material the narrator (and any future analytics) needs to reconstruct what happened in a session.

We do not delete log entries. We do not implement retention windows or auto-expiry. Compression summarizes; it does not destroy.

## Why log management exists

Long-running sessions accumulate log entries linearly. Each `GET /state/{session_id}` call serializes the full log array into the response payload. At ~500 bytes per entry and 200+ turns, the payload grows to 100KB+. Postgres TOAST handles JSONB storage efficiently; the cost is on the read path — payload size and JSON deserialization on the client.

The May 2 session debrief surfaced log bloat as an emerging concern but did not yet quantify impact.

## Tools available

### `log_limit` query parameter (Brief 24)

`GET /state/{session_id}?log_limit=50` returns only the most recent 50 log entries. The response includes `log_total_entries` so callers know the full count.

Suitable for:
- The narrator GPT loading state at the start of a turn (recent context is what matters)
- Admin tooling that paginates through log entries
- Dashboards showing recent activity

The default (`log_limit` unset) returns the full log for backward compatibility.

Bounds: `log_limit` accepts integers from 1 to 10000. `log_limit=0` returns 422. A `log_limit` larger than the stored log returns the full log without error (Python tail-slice semantics).

### Compression-typed log entries (existing, since Brief 11+)

The narrator can submit a typed log entry of `type: "compression"` via `POST /state/{session_id}/delta`. The compression entry summarizes prior beats; the original entries remain in storage but the compression entry serves as the canonical narrative summary going forward.

Example payload to `/delta`:

```json
{
  "log_entry": {
    "type": "compression",
    "text": "Sylvara investigated the brookside contamination across multiple field surveys (turns 17-32), confirming the chain compromise and gathering evidence for council review. Key findings: vine-snare residue at three spring sites, witness testimony from two Heartwarden patrols, alchemical signature matched to Vaelaryn-licensed compounder."
  }
}
```

Note: compression entries currently use `text` only. The `payload` field on `TypedLogEntry` is reserved for `type: "closure_summary"` (validated by `payload_consistent_with_type`). If future work needs structured compression metadata (turn ranges, entry indices), the model would need to be extended deliberately.

The narrator decides when to compress. Reasonable triggers:
- After an arc settles (compress the field-investigation phase into one summary)
- When a session crosses ~50 turns and recent context dominates narration
- At natural pacing breaks (between sessions, between major arcs)

### Compression-typed entry semantics

A compression entry does not modify or delete prior entries. It adds a summary entry. Clients reading the log see both:
- The original detailed entries (for forensics, analytics, replay)
- The compression entry (for narrative-summary fast paths)

A future brief may add explicit "supersedes" semantics where compression entries can mark prior entries as superseded, allowing optional skip-on-read. That work waits for evidence that simple compression-as-summary is insufficient.

### `/state/{session_id}/annotation` (Brief 16)

Admin corrections, rule clarifications, and operational notes go through `POST /state/{session_id}/annotation` rather than `/delta`. They are recorded as `admin_correction` typed log entries and prefixed with their category. This separates canon-correction noise from gameplay log entries — useful when reading or compressing.

## Measurement guidance for future work

Before adding a compression endpoint, retention policy, or auto-truncation, capture measurements:

1. **Log size distribution across sessions**: median, p95, max entry count and byte size. SQL: `SELECT session_id, jsonb_array_length(log), pg_column_size(log) FROM game_states`.
2. **Read latency by log size**: instrument `GET /state/{session_id}` to record (log_size, response_time). Look for inflection points where size correlates with slowdown.
3. **Client-side parse cost**: if the narrator GPT processes the log on each turn, measure the parse and analysis cost as log grows.
4. **Compression-entry adoption**: how often do narrators actually submit compression entries through `/delta`? If usage is low, add tooling; if high, the manual path is sufficient.

If measurements show the existing manual-compression path is sufficient, no further work is needed. If they show it is not, a future brief can design with informed scope.

## What we do NOT do

- **Do not auto-truncate.** Authority requires durability.
- **Do not implement retention windows.** Game state is not log data; the same retention semantics do not apply.
- **Do not add background compression jobs.** Compression is a creative summary; it benefits from narrator judgment.
- **Do not return compressed entries by default.** The full log is the source of truth; the tail-read pattern is opt-in.

## Related work

- **Brief 11** — typed log entries introduced (`closure_summary`, `compression`, `narrative_non_arc`, etc.)
- **Brief 16** — `/state/{session_id}/annotation` separated admin corrections from gameplay log
- **Brief 24** — `log_limit` query parameter and this document
- Future: optional supersedes-semantics, dedicated compression endpoint, measurement-driven decisions
