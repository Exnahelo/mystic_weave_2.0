# Character System v4.0.0 Handoff

This handoff summarizes the v4.0.0 character-system migration work completed in this branch and identifies the remaining environment-dependent checks Daniel should run locally once a real database connection is available.

## Task Status Summary

| Task | Status | Notes |
|---|---|---|
| 1. Retire `species.json` refs | Complete | Ancestry/culture loaders added, template filtering added. |
| 2. Update Pydantic models | Complete | `ancestry`/`culture`/`fields` landed; adjustment caps updated. |
| 3. Rewrite `seed_character` | Complete | 4-layer domain math, stacking, and field support implemented. |
| 4. Update session/character routes | Complete | Routes now pass ancestry + culture into seeding. |
| 5. Update `/options` | Complete | `ancestries`, `cultures`, `focus`, `backgrounds` exposed. |
| 6. Update `/version` | Complete | API version now `4.0.0`; ancestry/culture counts added. |
| 7. Rewrite data validator | Complete | New ancestry/culture/focus/background rules + `field_tags` validation. |
| 8. Update production verifier | Complete | Local contract verification passed. |
| 9. Migration script | Conditionally complete | Pure transform + unit tests complete; real DB execution deferred to Daniel. |
| 10. Regenerate OpenAPI | Complete | OpenAPI regenerated and drift check passed. |
| 11. Update unit tests | Complete | `pytest tests/unit/ -v` and `pytest tests/contract/ -v` passed. |
| 12. Update prompts | Complete | Prompt validation passed; `engine.md` under 8k chars. |
| 13. Final smoke test | Conditionally complete | `/options` smoke passed; DB-backed session/location flow deferred to Daniel. |

## Environment-Deferred Acceptance Items

These checks were blocked only by missing `DATABASE_URL` in the local environment:

1. **Task 9 migration against real DB**
   - `python scripts/migrate_character_v4.py --dry-run`
   - `python scripts/migrate_character_v4.py --session 74a30d9f`

2. **Task 13 live session creation against local DB-backed server**
   - `POST /session/new` with the v4 sample payload

3. **Full `loop_test.py` run against local DB-backed server**
   - `python tests/loop_test.py http://localhost:8000`

## Commands Daniel Should Run Once DB Is Available

```bash
export DATABASE_URL=<his-connection-string>
python scripts/migrate_character_v4.py --dry-run
python scripts/migrate_character_v4.py --session 74a30d9f
python -m pytest tests/ -v
python tests/loop_test.py http://localhost:8000
curl -X POST http://localhost:8000/session/new -H "Content-Type: application/json" -d @tests/fixtures/v4_sample_character.json
```

## Sample Payload File

Committed at:

`tests/fixtures/v4_sample_character.json`

This payload uses:
- ancestry: `dragonborn`
- culture: `draconic_grasslands`
- focus: `devoted`
- background: `acolyte`
- adjustments: `will +5`, `endurance +5`

Expected smoke outcome after DB-backed create:
- HTTP 201 from `POST /session/new`
- returned character has `fields.sacred >= 2` (currently stacks to 3)

## Commits Created In This Workstream

- `d091f84` — v4.0.0 task 1 — retire species references
- `11ca3c3` — v4.0.0 task 2 — update models for four layers
- `b4b1234` — v4.0.0 task 3 — rewrite seed character for four layers
- `7c24fb0` — v4.0.0 task 4 — update route seed params
- `6743732` — v4.0.0 task 6 — update version metadata
- `0211dcf` — v4.0.0 task 7 — rewrite data validator
- `00a863a` — v4.0.0 task 8 — update production verifier
- `0988592` — v4.0.0 task 9 — add character migration script
- `07091ca` — v4.0.0 task 10 — regenerate openapi schema
- `e8fd5e1` — v4.0.0 task 11 — update tests for four layers
- `272e03b` — v4.0.0 task 12 — update prompts for four layers

Note: Task 5 changes were included in the earlier route/options commit path rather than a standalone new commit.

## Remaining TODOs Noticed During Implementation

1. `tests/loop_test.py` and several regression tests still reference legacy species-era payloads and legacy state semantics; these were not completed because the task sequence stopped before full regression suite modernization.
2. DB-backed endpoints now fail clearly when `DATABASE_URL` is absent, but they still require a real database for live end-to-end smoke.
3. Companion schema intentionally still uses `species`; this was preserved by decision and is reflected in OpenAPI.