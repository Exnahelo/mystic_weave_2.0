# Mystic Weave — TODO

Updated after world expansion, magic system, progression redesign, and item catalog passes.

## ✅ Recently Completed

- [x] Enforce model validation at persistence boundaries for:
  - [x] `POST /session/new`
  - [x] `GET/POST /state/{session_id}`
  - [x] `POST /character/create`
- [x] Preserve and validate historical v3.1.1 schema blocks end-to-end:
  - [x] character `identity`, `equipment`, `reputation`
  - [x] world `companions`, `economy`, `politics`
- [x] Ensure `Economy.coin` and `Economy.wealth_tier` are enforced via model validation
- [x] Replace mutable defaults with `Field(default_factory=...)` across affected models
- [x] Type response models for stronger OpenAPI/schema parity:
  - [x] `NewSessionResponse.character/world`
  - [x] `CreateCharacterResponse.character`
- [x] Fix `/location` UPSERT response semantics:
  - [x] `201` on create
  - [x] `200` on update
  - [x] include both responses in OpenAPI metadata
- [x] Expand contract/regression coverage:
  - [x] endpoint schema refs in OpenAPI contract tests
  - [x] validation regression tests for negative coin and invalid wealth tier
- [x] Align version/docs consistency items:
  - [x] `api/main.py` version advanced beyond the historical `3.1.1` release line
  - [x] `scripts/verify_production_contract.py` checks the current backend release version
  - [x] README cleanup and `.env.example` added
- [x] Validation test run passing for hardened scope (`11 passed`)
- [x] Add Alembic migrations for schema lifecycle (replace ad hoc/manual DB evolution)
- [x] Add CI guard for OpenAPI drift (`app.openapi()` vs `schemas/openapi.yaml`)
- [x] Add data/prompt validation gates:
  - [x] schema checks for `data/*.json`
  - [x] structural/lint checks for prompt files used in production
- [x] Strengthen deployment pipeline checks (pre-deploy contract + smoke bundle)
- [x] Expand end-to-end coverage for multi-turn narrative persistence edge cases
- [x] Add lightweight operational runbook for local/Railway troubleshooting
- [x] Add explicit await/validate checkpoints in `prompts/engine.md`
- [x] Add explicit player-confirmation gates for irreversible outcomes in turn flow
- [x] Add canonical precedence block in runtime prompts
- [x] Resolve cross-file canon contradictions
- [x] Add deterministic tie-break rules for ambiguous domain/tag adjudication
- [x] Add deterministic state-write order for complex multi-change turns
- [x] Add standardized handling for sparse/unknown faction reputation data
- [x] Add global stub-handling policy for unfinished organizations/lore
- [x] Extend `scripts/validate_prompts.py` checks
- [x] Add optional `reason` field to `RollRequest` for roll observability
- [x] Make `LocationResponse.data` typed (`LocationData`) instead of opaque object
- [x] Upgrade response schemas in `schemas/openapi.yaml` to concrete `$ref` usage
- [x] Add `required` arrays for key response schemas used by GPT branching
- [x] Normalize updated nullable fields to OpenAPI 3.1 style (`anyOf` with `null`)
- [x] Design and write magic system reference
- [x] Write difficulty reference
- [x] Write notable items reference
- [x] Run reciprocity audit on world connections
- [x] Document intentionally one-way connections
- [x] Add changelog note and release checkpoint for world topology baseline
- [x] Redesign progression system — AP-purchased domain advancement, tiered brackets, use-based tags
- [x] Add reputation growth rules to `world_rules.md` and `engine.md`
- [x] Coin system redesigned — copper-as-base-unit, stored as integer CD
- [x] Weapon application tags updated to new taxonomy (Grappling, Melee, Reach, Ranged, Mechanical, Unconventional)
- [x] Created `prompts/mundane_items_reference.md`
- [x] Created `prompts/weapons_armor_reference.md`
- [x] Created `prompts/sstc_operations.md`
- [x] Created `prompts/magical_items_reference.md`
- [x] Holy water reclassified — removed from mundane catalog, added to `prompts/magical_items_reference.md`
- [x] Blessed water added to mundane consumables as sacred preparation at `0 CD`
- [x] World expanded — 13 new location stubs + 7 wilderness/trail stubs authored and seeded
- [x] Magic system redesigned — fields as knowledge tags, spells as application tags, access bands, failure model
- [x] Created `data/magic-spells.json` baseline
- [x] Added species traits block to dragonborn in `data/charachter-species.json`
- [x] Add character payload compatibility support for legacy/expanded keys:
  - [x] accept deprecated `level`
  - [x] accept `magic_fields`
  - [x] accept `species_traits` via alias to `draconic_traits`
- [x] Re-sync `schemas/openapi.yaml` with runtime schema updates
- [x] Restore OpenAPI `servers` entry in contract
- [x] Bring OpenAPI route metadata into policy compliance:
  - [x] shorten over-limit operation descriptions
  - [x] restore explicit response `properties` for `/`, `/health`, `/version`

---

## 🔜 Active Work

### Schema & Model Cleanup

- [x] Decide deprecation timeline for legacy compatibility fields in `CharacterModel` (`level`, `magic_fields`, `draconic_traits` alias)
  - [x] **v3.2.x (now):** retain compatibility fields; mark as deprecated in schema/docs.
  - [x] **v3.3.0:** stop server-generated writes for `level`/`magic_fields`; continue read compatibility.
  - [x] **v4.0.0:** remove `level`, `magic_fields`, and `species_traits` alias acceptance (keep canonical `draconic_traits`).
- [x] If/when removing legacy compatibility fields, add migration + contract rollout plan for existing sessions/clients
  - [x] Pre-v4 migration script: normalize stored `game_states.character` JSON (`species_traits` → `draconic_traits`, drop `level` + `magic_fields`).
  - [x] Rollout gate: run migration in staging, then production, before deploying v4.0.0 schema.
  - [x] Contract rollout: keep legacy acceptance assertions during v3.x; invert/remove those assertions at v4.0.0 cutover.
  - [x] Client comms: publish deprecation in release notes for v3.2.x + v3.3.0 and include final removal notice in v4.0.0 notes.
- [x] Add explicit guard test coverage for OpenAPI policy constraints:
  - [x] route description max-length enforcement
  - [x] required object `properties` presence for health/version/root response schemas
  - [x] top-level `servers` URL presence

### Application Tag Updates

- [x] Update `data/charachter-backgrounds.json` — remap old weapon tags to new taxonomy
- [x] Update `data/charachter-focus.json` — remap old weapon tags to new taxonomy
- [x] Update `prompts/world_rules.md` application tag table with new weapon taxonomy
- [x] Update `prompts/character_creation.md` tag name references
- [x] Update `schemas/openapi.yaml` if weapon tags are enumerated
- [ ] Remap X's application tags in session `74a30d9f` via SQL

### Progression System Implementation

- [x] Update `world_rules.md` Advancement section with final AP system:
  - [x] Consequence scale table with one-sentence definitions
  - [x] AP cost brackets (25–60: 1 AP, 61–70: 2 AP, 71–80: 3 AP)
  - [x] Tag advancement rules (use-based, one per scene max, new tag introduction rule)
  - [x] AP earning clarification (one award per resolved scene, multi-leg job counts as one Situational)
- [x] Add progression runtime section to `prompts/engine.md`:
  - [x] When and how to award AP
  - [x] Consequence scale definitions
  - [x] AP spend handling for domain raise requests
  - [x] Mandatory state updates on each save

### Magic System Implementation

- [x] Update `prompts/world_rules.md` knowledge tag table with magical fields
- [x] Add Magic section to `world_rules.md` covering:
  - [x] Access bands (safe, risky, dangerous)
  - [x] Field tier access ceilings
  - [x] Failure model (minor miss, strain, backlash, catastrophic)
- [x] Update `prompts/magic_system_reference.md` with full specification
- [x] Update `prompts/character_creation.md` — add magical fields as valid knowledge tag choices, add dragonborn breath type establishment at creation
- [x] Add magic roll assembly to `prompts/engine.md` Step 3

### Item & Economy Cleanup

- [x] Remove weapon and armor price entries from `prompts/economy_currency_reference.md` — now live in `weapons_armor_reference.md`
- [x] Add tool sufficiency rule to `prompts/engine.md` Economy Runtime Checkpoint
- [x] Update `prompts/character_creation.md` domain ceiling references to 80

### World & Lore Updates

- [x] Update `prompts/geography.md` with new settlements and travel times
- [x] Add Vigil / Platinum Accord remnant to `prompts/groups.md`
- [x] Add Serevane and The Warden of Greymantle to `prompts/npcs.md`
- [x] Add Vigil faction entry to `prompts/groups.md`
- [x] Add regional economic nodes to `prompts/economy_currency_reference.md`
- [x] Update `prompts/sstc_operations.md` route network with new named locations
- [x] Update `WORLD_TOPOLOGY_BASELINE.md` for all new locations and reciprocity audit
- [x] Add `platinum-oath-approach` trail stub to `prompts/world/`
- [x] Add `draconic-grasslands-edge` stub to `prompts/world/`

### Gameplay Tracking

- [x] Add a lightweight survival state block to the schema in `api/models.py`
  - [x] Add hunger state
  - [x] Add hydration state
  - [x] Add fatigue state
  - [x] Add load state
  - [x] Keep all four as coarse enums/bands, not numeric meters
- [x] Update `schemas/openapi.yaml` to expose the new survival/load state fields
  - [x] Keep schema aligned with runtime models
  - [x] Preserve current response/request shapes outside the new added block
- [x] Add canonical survival and load rules to `prompts/world_rules.md`
  - [x] Hunger and hydration are low-frequency maintenance states, not per-action meters
  - [x] Hunger/hydration primarily change at rest, deprivation, or meaningful travel checkpoints
  - [x] Fatigue is the primary exertion economy
  - [x] Load modifies fatigue gain and physical/travel difficulty
  - [x] Avoid exact weight/dimension simulation unless explicitly requested later
- [x] Update `prompts/engine.md` with a Survival Runtime Checkpoint
  - [x] Validate and persist hunger, hydration, fatigue, and load when they change
  - [x] Only update survival states at clear triggers: rest, extended travel, deprivation, major exertion, or heavy overextension
  - [x] Keep bookkeeping sparse and deterministic
  - [x] Ensure survival state is included in turn-end save logic when changed
- [x] Implement hunger tracking as a simple state rule
  - [x] Add canonical bands such as `sated`, `hungry`, `starving`
  - [x] Tie changes to missed food / successful resupply / rest-cycle checkpoints
  - [x] Update item references only where needed to support food access and recovery logic
- [x] Implement hydration tracking as a simple state rule
  - [x] Add canonical bands such as `hydrated`, `thirsty`, `dehydrated`
  - [x] Tie changes to missed water / exposure / successful resupply / rest-cycle checkpoints
  - [x] Update item references only where needed to support water access and recovery logic
- [x] Implement fatigue tracking as the main active exertion state
  - [x] Add canonical bands such as `rested`, `tired`, `fatigued`, `exhausted`
  - [x] Increase fatigue on major exertion, forced travel, poor recovery, and similar clear triggers
  - [x] Reduce fatigue through proper rest, moderated by hunger/hydration state
- [x] Add lightweight load tracking instead of full encumbrance/dimensions simulation
  - [x] Add canonical bands such as `light`, `normal`, `burdened`, `overloaded`
  - [x] Use load as a modifier to fatigue gain, travel difficulty, and certain physical actions
  - [x] Do not implement exact item weight, container volume, or dimensions in this pass
- [x] Expand and normalize service pricing in `prompts/economy_currency_reference.md`
  - [x] Preserve existing baseline service prices already present
  - [x] Standardize missing services such as ferriage and any other commonly used travel/stable/lodging services
  - [x] Clarify when local scarcity, danger, or regional economy should shift baseline pricing
  - [x] Keep weapon/armor pricing out of this file
- [x] Update item references only where survival/load rules need canonical support
  - [x] Confirm food, water-carry, bedding, shelter, and load-bearing items support the new rules cleanly
  - [x] Add item-weight data only if the lightweight load approach proves insufficient

---

## 🔧 Architectural Improvements (Buildable)

These are structural improvements identified from architecture review. None require a rebuild — all are addable to the current system.

### Scene Manager — High Priority

- [x] Design a scene context builder that assembles a focused object for the GPT instead of sending full world state every turn
- [x] Scene object should include: current location summary, visible entities, immediate stakes, relevant character state, recent log entries (last 5), active threats, available opportunities
- [x] Implement as a pre-processing step before GPT turn narration — either a new endpoint or a context assembly function
- [x] Update `prompts/engine.md` to describe what the GPT should expect in scene context vs full state

### Fail-Forward Rule — Low Effort, High Value

- [x] Move fail-forward from narration style note to explicit mechanical rule in `world_rules.md`
- [x] Add three examples covering physical, social, and magical failure contexts
- [x] Add to `prompts/engine.md` Step 4 Narrate Outcome as a mandatory consideration

### NPC Relationship Propagation Rules

- [x] Add explicit relationship propagation rules to the Reputation section in `prompts/world_rules.md`
  - Define what changes when standing crosses into a new band
  - Treat propagation as a gameplay consequence layer, not just flavor text
  - Keep the rules lightweight and faction-agnostic unless a specific faction has authored exceptions
- [x] Define canonical standing-band effects in `prompts/world_rules.md`
  - `Revered` (61 to 100)
    - privileged access, proactive help, sensitive information, reduced scrutiny, stronger benefit of the doubt
  - `Respected` (21 to 60)
    - easier introductions, routine cooperation, standard services/opportunities opened, moderate institutional trust
  - `Neutral` (-20 to 20)
    - baseline access only, no special help, no automatic hostility
  - `Distrusted` (-21 to -60)
    - guarded interactions, reduced access, higher scrutiny, refusals on sensitive requests
  - `Despised` (-61 to -100)
    - denied access, active obstruction, possible reporting/hostility depending on faction and context
- [x] Clarify propagation scope in `prompts/world_rules.md`
  - Propagation affects:
    - service availability
    - information access
    - faction cooperation
    - escort/sanction/authorization likelihood
    - legal/social scrutiny
    - which jobs, requests, or aid offers become available
  - Propagation does not require separate subsystem math
  - Propagation should be applied conservatively and according to the faction’s nature
- [x] Define threshold-crossing behavior in `prompts/world_rules.md`
  - Apply propagation when standing crosses from one band into another
  - Do not re-trigger the same unlock/lock consequence every turn if the standing remains in the same band
  - On crossing a threshold, update access and posture for future scenes
  - Use `last_change` for the triggering event; use `note` only when the faction’s overall disposition meaningfully changes
- [x] Add faction-agnostic examples to `prompts/world_rules.md`
  - Crossing from Neutral -> Respected opens routine cooperation or trusted introductions
  - Crossing from Respected -> Revered opens sensitive access or proactive support
  - Crossing from Neutral -> Distrusted closes sensitive requests and increases scrutiny
  - Crossing from Distrusted -> Despised causes denial, expulsion, reporting, or active interference depending on faction context
- [x] Update `prompts/engine.md` turn-end save behavior
  - Require the GPT to check whether any faction standing crossed a band threshold during the turn
  - If a threshold was crossed, apply the appropriate propagation before save
  - Reflect the result in scene consequences, future availability, and reputation notes where applicable
  - Keep this as a turn-end rule, not a separate mid-scene subsystem unless the crossing itself is the scene outcome
- [x] Keep propagation bounded and compatible with current architecture
  - Do not add a new complex faction-simulation subsystem in this pass
  - Do not create automatic cross-faction chain reactions unless explicitly authored later
  - Keep propagation tied to the specific faction whose standing changed
  - Preserve existing reputation math and standing bands

### Pacing Variables

- [x] Add a typed `pacing` block to world state in `api/models.py`
  - Add a new `PacingState` model
  - Add it to `WorldModel` as a lightweight control block
  - Keep it small, deterministic, and GPT-readable
- [x] Define the canonical `pacing` fields in `api/models.py`
  - `tension` — integer 0–10
  - `last_consequence_weight` — `local` / `situational` / `regional` / `campaign`
  - `turns_since_social_beat` — non-negative integer
  - `turns_since_discovery` — non-negative integer
  - `turn_count` — non-negative integer
  - Add validation/clamping where appropriate
- [x] Resolve counter ownership before implementation
  - Decide whether `pacing.turn_count` replaces `world.turn`, mirrors it, or is derived from it
  - Prefer a single source of truth to avoid drift
  - If both are kept for compatibility, document which one is authoritative and when the other is synchronized
- [x] Update `schemas/openapi.yaml` to include the new `pacing` block
  - Keep schema aligned with `api/models.py`
  - Preserve existing request/response structure outside the added block
- [x] Add canonical pacing rules to `prompts/world_rules.md`
  - Define what each pacing field means in play
  - Define how tension should rise, fall, or hold
  - Define when `last_consequence_weight` changes
  - Define when social beats and discovery beats reset their counters
  - Keep pacing descriptive and directional, not a heavy subsystem
- [x] Add pacing read rules to `prompts/engine.md`
  - Require the GPT to check pacing before selecting scene type, pressure, and intensity
  - Use pacing to avoid repetitive scene selection
  - Use pacing to modulate escalation rather than override current stakes or canon
  - Keep prompt wording short and enforceable
- [x] Add pacing update rules to `prompts/engine.md`
  - Update `tension` when scene outcomes materially escalate or release pressure
  - Reset `turns_since_social_beat` when a meaningful social scene occurs; otherwise increment
  - Reset `turns_since_discovery` when a meaningful discovery occurs; otherwise increment
  - Update `last_consequence_weight` at scene resolution using the existing consequence scale
  - Synchronize `turn_count` with the chosen authoritative turn counter at save time
- [x] Keep pacing bounded and compatible with current architecture
  - Do not introduce a separate pacing engine or scheduler in this pass
  - Do not let pacing override dice results, location logic, or faction logic
  - Treat pacing as scene-selection guidance for the GPT, not a replacement for state consequences
- [x] Add tests for pacing model behavior
  - Validate field bounds and enum values
  - Validate default initialization
  - Validate synchronization behavior for `turn_count`
  - Validate that saves accept and return the new pacing block cleanly

### Extraction Step Separation

- [ ] Design a typed state-delta contract in `api/models.py`
  - Add a lightweight model for structured turn-end state changes
  - Keep it additive to the current full-state save contract in the first pass
  - Cover only fields that may change during a turn rather than resending the full stored state
- [ ] Define the extraction payload shape
  - Include structured updates for relevant character fields
  - Include structured updates for relevant world fields
  - Include log entry output
  - Keep the payload deterministic and machine-validated
  - Do not require the extractor to regenerate unchanged state
- [ ] Decide application semantics before implementation
  - Define how a validated delta is applied to the existing stored state
  - Preserve current deep-merge behavior where appropriate
  - Be explicit about which sections are merged and which sections are replaced
  - Avoid ambiguous partial-update behavior
- [ ] Implement schema validation for extracted state deltas
  - Validate extraction output before any save is committed
  - Reject malformed or incomplete extraction payloads cleanly
  - Keep error payloads short and plain
  - Preserve current state if validation fails
- [ ] Add a delta-application layer on the backend
  - Accept current stored state plus validated delta
  - Produce a final full state object for persistence
  - Reuse existing model validation before final save
  - Keep final persistence compatible with the existing saved `CharacterModel` + `WorldModel` contract
- [ ] Define two-step turn handling in the prompt/runtime design
  - Step 1: Narration receives scene context and produces prose only
  - Step 2: Extraction receives scene context + narration result and produces structured state delta only
  - Keep narration and extraction responsibilities explicitly separated
  - Do not allow narration prose to serve as the save payload
- [ ] Update `prompts/engine.md` to reflect the split
  - Clarify that narration is prose-only
  - Clarify that extraction is structured-output-only
  - Clarify that state changes are committed only after extraction validates
  - Keep the engine file within the current size limit
- [ ] Add extraction failure handling rules
  - If extraction validation fails, do not commit state
  - Retry extraction with a correction prompt, not a new narration pass
  - Preserve the original narration unless the failure proves the narration depended on invalid state assumptions
  - Limit retries to a bounded, deterministic path
- [ ] Keep rollout additive and backward-compatible
  - Do not remove the current full-state save path in the first pass
  - Keep existing GPT builder / Actions flows operational while the new extraction path is introduced
  - Treat this as a reliability upgrade layered onto current architecture, not a full rebuild
- [ ] Add tests for extraction and delta application
  - Validate accepted delta shapes
  - Validate rejection of malformed extraction payloads
  - Validate merge/application behavior for character and world updates
  - Validate no state commit occurs on failed extraction
  - Validate final saved state still conforms to canonical models
- [ ] Implement only after scene manager is stable
  - Scene context should be the primary input to narration and extraction before splitting the turn flow
  - Do not build extraction separation on top of raw full-state prompting if scene manager is the next intended architecture step

### Episodic Memory Compression

- [ ] Add session summary storage — compressed paragraph summaries of older log entries
- [ ] Write `scripts/compress_session_log.py` — compresses log entries older than N turns into a durable summary, stores in a `session_summaries` table
- [ ] Add summary retrieval to state load — GPT receives recent log entries plus compressed summaries for older sessions
- [ ] Trigger: manual initially, automated after every 20 turns later

--- world/ file mapping

## Mystic Weave World File Refactor — To-Do and Starter File Map

### Goal

Refactor world/location content into a hierarchical structure that scales cleanly for cities, wilderness zones, and future expansion.

The target model is:

- **Region**
- **Settlement**
- **District** (optional, for larger settlements)
- **Location node**
- **Sub-location node** only when it is truly navigable or mechanically distinct

This avoids:

- mega-files for entire cities
- filename hacks as pseudo-architecture
- brittle expansion as the world grows

--- world/ file mapping

### Repo To-Do

#### 1. Create a hierarchical world directory layout

Move from flat or loosely grouped location content to:

- region
- settlement
- district
- location

#### 2. Define canonical file roles

Use separate file types for:

- `region.json`
- `settlement.json`
- `district.json`
- `location.json`
- `region_zone.json` for wilderness/travel areas

#### 3. Add stable IDs and explicit parent references

Each file should explicitly declare where it belongs in the hierarchy.

Do not rely on filenames alone for structure.

#### 4. Use one file per navigable node

Create separate files for places that are actual travel or scene targets:

- shrines
- inns
- trade halls
- gates
- plazas
- forges
- towers
- cellars
- docks
- roads
- ruins

#### 5. Do not split minor scene flavor into files

These should usually remain inside the main location description:

- booths
- corners
- tables
- fireplaces
- generic upstairs seating

Create separate files only when a sub-area is meaningfully distinct.

#### 6. Normalize graph connections

Connections should point to stable location IDs, not free-text names.

#### 7. Separate canon from planning notes

World files intended for GPT upload should contain canonical usable data, not mixed author commentary.

#### 8. Add integrity validation

Validate:

- unique IDs
- valid parent references
- valid connection targets
- no orphaned locations
- no duplicate IDs
- no broken settlement/district/location references

#### 9. Migrate gradually

Do not try to restructure the whole world at once.

Use **Drakenvale** as the reference implementation first.

#### 10. Document the pattern

Add a short `README.md` in `data/world/` so future files follow one pattern instead of improvising.

---

### Recommended Directory Layout

```text
data/
  world/
    README.md

    regions/
      drakenvale/
        region.json

        settlements/
          stronghold_of_drakenvale/
            settlement.json

            districts/
              platinum_quarter.json
              trade_quarter.json
              forgeward.json
              lower_borough.json

            locations/
              platinum_heart.json
              infernal_forge.json
              amethyst_vault.json
              council_chamber.json
              wardens_hall.json
              sstc_tradehall.json
              lantern_rest.json
              east_gate.json
              market_square.json

          grasslands_edge_post/
            settlement.json
            locations/
              post_square.json
              quartermaster_office.json
              caravan_yard.json
              mess_hall.json
              watchtower.json

          dracelune/
            settlement.json
            districts/
              moonmarket.json
              riverward.json
            locations/
              moonmarket_plaza.json
              river_docks.json
              pilgrims_rest.json
              customs_house.json
              north_gate.json

        wilderness/
          draconic_grasslands/
            region_zone.json
            locations/
              southbound_route.json
              ambush_fold.json
              caravan_halt.json
              old_stone_marker.json

          feywood_glade/
            region_zone.json
            locations/
              glade_edge_path.json
              mist_hollow.json
              bent_oak_crossing.json
              vanished_trail.json

      ashfall_reaches/
        region.json

        settlements/
          cinderwatch/
            settlement.json
            locations/
              watch_keep.json
              ash_market.json
              pilgrim_gate.json

        wilderness/
          ember_road/
            region_zone.json
            locations/
              scorched_mile.json
              basalt_bridge.json

------

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
