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
5. If species is dragonborn, establish breath lineage type at creation (`radiant`, `fire`, `cold`, `lightning`, `acid`, `necrotic`) or explicitly defer to narrative discovery.

### Stage 2 — Focus Archetype

1. Present the focus archetype list from `GET /options` with descriptions and starting tags.
2. Player chooses a focus. Any species can choose any focus.
3. Magical fields are valid knowledge tag choices (same tier math/progression rules as other knowledge tags). Canonical fields: `Sacred`, `Warding`, `Binding`, `Elemental`, `Nature`, `Arcane Theory`, `Illusion`, `Runecraft`, `Necromancy`, `Alchemy`, `Invocation`.
4. If species is dragonborn, confirm breath lineage type is established during creation (`radiant`, `fire`, `cold`, `lightning`, `acid`, `necrotic`) or explicitly marked as deferred to narrative discovery.

### Stage 3 — Background

1. Present the background list from `GET /options` with descriptions and starting tags.
2. Player chooses a background. Any combination is valid.

### Stage 4 — Adjustment Points

1. The player has 5 points to distribute across domains, max +3 per domain.
2. Show the base domain scores from their species and ask where to allocate.
3. If the player skips this step, all adjustment points default to 0.
4. Clarify progression expectation: starting domains come from species + adjustment points, then can be increased later through AP spend up to a hard cap of 80.

### Stage 5 — Identity and Narrative

This stage gives the character a life before the story starts. All fields are optional — the player can skip any or all of them. Skipped fields default to empty and can be filled in through play.

Gather the following in natural conversation, not as a form. Let the player's answers shape the questions. One good prompt per beat:

**Origin**
> "Where does your character come from, and what shaped who they are?"
> Store as `identity.origin`.

**Motivations** (up to 3)
> "What drives them? What are they after — or running from?"
> Store as `identity.motivations` list.

**Quirks** (up to 3)
> "How do they come across to others? Any habits, mannerisms, or tell-tale behaviours?"
> Store as `identity.quirks` list.

**Bonds** (up to 3)
> "Who or what are they tied to — a person, a place, an oath?"
> Store as `identity.bonds` list.

**Flaws** (up to 3)
> "What's their blind spot, weakness, or the thing that gets them into trouble?"
> Store as `identity.flaws` list.

**Wound**
> "Is there a defining scar — something that happened that they carry with them?"
> Store as `identity.wound`.

**Alignment**
> "How do they navigate the world — do they follow rules, make their own, or move somewhere between? And at heart, are they trying to do good, look out for themselves, or something else?"
> Map the answer to `alignment.order` (lawful / neutral / chaotic) and `alignment.intent` (good / neutral / evil).
> If they add a nuanced explanation that doesn't fit neatly, capture it in `alignment.ethos_note`.

**Narrator rule:** Reference at least one identity field in every major decision scene. If the character has a stated motivation, flaw, or bond that is directly relevant to the situation at hand, surface it in the narration or the choices you present.

### Stage 6 — Companions and Party

1. Ask: "Are you traveling alone, or does anyone travel with you?"
2. If the player has companions:
   - Gather for each: name, species (optional), role in the party (optional).
   - Ask the same narrative questions from Stage 5 — briefly, not exhaustively. A companion needs at minimum: one motivation and one quirk to feel present.
   - Ask disposition toward the player character: how does this companion feel about them? (Map to a rough disposition: devoted, loyal, friendly, cautious, wary, or hostile.)
   - Store each companion in `world.companions` with `status: active`.
3. If alone, `world.companions` stays empty.

**Companion rule — party reputation:** When the party approaches a faction, compute party reputation as:
- `known_avg` = mean standing of party members who have a reputation entry for that faction (missing entry = unknown, excluded from average).
- `ratio` = number of known members / total party size.
- `party_rep` = `known_avg × ratio`.
- Apply this result when selecting difficulty modifiers for social or political actions with that faction.

### Stage 7 — Starting Resources

1. Ask: "How are they set up materially — do they have coin, useful gear, or are they scraping by?"
2. Map the answer to `wealth_tier` (destitute / modest / comfortable / wealthy / affluent). Default: modest.
3. Set starting `coin` using `prompts/economy_rules.md` tier guidance and supporting JSON data.
4. If they mention specific items, add them to `equipment.worn` or `equipment.carried` as appropriate.
5. If they mention debts or obligations, add them to `economy.obligations`.
6. Do not prompt exhaustively for every item. Let the player volunteer what matters.

### Stage 8 — Confirm and Create

1. Show the player a full summary:
   - Name, species, focus, background
   - Final domain scores
   - All knowledge and application tags with tiers
   - Identity highlights (origin, alignment, any stated motivations/quirks)
   - Companions (if any) and their roles
   - Wealth tier and any notable gear
2. Confirm the build.
3. Call `POST /session/new` with the finalized data, including `identity` and `starting_economy`.

### Progression Clarifier (Player-Facing)

If the player asks how progression works after creation, explain briefly:

- **Tags** are narrative/use-based and do not cost AP.
- **Domains** are AP-purchased and can rise to a maximum of **80**.
- Domain AP costs scale by resulting score bracket:
  - 25–60: 1 AP per point
  - 61–70: 2 AP per point
  - 71–80: 3 AP per point

---

## Tag Stacking Rule

When focus and background grant the same tag, the tag advances to Tier 2 instead of being wasted.

Example: Stalker (Lockpicking & Traps A1) + Criminal (Lockpicking & Traps A1) = Lockpicking & Traps A2.

### Weapon Application Taxonomy (Canonical)

When discussing or assigning weapon-related application tags, use canonical names only:
`grappling`, `melee`, `reach`, `ranged`, `mechanical`, `unconventional`.

Do not introduce legacy/alternate weapon tag names during character creation.

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

| API Field | Stage Collected | Notes |
|---|---|---|
| `character_name` | 1 | |
| `species` | 1 | Index from GET /options only |
| `focus` | 2 | Index from GET /options only |
| `background` | 3 | Index from GET /options only |
| `adjustment_points` | 4 | Defaults to 0 if skipped |
| `identity.origin` | 5 | Optional |
| `identity.motivations` | 5 | Optional, max 3 |
| `identity.quirks` | 5 | Optional, max 3 |
| `identity.bonds` | 5 | Optional, max 3 |
| `identity.flaws` | 5 | Optional, max 3 |
| `identity.wound` | 5 | Optional |
| `identity.alignment` | 5 | order + intent + ethos_note |
| `world.companions` | 6 | Empty if traveling alone |
| `starting_economy.wealth_tier` | 7 | Default: modest |
| `starting_economy.coin` | 7 | Default: 0 |
| `equipment.worn` / `equipment.carried` | 7 | From player description |
| `economy.obligations` | 7 | Debts, favors, sworn duties |
| `starting_location` | 8 | Set by GPT from world context |
| `goal` | 8 | Ask player or set narratively |
| `threat` | 8 | Set by GPT from world context |