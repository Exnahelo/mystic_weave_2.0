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

- [ ] Add Alembic migrations for schema lifecycle (replace ad hoc/manual DB evolution)
- [ ] Add CI guard for OpenAPI drift (`app.openapi()` vs `schemas/openapi.yaml`)
- [ ] Add data/prompt validation gates:
  - [ ] schema checks for `data/*.json`
  - [ ] structural/lint checks for prompt files used in production

## Later Enhancements

- [ ] Strengthen deployment pipeline checks (pre-deploy contract + smoke bundle)
- [ ] Expand end-to-end coverage for multi-turn narrative persistence edge cases
- [ ] Add lightweight operational runbook for local/Railway troubleshooting
