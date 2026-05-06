# arc.log[].source integrity

## What the constraint is

`ArcBeatLogEntry.source` is a strict literal union: `"progress"` or `"transition"`. Those are the only two values the code in this repository ever writes through normal flows.

Code write sites:

- `api/routes/arc.py:417` — `transition` (via `/arc/{session_id}/{arc_id}/transition` and the `/declare` orchestrator)
- `api/routes/arc.py:1167` — `progress` (via `/arc/{session_id}/{arc_id}/progress`)

The constant `ARC_BEAT_LOG_VALID_SOURCES` in `api/models/__init__.py` is the single source of truth and is referenced from the integrity migration.

## What can break it

Manual JSON patches against the `arcs.data` JSONB column. Any value outside the valid set will pass the database write (the column is unconstrained JSONB) but will fail Pydantic validation on read, surfacing as `GET /arc/{session_id}` returning HTTP 500.

This was first observed on 2026-05-05 after a Phase 9b session where the operator hand-patched the deadlocked black-tray arc (`arc-94f73453e294498e`) with a `settlement_correction` source.

## When the migration fails

Migration `20260505_0005_arc_log_source_integrity` is read-only. It does not modify rows. It scans every arc's `data->'log'` array and raises `RuntimeError` if any entry has a source outside the valid set. The error message names every offending `arc_id`, `session_id`, and bad value.

Failure flow:

1. Read the listed offending entries.
2. For each one, decide what the operational intent was:
   - If the entry was appended during a `/transition` (state-change) flow → repair source to `transition`.
   - If the entry was a beat-style narrative note appended during play → repair source to `progress`.
   - Anything else (e.g., reward-channel notes, post-hoc corrections) does not belong in `arc.log[]`. It belongs in the session log as a `TypedLogEntry` (`admin_correction` or similar). Strip the entry from `arc.log[]` and append it via `/state/{session_id}/annotation`.
3. Repair via the canonical script:

   ```bash
   python3 scripts/repair_arc_log_source.py
   ```

   The script connects to the same DB the API uses, lists every offending entry, and prompts for a replacement source per entry.
4. Re-run the migration. It should now pass.

## Do not "fix" by widening the schema

The literal union is the contract. Adding more values to absorb manual-patch artifacts would let the same drift happen silently next time. If a new source value is genuinely needed (i.e., a new code-side write site), add it to both the literal union in `ArcBeatLogEntry` and the `ARC_BEAT_LOG_VALID_SOURCES` constant, in the same commit that adds the write site.

## Last resort

If a beat is unrecoverable (text and timestamp lost, narrative intent unclear), strip the entry. Better to lose one log row than carry a permanently invalid arc that can't be read.
