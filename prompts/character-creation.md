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
5. If ancestry is drakari, establish their inherited magical field at creation. The drakari player picks one of the nine canonical fields (`Sacred`, `Warding`, `Binding`, `Elemental`, `Druidry`, `Illusion`, `Runecraft`, `Alchemy`, `Necromancy`) and gains it at knowledge tier 1, plus two tier-1 spells of their choice from that field. This is the drakari magical inheritance — a free starting endowment from their draconic descent — and is in addition to any field expertise gained from focus archetype, background, or culture.

### Stage 2 — Culture

1. Present the culture list from `GET /options` with descriptions, domain bonuses, and tag themes.
2. Player chooses a culture. Any ancestry can choose any culture.

### Stage 3 — Background

1. Present the background list from `GET /options` with descriptions and starting tags.
2. Player chooses a background. Any combination is valid.

### Stage 4 — Focus Archetype

1. Present the focus archetype list from `GET /options` with descriptions and starting tags.
2. Player chooses a focus. Any ancestry can choose any focus.
3. Magical fields use the same tier math/progression rules as knowledge groups. Canonical fields: `Sacred`, `Warding`, `Binding`, `Elemental`, `Druidry`, `Illusion`, `Runecraft`, `Alchemy`, `Necromancy`. Each field is recorded on the character with its tier and a `spells` map; per-character spell mastery is capped by the field's tier (parent-cap rule, structural). Field knowledge tiers are gated by the field's primary domain score — see `prompts/magic-rules.md`.
4. If ancestry is drakari, confirm the inherited magical field and the two T1 spells were established at Stage 1 step 5. Drakari magical inheritance is fixed at creation; it is not deferred to play.

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
2. If the player has companions, gather them one at a time.

For the current character creation flow, companions introduced at
creation may be **Sapient Companions** (people traveling with the
player character) or **Creature Companions** (non-sapient animals
bonded to the player or party). **Exceptional Companions**
(sub-sapient or magically significant entities) are not introduced
at creation; they are acquired through play.

For each Sapient Companion:

- **Name.**
- **Ancestry, culture, background, focus.** Use the same
  `GET /options` vocabularies as the player character. Any
  ancestry/culture/background/focus combination is valid.
- **Brief identity.** At minimum: one motivation and one quirk.
  Additional identity fields (bonds, flaws, wound, alignment) are
  optional — surface them through play if the player doesn't offer
  them at creation.
- **Bond to the player character.** Set `bond_links.primary` to the
  player character's ID. Add a `secondary` bond only if the player
  explicitly describes one.
- **Starting HP.** Default 100/100 unless the player specifies a
  wounded or weakened companion at creation.
- **Starting domain scores.** Use ancestry base + culture bonus +
  background bonus, the same math as the player character. Skip
  adjustment points for companions; creation-time companions do
  not get player-allocated adjustment points.
- **Equipment and reputation.** Skip at creation unless the player
  volunteers details. These develop through play.

For each Creature Companion:

- **Name.**
- **Species and subspecies.** What kind of animal it is (e.g.,
  moonthorn wolf, courser, falcon). Source from
  `data/companions/creatures.json` via `GET /catalog/creatures`. The
  GPT does not invent creature stat blocks; it uses catalog entries.
- **Size and age category.** Standard descriptors from the catalog
  entry.
- **Tactical roles.** One or more from the canonical role vocabulary
  (see `companion-rules.md`).
- **Training level.** Untrained / partially trained / well trained
  / specialist.
- **Bond level.** Default `bonded` for at-creation creatures unless
  the player specifies otherwise.
- **Bond to the player character.** Set `bond_links.primary` to the
  player character's ID.
- **Brief narrative block.** Optional. Origin (how this specific
  creature came to be with the handler) and drives (instinctive
  priorities). Skip unless the player volunteers.
- **Domain block.** Simplified domains (physical, instinct,
  composure) sourced from the catalog entry.

Store each companion as a `CompanionEnvelope` in
`world.companions` with the appropriate type discriminator. The
envelope's `id` is generated server-side from the player's
character_id plus a slug derived from the companion's name (for
sapients) or species + identifier (for creatures).

If the player is traveling alone, `world.companions` stays empty.

**Party reputation rule (sapient companions only):** When the
party approaches a faction, compute party reputation as:

- `known_avg` = mean standing of sapient party members who have a
  reputation entry for that faction (missing entry = unknown,
  excluded from average)
- `ratio` = number of known sapient members / total sapient party size
- `party_rep` = `known_avg × ratio`

Creature and Exceptional companions do not contribute to party
reputation. Apply `party_rep` when selecting difficulty modifiers
for social or political actions with that faction.

### Stage 8 — Starting Resources

1. Ask: "How are they set up materially — do they have coin, useful gear, or are they scraping by?"
2. Map the answer to `wealth_tier` (destitute / modest / comfortable / wealthy / affluent). Default: modest.
3. Set starting `coin` using `prompts/economy-rules.md` tier guidance and supporting JSON data.
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

- **Tags** advance through use. Applications grow when used under genuine challenge against meaningfully new conditions. Knowledge grows from understanding events — examining, observing, learning, reflecting. Field knowledge grows the same way for magic. Tags do not cost AP.
- **AP** is a single fungible pool spendable on any domain. It earns two ways:
  - **Tag-counter rollover:** every 3 tag advances adds 1 AP automatically.
  - **Awarded AP:** rare, pre-declared rewards from significant contracts (Council-level patrons, oath-bound commitments, world-imposed stakes). Scale is 1 / 2 / 3 / 4 AP by depth of commitment.
- **Domain spend** uses bracket costs:
  - 25–60: 1 AP per point
  - 61–70: 2 AP per point
  - 71–80: 3 AP per point
- Domain score cap is **80**.

---

## Tag Stacking Rule

When multiple layers grant the same tag, the tag advances by +1 tier per additional source, up to Tier 5.

Characters gain:
- **knowledge groups** for broad competency. Each group's record holds its tier and a nested `applications` map.
- **applications** for specific trained expression. Each application's tier is capped by its parent group's tier.
- **magic fields** for magical field access. Each field's record holds its tier and a nested `spells` map. Per-character spell mastery is capped by the parent field's tier.

For a normal non-spell roll, use **one knowledge group tier + one application tier**. Do not stack multiple groups or multiple applications into the same roll.

Example: Devoted + Acolyte + Draconic Grasslands all support sacred practice, so Sacred field stacks upward instead of being wasted.

### Weapon and Armor Application Taxonomy (Canonical)

Weapon and armor combat use the following canonical knowledge groups:

- `close_combat`
- `melee`
- `reach`
- `ranged`
- `mechanical`
- `unconventional`
- `martial_arts` — applications include `unarmored`
- `light_armor` — applications: `padded`, `leather`, `studded_leather`, `hide`
- `medium_armor` — applications: `chain_shirt`, `scale_mail`, `breastplate`
- `heavy_armor` — applications: `chain_mail`, `splint`, `plate`
- `shields` — applications: `shield` (additional shield types may be added later)

Do not introduce legacy or alternate weapon and armor tag names during character creation.

---

## Fallback Policy

If `GET /options` fails with an error, an oversized response, or a timeout:

- **Do not** enumerate ancestries, cultures, focus archetypes, or backgrounds from memory.
- **Do not** substitute option indices that the user provided if they appear unfamiliar — the user may be correct and the schema may have been extended.
- **Report the failure to the player directly.** Example: "I can't reach the character options endpoint right now. Please try again in a moment, or check the backend service."
- **Do not** proceed with creation using guessed values.

The backend is the sole source of truth for valid ancestry, culture, focus, and background indices.

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
| `companions` | 7 | Sapient only at creation; list of CompanionEnvelope; optional on `POST /session/new` |
| `equipment` | 9 | Optional on `POST /session/new` |
| `economy.obligations` | 8 | Debts, favors, sworn duties |
| `starting_location` | 9 | Set by GPT from world context |
| `goal` | 9 | Ask player or set narratively |
| `threat` | 9 | Set by GPT from world context |
