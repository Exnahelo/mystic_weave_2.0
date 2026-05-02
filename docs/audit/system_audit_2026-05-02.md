# Mystic Weave 2.0 — System Audit (2026-05-02)

Pre-wipe audit. Findings only — no code, schema, or content was changed by this brief. A subsequent brief will action cleanup.

## Executive summary

Three legacy hazards dominate. (1) The `draconic_traits` field still lives on `CharacterModel` and `CharacterStateDelta` even though the v3→v4 migration script strips it on input and `seed_character()` never populates it — the field is dead weight kept alive by a regression test that asserts persistence of legacy data. (2) `scripts/repair_structured_state.py` and `scripts/reconcile_topology.py` are session/region-scoped one-shots that should have been deleted after their single use; they remain hardcoded and wireable. (3) The `locations` table cannot distinguish canonical seed rows from runtime `POST /location` rows, so the wipe has no surgical option — it will be `TRUNCATE locations CASCADE; re-seed`, which is correct but loses any runtime discoveries. Schema/data registries (Targets 3) are clean. The narrator-invented threshold-watch and place names from the wiped pursuit chain (Target 2) have **zero** repo footprint — that drift is purely live-narrator, not data residue. Catalog has two real gaps: `chalk` (priced but not catalogued) and animal feed as a consumable.

## Findings by target

### Target 1: Draconic system residue

Findings ordered by disposition.

**Active model fields — propose retire:**
- `api/models.py:223` — `draconic_traits: list[str] = Field(default_factory=list)` on `CharacterModel`. Never written by `seed_character()`; only ever set via legacy delta path.
- `api/models.py:765` — `draconic_traits: list[str] | None = None` on `CharacterStateDelta`. Allows partial updates.
- `schemas/openapi.json` (3 occurrences around 3398, 3505, 3738) and `schemas/openapi.gpt.json` (same) — generated from the models above; will drop once models do.

**Legitimately active — keep:**
- `data/tags/applications.json:627-640` — `dragon_breath` application tag entry (domain Will/Power). The tag is no longer ancestry-auto-granted; it is a normal application tag any character can pick up.
- `prompts/world-rules.md:332` — rule text for `dragon_breath` application. Aligns with the active tag entry. **DECISION NEEDED:** keep as-is, or rephrase since field-level `draconic_traits` retirement may make the example name confusing.

**Migration / cleanup code — keep:**
- `scripts/migrate_character_v4.py:52` — strips `draconic_traits`, `magic_fields`, `level`, `species_traits` during v3→v4 migration. Legitimate.
- `tests/unit/test_migrate_character_v4.py` — asserts the strip. Keep.
- `tests/unit/test_seed_character.py:24-26` — asserts Drakari does NOT auto-grant `dragon_breath`. Documents the change. Keep.

**Legacy persistence test — propose retire:**
- `tests/regression/test_multi_turn_persistence.py:368-389` — `test_delta_save_persists_draconic_traits` writes `["dragon_breath", "scaled_hide"]` through delta and asserts persistence. This locks in the dead field. Retire alongside the field.

**One-shot script — propose retire:**
- `scripts/repair_structured_state.py:24, 37, 45, 68` — hardcoded for session `9ac30cc0`; assigns `dragon_breath: 2` and `draconic_traits: ["radiant_breath_lineage", "dragon_breath"]`. Single-use repair. Already in git history.

### Target 2: Threshold-watch / watcher legacy

**Threshold-watch is canonical, not invented.**
- `data/world/hollow_crown/surface/feywood/groups/rangers.json:14` — `"threshold-watch"` as Ranger group tag.
- `data/world/hollow_crown/surface/feywood/groups/rangers.json:7` — description states Rangers do "continuous threshold-watch at the realm-to-realm Border."
- `prompts/world_vault/hollow_crown/surface/feywood/groups/rangers.md` — extensive role detail.
- `prompts/world_vault/hollow_crown/surface/feywood/groups/greenshields.md` and `…/hall_of_trade.md` — confirming references.
- `prompts/groups.md` — top-level mention.

Classification: (a) canonical content. The recent live-play "threshold-watch institution parallel to the Rangers" was narrator drift treating a Ranger function as a separate body. No data fix needed; narrator discipline (Brief 7) addresses the upstream cause.

**Narrator-invented names — confirmed absent from repo:**
- Mosscourt — absent.
- Whispermark — absent.
- Greenveil — absent.
- Thalen — absent.
- Westreach Ranger House — absent.
- Runnelbreak — absent.
- Rootblind — absent.
- Needlewatch — absent.
- Rootfall — absent.

**"Serel" — example placeholder, not canonical:**
- `prompts/scene-structure.md:128, 132` — appears only as a tactical-example name ("Dusk scouts wide, Serel covers, Sylvara advances on the line") in the Companion Role Preservation section added by Brief 7. Not in any data file, not an NPC. No action.

**"Watcher/watchers" institutional usage — none found:**
- `prompts/groups.md` — "covert watchers" used as a generic descriptor in Drakenvale context. Not an institution name.
- `data/catalog/items/gear/heartroot_token.json` — "watcher-token", "watcher-post" are item-context descriptors, not institutional. No action.

**Sylvara mentions are canonical** (House Heartwood candidate; appears in `data/npcs/hollow_crown/feywood_glade/named.json`, `data/world/hollow_crown/surface/feywood/groups/noble_families.json`, `data/entities/feywood/longbough.json`, `data/catalog/items/gear/heartwood_bow.json`). No issue.

### Target 3: Schema vs data consistency

All seven structural checks pass clean. Validators (`validate_data_files.py data`, `validate_catalog.py`) both pass with zero errors.

- (1) Application → knowledge_groups: clean. Every `group` in `applications.json` resolves to an `index` in `knowledge_groups.json`.
- (2) Character template knowledge tags: clean. All references in `data/characters/{ancestry,culture,focus,background}.json` resolve.
- (3) `data/catalog/registries/magic_fields.json` matches `api/game_data.py::list_magic_fields()` exactly: `sacred, warding, binding, elemental, druidry, illusion, runecraft, alchemy, necromancy`.
- (4) Catalog directories all map via `CATEGORY_DIRS` in `scripts/validate_catalog.py`. 231 item files placed correctly.
- (5) Item-tag references all resolve in `data/catalog/registries/item_tags.json` (~600 unique tags).
- (6) Market-tag references all resolve in `data/catalog/registries/market_tags.json` (14 tags).
- (7) Magic-field references in materials all resolve.

**Defined-but-unreferenced (informational, not a defect):**
- 121 application tags exist in `applications.json` but are not referenced by any character template. These are the wider competency pool for advancement (weapon/armor skills, extended martial/crafting/lore) — characters pick them up post-creation.
- 3 knowledge groups (`close_combat`, `craft`, `warfare`) have no template reference; same rationale.

No action needed. The architecture deliberately separates "what creation grants" from "what is reachable via advancement." Listed here only so a subsequent cleanup brief does not mistake them for orphans.

### Target 4: Character record schema audit

**CharacterModel** (`api/models.py:217–239`) — `extra="forbid"`, so saved records cannot drift unmapped fields. Uses Pydantic v2.

Fields with defaults:
- `draconic_traits` default_factory=list (line 223) — proposed retire (see Target 1).
- `status_effects` default_factory=list (232).
- `notes` "" (233).
- `identity` default_factory=Identity (236).
- `equipment` default_factory=Equipment (237).
- `reputation` default_factory=list (238).
- `advancement` default_factory=AdvancementState (239).

Optional fields on `CharacterModel`: none directly. (All required or defaulted.)

`CharacterStateDelta` Optional fields (sparse update model, lines 743–765) include `draconic_traits: list[str] | None = None` (765) — proposed retire.

Nested-model defaults (informational):
- `HP.max=100` (api/models.py:85). `AdvancementState` four scalars all default 0 (130–133). `Identity` and `Equipment` collections default empty. `Alignment.order/intent` default neutral (144–145).

**Fields never populated by creation:**
- `draconic_traits` is the only field on `CharacterModel` not written by `seed_character()` (`api/game_data.py:992–1095`). Confirms the field is vestigial.

**Production-record divergence:**
- `tests/fixtures/v4_sample_character.json` is a `NewSessionRequest` shape (`character_name`, `ancestry`, `culture`, `focus`, `background`, `adjustment_points`), not a saved CharacterModel. Cannot be used to assert model-record divergence.
- No other production-shaped JSON fixture exists in the repo. Because `extra="forbid"` is set, any saved record that did diverge would fail validation on read — so divergence cannot accumulate silently.

### Target 5: Catalog gaps from active play

**`chalk` — confirmed gap:**
- No file `data/catalog/items/**/chalk*` exists.
- No item with `"id": "chalk"` in any catalog JSON.
- BUT: `data/economy/prices.json:787-793` lists `price_chalk_01` with `name: "Chalk (piece)", price_cd: 1, rarity: "common"`. So pricing is registered but the catalog item is missing. **High-value gap.**

**Animal feed as a consumable — confirmed gap:**
- `data/catalog/items/gear/gear_feed_bag.json` is the container, marked `consumable: false`.
- No consumable feed item exists in catalog. The 20 consumable items in catalog cover paper, oil, wine, pigments, adhesive, pitons, tourniquet, sealant, wax, holy water, torches, balm, ink, cider, parchment, alchemist's fire, candles, basic poison, honey, and field rations — none are animal feed.
- **Medium-value gap.** Mechanical pairing of the feed bag with no feed-as-consumable suggests designer intent.

**Other gaps:**
- `tests/loop_test.py:503-507` references `item_001` ("Battered plate armour") with no catalog backing. Test-only, ephemeral. Low-value gap; not a wipe blocker.

**Sylvara chalk reference (from brief):** Sylvara is a canonical NPC across multiple data files but has no character record with an inventory in the repo. The chalk-in-Sylvara's-inventory reference in the brief is from a runtime session record (which the wipe will clear). Repo-side fix is to add the chalk catalog item; the inventory reference will be reconstituted by the new character creation flow post-wipe.

### Target 6: Repair scripts and one-shot migrations

| Script | Hardcoded? | Run? | Disposition |
|---|---|---|---|
| `scripts/repair_structured_state.py` | Session `9ac30cc0` hardcoded (line 24) | Yes — single use | **Retire (delete)** |
| `scripts/migrate_character_v4.py` | Default culture hardcoded; otherwise parameterized via `--session`/`--dry-run` | Yes — v4.0.0 deploy | **Keep** (idempotent, parameterized) |
| `scripts/migrate_advancement_v4_2.py` | Parameterized; AP scalar names hardcoded | Yes — v4.2.0 deploy | **Keep** (idempotent) |
| `scripts/seed_locations.py` | `data/world/` path hardcoded | Yes — referenced in operational-runbook | **Keep** (idempotent UPSERT, runbook-cited) |
| `scripts/reconcile_topology.py` | hollow_crown rename map, edge fixups, file moves all hardcoded (lines 13–71) | Yes — single use during region restructure | **Retire (delete)** — git history retains it |

**Alembic migrations — all applied, chain intact:**
- `20260410_0001_initial_schema.py` — creates `game_states`, `locations`, `world_graph` (commit `ad67d5d`).
- `20260430_0002_create_arcs.py` — creates `arcs` (commit `007dc14`).
- `20260430_0003_create_arc_transitions.py` — creates `arc_transitions` (commit `3b1e70d`).

No unapplied migrations. No orphan revisions.

### Target 7: Test data divergence

**Stale data needing update:**
- `tests/fixtures/v4_sample_character.json:7` — contains `adjustment_points` field. The fixture is a creation-payload shape (where `adjustment_points` is a transient creation parameter, not a CharacterModel field). Not strictly stale — but the fixture is **orphaned**: no test in the repo loads it. Either delete it or wire it into a test.
- `tests/regression/test_multi_turn_persistence.py:368-389` — `test_delta_save_persists_draconic_traits` writes `["dragon_breath", "scaled_hide"]` and asserts round-trip. This is **not** a migration test; it's a regression test holding the legacy field alive. **Retire alongside the field.**

**Legitimate migration tests (keep):**
- `tests/unit/test_migrate_character_v4.py:38, 52` — deliberately exercises v3→v4 migration including legacy-key removal. Keep.
- `tests/unit/test_seed_character.py:24-26` — asserts Drakari does NOT receive `dragon_breath` via traits. Documents the removal. Keep.

**Acceptable:**
- `tests/loop_test.py:63-66` uses `adjustment_points` in a creation payload — that's a valid API parameter, not stale.

### Target 8: Prompt drift

**Endpoint references in prompts: clean.** Every endpoint cited in `prompts/engine.md` (and the ones spot-checked in other prompts) resolves to an operation in `schemas/openapi.json`. No orphan paths.

**Field references:**
- `prompts/world-rules.md:332` — uses `dragon_breath` as the application tag in a worked example. The application tag IS still active (Target 1), so this isn't strictly drift; but it's tied to the same legacy concept. **DECISION NEEDED:** keep, rephrase to a non-legacy example, or note that ancestry-bound traits are no longer the route.
- `prompts/character-creation.md:248` — `adjustment_points` shown in a creation-payload table. Valid (creation-time parameter), but worth a clarifying note that it adjusts domain seed and is not persisted as a model field. Low priority.

**Deprecated mechanics:** no references to legacy AP structures found in prompts. The four fungible scalars (`points_available`, `points_spent`, `points_earned_total`, `tag_counter`) are the only AP shape mentioned.

### Target 9: Untracked location records

**Storage:** `locations` table (`alembic/versions/20260410_0001_initial_schema.py:22-42`). Columns: `id` TEXT PK, `name` TEXT NOT NULL, `data` JSONB NOT NULL, `updated_at` TIMESTAMP default `now()`. Related: `world_graph` (`from_id, to_id` FKs to `locations.id`).

**Canonical vs runtime distinguishability: NONE.**
- No `source` column. No `is_seed` flag. No `created_via` tag.
- `updated_at` exists but `seed_locations.py` and `POST /location` (`api/routes/location.py:53–161`) both call `now()` and both UPSERT into the same row, so timestamps don't separate them.
- `data.discovered` defaults true on both paths.
- A runtime `POST /location` with the same id silently overwrites a canonical seed row.

**Wipe options:**
- **(A) `TRUNCATE locations CASCADE` then re-run `seed_locations.py`** — the only currently-safe option. Loses runtime discoveries. Recommended for the planned wipe; runtime discoveries from the to-be-wiped sessions are out of scope anyway.
- **(B) Add a `source` column (`'seed' | 'runtime'`) and `created_at`, then `DELETE WHERE source='runtime'`** — proper long-term fix. Requires a migration; flagged for a follow-up brief, not this one.
- **(C) Time-windowed delete** — fragile, not recommended.

**Recommendation for the wipe:** Option A is fine for this round given the wipe is total. Plan Option B as a follow-up so future per-tier resets don't have to nuke seed rows.

### Target 10: Legacy test files

- `tests/unit/test_migrate_character_v4.py` — exercises v3→v4 migration. **Keep** while `migrate_character_v4.py` is retained (Target 6). If/when production has zero v3 sessions remaining, retire as a pair.
- `tests/fixtures/v4_sample_character.json` — orphaned fixture (no loader found via grep). **Retire or wire into a test.**
- `tests/regression/test_multi_turn_persistence.py::test_delta_save_persists_draconic_traits` — single test (not a whole file) that holds the dead `draconic_traits` field alive. **Retire** as part of Target 1 cleanup.
- `tests/loop_test.py` — integration loop test. Active, keep. Contains `item_001` placeholder (Target 5) but that's tolerable for a loop test.

No whole-file legacy test retirements identified.

## Recommended cleanup order

1. **DECISION NEEDED**: confirm `draconic_traits` field retirement and `dragon_breath` application-tag disposition (Items 1 and 2 below).
2. Delete `tests/regression/test_multi_turn_persistence.py::test_delta_save_persists_draconic_traits`. (No dependencies; unblocks step 3.)
3. Remove `draconic_traits` from `CharacterModel` (`api/models.py:223`) and `CharacterStateDelta` (`api/models.py:765`). Regenerate OpenAPI specs (`python3 scripts/regenerate_openapi.py`). Run `pytest`.
4. Delete `scripts/repair_structured_state.py` and `scripts/reconcile_topology.py`. (Independent of step 3; can be done in parallel.)
5. Delete `tests/fixtures/v4_sample_character.json` (orphan). (Independent.)
6. Add `chalk` catalog item at `data/catalog/items/gear/chalk.json` matching the existing `price_chalk_01` entry. (Independent.)
7. Add animal-feed-as-consumable catalog item paired with `gear_feed_bag.json`. (Independent.)
8. **DECISION NEEDED**: rephrase or retain `prompts/world-rules.md:332` `dragon_breath` example.
9. Run the wipe: `TRUNCATE locations CASCADE` (and corresponding game-state truncate) → re-run `scripts/seed_locations.py`. (Depends on steps 3 and 6–7 ideally, so the post-wipe new-Sylvara character creation has a clean schema and a real chalk item.)
10. **Follow-up brief (separate)**: add `source` column + migration to `locations` table to enable per-tier wipes. Not required for this round.

## Items requiring user decision

1. **`draconic_traits` field disposition.** Confirmed legacy. Options: (a) retire entirely from `CharacterModel` and `CharacterStateDelta`, regenerate OpenAPI; (b) keep field, document as deprecated, leave default empty; (c) keep field and the persistence test (status quo). Recommendation: **(a)**. Cost is low (no live traffic should be writing this), benefit is a cleaner schema for the new character flow.

2. **`dragon_breath` application tag disposition.** Confirmed active and legitimately reachable post-creation, but conceptually tied to the retired ancestry-traits model. Options: (a) keep as a normal application tag (status quo); (b) keep but remove the Drakari example wording from `prompts/world-rules.md:332`; (c) retire the tag entirely. Recommendation: **(a) or (b)**. The mechanic is fine; only the prompt phrasing risks confusing the narrator post-Sylvara wipe.

3. **`tests/fixtures/v4_sample_character.json`.** Orphaned (no loader). Options: (a) delete; (b) wire into an existing creation test as a parameterized payload. Recommendation: **(a)**. If a creation-payload fixture is wanted later, it should reflect current shape.

4. **Animal-feed consumable.** Confirmed gap, but designer intent is unclear (one feed item with multiple flavors? feed-by-animal-type? a single generic feed?). Recommendation: defer to user — propose a minimal `gear_animal_feed.json` shaped after `gear_field_rations.json`.

## Data and items that should NOT change

These look legacy at a glance but are intentional:

- `dragon_breath` application tag in `data/tags/applications.json:627-640` — actively reachable; not ancestry-bound any more.
- All `Drakari` ancestry references in README, character templates, tests — Drakari remains a valid ancestry; only the auto-granted breath/scale traits are retired.
- `migrate_character_v4.py` and `migrate_advancement_v4_2.py` — keep; both are idempotent and parameterized.
- `seed_locations.py` — keep; runbook-cited and idempotent.
- `tests/unit/test_migrate_character_v4.py` and `tests/unit/test_seed_character.py` — both encode "this legacy thing is gone" assertions and are valuable regression guards.
- The 121 application tags and 3 knowledge groups not referenced by character templates — these are the post-creation advancement pool, not orphans.

## Additional findings

- **`prompts/character-creation.md:248`** describes `adjustment_points` as a model field in a layout table. It's actually a creation-time payload parameter that adjusts domain seeds, not a persisted field on `CharacterModel`. Minor doc clarity item; low priority but noted.
- **`prompts/world-rules.md`** (around line 332) and similar pages have several worked examples that use legacy terminology by name. Worth a sweep alongside the field retirement so the narrator's reading material stays self-consistent.
- **No production-shaped character JSON fixture exists in the repo.** This makes it impossible to audit saved-record drift without DB access. With `extra="forbid"` on `CharacterModel` this isn't strictly necessary — drift would fail validation on read — but a single sanitized fixture would make future audits much faster.
