# Mystic Weave — TODO

Last updated: 2026-05-02

## How to read this document

This is the project's primary work-tracking document. Anyone — Daniel, Claude Code, Claude (web), a future contributor — should be able to read this and understand:

1. What's the next thing to work on
2. What's deferred and why
3. What's structurally blocked and won't be addressed soon

If you walk in cold and only read one section, read **Current Focus**.

---

## CURRENT FOCUS

**New-Sylvara character creation walkthrough + GPT prompt re-upload.**

The architecture-cleanup arc is complete (Briefs 8–11, SHA `9331f9e`). Production DB is wiped and seeded clean. CI now enforces: engine.md byte ceiling, data↔vault mirror parity, README version sync, calendar canon parity, arc registry parity. Repo is in the cleanest state it's been in this session.

Two operational steps remain before resuming live play:

1. **Re-upload prompts to GPT Builder.** Specifically `engine.md`, `scene-structure.md`, `world-rules.md`, and `calendar.md`. The narrator GPT is currently running on stale prompts (pre-Brief-7 narrator discipline rules; pre-Brief-9 dragon_breath/draconic_traits removal; pre-Brief-11 calendar alignment).

2. **New Sylvara character creation + standing integration.** Walk through `/character/create` against the cleaned production DB. Verify the resulting character record has no legacy field artifacts. Then write Sylvara's lightweight standing data (generic group references — Heartwardens, Greenshields, Western Rangers, House Heartwood, House Vaelaryn, Sacred Grove — no named NPCs, no contaminated location data) as a state delta.

After that, live play resumes from a clean baseline.

---

## RECENTLY COMPLETED

- **Brief 11 — Architecture cleanup (2026-05-02, SHA `9331f9e`).** Calendar aligned to 360-day model in `prompts/calendar.md`; engine.md byte ceiling enforced in `validate_prompts.py`; data↔vault mirror parity enforced; README version synced 4.4.0 → 4.8.0 + drift check added; `MechanicalEffect` consolidated; state.py UPSERT SQL extracted to `api/sql/game_state_sql.py`; calendar parity test (3 assertions) and arc registry parity test (4 assertions) added. `StateRepository` retained as the arc-settlement state-mutation interface.
- **Brief 10 — Backend wipe + reseed (2026-05-02).** Production DB cleared (sessions/arcs/runtime locations); reseeded from `data/world/`. SHA `a5b424b` live at the time. Single-pass plan after discovering `.env` and Railway point at the same database.
- **Brief 9 — Pre-wipe cleanup (2026-05-02, SHA `a5b424b`).** Retired `draconic_traits` from `CharacterModel` and `CharacterStateDelta`; retired `dragon_breath` application tag entirely; removed Breath Weapon section from `world-rules.md`; deleted dead regression test; deleted `repair_structured_state.py`, `reconcile_topology.py`, orphan v4 fixture; added `chalk` and `gear-animal-feed` catalog items + price entry. API bumped to 4.8.0.
- **Brief 8 — System audit (2026-05-02, SHA `7ca54a7`).** Comprehensive read-only system audit at `docs/audit/system_audit_2026-05-02.md`. 10 targets covering legacy artifacts, schema drift, repair scripts, location-table runtime/seed indistinguishability, etc.
- **Architecture review (2026-05-02, SHA `09e3a66`).** Structural-choice review at `docs/audit/architecture_review_2026-05-02.md`. Picks up above the system audit. Surfaced the 360-vs-366-day calendar disagreement, unenforced engine.md ceiling, unenforced data↔vault mirror, README staleness, MechanicalEffect duplication, half-built (later: narrow-purpose) repository pattern.
- **Brief 7 — Narrator discipline (2026-05-01, SHA `ec87627`).** Backend-narration suppression rule, Pursuit Closure Shapes section, Companion Role Preservation section. engine.md tightened to 7,998 bytes (under 8,000 ceiling).
- **Brief 6 — Log entry discipline (2026-05-01, SHA `28d6b75a`).** Typed log entries with keep/exclude rules in `scene-structure.md`; engine.md pointer; weather Pydantic warnings suppressed; FastAPI HTTP_422 deprecations cleaned up; SyntaxWarning in test fixed.

---

## ENTITY REGISTRY — REMAINING WORK

PR 1 (consolidation) and PR 2 (companion vocab registry move) are complete. Two future items remain:

- [ ] Future facets: `combat`, `harvest`. Schema reserves the slots; not authored in PR 1.
- [ ] Future endpoint: `/catalog/entities` with `kind=` filter. Currently only `/catalog/creatures` is exposed (sources from filtered entities).

---

## CATALOG WORK

### Active

- [ ] **Cross-reference materials ↔ ecology**: items reference materials (silverbark-ash, thornroot-stalker-hide, etc.); materials reference biomes; entity files reference creatures whose materials we catalog. The links exist conceptually but aren't formalized. Decide if this needs a structured cross-reference layer or stays narrative-only.

### Catalog stabilization follow-ups

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

- [ ] **Pre-test review pass on prompts** — read each prompt file looking for stale references, contradictions with the current backend contract, and inconsistencies that have accumulated. Some of this was addressed in Brief 11 (calendar canon, world-rules dragon_breath retirement); a broader sweep would catch remaining accretion.
- [ ] **GPT Builder upload checklist documentation** — the architecture review (2026-05-02) flagged this as a Notable gap. `operational-runbook.md` covers Postgres, Railway, contract drift, smoke bundles — but no section on GPT-side artifacts. When prompts change, the human must remember to re-upload. Add a short section to the runbook listing which files trigger which uploads.
- [ ] **Decide on prompt restructuring strategy** — slot pressure is real (~17 of 20 used after `arc-rules.md` added). Options identified:
  1. Hybrid model — extract structured data (denomination tables, regional mappings, vocabularies) to JSON; leave reasoning prose in markdown. Saves ~30% per file. Lower payoff.
  2. Fold smaller rules files (economy-rules, difficulty-rules) into existing larger files like `world.md`. Frees full slots.
  3. Consolidate cross-referencing rules into a single `play-rules.md`. Items, economy, and difficulty all reference each other; merge might improve coherence.

  Decision deferred — not urgent until slot count climbs further.

---

## DEFERRED — ARCHITECTURE REVIEW FOLLOW-UPS

Items from `docs/audit/architecture_review_2026-05-02.md` not addressed in Brief 11. Listed in roughly descending value.

- [ ] **Add `source` column to `locations` table.** Currently runtime-created locations are indistinguishable from canonical seed rows, so the only wipe option is `TRUNCATE locations CASCADE` followed by reseed (which is what Brief 10 did). Adding a `source` column (`'seed' | 'runtime'`) would enable per-tier wipes. Migration + seed_locations.py update + POST /location update. Not urgent but valuable for future targeted resets.
- [ ] **Calendar vocabulary triplication elimination.** Month names + season map + festivals appear in `api/time_advance.py:8-31`, `prompts/calendar.md:22-48`, and as defaults in `api/models.py:621-622` and `api/routes/session.py:84-91`. Brief 11's parity test catches the most dangerous case (months and seasons); full elimination would require centralizing the source.
- [ ] **AdvancementState writability mismatch docstring update.** `CharacterStateDelta.advancement` accepts `AdvancementState | None` for "round-trip safety," but the route layer recomputes counters server-side — the value is effectively read-only. Docstring at `api/models.py:743-766` documents this; the schema does not surface it. Consumers reading the OpenAPI schema may believe they can set advancement values directly.
- [ ] **GPT-side spec validation against live GPT.** No equivalent of `verify_production_contract.py` exists for the GPT — i.e., no script that checks "the schema GPT Builder is actually serving matches `openapi.gpt.json`." Production verifier covers the API but not the GPT actions registration.
- [ ] **pytest filterwarnings configuration.** `pytest.ini` doesn't set `filterwarnings`. Brief 6 fixed weather Pydantic warnings by code change; the next deprecation/serializer warning will accumulate silently. Adding `filterwarnings = error::DeprecationWarning:pydantic` would convert the next one into a CI failure.
- [ ] **Marginal duplications.** `_plain_validation_errors` helper duplicated verbatim in 3 routes; `WorldModel` defaults reimplemented by hand in `api/routes/session.py:66-92`. Both are low drift risk; clean up when convenient.

---

## REFACTORING (INCREMENTAL)

- [ ] **`api/models.py` incremental split.** 1400-line kitchen sink. Per project policy: when any model in `models.py` next needs significant changes, that model moves to a new file as part of the same change. Concrete trigger: arc model edits → pull into `api/models/arc.py`. Same for character / world / item / advancement when each is next touched. Do not propose a single brief that splits the whole file at once. **Brief 13 (2026-05-02) extracted `character.py`; remaining models still in `__init__.py`.**

- [ ] **v5 → v5.1 armor migration (only if any v5-shaped record carrying `knowledge.armor` ever appears).** Brief 14 (2026-05-02, 5.0.0 → 5.1.0) retired the `armor` knowledge group. Production DB was empty when the brief landed, so no migration script was authored. If a v5 character record with `knowledge.armor` ever surfaces (e.g., a stale fixture, an exported snapshot, an import from another environment), the cleanup is: rewrite `knowledge.armor.applications.{light_armor,medium_armor,heavy_armor}` to top-level groups; move type-specific applications under the new parents (`padded` → `light_armor`, etc.); move `unarmored` to `martial_arts`; delete `knowledge.armor`. Sketch a script under `scripts/migrate_character_armor.py` if/when needed.

---

## DEFERRED PENDING ARC SYSTEM v1 OBSERVATIONS

Held until a sustained period of live play under Brief 7's narrator discipline rules and Brief 11's calendar canon. Watch for during live play:

- Whether the GPT correctly distinguishes formal vs emergent at arc creation
- Whether calibrated AP envelopes feel right in practice
- Whether hard-cap enforcement produces clean transitions or creates friction
- Whether the spawn vs replace vs merge decision tree (added 2026-05-01) is followed
- Whether Brief 7's Pursuit Closure Shapes rule actually prevents narrator drift on chase/investigation arcs
- Whether the typed log entry system reduces session log bloat
- Whether tag advancement counters increment correctly under the per-domain pattern
- Whether companion role-separation is honored on multi-vector commands

### Enchantment-rules arc

**Status:** design draft exists at `/mnt/user-data/outputs/enchantment-rules-design-draft.md` (321 lines). All five open questions have recommended answers. Implementation plan covers 5 commits.

**When to revisit:** once arc system v1 has been validated through 2–4 weeks of play.

**Risk if deferred too long:** GPT continues to lack a structural framework for how enchanted items are created, sustained, and contested. Current `mechanical_effect` field handles application; nothing handles lifecycle.

### NPC persistence (Phase A)

**Status:** design doc at `docs/design/npc-persistence-design.md` awaiting review.

### Backend scene records

**Status:** currently scene boundary remains GPT-judged per Arc System v1 design. If live play reveals scene undercount/overcount breaking envelope enforcement, this becomes necessary.

### Companion subsystem expansion

**Status:** not yet scoped.

---

## SUBSYSTEMS DEFERRED (LARGER ARCS)

- [ ] Services subsystem (`data/catalog/services/`)
- [ ] Vendors subsystem (`data/catalog/vendors/`)
- [ ] Crafting subsystem (`data/catalog/crafting/recipes.json`, `stations.json` beyond `materials.json`)
- [ ] Bestiary content. Authoring source exists at `prompts/future_development/fauna.md` (biome-scoped fauna palette, names only). Schema decision pending — would feed future bestiary/combat/encounter system work.
- [ ] **HP / armor system reassessment.** Flagged twice in dev session notes as "still kind of a mess." Needs a focused design pass to surface what specifically feels wrong before attempting a fix.
- [ ] **Magic progression mechanic.** Counter-based advancement (cast spell N times to bank advancement progress) plus failure-tier system for caster-tier-vs-spell-tier mismatches. Real mechanic gap; design conversation pending.
- [ ] **Planning vs dice — making contingencies matter.** Currently a clean plan can still be blown up by a single bad roll, even when contingencies were declared. System design problem at the same scale as Arc System v1.
- [ ] **Storage architecture review.** Single `game_states` row holding character + world + log JSONB hits scaling friction as content grows (sapient companions, expanded reputation, longer session logs). Splitting into separate tables/columns reduces coupling but is a substantial migration. Defer until response-size pressure becomes pain rather than projected pain.

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