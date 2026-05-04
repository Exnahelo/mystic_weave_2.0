# Mystic Weave 2.0 — Architecture Review (2026-05-02)

This review picks up above the system audit at `docs/audit/system_audit_2026-05-02.md` (SHA `7ca54a7`). That audit covered legacy artifacts and residue. This one covers structural choices.

## Executive summary

The biggest structural risk is **silent contract drift between things that must agree**: README version (4.4.0) vs API (4.8.0); `prompts/calendar.md` (366-day year, intercalary festivals) vs `api/time_advance.py` (360-day year, in-month festivals); the CLAUDE.md claim that "CI enforces" the data↔vault mirror that no script actually checks; the 8000-byte `engine.md` ceiling guarded only by hand (currently at 7998 bytes — 2 bytes from breaking GPT Builder upload). The biggest opportunity is a small set of cheap CI gates — a byte-count check, a calendar-canon parity assertion, a registry/Literal parity test — that would convert several already-existing manual disciplines into enforced ones.

## Q1. Duplication findings

### Critical: Calendar canon split between code and prompt with conflicting semantics
`prompts/calendar.md:12` declares "12 months × 30 days + 6 festival days = 366 days per year." `api/time_advance.py:41` declares "12 months × 30 days = 360 days/year. Festivals fall on..." The 6 festival days exist in `time_advance.py:24-31` as `(month, day)` lookups inside the regular 360-day cycle, while `calendar.md` describes them as outside-of-month observances. If a player asks "what day is it after Highharvestide?" the narrator's answer (from prompt) and the backend's answer (from code) will differ. **Severity: Critical.** The two stories disagree on year length. No validator notices.

### Notable: Calendar month/season/festival vocabulary triplicated
The 12 month names + season map + festivals appear in `api/time_advance.py:8-31`, `prompts/calendar.md:22-48`, and as defaults in `api/models.py:621-622` and `api/routes/session.py:84-91`. Adding a 13th month or renaming `Verdantrise` requires 4 lockstep edits; nothing enforces it.

### Notable: API version triplicated, README far behind
`api/main.py:45` says `4.8.0`. `schemas/openapi.json:6` says `4.8.0` (kept in sync by `check_openapi_drift.py:124`). `README.md:33,38,110,171,290` all say `4.4.0`. README is 4 minor versions stale because the drift checker only compares spec ↔ app, not README ↔ spec.

### Notable: `MechanicalEffect` defined twice with identical fields
`api/items.py:48-73` and `api/models.py:1223-1247` are two distinct Pydantic classes with the same name and identical-looking fields. Pydantic's OpenAPI generator deduplicates by class name, so they currently produce one `#/components/schemas/MechanicalEffect`. If one drifts (a new field added in items.py for catalog validation purposes), the OpenAPI generator will silently emit the last-written one and the other call sites get a wrong schema.

### Notable: Arc registry split between code Literals and JSON
`api/models.py:245-258` defines `ArcStakeScale`, `ArcOriginType`, `ArcState`, `ArcPrimaryType` as `Literal[...]` types. `data/catalog/registries/arc_types.json` independently declares `states`, `stake_scales`, `origin_types`, `subtypes`. Subtype is enforced from data via the validator at `api/models.py:482-491`; the rest are not cross-checked. Adding a state to one location and not the other = silent drift. The state machine in `api/arc_state_machine.py:16-40` is a third source.

### Notable: `INSERT INTO game_states ... ON CONFLICT` UPSERT replicated 4×
`api/routes/state.py:425-432`, `api/routes/state.py:509-517`, `api/routes/companion.py:80-94`, and `api/routes/session.py:105-111`. Three include the `log = log || $5::jsonb` append; one does not. `api/repositories/state_repository.py` only has UPDATE variants, not the UPSERT — so the repository abstraction was created but not finished. A column added to `game_states` requires editing 4 raw SQL strings.

### Marginal: `_plain_validation_errors` helper duplicated verbatim
Identical implementation in `api/routes/state.py:43-52`, `api/routes/arc.py:98-107`, `api/routes/companion.py:34-42`. Three lines, low drift risk.

### Marginal: Initial world hardcoded twice
`api/routes/session.py:66-92` hardcodes a fresh `WorldModel` shape with magic strings (`"Verdantrise"`, `847`, `"morning"`, `"unknown"`). `WorldModel` defaults at `api/models.py:701-735` already produce essentially the same defaults. The route reimplements them by hand.

## Q2. Workflow friction findings

### Critical: 8000-byte engine.md ceiling not enforced anywhere
`engine.md` is currently 7998 bytes. Cap is 8000 bytes per CLAUDE.md:40 and README.md:161. No script checks it: `scripts/validate_prompts.py` validates section headers but never byte size. CI runs validate_prompts.py; CI does not check size. A two-character addition silently breaks the GPT Builder upload step that no automation ever executes. **Severity: Critical.** The ceiling exists, the manual discipline is documented in three places, the discipline is not encoded.

### Critical: `data/world/` ↔ `prompts/world_vault/` mirror not actually CI-enforced
CLAUDE.md:51 states "CI enforces the mirror." `scripts/validate_prompts.py:63-120` only validates frontmatter / tag formatting *inside* vault markdown files. It does not assert that every `data/world/**/*.json` has a paired `prompts/world_vault/**/*.md` or vice versa. `scripts/validate_naming.py` validates file naming, not pairing. Today the pairs match by inspection; tomorrow they could silently diverge. **Severity: Critical** — the contract is stated as enforced but isn't. The fix is one short script — diff the two stem sets — added to CI.

### Notable: GPT Builder upload procedure undocumented
When `prompts/engine.md`, `prompts/character-creation.md`, `prompts/world-rules.md`, etc. change, the human must manually re-upload to GPT Builder. `operational-runbook.md` covers Postgres, Railway, contract drift, smoke bundles — and not a single section about GPT-side artifacts. README.md scattered hints. There is no "prompt change → these files need re-uploading" checklist. The narrator silently runs on a stale prompt for as long as the human forgets.

### Notable: GPT-side spec regenerated separately but never validated against the live GPT
`scripts/regenerate_openapi.py` produces `openapi.gpt.json` from the live FastAPI app, with 6 hardcoded exclusions at lines 25-32. `scripts/check_openapi_drift.py:80-114` validates the file is a strict subset of the full spec and ≤30 ops. There is no equivalent of `verify_production_contract.py` for the GPT — i.e., no script that checks "the schema GPT Builder is actually serving matches `openapi.gpt.json`." Production verifier covers the API but not the GPT actions registration.

### Marginal: pytest configuration silent on warnings
`pytest.ini` does not set `filterwarnings`. Brief 6 fixed weather Pydantic warnings by code change rather than by elevating them via `-W error`. The next deprecation/serializer warning will accumulate silently until someone runs the full suite verbosely. Brief 6 manually scrubbed; nothing prevents the next one.

## Q3. Architectural fit findings

### Notable: `api/repositories/state_repository.py` is a half-finished abstraction
The repository class exists and exposes `get_character`, `get_world`, `update_character`, `update_world`, `append_log_entry` — but the actual write paths in `routes/state.py:425, 509`, `routes/companion.py:80`, and `routes/session.py:105` ignore it and use raw SQL. The repository imports `_normalize_character_state` from `routes/state.py` (note the underscore — reaching into a private helper). Only the arc repository fully uses it. Either commit to it (move all UPSERTs into it) or delete it. **Severity: Notable** for solo-dev velocity — the half-state forces every reader to ask "where is state actually written?" four times.

### Notable: `api/models.py` is a 1400-line kitchen sink
Characters, arcs, world, time, advancement, options, locations, scene, items, NPCs, companion forward-refs all in one file. Companions are split out (`api/companions.py`). Arc request/response shapes are split out (`api/schemas/arc_schemas.py`). Item is split out (`api/items.py`). The split happened halfway. Result: importers have to know which models live where, and class-name collisions like `MechanicalEffect` arise.

### Marginal: `extra="forbid"` is set on virtually every model
20+ `model_config = ConfigDict(extra="forbid")` declarations. Correct and protective at boundaries, but applied uniformly to every nested sub-model with no central base-class enforcing it. A new model added without it will silently pass through. Not a current bug, just a consistency-by-discipline pattern.

### Non-issue: `extra="forbid"` itself
First glance suggests defensive overkill for solo-dev. It is actually load-bearing: it prevents stored JSONB from accumulating drift fields and surfaces deltas-shape bugs as 422s. Keep it.

### Non-issue: FastAPI + Postgres + Alembic + Railway + asyncpg stack
Single Postgres, single uvicorn, single GPT, no caching, no queues, no Redis. Correctly sized for the use case. Don't touch.

## Q4. Missing capabilities findings

### Critical: No `wc -c prompts/engine.md` CI gate
The 8000-byte ceiling exists. The current value is 7998. The next routine prompt edit that adds a few characters will quietly produce a file too large for GPT Builder to ingest, the developer pushes, the GPT silently keeps running on whatever was last uploaded. Three lines of bash in `scripts/validate_prompts.py` (or the predeploy workflow) would prevent this entirely. Same shape would catch a future ceiling change for any other size-capped prompt.

### Critical: No `data/world/` ↔ `prompts/world_vault/` mirror parity check
CLAUDE.md says CI enforces it. Nothing does. A short Python script: `set(stems(data/world)) ^ set(stems(prompts/world_vault))` should be empty. Add to `validate_prompts.py`. Fixes the documented-vs-real gap.

### Notable: No registry-vs-Literal parity test for arcs
`data/catalog/registries/arc_types.json` lists `states`, `stake_scales`, `origin_types`, `subtypes`. `api/models.py:245-258` repeats them as `Literal[...]`. A unit test asserting `set(get_args(ArcState)) == set(load_arc_types()["states"])` etc. would catch silent drift the moment one side updates without the other. ~30 lines.

### Notable: No calendar parity test
`api/time_advance.py:8-31` and `prompts/calendar.md:22-48` independently declare 12 month names, 4 seasons, 6 festivals. A test that parses the `## Months` table out of `calendar.md` and asserts the names match `MONTHS` and seasons match `SEASON_BY_MONTH` would have caught the 360 vs 366 day discrepancy when whichever file was edited later.

### Notable: No assertion that README's option counts match data file counts
README.md:28-31 hardcodes "8 ancestries / 11 cultures / 9 focus / 8 backgrounds." The runtime values come from JSON. A README adding an ancestry without updating the count, or vice versa, currently happens silently — only the per-deploy `loop_test.py` exercises any of these. Add a unit test reading both. ~15 lines.

### Marginal: `pytest.ini` could elevate Pydantic deprecation warnings
Per CLAUDE.md "Known cosmetic issues" section and Brief 6 history, weather-related Pydantic warnings have already appeared and been suppressed once. Adding `filterwarnings = error::DeprecationWarning:pydantic` in `pytest.ini` would convert the next one into a CI failure rather than a slow accretion. The scope filter avoids unrelated `cryptography`/`asyncpg` deprecations.

## Q5. Architecture coherence findings

### Critical: Year length disagreement between calendar.md and time_advance.py
Already covered in Q1 — the prompt and the code give different answers to "what day comes after Highharvestide?" The narrator (reading the prompt) will treat festivals as not-in-month and produce a 366-day year. The backend (running time_advance) will treat them as `(month, day)` tuples in a 360-day year. When the player asks for day skip during a festival, narration and backend will diverge. The narrator says it's a festival; the backend will tick to the next month-day even on a festival day.

### Notable: Domain score range disagreement
`README.md:22` says "scored 25–60." `prompts/world-rules.md:9` says "scored 25–80." `prompts/world-rules.md:21` clarifies "Starting values are usually within ancestry baselines (commonly 25–60 before bonuses), but campaign progression can raise domains to 80." `api/models.py` validates `1 ≤ score ≤ 80`. So the prompt is internally correct (range 25–80, starting 25–60); the README is stale and misleading by stripping the "starting" qualifier. A player reading README believes the cap is 60.

### Notable: knowledge_groups + applications + magic_fields registries split between two directories
Per `api/game_data.py:28-32`: knowledge_groups and applications live at `data/tags/`. Magic_fields lives at `data/catalog/registries/`. All three are validated in `validate_data_files.py:844-848`. This split is semantically arbitrary — applications are no less catalog than magic fields, and treating them differently means new developers have to look in two places. Cognitive friction; cost to consolidate is moderate (validators and loaders both point at literal paths).

**Resolved (Brief 23, 5.4.3):** `applications.json` and `knowledge_groups.json` consolidated into `data/catalog/registries/`. The three `_template_*.json` files moved alongside. `data/tags/` directory removed. `data/catalog/registries/` is now the single canonical location for registry-style vocabulary files.

### Notable: AdvancementState recomputation policy contradicts the model's writability
`api/models.py:743-766` declares `CharacterStateDelta.advancement` accepts `AdvancementState | None` for "round-trip safety," explicitly noting the value is *replaced server-side* (the route layer recomputes counters in `state.py:265`). The narrator looking at the schema sees a writable field; the runtime treats it as read-only. The mismatch is documented in the docstring but not surfaced to the GPT or to any consumer of the OpenAPI schema. Anyone reading the schema will believe they can set `advancement.points_available` directly.

### Non-issue: Arc registry partly from code, partly from JSON
At first glance this looks incoherent (Q1 finding above). It is — but the data-driven `subtype` was the deliberate forward-only path because subtypes change more often than the lifecycle states. Code Literals for the slow-changing axes is intentional. The fix is the parity test (Q4), not a redesign.

## Recommended action order

1. **DECISION NEEDED — Resolve calendar canon disagreement.** Decide whether the year is 360 or 366 days, then align `prompts/calendar.md`, `api/time_advance.py`, `api/models.py` defaults, and `api/routes/session.py` initial state. Add a unit test parsing the `## Months` table from `calendar.md` and asserting equality with `MONTHS` / `SEASON_BY_MONTH`. Without this, narrator and backend currently disagree on any cross-festival time arithmetic.

2. **Add `wc -c prompts/engine.md` ≤ 8000 to `validate_prompts.py`.** Two lines. Currently 2 bytes from breaking the GPT Builder upload.

3. **Add data↔vault mirror parity check to `validate_prompts.py`.** Closes the CLAUDE.md-says-CI-enforces gap.

4. **Update `README.md`:** version 4.4.0 → 4.8.0 in 5 places (lines 33, 38, 110, 171, 290); domain range "25–60" → "25–80 (starting values 25–60)" at line 22; add a `_check_readme_version` step in `check_openapi_drift.py` that asserts `info.version` matches the README version line.

5. **Add registry/Literal parity test for arc types.** Unit test asserting `Literal` args match `arc_types.json` for `states`, `stake_scales`, `origin_types`. ~30 lines.

6. **Consolidate `MechanicalEffect`.** Either delete `api/items.py:48-73` and import from `api/models.py`, or vice versa. They're textually equivalent today.

7. **DECISION NEEDED — Resolve the repository pattern.** Either move all `INSERT INTO game_states ... ON CONFLICT` paths into `state_repository.py`, or delete the repository and accept raw SQL. The current half-state is the worst option.

8. **Add a "Prompt change → re-upload to GPT Builder" section to `operational-runbook.md`.** List the files: `engine.md` (system prompt) + every other `prompts/*.md` that's listed as a knowledge file in CLAUDE.md / README. One short table.

9. **(Lower priority) Split `api/models.py`.** Pull arc models, item-presentation models, scene context, options into separate modules. Keeps drift surfaces narrower.

## Items requiring user decision

1. **Calendar year length.** Is the year 360 days (festivals are normal calendar days) or 366 days (festivals are intercalary)? The prompt and the code currently disagree. The fix has visible narrative consequences; the user must pick which is canon.

2. **State-write repository commitment.** Either commit to `StateRepository` and migrate the 4 raw UPSERTs, or delete the repository class and accept the raw SQL pattern as the convention. The current state is decision-deferred.

3. **`api/models.py` split.** A 1400-line model module is a churn target but breaking it up is a non-trivial diff that touches every importer. Worth doing? User call.

## What is sound (don't change)

- **FastAPI + Postgres + asyncpg + Alembic + Railway + ChatGPT GPT.** Correctly sized.
- **`extra="forbid"` discipline on every model.** Load-bearing for stored-state safety; Brief 8 audit confirmed it prevents accumulated JSONB drift.
- **Backend-as-source-of-truth pattern.** The narrator-narrates / backend-enforces split is coherent and well-policed by the prompts.
- **`check_openapi_drift.py`.** Correctly enforces `info.version` parity, request/response schema-ref parity, and GPT spec subset/cap. The only place it doesn't reach is README, which the rec above fixes.
- **CI matrix (ci/predeploy/nightly/production_verify).** Right shape: fast lint+contract, full smoke on PRs, full integration nightly, scheduled prod verify. Don't restructure.
- **Alembic migration chain** (3 migrations, cleanly named with date prefixes, no orphans).
- **`core/dice_roller.py` sealed.** Correct — that's the one component you really do want frozen.
- **The audit boundary.** Brief 8 cleaned up the residue layer; this review correctly stops there and addresses structural choices, not legacy.
