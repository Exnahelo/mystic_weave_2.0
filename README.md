# Mystic Weave

A persistent game state backend for a text-based RPG set in **Drakenvale** — a hidden dragon sanctuary governed by the Ptarian Code. A custom ChatGPT GPT acts as the narrator and game master. This API is the memory.

---

## What It Is

The player interacts entirely through a ChatGPT custom GPT. The GPT runs a structured game loop each turn: load location → present choices → resolve risk with dice → narrate outcome → save state. The world reacts permanently to every decision. Failure is irreversible.

The API gives the GPT persistent memory across sessions. Without it, the GPT forgets everything between conversations.

---

## Architecture

```text
Player
  ↓ natural language
ChatGPT custom GPT (narrator + game master)
  ↓ OpenAPI Actions (schemas/openapi.yaml)
FastAPI app (Railway)
  ↓ asyncpg
Postgres (Railway plugin)
```

**Stack:** Python 3.13 · FastAPI · uvicorn · asyncpg · Pydantic v2 · Postgres on Railway

D&D 5e SRD data (2014+2024 merged) is stored locally as JSON snapshots in `data/srd/`. The external SRD API is never called at runtime.

---

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `GET` | `/options` | Enumerate classes, species, subspecies, backgrounds, languages |
| `POST` | `/session/new` | Create a new game session (seeds character from SRD) |
| `GET` | `/state/{session_id}` | Load full game state (call at session start) |
| `POST` | `/state/{session_id}` | Save game state + append log entry (call after each turn) |
| `POST` | `/character/create` | Seed or re-seed a character into an existing session |
| `POST` | `/roll` | Authoritative dice resolution with 5e modifier math |
| `GET` | `/location/{id}` | Load location data (call before describing any place) |
| `POST` | `/location` | Create or update a location node |
| `GET` | `/location/{id}/connections` | Get valid movement options from a location |

Interactive docs at `/docs` when running locally.

---

## Game State Model

State is stored in Postgres as two JSONB objects (`character` and `world`) plus a `log` array of one-sentence turn summaries. Saves are full overwrites — no partial patches.

```json
{
  "session_id": "a1b2c3d4",
  "character": {
    "name": "...",
    "class": "...",
    "species": "...",
    "subspecies": "...",
    "background": "...",
    "ability_scores": { "STR": 15, "DEX": 16, "CON": 13, "INT": 10, "WIS": 14, "CHA": 8 },
    "hp": { "current": 11, "max": 11 },
    "skills": ["perception", "stealth"],
    "proficiencies": ["..."]
  },
  "world": {
    "location": "drakenvale-stronghold",
    "threat": "...",
    "goal": "...",
    "turn": 1
  },
  "log": ["Turn 1: ..."]
}
```

---

## Dice Resolution

All risk is resolved by the backend. The GPT calls `POST /roll` before narrating any contested outcome and must narrate exactly what the dice determined — no softening, no reinterpretation.

- **Natural 1** → always critical failure
- **Natural 20** → always critical success
- Modifier math follows D&D 5e SRD: ability modifier + proficiency bonus (if applicable)

The dice roller (`core/dice_roller.py`) is the authoritative source. Do not modify it.

---

## The World: Drakenvale

Drakenvale is a hidden sanctuary carved into a secluded mountain valley, governed by the **Ptarian Code** — justice tempered by mercy, power tempered by restraint. The valley is home to metallic, chromatic, and gem dragons coexisting alongside dragonborn, kobolds, and mortals.

**The Draconic Council** rules by consensus:

| Dragon | Type | Domain |
| --- | --- | --- |
| Eryndor the Radiant | Gold Dragon | Justice, diplomacy |
| Zarkeros the Inferno | Red Dragon | Strength, defense |
| Varethyn of the Amethyst Gaze | Amethyst Dragon | Wisdom, arcane knowledge |

World locations are authored as Obsidian markdown files in `prompts/world/` with YAML front matter and seeded into Postgres via `scripts/seed_locations.py`. The GPT loads location data before describing any place and can only move the player along defined connections.

**Phase 4 (Drakenvale content layer) is locked until the live GPT loop test passes.**

---

## Repository Structure

```text
api/
  main.py              # FastAPI app
  models.py            # Pydantic v2 models
  srd5e.py             # Unified SRD loader
  database.py          # asyncpg pool management
  routes/
    character.py       # POST /character/create
    location.py        # GET/POST /location
    options.py         # GET /options
    roll.py            # POST /roll
    session.py         # POST /session/new
    state.py           # GET/POST /state/{session_id}
core/
  dice_roller.py       # Dice rolling logic — do not modify
data/
  srd/                 # 25 unified SRD JSON files (2014+2024 merged)
prompts/               # Obsidian vault — GPT knowledge files + world content
  engine.md            # GPT system instructions (upload to GPT builder)
  character_creation.md
  world_rules.md
  drakenvale_world.md
  drakenvale_organizations.md
  drakenvale_characters.md
  drakenvale_biomes.md
schemas/
  openapi.yaml         # OpenAPI 3.1.1 spec for GPT Actions (v2.1.0)
scripts/
  merge_srd.py         # MAINTENANCE ONLY: merge SRD source data
  seed_locations.py    # Seed world locations from prompts/world/ into DB
tests/
  loop_test.py         # Local API loop test (no GPT required)
  e2e_test.py          # End-to-end GPT flow simulation (targets Railway)
  gpt_test_template.md # Manual checklist for live GPT testing
```

---

## Local Development

### Prerequisites

- Python 3.13
- Postgres (local or Railway)

### Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Set DATABASE_URL in .env
uvicorn api.main:app --reload
```

API available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### Smoke Tests

```bash
# Health check
curl http://localhost:8000/health

# List options
curl http://localhost:8000/options

# Create a session
curl -X POST http://localhost:8000/session/new \
  -H "Content-Type: application/json" \
  -d '{
    "character_name": "Soren",
    "class": "ranger",
    "species": "human",
    "background": "soldier",
    "ability_scores": {"STR": 13, "DEX": 15, "CON": 12, "INT": 10, "WIS": 14, "CHA": 8},
    "skill_choices": ["perception", "stealth"],
    "starting_location": "drakenvale-stronghold",
    "goal": "Gain an audience with the Draconic Council",
    "threat": "Suspicion from the Dragon Guard"
  }'

# Roll a check
curl -X POST http://localhost:8000/roll \
  -H "Content-Type: application/json" \
  -d '{"dice": "1d20", "ability": "DEX", "score": 15, "proficient": true, "dc": 14}'
```

### Running Tests

```bash
# Local API test (requires local server running)
python tests/loop_test.py

# End-to-end test against Railway production
python tests/e2e_test.py

# End-to-end test against local
python tests/e2e_test.py --base-url http://localhost:8000
```

---

## Deployment (Railway)

1. Add a Postgres plugin in the Railway dashboard
2. Railway injects `DATABASE_URL` automatically
3. Push to `main` — Railway auto-deploys via `railway.toml`

Start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

---

## Environment Variables

| Variable | Required | Notes |
| --- | --- | --- |
| `DATABASE_URL` | Yes | Postgres connection string. Injected automatically by Railway in production. |

See `.env.example` for the local development template. Never hardcode credentials.

---

## Seeding World Locations

Author locations as Obsidian markdown files in `prompts/world/` with YAML front matter:

```markdown
---
id: drakenvale-stronghold
name: Stronghold of Drakenvale
type: fortress
description: The central fortress carved from platinum-veined stone. Dragon-spine architecture rises above the valley floor. The Draconic Hall sits at its heart.
tags: [drakenvale, fortress, high-magic]
connections: [the-aeries, draconic-hall, infernal-forge]
threat_level: 1
known_npcs: [Eryndor the Radiant, Zarkeros the Inferno, Varethyn of the Amethyst Gaze]
discovered: true
---
```

```bash
python3 scripts/seed_locations.py
```

---

## SRD Data

Local snapshots of the D&D 5e SRD (2014+2024 merged) live in `data/srd/` — 25 JSON files committed to the repo. 2024 rules take priority on conflicts. 2014-only data (classes, features, levels, monsters, spells) is preserved. The merge script (`scripts/merge_srd.py`) is maintenance-only and not called at runtime.

---

## GPT Integration

The GPT system prompt (`prompts/engine.md`) is a single document pasted into the ChatGPT custom GPT builder's Instructions field. It must stay under 8,000 characters. Knowledge files (`character_creation.md`, `world_rules.md`, and Drakenvale lore files) are uploaded manually to the GPT builder — there is no automated sync.

The GPT calls the API through OpenAPI 3.1.1 Actions defined in `schemas/openapi.yaml`. The `prompts/` directory is an Obsidian vault; `.obsidian/` config is gitignored.

---

## Development Rules

- Prefer minimal diffs. Do not refactor working code unless asked.
- Do not modify `core/dice_roller.py` under any circumstances.
- Do not modify files in `data/srd/`.
- Use Pydantic v2 syntax. Use async throughout.
- Never hardcode database credentials.
- Keep error payloads short and plain. Return meaningful HTTP status codes.
- Do not introduce factions, inventories, spell slots, combat subsystems, or advanced features until explicitly instructed.
- GPT system prompt must stay under 8,000 characters.

Free to modify: import paths, type hints, docstrings, test files, seed scripts, documentation.

---

## Licensing

Code and SRD content are open source under the terms in `LICENSE` and `ATTRIBUTION.md`.

**Drakenvale content** (files in `prompts/` and any Drakenvale-specific narrative content) is © Daniel Howe. Personal, non-commercial use is permitted. Commercial use, redistribution, or adaptation requires explicit written permission. See `DRAKENVALE_CONTENT_LICENSE.md`.
