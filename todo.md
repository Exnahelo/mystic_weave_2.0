# Mystic Weave — TODO

Last updated: 2026-04-30

## How to read this document

This is the project's primary work-tracking document. Anyone — Daniel, Cline, Claude, a future contributor — should be able to read this and understand:

1. What's the next thing to work on
2. What recent context they need to be effective
3. What's deferred and why
4. What's structurally blocked and won't be addressed soon

The top section (Active Architectural Arc) is the single most important piece of work currently scoped. Everything below it is either follow-up to that work, smaller independent improvements, or deferred items waiting on capacity or prerequisites.

If you walk in cold and only read one section, read the Arc System v1 section. That's where the project is going next.

---

## ACTIVE ARCHITECTURAL ARC: Arc System v1

### Why this exists

The GPT-driven game has a recurring structural failure: anywhere the rules give the narrator discretion over mechanical outcomes, the narrator drifts. Examples surfaced in recent play:

- The Stalkerhide Cloak's `mechanical_effect` field was ignored twice in close succession until the player explicitly forced application. We addressed the immediate symptom by strengthening the prompt-level enumeration rule, but the underlying pattern is broader.
- Mission closure for Thinwatch Spring undercredited Sylvara across multiple reward tracks. The narrator gave Druidry 3 in the middle of the arc, then closed the mission with "no further rewards" because it incorrectly collapsed the field/knowledge/application/AP/reputation tracks into a single yes/no question.
- Historic mission drift: in past play, simple dungeon arcs expanded indefinitely because nothing constrained scope.

These are the same problem at three different layers. The fix at every layer is the same: **remove narrator discretion over mechanics, give the backend authority over structure, leave the narrator the creative work.**

The arc system is the structural answer to this class of problems. Once the GPT cannot continue past hard cap without an explicit transition, cannot close an arc without calling settle, and cannot improvise reward enumeration because the backend computes it, the entire class of drift bugs becomes structurally impossible at the type level.

This is months-of-work scope, but it's the highest-leverage architectural fix available to the project right now. Everything else (enchantment-rules arc, scene-level structure, encounter budgeting, etc.) is more tractable once arcs exist.

### Locked design decisions

These are settled and not revisitable without explicit re-design:

```json
{
  "ap_policy": {
    "mode": "formal_contract_only",
    "formal_contract_provenance": "strict",
    "formal_contract_inheritance_via_introducer_or_trust_chain": false
  },
  "state_model_v1": {
    "accepted_state_present": false,
    "active_state_name": "in_progress",
    "merged_into_parent_terminal_for_child": true
  },
  "failure_policy_v1": {
    "partial_ap_on_failure": false
  },
  "location_counting_v1": {
    "basis": "canonical_location_ids_only"
  }
}
```

**What "strict provenance" means in practice:** an arc is `formal_contract_qualified: true` only if it was created with an explicit patron (NPC or faction), an explicit objective, and an expected return or deliverable. Trust-network introductions, family connections, social proximity, and emergent problem discovery do **not** confer formal status. Sylvara finding Thinwatch Spring on her own initiative in the western wilds is emergent, regardless of who introduced her to Mereth. Only emergent arcs that get formally chartered (returned to a patron and explicitly tasked) become AP-eligible.

**What this changes about play:** under the arc system, players who want AP from an investigation must convert it into a formal contract with a patron before pursuing it. This is a deliberate game-design pressure toward engaging with the world's social structures. Emergent threads still pay out in tag advancement, reputation, evidence, leverage, and economy — they just don't pay AP.

### Calibrated type defaults

These are the per-type envelope numbers, calibrated against Sylvara's actual play history (Heartwater chain, Thinwatch Spring):

```json
{
  "task_local": {
    "stake_scale_default": "local",
    "ap_award": { "min": 0, "max": 1, "fixed": false },
    "scene_soft_cap": 2,
    "scene_hard_cap": 4,
    "location_soft_cap": 1,
    "location_hard_cap": 2
  },
  "contract_delicate": {
    "stake_scale_default": "situational",
    "ap_award": { "min": 1, "max": 1, "fixed": true },
    "scene_soft_cap": 4,
    "scene_hard_cap": 6,
    "location_soft_cap": 2,
    "location_hard_cap": 3
  },
  "mission_multi_leg": {
    "stake_scale_default": "situational",
    "ap_award": { "min": 1, "max": 2, "fixed": false },
    "scene_soft_cap": 6,
    "scene_hard_cap": 10,
    "location_soft_cap": 3,
    "location_hard_cap": 5
  },
  "undertaking_regional": {
    "stake_scale_default": "regional",
    "ap_award": { "min": 2, "max": 3, "fixed": false },
    "scene_soft_cap": 10,
    "scene_hard_cap": 16,
    "location_soft_cap": 4,
    "location_hard_cap": 7
  },
  "arc_campaign": {
    "stake_scale_default": "campaign",
    "ap_award": { "min": 3, "max": 4, "fixed": false },
    "scene_soft_cap": 16,
    "scene_hard_cap": 24,
    "location_soft_cap": 6,
    "location_hard_cap": 12
  }
}
```

### State machine (v1)

```
proposed → available → in_progress → at_scope_cap → ready_to_close → complete
                                                  ↘                ↘
                                                   failed           failed
                       in_progress → ready_to_close → failed
                       in_progress → abandoned
                       in_progress → replaced_by_successor
                       in_progress → merged_into_parent (terminal for child)
```

`at_scope_cap` is the most important state. When the resolved-scene count hits the type's hard cap, the arc enters `at_scope_cap` and ordinary continuation is refused by the backend. The narrator must propose a transition: `ready_to_close`, `failed`, `replaced_by_successor`, or `merged_into_parent`. This is the structural lever that prevents mission drift.

### Migration policy

Legacy sessions (Sylvara's existing play) remain untyped. **No retroactive arc reconstruction.** The arc system applies to new arcs only, created after Commit 2 lands. Sylvara's first new arc post-Thinwatch becomes the first typed arc in the system.

### Implementation plan: 6 commits, sequential

#### Commit 1 — `feat(arc): add arc data model and persistence`

**Goal:** core schema, no behavior yet.

- `api/models.py`: `Arc`, `ArcBudget`, `ArcConsumption`, `ArcRewardEnvelope`, `ArcConditionSet`, `ArcCondition`, `ArcEscalationRules`, `ArcFlags`, `ArcTimestamps`, all sub-models per the locked design
- Postgres migration: new `arcs` table, JSONB columns for nested structures, indexed on `session_id` and `state`
- `data/catalog/registries/arc_types.json`: type definitions, calibrated defaults, condition vocabulary, state enum (read-only registry data per the catalog convention)
- Read-only repository layer in `api/repositories/arc_repository.py`

No endpoints yet. No business logic. Just the bones.

**Acceptance:** migration runs clean, `Arc.model_validate` works on a sample payload, registry loads with all 5 types and 20+ condition types, validators pass, OpenAPI regen clean.

**Estimate:** 1–2 days.

#### Commit 2 — `feat(arc): add create and read endpoints with provenance validation`

**Goal:** arc creation with full validation, lookup, basic state read.

- `POST /arc/{session_id}/create` — validates type, applies calibrated defaults from registry, enforces strict provenance for `formal_contract_qualified: true`
- `GET /arc/{session_id}` — list arcs for session
- `GET /arc/{session_id}/{arc_id}` — single arc detail
- `GET /arc/{session_id}/active` — filter to `in_progress` and `at_scope_cap`
- Provenance validator: `patron_npc_id_or_patron_faction_present` + `explicit_objective_present` + `expected_return_or_deliverable_present` all required for formal status

**Acceptance:** create endpoint rejects payloads missing required formal-contract fields when `formal_contract_qualified: true`. Read endpoints return correct shape. Contract tests cover happy path plus each insufficient-for-formal-status rejection case (introduction-only, trust-network-only, social-proximity-only, family-connection-only, problem-discovery-without-explicit-tasking).

**Estimate:** 1 day.

#### Commit 3 — `feat(arc): state machine transitions with cap enforcement` ⭐ P0

**Goal:** the heart of the system. Without this, the rest is descriptive rather than prescriptive.

- `POST /arc/{session_id}/{arc_id}/transition` — validates against state machine matrix, enforces closure conditions on `ready_to_close`, enforces failure conditions on `failed`, refuses `in_progress → in_progress` once at hard cap
- `POST /arc/{session_id}/{arc_id}/progress` — consumes resolved scene event, increments `resolved_scenes_used`, updates `locations_visited`, checks soft and hard caps, transitions to `at_scope_cap` when hard cap hit
- State machine validation engine: encodes the allowed transition matrix from the design
- Audit log entries written for every transition

**Acceptance:**
- Hard cap enforcement test: create `mission_multi_leg`, progress 11 scenes, 11th progress call returns transition-required error rather than incrementing
- Soft cap test: at scene 7 of `mission_multi_leg`, progress succeeds but response includes warning flag
- State matrix tests: all illegal transitions rejected with clear error
- Closure condition test: `ready_to_close` rejected if conditions not satisfied
- Failure condition test: `failed` rejected if conditions not satisfied

**Estimate:** 2 days. State machine logic is fiddly; cap enforcement is the most-tested commit.

#### Commit 4 — `feat(arc): spawn, settle, and merge endpoints`

**Goal:** parent/child relationships and reward settlement.

- `POST /arc/{session_id}/{arc_id}/spawn` — creates child arc with parent reference, validates parent state allows spawning, enforces AP envelope partition (parent retains AP unless `ap_ownership: child` explicitly set)
- `POST /arc/{session_id}/{arc_id}/settle` — final reward computation, validates rewards against envelope, writes terminal state, enforces `partial_ap_on_failure: false`
- Merge handling: `merged_into_parent` transition contributes to parent's settlement record, child becomes terminal
- Reward channel non-overlap validation between parent and active children

**Acceptance:**
- Spawn test: parent `undertaking_regional` spawns three children, each with own envelope
- Settle test: `complete` settles AP within envelope, rejects out-of-envelope payouts
- Failure-AP test: failed arc with `awarded_ap > 0` rejected
- Merge test: child `merged_into_parent` contributes to parent's `merge_source_arc_ids` list and emits no own AP

**Estimate:** 1–2 days.

#### Commit 5 — `feat(arc): integrate with progression, reputation, and economy systems`

**Goal:** wire arc settlement into existing game machinery.

- Settlement endpoint calls into existing AP progression code, not a parallel implementation
- Reputation deltas apply via existing reputation update logic, bounded by envelope
- Economy deltas apply via existing economy logic
- Tag advancement remains scene-bound and independent (per locked decision: scene-bound tag advancement is allowed regardless of arc origin or AP eligibility)
- Consequence event emission: closure produces `consequence_events_emitted` list as world-state events

**Acceptance:**
- Integration tests: full lifecycle from create through settle produces correct character and world state changes
- Reputation cap tests: envelope max enforced
- Tag-vs-AP independence test: emergent arc resolved scenes still advance tags despite zero AP eligibility

**Estimate:** 1 day. Mostly wiring.

#### Commit 6 — `feat(prompts): require arc enumeration on mission-shaped events`

**Goal:** prompt-level enforcement parallel to the `mechanical_effect` enumeration pattern that already landed.

- `prompts/engine.md`: when narrating an event that introduces a higher-level objective, narrator must call `/arc/create` before continuing. When closing an arc, narrator must call `/arc/settle` and report the returned envelope. When hard cap fires, narrator must call `/transition` rather than continue narration.
- `prompts/progression-rules.md`: replace contract-bound AP language with arc-bound AP language under the locked AP policy. Reference arc system as authoritative source of awarded AP envelope.
- `prompts/scene-structure.md`: reference arc cap warnings as primary scope-management mechanism (this prompt already exists)
- New top-level prompt `prompts/arc-rules.md`: 600–800 lines, mirrors `magic-rules.md` and `items-rules.md` shape, documents the type system, lifecycle, and procedure for the narrator

Verify `wc -c prompts/engine.md` stays under 8000.

**Acceptance:** prompt validation passes, all updated prompts internally consistent, OpenAPI regen clean, full test suite green, engine.md under 8000 bytes.

**Estimate:** 1 day.

### Total estimate

7–9 days of focused implementation work. Roughly 2 weeks at a normal cadence with normal interruptions.

### What this delivers when complete

- The narrator cannot continue past hard cap without explicit transition
- The narrator cannot close an arc without calling settle
- Settle returns the envelope, so reward enumeration is automatic
- Reward tracks are independent and individually settled — no cross-track collapse
- Spawn is the expected flow for arcs crossing structural boundaries
- Mission drift becomes structurally impossible at the type level

The narrator's discretion over mechanical adjudication of arcs is removed. It retains full discretion over fiction *within* validated arc bounds.

### Out of scope for v1

Per the locked design:

- Backend scene records and scene boundary validation (scene resolution remains GPT-judged)
- Encounter-level or beat-level budgeting
- Evidence-grade subsystem (uses generic `world_flag_present` for now)
- Multi-parent arcs
- Automatic arc creation from narration parser (narrator must explicitly call create)
- Retroactive arc construction for legacy sessions

These are candidates for v2 if the v1 system reveals their need.

---

## CATALOG WORK

### Active

- [ ] **Wire `data/environment/`** (`feywood_animals.json`, `feywood_plants.json`) into code. Currently authored but unread. Decide read pattern: pre-load into game_data like `data/companions/`, or load on demand from a new endpoint.
- [ ] **Cross-reference materials ↔ ecology**: items reference materials (silverbark-ash, thornroot-stalker-hide, etc.); materials reference biomes; environment files reference creatures whose materials we catalog. The links exist conceptually but aren't formalized. Decide if this needs a structured cross-reference layer or stays narrative-only.

### Catalog stabilization follow-ups

- [ ] Audit `data/catalog/registries/` for orphan tags (defined but never used) and missing tags (used in items but not registered).
- [ ] Decide intent of `data/catalog/crafting/materials.json`. Crafting subsystem is documented as deferred but `materials.json` exists.
- [ ] Resolve singular vs plural directory naming inconsistency (`weapon/` vs `weapons/`, `shield/` vs `shields/`). See `docs/items-schema.md`.
- [ ] Review parallel namespaces against `docs/items-schema.md` "What Lives Outside data/catalog/" section. Decide whether to consolidate or keep separate, one namespace at a time:
  - `data/tags/` vs `data/catalog/registries/`
  - `data/economy/` vs `data/catalog/economy/`
  - `data/magic/`, `data/companions/`, `data/characters/`, `data/npcs/`

### Item schema follow-ups

- [ ] Author next batch of items (10–20 mundane) — gear, ammunition, apparel coverage gaps.
- [ ] JSON Schema export: emit `data/catalog/schemas/*.schema.json` from Pydantic models for non-Python consumers (GPT builder).
- [ ] Pricing rules engine: design and implement `economy/price_rules.json` so future items can use computed pricing rather than authored `value_cd`.

---

## LORE / WORLDBUILDING

- [ ] **Institutional structure for Feywood** is implied by the catalog (Heartwardens, Greenshields, House Thornmere, House Ironsap) but not yet authored canonically. Sketch governance and access hierarchy when the catalog hints make it necessary.
- [ ] `data/world/` continues catching up to `prompts/world_vault/`. The vault is the leading edge; data files lag. This is ongoing authoring work, not a single task.

---

## PROMPT ARCHITECTURE

- [ ] **Decide on prompt restructuring strategy** — slot pressure is real (~16 of 20 used). Options identified:
  1. Hybrid model — extract structured data (denomination tables, regional mappings, vocabularies) to JSON; leave reasoning prose in markdown. Saves ~30% per file. Lower payoff.
  2. Fold smaller rules files (economy-rules, difficulty-rules) into existing larger files like `world.md`. Frees full slots.
  3. Consolidate cross-referencing rules into a single `play-rules.md`. Items, economy, and difficulty all reference each other; merge might improve coherence.

  Decision deferred — not urgent until slot count climbs further. **Note:** the arc system will add `prompts/arc-rules.md`, pushing slot count to ~17. Re-evaluate after arc system v1 lands.

---

## CI / PROCESS DEBT

- [ ] Configure branch protection on main: require Lint+Unit+Contract, Integration+Loop Test, Item Catalog Validation, and Pre-Deploy Contract+Smoke Bundle status checks before merge. (User must do this in GitHub UI; not scriptable.)
- [ ] Set up failure notification on main CI (GitHub email-on-failure or Slack webhook). Main CI was red for 30+ runs without anyone noticing in the past.
- [ ] Audit recent direct-to-main pushes: commit `0c4b579b` ("Renames Feywood Glade to Feywood in all content") corrupted `tests/unit/test_companion_models.py` via sloppy find-replace and merged anyway. Investigate whether mass-rename commits go through PR review.
- [ ] Update GitHub Actions to Node.js 24 before Sept 16 2026 deprecation.

---

## DEFERRED PENDING ARC SYSTEM v1

These are designed or partially designed but explicitly held until arc system lands. They are likely to need revision once we see how the arc system behaves in actual play.

### Enchantment-rules arc

**Status:** design draft exists at `/mnt/user-data/outputs/enchantment-rules-design-draft.md` (321 lines). All five open questions have recommended answers. Implementation plan covers 5 commits.

**Why deferred:** the enchantment-rules arc adds activation modes, charges, recharge mechanisms, stability/decay, crafting rules, and stacking/conflict to magical items. Under the arc system, magical items become reward channel outputs of arc settlement. Some of the design decisions in the enchantment draft (how rare is enchantment? routine PC activity or rare narrative beat?) are best answered after seeing how arc-driven reward channels behave in real play.

**When to revisit:** once arc system v1 has been live for enough sessions to validate the reward envelope behavior. Probably 2–4 weeks of play after v1 lands.

**Risk if deferred too long:** GPT continues to lack a structural framework for how enchanted items are created, sustained, and contested. Current `mechanical_effect` field handles application; nothing handles lifecycle. Stalkerhide-class adjudication issues are addressed; Stalkerhide-creation-class issues are not.

---

## SUBSYSTEMS DEFERRED (LARGER ARCS)

- [ ] Services subsystem (`data/catalog/services/`)
- [ ] Vendors subsystem (`data/catalog/vendors/`)
- [ ] Crafting subsystem (`data/catalog/crafting/recipes.json`, `stations.json` beyond `materials.json`)

---

## IP / LICENSING (OPEN QUESTIONS)

- [ ] Decide on forking permissions — currently CC BY-NC-ND, which restricts derivatives. Confirm whether community forks for personal campaigns are acceptable under the license interpretation.
- [ ] Decide on redistribution scope — what parts of the world content are shareable, what stays restricted to the canonical repo.

---

## RECENTLY COMPLETED (for context)

- 2026-04-30 — `mechanical_effect` field for magical items: schema, catalog population, prompt enforcement, follow-up contract test fix
- 2026-04-30 — Stalkerhide cloak rebuilt: dropped "wearer still" trigger, split modifier into `+10 magical / +5 mundane`, fixed `does_not_apply` to no longer exclude ambient Feywood phenomena
- 2026-04-30 — Sylvara character reset under fungible AP system (4cca988): domains rebuilt, advancement layer corrected, 9 spell entries removed from `application`, AP recomputed at 22 earned + 2 awarded = 24, allocated to power+10 / perception+3 / will+3 / presence+4
- 2026-04-30 — 15 elven catalog items added across three commits: 6 items including baseline saddle (`7b86b0a`), 7 items (`3d2b043`), 2 apparel items (`23f6e2c`)
- 2026-04-30 — Time-as-delta architecture migration (6 commits): GPT no longer writes absolute time; sends `time_elapsed` deltas; backend computes day/month/year/time_of_day/season/festival deterministically
- 2026-04-30 — YAML→JSON migration for `data/world/` (94 files) and OpenAPI spec
- 2026-04-30 — Five-finding security/correctness audit closed (F1–F5): full-state save advancement bypass, delta endpoint advancement leak, tag tier validation, stale location edges, session ID collision
- 2026-04-30 — `exclude_unset` fix on delta endpoint resolved silent time clobbering bug
- 2026-04-29 / `abe1d83` — Production verifier version assertion now derives from `schemas/openapi.yaml` and fails loudly on schema/version drift
- 2026-04-29 / `abe1d83` — Production verifier coverage expanded for `/options` key parity, `/tags` shape/non-empty values, and usable `data_fingerprint`
- 2026-04-29 / `c72b3ab` — README character-option and layer-version drift reconciled
- Foundation reset to canonical Mystic Weave item schema (`731b9ab`)
- API v4.4.0 with `/catalog/items/{item_id}` endpoint (`ec1d3b9`)
- items-rules.md v2.0 + economy-rules.md v1.1 (`3b14353`)
- Weapon curation pass — 36 items (`248af6c`)
- Armor + shield + ammunition curation pass — 42 items (`7e94340`)
- JSON Schema export tooling (`1e6e07c`)

---

## 🚫 RESTRICTED FUTURE BUILDS

These items are not buildable within the current architecture without significant rebuild. Documented for future planning.

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