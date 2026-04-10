# Mystic Weave — TODO

Updated after hardening passes pushed through commit `02d7fcb`.

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

- [ ] Add explicit await/validate checkpoints in `prompts/engine.md`:
  - [ ] Await endpoint response before narration
  - [ ] Validate required payload fields before irreversible updates
  - [ ] Define fallback behavior for incomplete API responses (retry/conservative narration)
- [ ] Add explicit player-confirmation gates for irreversible outcomes in turn flow
- [ ] Add canonical precedence block in runtime prompts (conflict-resolution order)
- [ ] Resolve cross-file canon contradictions:
  - [ ] Economy model consistency (`drakenvale_world.md` vs `drakenvale_factions.md`)
  - [ ] Arcane Conservatory access consistency (`drakenvale_factions.md` vs `drakenvale_organizations.md`)
  - [ ] Crisis protocol maturity/status consistency across canon docs
- [ ] Add deterministic tie-break rules for ambiguous domain/tag adjudication
- [ ] Add deterministic state-write order for complex multi-change turns
- [ ] Add standardized handling for sparse/unknown faction reputation data
- [ ] Add global stub-handling policy for unfinished organizations/lore
- [ ] Extend `scripts/validate_prompts.py` checks for:
  - [ ] presence of await/checkpoint sections in required runtime prompts
  - [ ] presence of canon precedence marker
  - [ ] warning markers for known contradiction pairs
