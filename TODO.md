# Mystic Weave — TODO

## Phase 1: Foundation ✅

- [x] Repo cleanup and scaffolding
- [x] PostgreSQL setup on Railway
- [x] Pydantic v2 models for all game entities
- [x] Unified SRD data (2014+2024 merged into `data/srd/`)
- [x] `api/srd5e.py` — unified SRD loader (array format, O(1) lookup by index)

## Phase 2: State Endpoints ✅

- [x] FastAPI app (`api/main.py`)
- [x] `POST /session/new` — create session, seed character from SRD
- [x] `GET /state/{session_id}` — load game state
- [x] `POST /state/{session_id}` — save game state (UPSERT)
- [x] `POST /roll` — authoritative dice resolution with 5e modifier math
- [x] `GET /location/{id}` — load location data
- [x] `POST /location` — create/update location
- [x] `GET /location/{id}/connections` — get valid movement options
- [x] `POST /character/create` — re-seed character into existing session
- [x] `GET /options` — enumerate supported classes, species, subspecies, backgrounds
- [x] Railway deploy

## Phase 3: GPT Integration ✅

- [x] OpenAPI spec (`schemas/openapi.yaml`) — v2.1.0 with species/subspecies/backgrounds
- [x] GPT engine instructions (`prompts/engine.md`)
- [x] Character creation knowledge file (`prompts/character_creation.md`)
- [x] World rules knowledge file (`prompts/world_rules.md`)
- [x] 2024 migration complete (race → species, background-based ability bonuses, subspecies)
- [x] Custom mechanics removal (pure 5e SRD baseline)
- [x] Backgrounds — 16 backgrounds with full data
- [x] Species — 10 species with language selection, Aasimar added
- [x] Ability score methods (standard array, point buy, manual)
- [x] Character model gaps addressed (equipment, gold, tool proficiencies, weapon masteries, spell slots)
- [x] Housekeeping (requirements.txt, .env.example, deploy.yml, LICENSE, ATTRIBUTION.md)
- [x] Local loop test — `tests/loop_test.py` — **64/64 PASS**
- [x] End-to-end API test — `tests/e2e_test.py` — **84/84 PASS**

### Remaining Phase 3 Item

- [ ] End-to-end loop test with live GPT (requires Railway deploy + GPT builder + seeded locations)
  - [ ] New session creation (species + subspecies + background + class)
  - [ ] Turn loop (location load → action → roll → save)
  - [ ] Session resume
  - [ ] Edge cases: hp=0, invalid class/species

> **Blocked by:** Phase 5A1 — no authored location files exist to seed. The live GPT test requires at least a starter region in the database.

## Phase 4: Content Layer ✅

- [x] Obsidian world files (lore, factions, NPCs) in `prompts/`
- [x] Update `seed_locations.py` to read from `prompts/world/`
- [x] Subclass selection at character creation
- [x] Level-up system (`POST /character/levelup`)
- [x] Spell support (`GET /spells`, `GET /spells/{index}`)
- [x] Monster encounters (`GET /monsters`, `GET /monsters/{index}`)

### Drakenvale Lore Files (GPT-Ready, Not Yet Uploaded)

| File | Status |
| --- | --- |
| `drakenvale_world.md` | Complete |
| `drakenvale_organizations.md` | Complete |
| `drakenvale_characters.md` | Complete |
| `drakenvale_biomes.md` | Complete |
| `drakenvale_design_notes.md` | Living document (not for GPT builder) |

> **Do not upload lore files to GPT builder until the live loop test (Phase 3 remaining item) passes.**

---

## Phase 5: Location Graph (Current Priority)

The GPT can only move players along defined connections. Zero location markdown files exist in `prompts/world/`. This phase authors the minimum playable graph so a 20-turn session has no dead ends.

Each location is a markdown file in `prompts/world/` with YAML front matter matching the `seed_locations.py` schema: `id`, `name`, `type`, `description`, `tags`, `connections`, `threat_level`, `known_npcs`, `discovered`.

### 5A — Approach and Entry (6–8 locations)

The player's arrival arc. Covers the Alpine Peaks outer ring, the ward threshold, and first steps into the valley. Enough nodes for a full 20-turn loop test.

Source biomes: Alpine Peaks (outer shell, first biome encountered), Mystic Wetlands (valley edge, borders outside world).

- [ ] `alpine-pass.md` — High mountain pass through the outer ring. Ice drakes and frost wyverns patrol as territorial creatures, not guards. Glacial crystals, treacherous terrain. Starting location for new sessions. Threat 3. Tags: [alpine, high-altitude, entry-point].
- [ ] `glacial-stream-crossing.md` — Stream fed by the peaks, bridged by ancient stone. Rest point, water source. Connects pass to lower slopes. Threat 2. Tags: [alpine, water, transition].
- [ ] `ironwood-ridge.md` — Frost-tolerant ironwood forest on the mountain slope. Frostwing Owls, Snowbound Yeti territory nearby. Shelter available but watched. Threat 2. Tags: [alpine, forest, shelter].
- [ ] `wardline-threshold.md` — The boundary where Drakenvale's ancient wards begin. Magical barrier that deters intruders — requires draconic guidance or knowledge of the ward-paths to cross. Major narrative gate. Threat 2. Tags: [ward, threshold, magical-barrier].
- [ ] `misty-descent.md` — The fog-shrouded slope below the wards, transitioning from alpine cold to valley warmth. Disorienting mist, restorative pools at the edges. Mystic Wetlands influence bleeds in here. Threat 2. Tags: [transition, mist, wetland-edge].
- [ ] `valley-edge-overlook.md` — First clear view of Drakenvale below. Breathtaking vista: the Stronghold in the distance, temperate forest canopy, crystalline rivers. Safe vantage point. Threat 1. Tags: [overlook, safe, vista].
- [ ] `silverwood-trail.md` — Path through the outer Temperate Forest. Silver-barked trees, glowing mushrooms, whispering vines. First encounter with Drakenvale's enchanted ecosystem. Threat 2. Tags: [forest, temperate, enchanted-flora].
- [ ] Verify: all connections are bidirectional where appropriate, no dangling references
- [ ] Run `seed_locations.py` against local Postgres, confirm all locations and edges seed cleanly

> **After 5A:** Run the live GPT loop test (Phase 3 remaining item). If it passes, proceed to 5B.

### 5B — Stronghold and Interior (8–10 locations)

The fortress and its key spaces, plus the surrounding valley biomes a player will explore. Draw from `drakenvale_world.md`, `drakenvale_biomes.md`, and the Key Locations table.

- [ ] `stronghold-gates.md` — Main entrance to the Stronghold. Dragon-spine architecture, draconic aura. Dragonborn guards. Hub connecting exterior valley to interior spaces. Threat 0. Tags: [stronghold, entrance, hub].
- [ ] `draconic-hall.md` — Seat of governance. Vaulted chamber, Bahamut/Tiamat mosaic floor, Radiant Crystal at center. Council convenes here. Threat 0. Tags: [stronghold, governance, sacred].
- [ ] `the-aeries.md` — Open-air dragon perches above the fortress. Warded platforms, panoramic valley views. Dragons rest here. Threat 0. Tags: [stronghold, dragon-perch, elevated].
- [ ] `platinum-heart.md` — Sanctum dedicated to Bahamut. Houses the Platinum Flame. Focal point for rituals and prayers. Guarded by divine wards. Threat 0. Tags: [stronghold, sacred, bahamut].
- [ ] `sacred-pools.md` — Mirror-still pools on the Platinum Heart exterior grounds. Tranquility aura (DC 14 Wis save to act aggressively). Platinum Acolytes tend them. Healing properties. Threat 0. Tags: [sacred, pools, healing, safe].
- [ ] `amethyst-vault.md` — Varethyn's meditative space. Enchanted mirrors and reflective pools revealing hidden truths. Used for dispute mediation and introspection. Threat 0. Tags: [stronghold, wisdom, varethyn].
- [ ] `infernal-forge.md` — Powered by volcanic heat and dragon fire. Enchanted weapon and artifact crafting. Overseen by Zarkeros, staffed by dragonborn artisans. Threat 1. Tags: [stronghold, crafting, volcanic, zarkeros].
- [ ] `draconic-grasslands.md` — Open valley terrain between the forest and the Stronghold. Latent growth magic. Ceremonial space, exposed. Threat 1. Tags: [valley, open, ceremonial].
- [ ] `crystalline-river.md` — Sparkling river fed by glacial streams, waters infused with latent magic. Runs through the valley floor. Connects forest to grasslands. Threat 1. Tags: [valley, water, magical-flora].
- [ ] Verify graph connectivity — every stronghold interior connects back to stronghold-gates hub

### 5C — Danger Zones (3–5 locations)

High-threat areas that exist in the graph but are not on the main path. Discovery sites, narrative hooks, endgame content. The GPT should warn players about these — they are not casual destinations.

Source: Shadowed Hollows, Rift of Discord, Sealed Temple, Crystal Caverns, Volcanic Highlands.

- [ ] `shadowed-hollows-edge.md` — The border where the Temperate Forest darkens and thickens. Necrotic seepage from the sealed Temple below. Warped flora, oppressive atmosphere. No one holds this space — it is watched, not controlled. Threat 4. Tags: [dark, necrotic, tiamat-influence, watched].
- [ ] `rift-of-discord.md` — Chasm of unstable magical energy. Scar from the Discordant War. Not a dungeon — a wound. Chaos energy interacts with the Hollows' necrotic energy. Genuine risk without clear reward. Threat 5. Tags: [chaotic, unstable, hazard, endgame].
- [ ] `crystal-caverns-entrance.md` — Access point to the underground labyrinth beneath the valley. Radiant crystal formations, spell amplification. Connected to Varethyn's lair region — assume you may be observed. Threat 3. Tags: [underground, caverns, varethyn, spell-amplification].
- [ ] `volcanic-highlands-trail.md` — Path into the mountain interior toward Zarkeros's domain. Basalt formations, geothermal vents, ash in the air. Fire elementals and red drakes are wild, not guards. Threat 3. Tags: [volcanic, fire, zarkeros-territory, hazardous-terrain].
- [ ] Verify: danger zones connect to main graph but are clearly marked as high-threat

### 5D — Seed and Validate

- [ ] Run `seed_locations.py` with complete graph (5A + 5B + 5C)
- [ ] Verify all edges resolve (no WARN messages)
- [ ] Spot-check: `GET /location/{id}` and `GET /location/{id}/connections` for 3+ locations
- [ ] Confirm graph supports at least 20 turns of movement without dead ends
- [ ] Update `starting_location` in README smoke tests and test fixtures from `thornvale` to `alpine-pass`
- [ ] Update `tests/e2e_test.py` seed data (THORNVALE, ASHWOOD_TRAIL constants) to use Drakenvale locations

---

## Phase 6: Lore Gaps

World rules and protocols that give the GPT coherent rails for improvisation. Prioritized by likelihood of being hit in a typical session.

### 6A — Crisis Protocols (High Priority)

Players will trigger threat responses. The GPT needs a decision framework.

- [ ] Add a Crisis Protocols section to `drakenvale_world.md`
  - [ ] Tiered alert system (3 levels: Vigilance, Mobilization, Existential)
  - [ ] Command chain (Zarkeros → military, Eryndor → civilian/Wardens, Varethyn → intel/countermeasures)
  - [ ] Communication network (how alerts propagate)
  - [ ] Non-combatant evacuation basics

### 6B — Alignment Dispute Protocols (Medium-High Priority)

Council tension is a core narrative dynamic. The GPT needs rules for when dragons disagree.

- [ ] Add Alignment Dispute Protocols subsection to `drakenvale_world.md` Governance
  - [ ] Council dispute resolution (debate → Radiant Crystal tiebreaker → Trial of Wings escalation)
  - [ ] Joint operation rules (who leads when jurisdictions overlap)
  - [ ] Cross-faction friction handling (chromatic vs. metallic tension points)

### 6C — Non-Draconic Resident Integration (Medium Priority)

Players may be mortals or interact heavily with mortal NPCs.

- [ ] Expand `drakenvale_world.md` Advisory Roles and Military sections
  - [ ] Harmony Assembly — mortal advisory body, petition process
  - [ ] Kobold Coordination Corps — welfare, infrastructure, community roles
  - [ ] Mortal combat roles (Acolytes of Justice, militia, support)
- [ ] Add brief org entries to `drakenvale_organizations.md`

### 6D — Tiamat Corruption Response (Medium Priority)

Almost certainly a story arc. The GPT needs a protocol, not a script.

- [ ] Add GM-facing Corruption Response protocol to `drakenvale_world.md` or `drakenvale_organizations.md`
  - [ ] Detection: what Wardens look for (behavioral signs, magical signatures)
  - [ ] Investigation: how they confirm (Amethyst Vault mirrors, Varethyn's network)
  - [ ] Containment: immediate response (isolation, ward reinforcement)
  - [ ] Escalation: when to involve the Council

### 6E — Resource Management (Lower Priority)

Only matters if a player asks about trade, economics, or scarcity.

- [ ] Expand Economy section of `drakenvale_world.md`
  - [ ] Resource allocation (who controls what, how decisions are made)
  - [ ] Sustainability protocols (Ptarian Code mining rules)
  - [ ] Scarcity triggers (what causes resource tension, narrative hooks)

### 6F — Design Notes Cleanup

- [ ] Update `drakenvale_design_notes.md` to mark 6A–6E as resolved decisions once implemented
- [ ] Remove Phase 4 gate notice (it's passed)

---

## Deferred Work

Items that are tracked but explicitly not scheduled. Do not work on these until instructed.

### Stub Organizations

Named in source material, no authored content. The GPT should treat them as existing but unknown.

- Verdant Concord, Solace Pact, Horizon Seekers, Cogwright Accord, Concord of Voices
- Sapphire Sentinels (partial), Silver Wing Envoys (partial), Circle of Artisans, Sapphire Choir
- Order of the Platinum Flame (summary only)

### Species-Specific Choices (Deferred)

In the SRD JSON but not enforced by the API. The GPT can present these narratively; backend validation is deferred.

- Spellcasting ability choice — Elf/Gnome/Tiefling lineage (CHA/INT/WIS) via `species_choices`
- Human skill choice — Skillful trait (1 free skill) via `species_choices`
- Human origin feat — Versatile trait (1 Origin feat) via `species_choices`
- Size choice — Aasimar/Human/Tiefling Medium/Small via `species_choices` (field exists, enforcement deferred)

### Post-Crisis Recovery

Renewal Rites concept referenced in Apple Notes. Short entry under Platinum Acolytes when needed.

### Mortal/Kobold Cultural Identity

Artistic traditions, festivals, spiritual life distinct from draconic practice. Candidate for a standalone `drakenvale_culture.md`. Low priority for GPT function, high priority for world texture.

### Artifact Tracking System

Mechanism for reclaiming misused artifacts that leave Drakenvale. Likely handled covertly by the Amethyst Veil via SSTC trade routes. Worth a GM note when the SSTC org entry is expanded.

---

## Known Tech Debt

- No Python `__init__.py` files in `api/` directories
- `api/routes/roll.py` uses a `sys.path` hack to import the dice roller
- No automated test suite beyond manual smoke tests and `loop_test.py` / `e2e_test.py`
- Class subclass validation exists but subclass *selection* UI guidance in knowledge files could be richer

---

## File Map

```
mystic_weave/
├── api/
│   ├── main.py              # FastAPI app, router registration
│   ├── models.py            # Pydantic v2 models (CharacterModel, WorldModel, etc.)
│   ├── srd5e.py             # Unified SRD loader (2014+2024 merged data)
│   ├── database.py          # asyncpg pool management
│   └── routes/
│       ├── character.py     # POST /character/create
│       ├── levelup.py       # POST /character/levelup
│       ├── location.py      # GET/POST /location
│       ├── monsters.py      # GET /monsters, GET /monsters/{index}
│       ├── options.py       # GET /options
│       ├── roll.py          # POST /roll
│       ├── session.py       # POST /session/new
│       ├── spells.py        # GET /spells, GET /spells/{index}
│       └── state.py         # GET/POST /state/{session_id}
├── core/
│   └── dice_roller.py       # Dice rolling logic (do not modify)
├── data/
│   └── srd/                 # Unified SRD data (25 JSON files, 2014+2024 merged)
├── prompts/                 # Obsidian vault (GPT knowledge files + world content)
│   ├── engine.md            # GPT system instructions (upload to GPT builder)
│   ├── character_creation.md # Character creation reference (knowledge file)
│   ├── world_rules.md       # World mechanics reference (knowledge file)
│   ├── drakenvale_world.md  # Drakenvale lore (knowledge file — upload after loop test)
│   ├── drakenvale_organizations.md  # Organizations (knowledge file)
│   ├── drakenvale_characters.md     # NPCs and dragons (knowledge file)
│   ├── drakenvale_biomes.md         # Biome data (knowledge file)
│   ├── drakenvale_design_notes.md   # Internal design notes (do NOT upload)
│   └── world/               # Location markdown files for seed_locations.py
├── schemas/
│   └── openapi.yaml         # OpenAPI 3.1.1 spec for GPT Actions
├── scripts/
│   ├── merge_srd.py         # MAINTENANCE ONLY: merge 2014+2024 SRD data
│   └── seed_locations.py    # Seed locations from prompts/world/ into Postgres
├── tests/
│   ├── gpt_test_template.md # GPT integration test template
│   ├── loop_test.py         # Local API loop test — 64/64 PASS
│   └── e2e_test.py          # End-to-end GPT flow simulation — 84/84 PASS
├── .env.example
├── ATTRIBUTION.md
└── LICENSE
```
