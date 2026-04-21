# Mystic Weave — TODO

Updated after post-cleanup audit — 2026-04-18.

## ✅ Recently Completed

- [x] 2026-04-18 / `6bec194` — merged naming-convention cleanup onto `main`
- [x] 2026-04-18 / `5313168` — removed authoring meta tags from canonical world data
- [x] 2026-04-18 / `6eb3959` — normalized underscore tag variants to kebab-case
- [x] 2026-04-18 / `eea3826` — fixed `hollow-crowm` typo in canonical tags
- [x] 2026-04-18 / `08c64eb` — normalized two world YAML filenames to snake_case
- [x] 2026-04-18 / `2b8829c` — committed convention-drift audit document
- [x] 2026-04-18 / `90f10c9` — added `docs/conventions.md`
- [x] 2026-04-10 to 2026-04-18 / `2231394`, `701bda2`, `2eb11fe` — reconciled topology, region IDs, and route/link hygiene

---

## 🔜 Active Work

### Blocking

- [x] Restore passing regression coverage for state save/delta and scene-context flows.
  - affected paths: `tests/regression/test_endpoint_validation.py`, `tests/regression/test_multi_turn_persistence.py`, `tests/regression/test_scene_context.py`, `api/routes/state.py`, `api/routes/scene.py`, `api/models.py`
  - size estimate: L
- [x] Make the local narrator play-test path pass end-to-end in `tests/loop_test.py`.
  - affected paths: `tests/loop_test.py`, `api/routes/session.py`, `api/routes/location.py`, `api/routes/character.py`, `api/game_data.py`
  - size estimate: L
- [x] Align remaining `/session/new` and `/character/create` test payloads to the current `ancestry` + `culture` schema.
  - affected paths: `tests/loop_test.py`, `tests/regression/test_endpoint_validation.py`
  - size estimate: M

### Should-Do

- [x] Finish filename-stem parity cleanup for remaining world YAML and vault Markdown files.
  - affected paths: `data/world/hollow_crown/surface/alpine_peaks/`, `data/world/hollow_crown/surface/inner_ramparts/`, `data/world/hollow_crown/surface/northeastern_volcanic_highlands/`, `data/world/hollow_crown/surface/western_temperate_forest/`, `data/world/hollow_crown/underworld/`, `prompts/world_vault/hollow_crown/surface/alpine_peaks/`, `prompts/world_vault/hollow_crown/surface/inner_ramparts/`, `prompts/world_vault/hollow_crown/surface/northeastern_volcanic_highlands/`, `prompts/world_vault/hollow_crown/surface/western_temperate_forest/`, `prompts/world_vault/hollow_crown/underworld/`
  - size estimate: L
- [x] Refresh README version strings, endpoint inventory, project-structure listing, and `/session/new` sample payload.
  - affected paths: `README.md`
  - size estimate: S
- [x] Add contract-path coverage for uncovered route handlers.
  - affected paths: `tests/contract/test_openapi_contract.py`, `api/routes/location.py`, `api/routes/roll.py`, `api/routes/scene.py`, `api/routes/state.py`, `api/routes/tags.py`
  - size estimate: M

### Nice-to-Have

- [x] Remove the lingering `Zarkeros's Fortress` display name if canon authority confirms the rename.
  - affected paths: `data/world/hollow_crown/surface/northeastern_volcanic_highlands/zarkeros_lair.yaml`, `prompts/world_vault/hollow_crown/surface/northeastern_volcanic_highlands/zarkeros_lair.md`
  - size estimate: S
- [x] Fill or remove empty `tags` lists on canonical world nodes and mirrors.
  - affected paths: `data/world/hollow_crown/surface/central_draconic_grasslands/draconic_grasslands_edge.yaml`, `data/world/hollow_crown/surface/southwestern_mystic_wetlands/valley_edge_overlook.yaml`, `prompts/world_vault/hollow_crown/surface/central_draconic_grasslands/draconic_grasslands_edge.md`, `prompts/world_vault/hollow_crown/surface/southwestern_mystic_wetlands/valley_edge_overlook.md`
  - size estimate: S
- [x] Remove the legacy `hollow-crowm` string from audit artifacts if repo-wide grep should stay at zero.
  - affected paths: `docs/audit_convention_drift.md`
  - size estimate: S
- [ ] Confirm Alembic filename behavior remains compatible with `validate_naming.py` before the next migration lands.
  - note: existing migration passes current regex; future non-snake revision stems should fail CI.
  - affected paths: `alembic/versions/`, `scripts/validate_naming.py`
  - size estimate: XS
- [ ] Trim `prompts/engine.md` before any future content addition.
  - note: current GPT Builder budget is effectively exhausted at 7999/8000 chars.
  - affected paths: `prompts/engine.md`
  - size estimate: XS
- [ ] Revisit a stronger `validate_naming.py` ↔ `docs/conventions.md` drift guard if documented exceptions return in a more explicit section.
  - note: current parser cross-check exists for the present exception lists; future doc structure changes may warrant a stricter implementation.
  - affected paths: `scripts/validate_naming.py`, `docs/conventions.md`
  - size estimate: XS

---

## 🚫 Restricted Future Builds

These items are not buildable within the current architecture without significant rebuild. Documented here for future planning.

### Full Multi-Agent Orchestration

**Barrier:** Mystic Weave uses a single custom GPT instance via the GPT builder. Running separate specialized model instances for Narrator, Referee, Planner, and Extractor roles requires an orchestration layer — either a custom backend that manages multiple API calls and coordinates outputs, or migrating away from the GPT builder entirely to a direct API implementation. Neither is a small change.
**When to revisit:** When the GPT builder becomes the bottleneck and direct API control is needed for reliability or cost.

### Combat Subsystem

**Barrier:** Explicitly deferred. A real combat system requires its own turn structure, initiative, action economy, and resolution model distinct from the current narrative roll system. Building it on top of the existing d100 roll-under framework is possible but requires new endpoints, new state schema (combat status, turn order, active effects), and significant GPT instruction changes. The current system handles combat narratively.
**When to revisit:** When narrative combat resolution feels insufficient and players need tactical depth.

### NPC Simulation — Independent Goals and Schedules

**Barrier:** Treating NPCs as autonomous agents with their own goals, schedules, and world-modifying actions requires a simulation layer that runs independently of player turns. This is architecturally separate from the current request-response game loop. NPCs currently have static attitude scores and narrative flavor — they react, they do not act.
**When to revisit:** When the world needs to feel like it moves without the player.

### Procedural Content Generation

**Barrier:** Encounter generation, dynamic loot tables, and procedural world events require a generation layer with its own rules and randomness model separate from the dice roller. The current world is entirely authored. Procedural content would need to integrate with the location graph, the faction system, and the economy without contradicting canon.
**When to revisit:** When authored content cannot keep pace with player exploration.

### Vector Search Lore Retrieval

**Barrier:** Currently all lore is in static knowledge files uploaded to the GPT builder. A semantic retrieval layer would allow the GPT to query specific lore on demand rather than having everything in context. Requires embedding infrastructure, a vector database, and a retrieval API — meaningful infrastructure that doesn't exist in the current stack.
**When to revisit:** When the GPT knowledge file upload limit or context ceiling becomes a real constraint on world depth.

### Multi-Player Support

**Barrier:** The entire architecture assumes one player per session. Session state, character state, and the turn loop are single-player constructs. Multi-player would require concurrent session management, shared world state with conflict resolution, and a turn coordination layer. Not a small addition.
**When to revisit:** If the game ever needs to support shared campaigns.
