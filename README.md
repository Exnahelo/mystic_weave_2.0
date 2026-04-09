# Mystic Weave

Text-based narrative RPG engine powered by a custom ChatGPT GPT narrator, backed by FastAPI and Postgres. d100 roll-under resolution system designed for LLM-driven gameplay.

---

## How It Works

The player talks to a custom GPT in natural language. The GPT runs a structured game loop each turn: describe the location, present choices, resolve risk with dice, narrate the outcome, save state. The world reacts permanently to every decision. Failure is irreversible.

The GPT cannot hand-wave outcomes. All contested actions resolve through an authoritative d100 roll endpoint. The GPT makes two language judgments — which domain applies and which competency tags are relevant — assembles a target number, and sends it to the server. The server rolls. The GPT narrates exactly what the dice determined.

No ability score modifiers. No proficiency bonus calculations. No AC comparisons. Everything equals one point.

## Stack

Python 3.13 · FastAPI · uvicorn · asyncpg · Pydantic v2 · Postgres on Railway · ChatGPT custom GPT builder

## Game System

- **7 domains** (Power, Agility, Perception, Endurance, Intellect, Will, Presence) scored 25–60
- **8 species** — one generalist (Human), seven specialists (Orc, Elf, Halfling, Dwarf, Gnome, Tiefling, Dragonborn)
- **7 focus archetypes** — Champion, Sentinel, Stalker, Wayfinder, Arcanist, Devoted, Speaker
- **8 backgrounds** — Soldier, Scholar, Criminal, Noble, Outlander, Artisan, Acolyte, Performer
- **d100 roll-under** with 7-tier difficulty ladder (Trivial to Legendary)
- **5-tier competency system** for knowledge and application tags
- **6 outcome bands** — Critical Success through Critical Failure, margin-based

Full specification: `docs/mystic_weave_system_spec.md`

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
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
  main.py              # FastAPI app
  models.py            # Pydantic v2 models
  game_data.py         # Game system data loader
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
docs/
  mystic_weave_system_spec.md
prompts/               # Obsidian vault — GPT knowledge files + world content
  engine.md
  character_creation.md
  world_rules.md
schemas/
  openapi.yaml         # OpenAPI 3.1.1 spec for GPT Actions (v3.0.0)
scripts/
  seed_locations.py    # Seed locations from prompts/world/ into DB
tests/
  loop_test.py
  gpt_test_template.md
```

## Local Development

```bash
pip install -r requirements.txt
cp .env.example .env
# Set DATABASE_URL in .env
uvicorn api.main:app --reload
```

API at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

Version metadata is available at `http://localhost:8000/version`.

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

## Deployment (Railway)

1. Add a Postgres plugin in the Railway dashboard
2. Railway injects `DATABASE_URL` automatically
3. Push to `main` — Railway auto-deploys

Start command (in `railway.toml`):
```
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

## Environment Variables

| Variable | Required | Notes |
|---|---|---|
| `DATABASE_URL` | Yes | Postgres connection string. Railway injects automatically. |
| `RAILWAY_GIT_COMMIT_SHA` | No | Exposed by Railway; returned by `/version` when available. |
| `GIT_SHA` | No | Optional fallback commit SHA for non-Railway deployments. |
