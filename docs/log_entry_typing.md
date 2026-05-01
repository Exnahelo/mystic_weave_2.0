# Log entry typing — migration boundary

Introduced in API version 4.6.0.

## Summary

`game_states.log` accepts two entry shapes:

- Legacy: plain string (any session log written before 4.6.0)
- Typed: `{ "type": "<enum>", "text": "<string>" }` (forward only)

Typed enum values:
- `narrative_non_arc` — rare non-arc fiction beat
- `world_change` — durable state change outside arc framing
- `admin_correction` — narrator correction not tied to fiction change
- `inventory_normalization` — storage/inventory reshape only
- `time_correction` — calendar adjustment only
- `compression` — migration or summary pass

## Migration policy

Pre-4.6.0 log entries are legacy freeform records. They are not retroactively
classified, migrated, or rewritten. Typed semantics apply only to entries
written after the schema change.

## Save-without-logging

`POST /state/{session_id}` and `POST /state/{session_id}/delta` accept
`log_entry: null` (or omitted). Saves with no log entry persist state
without appending to the log. Use this for the omit categories enumerated
in `prompts/engine.md` §5.
