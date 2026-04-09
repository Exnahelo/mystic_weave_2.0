# Mystic Weave 2.0 — TODO

## Phase 1: 2.0 Rebuild

### Completed
- [x] Game system specification (`docs/mystic_weave_system_spec.md`)
- [x] Species definitions (8 species, 280 point budget, one specialist per domain)
- [x] Focus archetypes (7 archetypes, playstyle-based, not domain-aligned)
- [x] Background archetypes (8 backgrounds, 3 tags each)
- [x] Knowledge skill lists (5 per domain, 35 total)
- [x] Application categories (12 categories, 2 per domain max)
- [x] Difficulty modifier ladder (7 tiers, Trivial to Legendary)
- [x] Degree of success bands (6 bands, margin-based)
- [x] Advancement rules
- [x] JSON character schema
- [x] GPT instruction block (under 800 characters)

### In Progress
- [ ] Delete SRD files and D&D-specific code
  - [ ] Remove `data/srd/` (25 JSON files)
  - [ ] Remove `src/2014/` and `src/2024/`
  - [ ] Remove `api/srd5e.py`
  - [ ] Remove `scripts/merge_srd.py`
  - [ ] Remove `ATTRIBUTION.md`
  - [ ] Remove `api/routes/levelup.py`
  - [ ] Remove `api/routes/monsters.py`
  - [ ] Remove `api/routes/spells.py`
- [ ] Deploy rewritten files
  - [ ] `api/models.py` — new Pydantic models
  - [ ] `api/game_data.py` — new data loader (replaces srd5e.py)
  - [ ] `api/routes/roll.py` — d100 roll-under
  - [ ] `api/routes/session.py` — new session creation
  - [ ] `api/routes/character.py` — new character seeding
  - [ ] `api/routes/options.py` — new options endpoint
  - [ ] `data/species.json` — species definitions
  - [ ] `data/focus.json` — focus archetype definitions
  - [ ] `data/backgrounds.json` — background definitions
  - [ ] `schemas/openapi.yaml` — v3.0.0
  - [ ] `prompts/engine.md` — rewritten GPT system prompt
  - [ ] `prompts/character_creation.md` — rewritten creation reference
  - [ ] `prompts/world_rules.md` — rewritten world rules
- [ ] Update `api/main.py` router registration (remove deleted routes)
- [ ] Update `README.md`

## Phase 2: Testing

- [ ] Rewrite `tests/loop_test.py` for 2.0 schema
- [ ] Rewrite `tests/e2e_test.py` for 2.0 schema
- [ ] Rewrite `tests/gpt_test_template.md` for 2.0 flow
- [ ] All tests passing locally
- [ ] Railway deploy
- [ ] Live GPT loop test against Railway deployment

## Phase 3: Content Layer

- [ ] Seed starter region locations (Drakenvale)
- [ ] Upload knowledge files to GPT builder
- [ ] Live gameplay test

---

## Known Tech Debt

- *(resolved)* `__init__.py` files added to `api/`, `api/routes/`, `core/`
- *(resolved)* `sys.path` hack removed — clean package imports throughout

---

## File Map (2.0 Target)

```
mystic_weave/
├── api/
│   ├── main.py              # FastAPI app, router registration
│   ├── models.py            # Pydantic v2 models (2.0 schema)
│   ├── game_data.py         # Game system data loader
│   ├── database.py          # asyncpg pool management
│   └── routes/
│       ├── character.py     # POST /character/create
│       ├── location.py      # GET/POST /location
│       ├── options.py       # GET /options
│       ├── roll.py          # POST /roll (d100 roll-under)
│       ├── session.py       # POST /session/new
│       └── state.py         # GET/POST /state/{session_id}
├── core/
│   └── dice_roller.py       # Dice rolling logic (do not modify)
├── data/
│   ├── species.json         # 8 species with domain scores
│   ├── focus.json           # 7 focus archetypes with tags
│   └── backgrounds.json     # 8 backgrounds with tags
├── docs/
│   └── mystic_weave_system_spec.md  # Complete game system specification
├── prompts/                 # Obsidian vault (GPT knowledge files + world content)
│   ├── engine.md            # GPT system instructions
│   ├── character_creation.md # Character creation reference
│   ├── world_rules.md       # World mechanics reference
│   ├── drakenvale_world.md
│   ├── drakenvale_organizations.md
│   ├── drakenvale_characters.md
│   ├── drakenvale_biomes.md
│   ├── drakenvale_design_notes.md   # Internal — do NOT upload
│   └── world/               # Location markdown files for seed_locations.py
├── schemas/
│   └── openapi.yaml         # OpenAPI 3.1.1 spec v3.0.0
├── scripts/
│   └── seed_locations.py    # Seed locations from prompts/world/ into Postgres
├── tests/
│   ├── gpt_test_template.md
│   ├── loop_test.py
│   └── e2e_test.py
├── .env.example
└── LICENSE
```
