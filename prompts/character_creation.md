# Mystic Weave — Character Creation Reference

This document is the authoritative, step-by-step reference for character creation. The GPT follows this flow exactly when starting a new session.

**IMPORTANT:** Always call `GET /options` first. Never enumerate species, focus archetypes, or backgrounds from this document or from memory. Use only what the backend returns.

---

## Character Creation Flow

### Stage 1 — Name and Species

1. Ask the player for a character name.
2. Call `GET /options` to retrieve all valid species.
3. Present the species list with their primary domain and domain score spread.
4. Player chooses a species.

### Stage 2 — Focus Archetype

1. Present the focus archetype list from `GET /options` with descriptions and starting tags.
2. Player chooses a focus. Any species can choose any focus.

### Stage 3 — Background

1. Present the background list from `GET /options` with descriptions and starting tags.
2. Player chooses a background. Any combination is valid.

### Stage 4 — Adjustment Points

1. The player has 5 points to distribute across domains, max +3 per domain.
2. Show the base domain scores from their species and ask where to allocate.
3. If the player skips this step, all adjustment points default to 0.

### Stage 5 — Confirm and Create

1. Show the player a summary: name, species, focus, background, final domain scores, all knowledge and application tags with tiers.
2. Confirm the build.
3. Call `POST /session/new` with the finalized data.

---

## Tag Stacking Rule

When focus and background grant the same tag, the tag advances to Tier 2 instead of being wasted.

Example: Stalker (Lockpicking & Traps A1) + Criminal (Lockpicking & Traps A1) = Lockpicking & Traps A2.

---

## Species Reference (verify against GET /options)

| Species | Primary | Pow | Agi | Per | End | Int | Wil | Pre |
|---|---|---|---|---|---|---|---|---|
| Human | — | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| Orc | Power | 55 | 35 | 30 | 50 | 30 | 45 | 35 |
| Elf | Agility | 30 | 55 | 45 | 30 | 40 | 35 | 45 |
| Halfling | Perception | 30 | 45 | 55 | 35 | 35 | 45 | 35 |
| Dwarf | Endurance | 50 | 30 | 35 | 55 | 40 | 40 | 30 |
| Gnome | Intellect | 30 | 40 | 45 | 30 | 55 | 45 | 35 |
| Tiefling | Will | 35 | 40 | 35 | 35 | 45 | 55 | 35 |
| Dragonborn | Presence | 45 | 35 | 35 | 40 | 25 | 45 | 55 |

## Focus Reference (verify against GET /options)

| Focus | Signature Tag | Description |
|---|---|---|
| Champion | Athletics K2 | Front-line fighter, direct combat |
| Sentinel | Courage K2 | Protector, holds the line |
| Stalker | Stealth K2 | Ambush, infiltration, precision |
| Wayfinder | Survival K2 | Explorer, survivalist, tracker |
| Arcanist | Arcana K2 | Arcane scholar, magical power |
| Devoted | Discipline K2 | Spiritual warrior, faith and authority |
| Speaker | Persuasion K2 | Social operator, inspirer, manipulator |

## Background Reference (verify against GET /options)

| Background | Description |
|---|---|
| Soldier | Military service, structured discipline |
| Scholar | Academic upbringing, libraries and labs |
| Criminal | Street life, underground economy |
| Noble | Privilege, courts, political education |
| Outlander | Wilderness upbringing, self-reliance |
| Artisan | Trade skills, craftsmanship, practical knowledge |
| Acolyte | Temple-raised, spiritual foundation |
| Performer | Entertainer, traveler, social chameleon |

---

## API Fields for Character Creation

| API Field | When Collected |
|---|---|
| `character_name` | Stage 1 |
| `species` | Stage 1 |
| `focus` | Stage 2 |
| `background` | Stage 3 |
| `adjustment_points` | Stage 4 |
| `starting_location` | Set by GPT based on world context |
| `goal` | Ask player or set narratively |
| `threat` | Set by GPT based on world context |
