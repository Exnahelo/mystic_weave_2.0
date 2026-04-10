# Mystic Weave — TODO

Updated after hardening + world/prompt alignment passes through commit `985b5ba`.

## ✅ Recently Completed

- [x] Enforce model validation at persistence boundaries for:
  - [x] `POST /session/new`
  - [x] `GET/POST /state/{session_id}`
  - [x] `POST /character/create`
- [x] Preserve and validate v3.1.0 schema blocks end-to-end:
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
  - [x] `api/main.py` version set to `3.1.0`
  - [x] `scripts/verify_production_contract.py` checks `3.1.0`
  - [x] README cleanup and `.env.example` added
- [x] Validation test run passing for hardened scope (`11 passed`)

## 🔜 Next Priority Backlog

- [x] Add Alembic migrations for schema lifecycle (replace ad hoc/manual DB evolution)
- [x] Add CI guard for OpenAPI drift (`app.openapi()` vs `schemas/openapi.yaml`)
- [x] Add data/prompt validation gates:
  - [x] schema checks for `data/*.json`
  - [x] structural/lint checks for prompt files used in production

## Later Enhancements

- [x] Strengthen deployment pipeline checks (pre-deploy contract + smoke bundle)
- [x] Expand end-to-end coverage for multi-turn narrative persistence edge cases
- [x] Add lightweight operational runbook for local/Railway troubleshooting

## Prompt System Follow-Up (from 2026-04-10 audit)

- [x] Add explicit await/validate checkpoints in `prompts/engine.md`:
  - [x] Await endpoint response before narration
  - [x] Validate required payload fields before irreversible updates
  - [x] Define fallback behavior for incomplete API responses (retry/conservative narration)
- [x] Add explicit player-confirmation gates for irreversible outcomes in turn flow
- [x] Add canonical precedence block in runtime prompts (conflict-resolution order)
- [x] Resolve cross-file canon contradictions:
  - [x] Economy model consistency (`drakenvale_world.md` vs `drakenvale_factions.md`)
  - [x] Arcane Conservatory access consistency (`drakenvale_factions.md` vs `drakenvale_organizations.md`)
  - [x] Crisis protocol maturity/status consistency across canon docs
- [x] Add deterministic tie-break rules for ambiguous domain/tag adjudication
- [x] Add deterministic state-write order for complex multi-change turns
- [x] Add standardized handling for sparse/unknown faction reputation data
- [x] Add global stub-handling policy for unfinished organizations/lore
- [x] Extend `scripts/validate_prompts.py` checks for:
  - [x] presence of await/checkpoint sections in required runtime prompts
  - [x] presence of canon precedence marker
  - [x] warning markers for known contradiction pairs

## API/OpenAPI Follow-Up (from 2026-04-10 review)

- [x] Add optional `reason` field to `RollRequest` for roll observability
- [x] Make `LocationResponse.data` typed (`LocationData`) instead of opaque object
- [x] Upgrade response schemas in `schemas/openapi.yaml` to concrete `$ref` usage where needed
- [x] Add `required` arrays for key response schemas used by GPT branching
- [x] Normalize updated nullable fields to OpenAPI 3.1 style (`anyOf` with `null`)

## Current Open Work (Next)

### Priority 1 — Game System Reference Docs

- [x] Design and write magic system reference (domain mappings, knowledge/application tags for magic, effect-scaling difficulty ladder)
- [x] Write difficulty reference (tiered encounter/challenge list with default modifiers; target ~30–40 entries)
- [x] Write notable items reference (canonical gear with roll tags + mechanical effects)

Added:

- [x] `prompts/magic_system_reference.md`
- [x] `prompts/difficulty_reference.md`
- [x] `prompts/notable_items_reference.md`

### Priority 2 — World Navigation Consistency

- [x] Run explicit reciprocity audit on `prompts/world/*.md` connections and decide intentional one-way vs two-way links
- [x] Document any intentionally one-way connections in a short note for future content updates

### Priority 3 — Documentation / Release Hygiene

- [x] Add short changelog note in `README.md` or `OPERATIONAL_RUNBOOK.md` for new world locations/lairs and access/discovery assumptions
- [x] Create lightweight release checkpoint (tag or release note) for post-audit + world topology baseline

## Gamplay upgrades from walkthrough

- [ ] Hunger tracking
- [ ] Hydration tracking
- [ ] Fatigue tracking
- [ ] Carrying Weight?
- [ ] We need to better define/understand how Domain/Knowledge/Application grow. Also the point Domain point distributions and how many are available/how they grow.
- [ ] Clarify how reputation grows.
- [ ] Coin sytem is in bad shape
