# Mystic Weave

Text-based narrative RPG engine powered by a custom ChatGPT GPT narrator, backed by FastAPI and Postgres. d100 roll-under resolution system designed for LLM-driven gameplay.

---

## How It Works

The player talks to a custom GPT in natural language. The GPT runs a structured game loop each turn: describe the location, present choices, resolve risk with dice, narrate the outcome, save state. The world reacts permanently to every decision. Failure is irreversible.

The GPT cannot hand-wave outcomes. All contested actions resolve through an authoritative d100 roll endpoint. The GPT makes two language judgments — which domain applies and which competency tags are relevant — assembles a target number, and sends it to the server. The server rolls. The GPT narrates exactly what the dice determined.

No ability score modifiers. No proficiency bonus calculations. No AC comparisons. Everything resolves through one number.

## Stack

Python 3.13 · FastAPI · uvicorn · asyncpg · Pydantic v2 · Postgres on Railway · ChatGPT custom GPT builder

## Game System

**Resolution**
- **7 domains** (Power, Agility, Perception, Endurance, Intellect, Will, Presence) scored 25–60
- **d100 roll-under** with 7-tier difficulty ladder (Trivial to Legendary)
- **5-tier competency system** for knowledge and application tags
- **6 outcome bands** — Critical Success through Critical Failure, margin-based

**Character options** (all verified against `GET /options` — never hardcoded)
- **8 species** — one generalist (Human), seven specialists (Orc, Elf, Halfling, Dwarf, Gnome, Tiefling, Dragonborn)
- **7 focus archetypes** — Champion, Sentinel, Stalker, Wayfinder, Arcanist, Devoted, Speaker
- **8 backgrounds** — Soldier, Scholar, Criminal, Noble, Outlander, Artisan, Acolyte, Performer

**Character layers** (v3.1.0)
- **Identity** — origin, motivations, quirks, bonds, flaws, wound, alignment (two-axis enum + ethos note)
- **Equipment** — worn / carried / stashed slots, optional `roll_tag` linking items to application tags
- **Reputation** — per-faction standing (−100 to +100); party reputation computed by GPT at resolution time

**World layers** (v3.1.0)
- **Companions** — lightweight companion schema with identity, optional stat block, disposition, and faction standing
- **Economy** — wealth tier (universal) + raw coin (currency regions); trade goods and obligations
- **Politics** — faction memberships, active obligations, legal standing, leverage, tensions, Conclave status

System reference: `prompts/world_rules.md` and `prompts/character_creation.md`

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/version` | Build metadata, data fingerprint, option counts |
| GET | `/options` | Enumerate species, focus, background options |
| POST | `/session/new` | Create new session and character |
| POST | `/character/create` | Re-seed character into existing session |
| GET | `/state/{session_id}` | Load game state |
| POST | `/state/{session_id}` | Save game state (UPSERT) |
| POST | `/roll` | Authoritative d100 dice resolution |
| GET | `/location/{id}` | Load location data |
| GET | `/location/{id}/connections` | Get valid movement options |
| POST | `/location` | Create/update location |

## Project Structure

```
api/
  main.py              # FastAPI app — version string here (keep in sync with openapi.yaml)
  models.py            # Pydantic v2 models (v3.1.0 schema)
  game_data.py         # Game system data loader + seed_character
  database.py          # asyncpg pool management
  routes/
    character.py       # POST /character/create
    location.py        # GET/POST /location
    options.py         # GET /options
    roll.py            # POST /roll (d100 roll-under)
    session.py         # POST /session/new
    state.py           # GET/POST /state/{session_id}
core/
  dice_roller.py       # Dice rolling logic — do not modify
data/
  species.json         # 8 species with domain scores
  focus.json           # 7 focus archetypes with tags
  backgrounds.json     # 8 backgrounds with tags
prompts/               # Obsidian vault — GPT knowledge files + world content
  engine.md            # GPT system prompt — paste into GPT builder Instructions (<8000 chars)
  character_creation.md
  world_rules.md
  drakenvale_world.md
  drakenvale_organizations.md
  drakenvale_characters.md
  drakenvale_biomes.md
  drakenvale_factions.md
  drakenvale_design_notes.md  # Internal — do NOT upload to GPT builder
schemas/
  openapi.yaml         # OpenAPI 3.1.1 spec v3.1.0 — upload to GPT builder Actions
scripts/
  seed_locations.py    # Seed locations from prompts/world/ into DB
  verify_production_contract.py  # Validate production against repo expectations
tests/
  loop_test.py         # Full API loop test (local or Railway)
  gpt_test_template.md # Manual GPT live test script (10 blocks)
  unit/                # Fast deterministic unit tests
  contract/            # OpenAPI contract assertions
```

## Local Development

```bash
pip install -r requirements.txt
cp .env.example .env
# Set DATABASE_URL in .env
# (optional) run migrations manually
alembic upgrade head
uvicorn api.main:app --reload
```

API at `http://localhost:8000`. Docs at `http://localhost:8000/docs`. Version metadata at `http://localhost:8000/version`.

### Database Migrations (Alembic)

Schema lifecycle is now managed by Alembic instead of ad hoc `CREATE TABLE` on startup.

```bash
# Apply latest schema
alembic upgrade head

# Create a new migration after schema changes
alembic revision -m "describe change"

# Roll back one migration
alembic downgrade -1
```

Note: app startup runs `alembic upgrade head` automatically using `DATABASE_URL`.

### Smoke Tests

```bash
curl http://localhost:8000/health
curl http://localhost:8000/version
curl http://localhost:8000/options
curl -X POST http://localhost:8000/session/new \
  -H "Content-Type: application/json" \
  -d '{"character_name":"Krath","species":"dragonborn","focus":"devoted","background":"soldier","adjustment_points":{"will":2,"endurance":3},"starting_location":"thornvale"}'
curl -X POST http://localhost:8000/roll \
  -H "Content-Type: application/json" \
  -d '{"target":64}'
```

### Run Tests

```bash
# Static contract/data/prompt guards
python scripts/check_openapi_drift.py
python scripts/validate_data_files.py
python scripts/validate_prompts.py

# Fast tests (unit + contract)
pytest tests/unit tests/contract

# Full loop smoke (requires running server + DB)
python tests/loop_test.py

# Against Railway
python tests/loop_test.py https://mysticweave-production.up.railway.app
```

## Deployment (Railway)

1. Add a Postgres plugin in the Railway dashboard
2. Railway injects `DATABASE_URL` automatically
3. Push to `main` — Railway auto-deploys

Start command (in `railway.toml`):
```
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Production Verification

```bash
python scripts/verify_production_contract.py
```

Checks that the live deployment matches the repo: OpenAPI required fields, option indices, and version metadata.

## Environment Variables

| Variable | Required | Notes |
|---|---|---|
| `DATABASE_URL` | Yes | Postgres connection string. Railway injects automatically. |
| `RAILWAY_GIT_COMMIT_SHA` | No | Exposed by Railway; returned by `/version` when available. |
| `GIT_SHA` | No | Optional fallback commit SHA for non-Railway deployments. |

## Version Notes

When bumping the API version, update it in **two places**:
1. `api/main.py` — the `version=` argument to `FastAPI()`
2. `schemas/openapi.yaml` — the `info.version` field

Both must stay in sync. The contract test at `tests/contract/test_openapi_contract.py` asserts the version string — update that assertion too.

**Current version:** 3.1.0
