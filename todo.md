# Mystic Weave — TODO

Last updated: 2026-05-03

## How to read this document

This is the project's primary work-tracking document. Anyone — Daniel, Claude Code, Claude (web), a future contributor — should be able to read this and understand:

1. What's the next thing to work on
2. What's deferred and why
3. What's structurally blocked and won't be addressed soon

If you walk in cold and only read one section, read **Current Focus**.

---

## CURRENT FOCUS

**Backend Authority Arc (active).**

Sylvara has been authored against the v5.1 schema and live play has resumed. The May 2 session debrief surfaced that the narrator GPT cannot reliably handle the volume of rule-following currently asked of it: progression workflow drifted, arc structure decisions slipped, parent-cap and registry classification leaned on memory rather than authority, and admin-correction-only updates couldn't be expressed against the existing `/delta` endpoint.

The strategic response is to move enforcement and rules-application from the narrator GPT into the backend. The narrator's job collapses to prose, dialogue, and pacing; structure becomes the backend's responsibility. Three phases (Briefs 16–23) installed below as the active plan.

If a future brief changes plan, retire that brief's section here rather than letting the arc plan rot.

---

## RECENTLY COMPLETED

- **Brief 18 — Progression scan + commit endpoints (2026-05-03, 5.1.3 → 5.2.0).** `POST /progression/scan` validates proposed tag advances against structured scene actions; returns ranked candidates with explicit/implicit/contextual fit, parent-cap and registry checks, and proposed-vs-strongest comparison. `POST /progression/commit` atomically applies one validated advance inside a SELECT FOR UPDATE transaction; reuses `_apply_tag_advancement_counters` from `state.py` for counter-rollover math; auto-bumps parent group/field when needed (matches Brief 15 seed behavior); appends a typed log entry of new type `progression`. Seven scene action types (`spell_cast`, `weapon_attack`, `social_roll`, `perception_roll`, `movement`, `defense`, `generic_roll`) form a discriminated union. The optional `scene_id` parameter is accepted but inert; activates in Brief 19. 22 new contract tests. GPT spec at 30/30 — Brief 19 will need consolidation.
- **Brief 17 — Registry lookup endpoint + GPT spec slot recovery (2026-05-03, 5.1.2 → 5.1.3).** `GET /registry/{name}` for single-entity lookup across applications, knowledge groups, magic fields, and spells; returns `{name, kind, data}` or 404 with closest-match suggestions. New `list_spells()` accessor in `api/game_data.py` (closes a long-standing gap). GPT spec excludes `POST /state/{session_id}` and `GET /companion/{companion_id}` to recover slots — both stay in `openapi.json`. Net GPT spec change 29/30 → 28/30.
- **Brief 16 — Backend hygiene + annotation endpoint (2026-05-03, 5.1.1 → 5.1.2).** `POST /state/{session_id}/annotation` for canon corrections that don't mutate gameplay state. `AdvancementState` server-recompute behavior documented in docstrings. `_plain_validation_errors` consolidated into `api/routes/_helpers.py`; `WorldModel` defaults in `session.py` use `WorldModel().model_dump()`. todo.md rewritten with Backend Authority Arc as active focus.
- **Brief 15 — `seed_character` parent-tier bump (2026-05-03, 5.1.0 → 5.1.1).** When stacking pushed an application tier above its parent group's stacked tier, `seed_character` now bumps the parent up to match. Prevents 500s on `/session/new` for combinations like elf/feywood_wilds/warden/outlander where ecology stacks to T3 but nature only to T2. Smoke-checked across all 6336 ancestry × culture × focus × background combos: zero failures. New regression test added.
- **Brief 14 — Retire `armor` knowledge group; promote `light_armor`/`medium_armor`/`heavy_armor`/`shields` (2026-05-02, 5.0.0 → 5.1.0).** Registry data correction: `armor` group deleted; the four armor classes become knowledge groups; type-specific armors (`padded`, `chain_shirt`, `plate`, etc.) become applications under their class; `unarmored` reparented to `martial_arts`. Catalog items, creation templates, prompt docs, and combat registries (`combat_knowledge.json`, `combat_applications.json`) all aligned. Combat code untouched.
- **Brief 13 — Nested character schema (2026-05-02, 4.8.0 → 5.0.0, SHA `4c6d218`).** `CharacterModel` knowledge groups visibly contain their applications and magic fields visibly contain their spells. New `KnowledgeGroupRecord` and `MagicFieldRecord` (and `-Delta` variants) with structural parent-cap validators. Package split: `api/models.py` → `api/models/{__init__.py, character.py}`. v4→v5 migration script + idempotent chained migration in `migrate_character_v4`. Twelve test files updated.
- **Brief 12 — `closure_summary` log payload optional (SHA `6f6356d`).** Arc record holds the structured settlement ledger; the closure_summary log entry no longer requires a payload. Cleans up the small UX wart where every closure_summary forced an empty `payload: {}`.
- **Brief 11 — Architecture cleanup (2026-05-02, SHA `9331f9e`).** Calendar aligned to 360-day model in `prompts/calendar.md`; engine.md byte ceiling enforced in `validate_prompts.py`; data↔vault mirror parity enforced; README version synced 4.4.0 → 4.8.0 + drift check added; `MechanicalEffect` consolidated; state.py UPSERT SQL extracted to `api/sql/game_state_sql.py`; calendar parity test (3 assertions) and arc registry parity test (4 assertions) added. `StateRepository` retained as the arc-settlement state-mutation interface.
- **Brief 10 — Backend wipe + reseed (2026-05-02).** Production DB cleared (sessions/arcs/runtime locations); reseeded from `data/world/`. SHA `a5b424b` live at the time. Single-pass plan after discovering `.env` and Railway point at the same database.
- **Brief 9 — Pre-wipe cleanup (2026-05-02, SHA `a5b424b`).** Retired `draconic_traits` from `CharacterModel` and `CharacterStateDelta`; retired `dragon_breath` application tag entirely; removed Breath Weapon section from `world-rules.md`; deleted dead regression test; deleted `repair_structured_state.py`, `reconcile_topology.py`, orphan v4 fixture; added `chalk` and `gear-animal-feed` catalog items + price entry. API bumped to 4.8.0.
- **Brief 8 — System audit (2026-05-02, SHA `7ca54a7`).** Comprehensive read-only system audit at `docs/audit/system_audit_2026-05-02.md`. 10 targets covering legacy artifacts, schema drift, repair scripts, location-table runtime/seed indistinguishability, etc.
- **Architecture review (2026-05-02, SHA `09e3a66`).** Structural-choice review at `docs/audit/architecture_review_2026-05-02.md`. Picks up above the system audit. Surfaced the 360-vs-366-day calendar disagreement, unenforced engine.md ceiling, unenforced data↔vault mirror, README staleness, MechanicalEffect duplication, half-built (later: narrow-purpose) repository pattern.
- **Brief 7 — Narrator discipline (2026-05-01, SHA `ec87627`).** Backend-narration suppression rule, Pursuit Closure Shapes section, Companion Role Preservation section. engine.md tightened to 7,998 bytes (under 8,000 ceiling).
- **Brief 6 — Log entry discipline (2026-05-01, SHA `28d6b75a`).** Typed log entries with keep/exclude rules in `scene-structure.md`; engine.md pointer; weather Pydantic warnings suppressed; FastAPI HTTP_422 deprecations cleaned up; SyntaxWarning in test fixed.

---

## BACKEND AUTHORITY ARC (active)

The May 2 debrief made it clear: the narrator cannot reliably enforce structure across 17+ prompt files. The fix is structural — move enforcement into the backend so the narrator focuses on prose. Three phases, eight briefs (16–23).

### Phase 1 — Foundation hygiene (Briefs 16–17)

Lay groundwork: small endpoints and registry exposure that the later enforcement phases depend on. Patch-level versions; no schema breaks.

- [x] **Brief 16 — Backend hygiene + annotation endpoint.** Adds `POST /state/{session_id}/annotation` for canon corrections that don't mutate gameplay state. Cleans up `AdvancementState` docstrings, helper duplication, and `WorldModel` defaults. Refreshes this todo. Landed as 5.1.2.
- [x] **Brief 17 — Registry lookup endpoint.** Single consolidated `GET /registry/{name}` returns `{name, kind, data}` across applications, knowledge groups, magic fields, and spells, with 404 + closest-match suggestions for unknown names. Backend becomes the source of truth for tag classification. Landed as 5.1.3.

### Phase 2 — Enforcement migration (Briefs 18–20)

Move the structure-heavy workflows the narrator demonstrably can't run reliably into backend endpoints. Each brief in this phase should reduce prompt content as a side effect.

- [x] **Brief 18 — Progression scan + commit endpoints.** `POST /progression/scan` validates proposed advances against structured scene actions and returns ranked candidates; `POST /progression/commit` atomically applies one validated advance with counter-rollover math and parent-bump fallback. Replaces the prompt-side progression workflow the May 2 debrief showed the GPT cannot reliably execute. Landed as 5.2.0.
- [ ] **Brief 19 — Backend scene records.** Scene boundaries become server-known events with a dedicated table. Activates the previously-deferred "Backend scene records" item: enables real envelope enforcement (caps, locations-visited, scenes-since-last-progression) instead of GPT-judged scene counting. Probable 5.4.0 (schema change).
- [ ] **Brief 20 — Origin vs phase clarification.** Rules + mechanism for emergent → formal arc conversion when phase shifts trigger institutional uptake. Clarifies AP eligibility and prevents "emergent forever" as a permanent escape hatch. Activates the deferred "Whether the GPT correctly distinguishes formal vs emergent" observation.

### Phase 3 — Prompt collapse + catalog unification (Briefs 21–23)

With backend enforcement in place, prompts can shrink dramatically. Catalog and registry parallels can be unified now that backend authority replaces redundant prose.

- [ ] **Brief 21 — Prompt content audit and shrink.** Retire content the backend now serves. Aim for a much smaller prompt set — many slot-pressure decisions in current `## PROMPT ARCHITECTURE` become moot.
- [ ] **Brief 22 — Registry / catalog unification.** Resolve `data/tags/` ↔ `data/catalog/registries/` parallels, `data/economy/` ↔ `data/catalog/economy/`, etc. Single source per category. Absorbs the existing "Catalog stabilization follow-ups" items.
- [ ] **Brief 23 — Log management strategy.** Periodic compression, retention, or move admin corrections out of the gameplay log. Addresses log bloat surfaced in the May 2 debrief and gives `/state/{session_id}/annotation` (Brief 16) a more permanent home if the log-append substrate proves cramped.

---

## ENTITY REGISTRY — REMAINING WORK

PR 1 (consolidation) and PR 2 (companion vocab registry move) are complete. Two future items remain:

- [ ] Future facets: `combat`, `harvest`. Schema reserves the slots; not authored in PR 1.
- [ ] Future endpoint: `/catalog/entities` with `kind=` filter. Currently only `/catalog/creatures` is exposed (sources from filtered entities).

---

## CATALOG WORK

### Active

- [ ] **Cross-reference materials ↔ ecology**: items reference materials (silverbark-ash, thornroot-stalker-hide, etc.); materials reference biomes; entity files reference creatures whose materials we catalog. The links exist conceptually but aren't formalized. Decide if this needs a structured cross-reference layer or stays narrative-only.

### Catalog stabilization follow-ups (now Brief 22 territory)

The items below are the unification target for Brief 22 in the Backend Authority Arc.

- [ ] Review remaining parallel namespaces. `data/tags/magic_fields.json` was consolidated into `data/catalog/registries/magic_fields.json` 2026-05-01. The remaining parallels:
  - `data/tags/applications.json` and `data/tags/knowledge_groups.json` still separate from `data/catalog/registries/`. These have rich content (8+ fields per entry); deliberate consolidation pass needed if pursued.
  - `data/economy/` vs `data/catalog/economy/`
  - `data/magic/`, `data/companions/`, `data/characters/`, `data/npcs/`

### Item schema follow-ups

- [ ] Author next batch of items (10–20 mundane) — gear, ammunition, apparel coverage gaps. Items in progress at prior session close: short sword, hand axe, studded leather armor, Thornroot stalker-derived item.
- [ ] JSON Schema export: emit `data/catalog/schemas/*.schema.json` from Pydantic models for non-Python consumers (GPT builder).
- [ ] Pricing rules engine: design and implement `economy/price_rules.json` so future items can use computed pricing rather than authored `value_cd`.
- [ ] Mundane catalog sub-filtering: response size approaching ~80KB threshold; sub-filter `kind=mundane` before it crosses.

---

## LORE / WORLDBUILDING

- [ ] **Institutional structure for Feywood** is implied by the catalog (Heartwardens, Greenshields, House Thornmere, House Ironsap) but not yet authored canonically. Sketch governance and access hierarchy when the catalog hints make it necessary.
- [ ] `data/world/` continues catching up to `prompts/world_vault/`. The vault is the leading edge; data files lag. Ongoing authoring work, not a single task. (Note: as of Brief 11 the mirror is now CI-enforced; new files added on either side without a paired file on the other will fail CI.)

---

## PROMPT ARCHITECTURE

The Backend Authority Arc reframes most of this section: Brief 21 will subsume the restructuring decision once backend enforcement absorbs current prompt content.

- [ ] **Pre-test review pass on prompts** — read each prompt file looking for stale references, contradictions with the current backend contract, and inconsistencies that have accumulated. Some of this was addressed in Brief 11 (calendar canon, world-rules dragon_breath retirement); a broader sweep would catch remaining accretion. Brief 21 will likely absorb this.
- [ ] **GPT Builder upload checklist documentation** — the architecture review (2026-05-02) flagged this as a Notable gap. `operational-runbook.md` covers Postgres, Railway, contract drift, smoke bundles — but no section on GPT-side artifacts. When prompts change, the human must remember to re-upload. Add a short section to the runbook listing which files trigger which uploads.

---

## DEFERRED — ARCHITECTURE REVIEW FOLLOW-UPS

Items from `docs/audit/architecture_review_2026-05-02.md` not addressed in Brief 11. Listed in roughly descending value.

- [ ] **Add `source` column to `locations` table.** Currently runtime-created locations are indistinguishable from canonical seed rows, so the only wipe option is `TRUNCATE locations CASCADE` followed by reseed (which is what Brief 10 did). Adding a `source` column (`'seed' | 'runtime'`) would enable per-tier wipes. Migration + seed_locations.py update + POST /location update. Not urgent but valuable for future targeted resets.
- [ ] **Calendar vocabulary triplication elimination.** Month names + season map + festivals appear in `api/time_advance.py:8-31`, `prompts/calendar.md:22-48`, and as defaults in `api/models/__init__.py` and `api/routes/session.py`. Brief 11's parity test catches the most dangerous case (months and seasons); full elimination would require centralizing the source.
- [x] **AdvancementState writability mismatch docstring update.** Addressed in Brief 16: docstring updates on `AdvancementState` and `CharacterStateDelta.advancement` document server-recompute behavior so consumers reading the OpenAPI schema don't believe they can set advancement values directly.
- [ ] **GPT-side spec validation against live GPT.** No equivalent of `verify_production_contract.py` exists for the GPT — i.e., no script that checks "the schema GPT Builder is actually serving matches `openapi.gpt.json`." Production verifier covers the API but not the GPT actions registration.
- [ ] **pytest filterwarnings configuration.** `pytest.ini` doesn't set `filterwarnings`. Brief 6 fixed weather Pydantic warnings by code change; the next deprecation/serializer warning will accumulate silently. Adding `filterwarnings = error::DeprecationWarning:pydantic` would convert the next one into a CI failure.
- [x] **Marginal duplications.** Addressed in Brief 16: `_plain_validation_errors` consolidated into `api/routes/_helpers.py`; `WorldModel` defaults in `session.py` now use `WorldModel().model_dump()` rather than a hand-built dict.

---

## REFACTORING (INCREMENTAL)

- [ ] **`api/models.py` incremental split.** 1400-line kitchen sink. Per project policy: when any model in `models.py` next needs significant changes, that model moves to a new file as part of the same change. Concrete trigger: arc model edits → pull into `api/models/arc.py`. Same for character / world / item / advancement when each is next touched. Do not propose a single brief that splits the whole file at once. **Brief 13 (2026-05-02) extracted `character.py`; remaining models still in `__init__.py`.**

- [ ] **v5 → v5.1 armor migration (only if any v5-shaped record carrying `knowledge.armor` ever appears).** Brief 14 (2026-05-02, 5.0.0 → 5.1.0) retired the `armor` knowledge group. Production DB was empty when the brief landed, so no migration script was authored. If a v5 character record with `knowledge.armor` ever surfaces (e.g., a stale fixture, an exported snapshot, an import from another environment), the cleanup is: rewrite `knowledge.armor.applications.{light_armor,medium_armor,heavy_armor}` to top-level groups; move type-specific applications under the new parents (`padded` → `light_armor`, etc.); move `unarmored` to `martial_arts`; delete `knowledge.armor`. Sketch a script under `scripts/migrate_character_armor.py` if/when needed.

- [ ] **Creation template parent-tier audit (deferred from Brief 15).** Brief 15 (2026-05-03, 5.1.0 → 5.1.1) added an auto-bump in `seed_character`: when stacking produces an application tier above its parent group's stacked tier, the parent is bumped to match. This is a safe fix that prevents creation crashes, but it can produce characters with knowledge tiers higher than templates explicitly grant. The Phase 3 smoke check across all 6336 combos showed candidate bumps clustering in `influence`, `discipline`, `nature`, `lore`, `arcana`. Audit each focus/culture/background combination in those groups to determine whether the bump represents intent drift (templates should grant matching knowledge directly) versus coincidence (single-layer grants that already match). Adjust authored templates where the bump is unintentional. Out of scope at fix time; flagged here for intentional cleanup.

---

## DEFERRED PENDING ARC SYSTEM v1 OBSERVATIONS

The May 2 session provided substantial observations. Two items below are now activated as part of the Backend Authority Arc:

- "Backend scene records" → activated as **Brief 19**
- "Whether the GPT correctly distinguishes formal vs emergent at arc creation" → activated by **Brief 20**

The remaining observations stay deferred pending more sustained play under the post-arc enforcement model:

- Whether calibrated AP envelopes feel right in practice
- Whether hard-cap enforcement produces clean transitions or creates friction
- Whether the spawn vs replace vs merge decision tree (added 2026-05-01) is followed
- Whether Brief 7's Pursuit Closure Shapes rule actually prevents narrator drift on chase/investigation arcs
- Whether the typed log entry system reduces session log bloat (related: Brief 23 log management)
- Whether tag advancement counters increment correctly under the per-domain pattern (related: Brief 18 progression scan)
- Whether companion role-separation is honored on multi-vector commands

### Enchantment-rules arc

**Status:** design draft exists at `/mnt/user-data/outputs/enchantment-rules-design-draft.md` (321 lines). All five open questions have recommended answers. Implementation plan covers 5 commits.

**When to revisit:** once arc system v1 has been validated through 2–4 weeks of play under the new backend authority model.

**Risk if deferred too long:** GPT continues to lack a structural framework for how enchanted items are created, sustained, and contested. Current `mechanical_effect` field handles application; nothing handles lifecycle.

### NPC persistence (Phase A)

**Status:** design doc at `docs/design/npc-persistence-design.md` awaiting review.

### Companion subsystem expansion

**Status:** not yet scoped.

---

## SUBSYSTEMS DEFERRED (LARGER ARCS)

The Backend Authority Arc reframes several of these. Notes inline.

- [ ] Services subsystem (`data/catalog/services/`)
- [ ] Vendors subsystem (`data/catalog/vendors/`)
- [ ] Crafting subsystem (`data/catalog/crafting/recipes.json`, `stations.json` beyond `materials.json`)
- [ ] Bestiary content. Authoring source exists at `prompts/future_development/fauna.md` (biome-scoped fauna palette, names only). Schema decision pending — would feed future bestiary/combat/encounter system work.
- [ ] **HP / armor system reassessment.** Flagged twice in dev session notes as "still kind of a mess." Needs a focused design pass to surface what specifically feels wrong before attempting a fix. Reframes after Phase 2: with backend enforcement in place, the HP/armor reassessment becomes a backend redesign rather than a prompt-rules redesign.
- [ ] **Magic progression mechanic.** Counter-based advancement (cast spell N times to bank advancement progress) plus failure-tier system for caster-tier-vs-spell-tier mismatches. Real mechanic gap; design conversation pending. Reframes as a backend endpoint design after Brief 18 (progression scan) lands.
- [ ] **Planning vs dice — making contingencies matter.** Currently a clean plan can still be blown up by a single bad roll, even when contingencies were declared. System design problem at the same scale as Arc System v1. Reframes as a backend mechanism after Phase 2 — contingency-recognition logic is exactly the kind of structure the narrator can't reliably handle.
- [ ] **Storage architecture review.** Single `game_states` row holding character + world + log JSONB hits scaling friction as content grows (sapient companions, expanded reputation, longer session logs). Splitting into separate tables/columns reduces coupling but is a substantial migration. Connects to **Brief 23** (log management) — the log column in particular is the early pressure point.

---

## IP / LICENSING (OPEN QUESTIONS)

- [ ] Decide on forking permissions — currently CC BY-NC-ND, which restricts derivatives. Confirm whether community forks for personal campaigns are acceptable under the license interpretation.
- [ ] Decide on redistribution scope — what parts of the world content are shareable, what stays restricted to the canonical repo.

---

## CI / PROCESS DEBT

(Most resolved as of late 2026-04. Items below are watch-items only.)

- [ ] Confirm branch protection on main is configured: require Lint+Unit+Contract, Integration+Loop Test, Item Catalog Validation, and Pre-Deploy Contract+Smoke Bundle status checks before merge. (Manual GitHub UI configuration.)
- [ ] Confirm failure notification on main CI is configured.
- [ ] Update GitHub Actions to Node.js 24 before Sept 16 2026 deprecation.

---

## 🚫 RESTRICTED FUTURE BUILDS

These items are not buildable within the current architecture without significant rebuild. Documented for future planning.

### Martial arts as parallel to weapons + armor

**Barrier:** Three fields (defensive, offensive, utility) anchored to different domains, with unarmored as the parallel to armored builds. Worth doing eventually for player builds that go unarmored. Not urgent — current unarmored is underweight but functional.

**When to revisit:** if a player build genuinely tries to be unarmored and the lack of competitive martial-arts progression makes it feel hollow.

### Full Multi-Agent Orchestration

**Barrier:** Mystic Weave uses a single custom GPT instance via the GPT builder. Running separate specialized model instances for Narrator, Referee, Planner, and Extractor roles requires an orchestration layer — either a custom backend that manages multiple API calls and coordinates outputs, or migrating away from the GPT builder entirely to a direct API implementation. Neither is a small change.

**When to revisit:** when the GPT builder becomes the bottleneck and direct API control is needed for reliability or cost.

### Combat Subsystem

**Barrier:** Explicitly deferred. A real combat system requires its own turn structure, initiative, action economy, and resolution model distinct from the current narrative roll system. Building it on top of the existing d100 roll-under framework is possible but requires new endpoints, new state schema (combat status, turn order, active effects), and significant GPT instruction changes. The current system handles combat narratively.

**When to revisit:** when narrative combat resolution feels insufficient and players need tactical depth.

### NPC Simulation — Independent Goals and Schedules

**Barrier:** Treating NPCs as autonomous agents with their own goals, schedules, and world-modifying actions requires a simulation layer that runs independently of player turns. This is architecturally separate from the current request-response game loop. NPCs currently have static attitude scores and narrative flavor — they react, they do not act.

**When to revisit:** when the world needs to feel like it moves without the player.

### Procedural Content Generation

**Barrier:** Encounter generation, dynamic loot tables, and procedural world events require a generation layer with its own rules and randomness model separate from the dice roller. The current world is entirely authored. Procedural content would need to integrate with the location graph, the faction system, and the economy without contradicting canon.

**When to revisit:** when authored content cannot keep pace with player exploration.

### Vector Search Lore Retrieval

**Barrier:** Currently all lore is in static knowledge files uploaded to the GPT builder. A semantic retrieval layer would allow the GPT to query specific lore on demand rather than having everything in context. Requires embedding infrastructure, a vector database, and a retrieval API — meaningful infrastructure that doesn't exist in the current stack.

**When to revisit:** when the GPT knowledge file upload limit or context ceiling becomes a real constraint on world depth.

### Multi-Player Support

**Barrier:** The entire architecture assumes one player per session. Session state, character state, and the turn loop are single-player constructs. Multi-player would require concurrent session management, shared world state with conflict resolution, and a turn coordination layer. Not a small addition.

**When to revisit:** if the game ever needs to support shared campaigns.
