# Mystic Weave — TODO

Last updated: 2026-04-29

## Active Catalog Work

- [x] **Apparel curation pass** (25 items): populate `market_tags` and
      `wealth_tier_floor`, flag any magical items needing tier+magic_field.
      Pattern matches the weapon/armor/shield/ammunition passes already
      completed.
- [x] **Gear curation pass** (132 items, the big one): same fields plus
      tier+magic_field for magical trinkets, foci, and consumables. Probably
      its own session.
- [x] **Retroactive T0 + celestial-metal tag** for three weapons whose
      identity centers on recovered Elarith:
      `weapon/moon-blade`, `weapon/sword-greenshield-pattern`,
      `weapon/proven-handaxe`. Set `tier: T0` and add `celestial-metal` to
      `tags`. Validator passes; small follow-up patch.
- [x] **Stale 5e cleanup**: delete `data/catalog/economy/currencies.json`
      (uses cp/sp/ep/gp/pp; canonical CD/SD/GD/PD lives in
      `data/economy/currency.json`) and remove the empty parent dir.
      Keep `data/catalog/services/README.md` and
      `data/catalog/vendors/README.md` as future-work placeholders.

## Lore / Worldbuilding
crafting/materials.json`
- [ ] **Wire `data/environment/`** (`feywood_animals.json`,
      `feywood_plants.json`) into code. Currently authored but unread.
      Decide read pattern: pre-load into game_data like `data/beasts/`,
      or load on demand from a new endpoint.
- [ ] **Cross-reference materials ↔ ecology**: items reference materials
      (silverbark-ash, thornroot-stalker-hide, etc.); materials reference
      biomes; environment files reference creatures whose materials we
      catalog. The links exist conceptually but aren't formalized.
      Decide if this needs a structured cross-reference layer or stays
      narrative-only.
- [ ] **Institutional structure for Feywood** is implied by the catalog
      (Heartwardens, Greenshields, House Thornmere, House Ironsap) but not
      yet authored canonically. Sketch governance and access hierarchy
      when the catalog hints make it necessary.
- [x] **Author Feywood lore prose** into existing files (no new prompt file
      to preserve slot budget under GPT builder's 20-doc cap):
      * Recovery economy → section in `economy-rules.md`
      * Composite craft philosophy + reserve access hierarchy → section in
        `items-rules.md`
      * Brief naming culture note (Elarith / Heartfall / starvein) →
        `items-rules.md`, cross-reference to `data/catalog/

## Prompt Architecture

- [ ] **Decide on prompt restructuring strategy** — slot pressure is
      real (~16 of 20 used). Options identified:
      1. Hybrid model — extract structured data (denomination tables,
         regional mappings, vocabularies) to JSON; leave reasoning prose
         in markdown. Saves ~30% per file. Lower payoff.
      2. Fold smaller rules files (economy-rules, difficulty-rules) into
         existing larger files like `world.md`. Frees full slots.
      3. Consolidate cross-referencing rules into a single `play-rules.md`.
         Items, economy, and difficulty all reference each other; merge
         might improve coherence.
      Decision deferred — not urgent until slot count climbs further.

## CI / Process Debt

- [ ] Configure branch protection on main: require Lint+Unit+Contract,
      Integration+Loop Test, Item Catalog Validation, and Pre-Deploy
      Contract+Smoke Bundle status checks before merge. (User must do
      this in GitHub UI; not scriptable.)
- [ ] Set up failure notification on main CI (GitHub email-on-failure
      or Slack webhook). Main CI was red for 30+ runs without anyone
      noticing.
- [ ] Audit recent direct-to-main pushes: commit 0c4b579b ("Renames
      Feywood Glade to Feywood in all content") corrupted
      tests/unit/test_companion_models.py via sloppy find-replace and
      merged anyway. Investigate whether mass-rename commits go through
      PR review.
- [ ] Update GitHub Actions to Node.js 24 before Sept 16 2026
      deprecation.

## Catalog Stabilization Follow-ups

- [ ] Audit `data/catalog/registries/` for orphan tags (defined but never
      used) and missing tags (used in items but not registered).
- [ ] Decide intent of `data/catalog/crafting/materials.json`. Crafting
      subsystem is documented as deferred but `materials.json` exists.
- [ ] Resolve singular vs plural directory naming inconsistency
      (`weapon/` vs `weapons/`, `shield/` vs `shields/`). See
      `docs/items-schema.md`.
- [ ] Review parallel namespaces against `docs/items-schema.md`
      "What Lives Outside data/catalog/" section. Decide whether to
      consolidate or keep separate, one namespace at a time:
      - `data/tags/` vs `data/catalog/registries/`
      - `data/economy/` vs `data/catalog/economy/`
      - `data/magic/`, `data/beasts/`, `data/characters/`, `data/npcs/`

## Item Schema Follow-ups

- [ ] Tighten `Effect.params` validation against effect registry param
      contracts in `mechanics/effects.json`. (NOTE: this referenced the
      modular schema that was rolled back; reconsider whether it
      applies to the current flat schema.)
- [ ] Author next batch of items (10-20 mundane) — gear, ammunition,
      apparel coverage gaps.
- [ ] JSON Schema export: emit `data/catalog/schemas/*.schema.json` from
      Pydantic models for non-Python consumers (GPT builder).
- [ ] Pricing rules engine: design and implement `economy/price_rules.json`
      so future items can use computed pricing rather than authored
      `canonical_value_cd`.
- [ ] API integration: confirm endpoints reading from `data/catalog/`
      are stable, plan retirement of any legacy `data/items/` paths if
      they still exist.

## Subsystems Deferred

- [ ] Services subsystem (`data/catalog/services/`)
- [ ] Vendors subsystem (`data/catalog/vendors/`)
- [ ] Crafting subsystem (`data/catalog/crafting/recipes.json`,
      `stations.json` beyond `materials.json`)

## IP / Licensing (Open Questions)

- [ ] Decide on forking permissions — currently CC BY-NC-ND, which
      restricts derivatives. Confirm whether community forks for personal
      campaigns are acceptable under the license interpretation.
- [ ] Decide on redistribution scope — what parts of the world content are
      shareable, what stays restricted to the canonical repo.

---

## Recently Completed (for context)

- [x] 2026-04-29 / `abe1d83` — Production verifier version assertion now derives from `schemas/openapi.yaml` and fails loudly on schema/version drift.
- [x] 2026-04-29 / `abe1d83` — Production verifier coverage expanded for `/options` key parity, `/tags` shape/non-empty values, and usable `data_fingerprint`.
- [x] 2026-04-29 / `c72b3ab` — README character-option and layer-version drift reconciled to ancestry/culture/current archetype wording.
- Foundation reset to canonical Mystic Weave item schema (commit `731b9ab`)
- Mechanics reference tables prompt (commit `ca94b73`)
- API v4.4.0 with `/catalog/items/{item_id}` endpoint (commit `ec1d3b9`)
- items-rules.md v2.0 + economy-rules.md v1.1 (commit `3b14353`)
- Weapon curation pass — 36 items (commit `248af6c`)
- Armor + shield + ammunition curation pass — 42 items (commit `7e94340`)
- Materials catalog with 9 entries plus biome_types and material_categories
  registries (queued, not yet committed at time of this update)
- JSON Schema export tooling (commit `1e6e07c`)
- GitHub Actions updated to latest major versions (commit `71316e8`)

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
