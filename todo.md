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

## ACTIVE ARCHITECTURAL ARC

*No active architectural arc currently. Arc System v1 closed 2026-04-30. Next architectural work pending live-play validation of v1 (2–4 week window).*

Candidates for next active arc, in approximate priority order:

- **Enchantment-rules arc** — design draft exists at `/mnt/user-data/outputs/enchantment-rules-design-draft.md`. Deferred pending arc system v1 live-play validation. See "Deferred pending arc system v1" section below.
- **Backend scene records** — currently scene boundary remains GPT-judged per Arc System v1 design. If live play reveals the GPT undercounting or overcounting scenes by enough to break envelope enforcement, scene records may become necessary. Out of v1 scope; candidate for v2 if needed.
- **Companion subsystem expansion** — currently minimal; expansion candidates not yet scoped.

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

**Why deferred:** Arc System v1 is implementation-complete (2026-04-30) but not yet validated through live play. Some enchantment-rules design decisions (how rare is enchantment? routine PC activity or rare narrative beat?) are best answered after observing how arc-driven reward channels behave in real use.

**When to revisit:** once arc system v1 has been validated through 2-4 weeks of play. Watch specifically for: whether GPT correctly distinguishes formal/emergent at creation, whether calibrated envelopes feel right, whether hard-cap enforcement produces clean transitions or creates friction.

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

- 2026-04-30 — **Arc System v1 complete**. Backend-authoritative arc framework governing scope, lifecycle, reward legality, and pacing for higher-level objectives. Six commits across foundation, endpoints, state machine, spawn/settle, progression integration, and prompt enforcement, plus two refactors and a GPT-facing OpenAPI spec trim to fit the 30-operation Actions cap. Locked decisions: formal-contract-only AP with strict provenance, calibrated envelope defaults validated against Sylvara's play history, scene-bound tag advancement preserved, parent/child spawn-as-expected, no retroactive arc reconstruction for legacy sessions. Activation requires re-uploading four prompts and the trimmed OpenAPI spec to GPT Builder. See commits 007dc14 → 3eb8066.
- 2026-04-30 — GPT-facing OpenAPI trim added: `schemas/openapi.json` remains the full canonical API contract; `schemas/openapi.gpt.json` is the ≤30-operation GPT Builder Actions subset.
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