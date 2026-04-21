# Mystic Weave — Character Creation Reference

This document is the authoritative, step-by-step reference for character creation. The GPT follows this flow exactly when starting a new session.

**IMPORTANT:** Always call `GET /options` first. Never enumerate ancestries, cultures, focus archetypes, or backgrounds from this document or from memory. Use only what the backend returns.

---

## Character Creation Flow

### Stage 1 — Name and Ancestry

1. Ask the player for a character name.
2. Call `GET /options` to retrieve all valid ancestries.
3. Present the ancestry list with their primary domain, domain score spread, and ancestry traits.
4. Player chooses an ancestry.
5. If ancestry is dragonborn, establish breath lineage type at creation (`radiant`, `fire`, `cold`, `lightning`, `acid`, `necrotic`) or explicitly defer to narrative discovery.

### Stage 2 — Culture

1. Present the culture list from `GET /options` with descriptions, domain bonuses, and tag themes.
2. Player chooses a culture. Any ancestry can choose any culture.

### Stage 3 — Background

1. Present the background list from `GET /options` with descriptions and starting tags.
2. Player chooses a background. Any combination is valid.

### Stage 4 — Focus Archetype

1. Present the focus archetype list from `GET /options` with descriptions and starting tags.
2. Player chooses a focus. Any ancestry can choose any focus.
3. Magical fields are valid field-tag choices and use the same tier math/progression rules as knowledge groups. Canonical fields: `Sacred`, `Warding`, `Binding`, `Elemental`, `Druidry`, `Illusion`, `Runecraft`, `Alchemy`, `Necromancy`. Field knowledge tiers are gated by the field's primary domain score — see `prompts/magic-rules.md`.
4. If ancestry is dragonborn, confirm breath lineage type is established during creation (`radiant`, `fire`, `cold`, `lightning`, `acid`, `necrotic`) or explicitly marked as deferred to narrative discovery.

### Stage 5 — Adjustment Points

1. The player has 10 points to distribute across domains, max +5 per domain.
2. Show the starting domain scores from ancestry base + culture bonus + background bonus, then ask where to allocate the player adjustment points.
3. If the player skips this step, all adjustment points default to 0.
4. Clarify progression expectation: starting domains come from ancestry base (280 total), culture bonus (10), background bonus (10), and player adjustment points (10), then can be increased later through AP spend up to a hard cap of 80.

### Stage 6 — Identity and Narrative

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

### Stage 7 — Companions and Party

1. Ask: "Are you traveling alone, or does anyone travel with you?"
2. If the player has companions:
   - Gather for each: name, species (optional), role in the party (optional).
   - Ask the same narrative questions from Stage 5 — briefly, not exhaustively. A companion needs at minimum: one motivation and one quirk to feel present.
   - Ask disposition toward the player character: how does this companion feel about them? (Map to a rough disposition: devoted, loyal, friendly, cautious, wary, or hostile.)
   - Store each companion in `world.companions` with `status: active`, and submit them with the `POST /session/new` call.
3. If alone, `world.companions` stays empty.

**Companion rule — party reputation:** When the party approaches a faction, compute party reputation as:
- `known_avg` = mean standing of party members who have a reputation entry for that faction (missing entry = unknown, excluded from average).
- `ratio` = number of known members / total party size.
- `party_rep` = `known_avg × ratio`.
- Apply this result when selecting difficulty modifiers for social or political actions with that faction.

### Stage 8 — Starting Resources

1. Ask: "How are they set up materially — do they have coin, useful gear, or are they scraping by?"
2. Map the answer to `wealth_tier` (destitute / modest / comfortable / wealthy / affluent). Default: modest.
3. Set starting `coin` using `prompts/economy_rules.md` tier guidance and supporting JSON data.
4. If they mention specific items, add them to `equipment.worn` or `equipment.carried` as appropriate, and submit them with the `POST /session/new` call.
5. If they mention debts or obligations, add them to `economy.obligations`.
6. Do not prompt exhaustively for every item. Let the player volunteer what matters.

### Stage 9 — Confirm and Create

1. Show the player a full summary:
   - Name, ancestry, culture, background, focus
   - Final domain scores
   - All knowledge, application, and field tags with tiers
   - Identity highlights (origin, alignment, any stated motivations/quirks)
   - Companions (if any) and their roles
   - Wealth tier and any notable gear
2. Confirm the build.
3. Call `POST /session/new` with the finalized data, including `identity`, `starting_economy`, any collected `companions`, and any collected starting `equipment`.
4. Retain the returned `session_id` exactly as returned and reuse it for all later `GET /state/{session_id}`, `GET /scene/{session_id}`, `POST /state/{session_id}`, and `POST /state/{session_id}/delta` calls.

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

When multiple layers grant the same tag, the tag advances by +1 tier per additional source, up to Tier 5.

Characters gain:
- **knowledge groups** for broad competency
- **applications** for specific trained expression
- **field tags** for magical field access

For a normal non-spell roll, use **one knowledge group tier + one application tier**. Do not stack multiple groups or multiple applications into the same roll.

Example: Devoted + Acolyte + Draconic Grasslands all support sacred practice, so Sacred field stacks upward instead of being wasted.

### Weapon Application Taxonomy (Canonical)

When discussing or assigning weapon-related application tags, use canonical names only:
`grappling`, `melee`, `reach`, `ranged`, `mechanical`, `unconventional`.

Do not introduce legacy/alternate weapon tag names during character creation.

---

## Ancestry Reference (verify against GET /options)

| Ancestry | Primary | Pow | Agi | Per | End | Int | Wil | Pre |
|---|---|---|---|---|---|---|---|---|
| Human | — | 40 | 40 | 40 | 40 | 40 | 40 | 40 |
| Orc | Power | 55 | 35 | 30 | 50 | 30 | 45 | 35 |
| Elf | Agility | 30 | 55 | 45 | 30 | 40 | 35 | 45 |
| Halfling | Perception | 30 | 45 | 55 | 35 | 35 | 45 | 35 |
| Dwarf | Endurance | 50 | 30 | 35 | 55 | 40 | 40 | 30 |
| Gnome | Intellect | 30 | 40 | 45 | 30 | 55 | 45 | 35 |
| Tiefling | Will | 35 | 40 | 35 | 35 | 45 | 55 | 35 |
| Dragonborn | Presence | 45 | 35 | 35 | 40 | 30 | 45 | 50 |

## Culture Reference (verify against GET /options)

| Culture | Domain Bonuses | Signature Tag Types |
|---|---|---|
| Alpine Peaks | Per +3, End +4, Wil +3 | survival, tracking, privation_endurance |
| Inner Ramparts | Pow +2, Agi +3, Per +2, End +3 | mobility, awareness, acrobatics, scan |
| Draconic Grasslands | Int +3, Wil +3, Pre +4 | influence, lore, diplomacy, command, sacred |
| Drakenvale | Int +4, Wil +3, Pre +3 | lore, influence, persuasion, history, linguistics |
| Volcanic Highlands | Pow +4, End +4, Wil +2 | combat, survival, hauling, intimidation_posture, elemental |
| Temperate Forest | Agi +3, Per +4, End +3 | tracking, stealth, ecology |
| Mystic Wetlands | Per +4, Int +3, Wil +3 | investigation, medicine, ecology, pharmacology |
| Feywood Glade | Int +3, Wil +3, Pre +4 | arcana, deception, tell_reading, illusion |
| Crystal Caverns | Per +3, Int +4, Wil +3 | arcana, investigation, meditation, runecraft |
| Platinum Oath Monastery | End +3, Wil +5, Pre +2 | discipline, meditation, courage, Warding field |

## Focus Reference (verify against GET /options)

| Focus | Signature Tag | Description |
|---|---|---|
| Champion | Athletics K2 | Front-line fighter, direct combat |
| Sentinel | Discipline K2 | Protector, holds the line |
| Stalker | Stealth K2 | Ambush, infiltration, precision |
| Wayfinder | Survival K2 | Explorer, survivalist, tracker |
| Arcanist | Arcana K2 | Arcane scholar, magical power |
| Devoted | Discipline K2 | Spiritual warrior, faith and authority |
| Speaker | Influence K2 | Social operator, inspirer, manipulator |

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
| `ancestry` | 1 | Index from GET /options only |
| `culture` | 2 | Index from GET /options only |
| `background` | 3 | Index from GET /options only |
| `focus` | 4 | Index from GET /options only |
| `adjustment_points` | 5 | Defaults to 0 if skipped |
| `identity.origin` | 6 | Optional |
| `identity.motivations` | 6 | Optional, max 3 |
| `identity.quirks` | 6 | Optional, max 3 |
| `identity.bonds` | 6 | Optional, max 3 |
| `identity.flaws` | 6 | Optional, max 3 |
| `identity.wound` | 6 | Optional |
| `identity.alignment` | 6 | order + intent + ethos_note |
| `world.companions` | 7 | Empty if traveling alone |
| `starting_economy.wealth_tier` | 8 | Default: modest |
| `starting_economy.coin` | 8 | Default: 0 |
| `equipment.worn` / `equipment.carried` | 8 | From player description |
| `companions` | 9 | Optional on `POST /session/new` |
| `equipment` | 9 | Optional on `POST /session/new` |
| `economy.obligations` | 8 | Debts, favors, sworn duties |
| `starting_location` | 9 | Set by GPT from world context |
| `goal` | 9 | Ask player or set narratively |
| `threat` | 9 | Set by GPT from world context |