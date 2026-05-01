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

## `closure_summary` — added in 4.7.0

Backend-assembled. The narrator does NOT write `closure_summary` entries; they
are emitted by `POST /arc/{session_id}/{arc_id}/settle` after a successful
arc settlement.

Shape:

- `type`: `"closure_summary"`
- `text`: brief one-line summary, e.g. `"Arc 'Heartwater Basin Investigation' settled as complete: 2 AP, 3 reputation change(s)"`
- `payload`: structured dict with the full settlement record. Fields:
  - `arc_id`, `arc_title`, `outcome`, `settled_at`
  - `awarded_ap`, `coin_cd_awarded`, `coin_cd_forfeit`
  - `items_awarded`, `leverage_gained`, `reputation_changes`, `obligations_added`
  - `consequence_events`
  - `resolved_scenes_used`, `locations_visited`

Per-arc beat logs (added in 4.7.0) hold full original beats. The
`closure_summary` entry on `game_states.log` is the compact, structured
record. Both layers preserve provenance; neither replaces the other.
