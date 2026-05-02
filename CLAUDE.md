# CLAUDE.md

Persistent context for Claude Code working in this repo. Read fully on every session.

## Project

Mystic Weave 2.0. Text-based narrative RPG with a custom ChatGPT GPT as narrator/GM, backed by a FastAPI + PostgreSQL backend on Railway. The backend is the source of truth for state, dice resolution, location graph, valid character-creation options, and arc lifecycle. The narrator GPT narrates only what backend endpoints return; it never fabricates mechanics, rolls, options, or arc state.

## Your role

Senior engineer collaborating on the project. You are NOT the narrator GPT — that's a separate ChatGPT custom GPT that runs gameplay. You implement backend, schema, prompt, and tooling changes against this repo.

- Diagnose before writing.
- Flag open questions explicitly. Do not silently assume.
- Push back on weak direction when correctness depends on it.
- Stay scoped: do not expand work beyond what was asked.

## Workflow

The standard pattern:

1. User describes a problem, design, or feature.
2. Diagnose and propose a plan or task brief.
3. Implement the work directly: read files, make edits, run validators, commit, push.
4. Report SHA. Verify the commit is on `origin/main` by `git log origin/main` after push.

Commit directly to `main`. No feature branches unless the user explicitly asks for one. The user works solo and prefers direct commits.

For multi-phase work, use validation gates between phases. Stop and report on any failure rather than guessing past it. Do not skip a gate to keep momentum.

## Standing orders

### Code

- Minimal diffs. Touch only what the task requires.
- Pydantic v2 syntax (`model_config`, `field_validator`, `model_validator`).
- `async` throughout FastAPI and asyncpg layers.
- Never hardcode DB credentials or commit secrets.
- Do not modify `core/dice_roller.py`. It is sealed.
- Keep `prompts/engine.md` under 8000 bytes. Verify with `wc -c` before finalizing prompt edits.
- Test data must be self-contained and ephemeral. No test fixtures in production paths.

### Architecture

- Backend is source of truth. GPT narrates; backend enforces.
- Field/scene/arc/AP rules in the repo's prompt files are canonical.
- Arc System v1 is live: AP is formal-contract-only, scope is envelope-bounded by type, settlement is endpoint-driven. See `prompts/arc-rules.md`.
- Fungible AP system (post-commit `4cca988`): advancement is four scalars (`points_available`, `points_spent`, `points_earned_total`, `tag_counter`). Do not reintroduce legacy AP structures.
- World content mirror: `data/world/**/*.yaml` ↔ `prompts/world_vault/**/*.md`. The vault leads, data follows. CI enforces the mirror.

### Scope discipline

- Do not expand scope into factions, combat subsystems, or other advanced features unless explicitly instructed.
- Migration policy: legacy session play remains untyped. New systems apply forward-only unless a migration is explicitly requested.

### API surface limits

- The GPT-facing OpenAPI spec (`schemas/openapi.gpt.json`) is capped at 30 operations by GPT Builder. The full spec (`schemas/openapi.json`) has no cap.
- When proposing new endpoints, check the GPT spec count first; if at the cap, propose trimming non-narration endpoints rather than splitting the spec.
- Static reference data (vocab, creatures, tags) belongs in GPT knowledge files, not as Action endpoints.

### Naming conventions

Per `docs/conventions.md` (canonical):

- Filesystem paths (files + directories) are `snake_case`.
- Content IDs, slugs, and tags are `kebab-case`.
- Filename stem relates to content ID by `stem == id.replace('-', '_')`.

## Authoritative repo docs

Repo wins on any conflict with this file — flag and proceed by repo:

- `README.md` — architecture and endpoint reference
- `docs/conventions.md` — naming
- `testing.md` — test and CI strategy
- `operational-runbook.md` — local and Railway ops
- `todo.md` — active work and recently completed
- `schemas/openapi.json` — full canonical API contract
- `schemas/openapi.gpt.json` — GPT Actions subset
- `prompts/arc-rules.md` — narrator-facing arc system rules
- `prompts/engine.md` — narrator engine procedures (8000-byte ceiling)

The API version is `info.version` in `schemas/openapi.json`. Do not memorize a number; read the spec.

## Tooling

- Python 3.13 · FastAPI · uvicorn · asyncpg · Pydantic v2 · PostgreSQL on Railway
- Tests: `pytest`. Validators: `python3 scripts/validate_data_files.py data`, `python3 scripts/validate_catalog.py`, `python3 scripts/validate_prompts.py`.
- Run Python as `python3` (not `python` — not aliased on this machine).
- Git: prefer plain shell `git`. The user has historically used GitKraken MCP but shell is faster and more reliable for verification.

## Validation expectations after changes

- Code changes: run `pytest`. Full suite is ~447 tests, ~30 seconds.
- Data file changes: run `python3 scripts/validate_data_files.py data`.
- Catalog changes: run `python3 scripts/validate_catalog.py`.
- Prompt changes: run `python3 scripts/validate_prompts.py` AND verify byte counts (especially `wc -c prompts/engine.md` against the 8000-byte ceiling).
- OpenAPI changes: regenerate via `python3 scripts/regenerate_openapi.py` if applicable.

## Known cosmetic issues — do NOT flag as regressions

- Up to 4 pytest warnings in weather-related contract tests if Pydantic serializer pre-existing warnings reappear. Mention only if relevant to the current task.

## When uncertain

Ask up to three precise clarifying questions only if missing information would materially change the implementation. Otherwise proceed and state key assumptions briefly. Do not ask clarifying questions about things visible in the repo — read the repo first.

## Communication style

The user prefers direct, analytical, structured responses. No fluff. No performative empathy. Concise prose. Lists only when they improve clarity. Push back on weak direction when correctness depends on it. Identify root causes, not symptoms.

## Verification of work landing

After commit and push, always run `git fetch origin && git log origin/main --oneline -3` to confirm the SHA actually landed on the remote. A common past failure mode has been work committed locally but not pushed.

## Recently completed (for context)

- Brief 6 (2026-05-01, SHA `28d6b75a`): Engine prompt refinement and warning cleanup. Added `## Spawn vs Replace vs Merge` section to `arc-rules.md`. Suppressed Pydantic weather warnings, FastAPI HTTP_422 deprecations, SyntaxWarning in test.
- Brief 5 / Catalog stabilization (2026-05-01): Armor tag conflict resolution, magic_fields registry consolidation, item directory renames (`weapons/`, `shields/`), 10 ecology facets, todo cleanup.
- Brief 3 / Companion vocab registry move (PR #13).
- Brief 2 / Arc beat logs + closure summary (PR #12). Adds typed log entries: `closure_summary`, `compression`, `narrative_non_arc`, `world_change`.
- Arc System v1 (2026-04-30, commits `007dc14` → `3eb8066`).