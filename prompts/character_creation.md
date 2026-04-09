# Mystic Weave — Character Creation Reference

This document is the authoritative, step-by-step reference for character creation. The GPT follows this flow exactly when starting a new session.

**IMPORTANT:** Always call `GET /options` first. Never enumerate classes, species, backgrounds, or languages from this document or from memory. Use only what the backend returns.

---

## Character Creation: Field Checklist

Fields collected during character creation and sent to the backend via `POST /session/new` or `POST /character/create`:

| API Field            | When Collected / Notes                                                                       |
| -------------------- | -------------------------------------------------------------------------------------------- |
| `name`               | Stage 1                                                                                      |
| `class`              | Stage 1                                                                                      |
| `subclass`           | Stage 1 (optional at level 1)                                                                |
| `skill_choices`      | Stage 1 (class skill choices) + Stage 2 (conflict replacements)                              |
| `prepared_spells`    | Stage 1 — spellcasters only; stored in character JSONB, not schema-validated                 |
| `fighting_style`     | Stage 1 — Fighter, Paladin, Ranger only; stored in character JSONB, not schema-validated     |
| `background`         | Stage 2                                                                                      |
| `tool_proficiencies` | Stage 2 (some backgrounds allow a choice); stored in character JSONB                        |
| `primary_score`      | Stage 2 — which of the 3 background scores gets +2. If null, all three get +1.              |
| `language_choices`   | Stage 2/3 — player-chosen languages only; automatic languages added by backend               |
| `species`            | Stage 3                                                                                      |
| `subspecies`         | Stage 3 (required for Dragonborn, Elf, Gnome, Goliath, Tiefling)                            |
| `species_choices`    | Stage 3 (e.g. size for Tiefling, Aasimar, Human)                                            |
| `ability_scores`     | Stage 4                                                                                      |
| `ability_score_method` | Stage 4                                                                                    |
| `equipment_choice`   | Stage 5 (`"equipment"` or `"gold"`)                                                          |
| `alignment`          | Stage 6 (optional)                                                                           |
| `faith`              | Stage 6 (optional)                                                                           |
| `biography`          | Stage 6.5 — stored in character JSONB, not schema-validated                                  |
| `feat_choices`       | Stage 6 if feat requires subchoices — stored in character JSONB, not schema-validated        |
| `starting_location`  | Stage 7                                                                                      |
| `goal`               | Stage 7                                                                                      |
| `threat`             | Stage 7                                                                                      |

Fields marked "stored in character JSONB" are saved as part of the character state object but are not validated by the backend schema. Pass them in the character state, not as top-level request fields.

---

## Creation Flow (7 Stages)

### Stage 1 — Class

1. Present all classes from the `GET /options` response.
2. Player chooses a class. Record as `class`.
3. Resolve all class internals immediately:
   - **Subclass:** present available subclasses from `GET /options`. Optional at level 1 (typically chosen at level 3). Record as `subclass` if chosen.
   - **Fighting style:** if the class is Fighter, Paladin, or Ranger, present available fighting styles and record as `fighting_style`.
   - **Skills:** present the class's available skill choices; player selects the allowed number. Record as `skill_choices`.
   - **Spells:** if the class is a spellcaster, present cantrip and spell options (see class list below). Record chosen spells as `prepared_spells`.

### Stage 2 — Background

1. Present all backgrounds from the `GET /options` response.
2. Player chooses a background. Record as `background`.
3. Resolve all background internals immediately:
   - **Granted automatically:** feat, skill proficiencies, tool proficiencies — inform the player, no choice needed.
   - **Tool choice:** if the background allows a choice, present options and record as `tool_proficiencies`.
   - **Ability score distribution:** the background grants bonuses to three specific scores. Ask the player to choose:
     - **+2/+1/+1:** +2 to one score (record as `primary_score`), +1 to the other two (implied by backend)
     - **+1/+1/+1:** +1 to all three equally (leave `primary_score` null)
   - **Skill conflicts:** if any class skill in `skill_choices` is already granted by the background, inform the player and ask for replacements. Update `skill_choices`.
   - **Language choice:** inform the player of their automatic languages (from species — see Stage 3). Present available languages from `GET /options` and ask for additional choices per the species' `language_choice_count`. Do not offer already-granted languages. Record as `language_choices`.

   > Language choices are presented here for narrative flow but are validated by the backend against species rules.

### Stage 3 — Species

1. Present all species from the `GET /options` response.
2. Player chooses a species. Record as `species`.
3. If the species has subspecies, present them and require a choice. Required for: Dragonborn, Elf, Gnome, Goliath, Tiefling. Record as `subspecies`.
4. If the species has additional choices (e.g. size for Tiefling, Aasimar, Human), present options and record as `species_choices`.
5. Inform the player of species traits and automatic languages.
6. If Stage 2 is already complete, confirm language choices now that automatic languages are known.

### Stage 4 — Ability Scores

1. Ask the player which method to use:
   - **Standard Array** — assign 15, 14, 13, 12, 10, 8 in any order (recommended)
   - **Point Buy** — spend 27 points; scores start at 8; see cost table below; max 15 before bonuses
   - **Manual** — assign any values 1–30 (no validation beyond range)
2. Player assigns scores to STR, DEX, CON, INT, WIS, CHA. Record as `ability_scores` and `ability_score_method`.
3. Background bonuses are applied automatically by the backend.
4. Show the player final scores after bonuses for confirmation.

### Stage 5 — Equipment

1. Player chooses a starting equipment package or starting gold. Record as `equipment_choice`.
2. If equipment is chosen, present class/background equipment options and record item indices as `equipment` in the character state.
3. If gold is chosen, record only the choice; the player purchases equipment in-game.

### Stage 6 — Final Character Sheet

Present the complete character before calling `POST /session/new`:

- Name, species, subspecies (if any), class, subclass (if chosen), background
- Ability scores (with bonuses applied)
- HP, hit die
- Proficiencies, skills, tool proficiencies
- Languages
- Starting feat
- Equipment (itemized) and gold
- Alignment, faith (if provided)

> **Feat subchoices:** if the starting feat requires selections (e.g. Skilled requires 3 skill choices, Magic Initiate requires a spell list), ask now. Store in `feat_choices` as `{ "feat-index": [...choices] }` and include in the character state.

> **Skill conflicts:** if the creation response includes `skill_conflicts`, inform the player and ask for replacement skills from the class's available options. Update `skill_choices` before proceeding.

Ask the player to confirm or make changes before proceeding to Stage 6.5.

#### Stage 6.5 — Character Biography

After the mechanical sheet is confirmed, ask three focused questions — one at a time, short answers accepted:

1. **Origin:** Where is your character from, and what is their family or background? (One or two sentences.)
2. **Reason:** What brought them to their current situation? What do they want?
3. **Tension:** What is one unresolved thing from their past — a debt, a loss, a question, a relationship — that still pulls at them?

Store answers in the character state as:

```json
{
  "biography": {
    "origin": "...",
    "reason": "...",
    "tension": "..."
  }
}
```

### Stage 7 — Campaign Setup

Only after the character is confirmed:

1. **Party:** Solo or with party members? If party, how many and what roles?
2. **Tone:** What kind of campaign? (heroic, grim survival, political intrigue, exploration, horror, etc.)
3. **Starting location:** Where does the character begin? Record as `starting_location`.
4. **Goal:** What is the character's initial objective? Record as `goal`.
5. **Threat:** What danger or opposition do they face? Record as `threat`.

Then call `POST /session/new` with all collected data.

---

## Ability Score Methods

### Standard Array (recommended)

Assign **15, 14, 13, 12, 10, 8** to the six scores in any order.

Pass `ability_score_method: "standard-array"`.

### Point Buy

Spend exactly **27 points**. Each score starts at 8. Maximum before bonuses: 15.

| Score | Cost |
| ----- | ---- |
| 8     | 0    |
| 9     | 1    |
| 10    | 2    |
| 11    | 3    |
| 12    | 4    |
| 13    | 5    |
| 14    | 7    |
| 15    | 9    |

Pass `ability_score_method: "point-buy"`. The backend validates the total and the 8–15 range.

### Manual

Assign any values 1–30. No point-budget validation.

Pass `ability_score_method: "manual"`.

---

Background bonuses are applied by the backend after the player assigns base scores.

---

## Skills

| Skill            | Ability |
| ---------------- | ------- |
| Acrobatics       | DEX     |
| Animal Handling  | WIS     |
| Arcana           | INT     |
| Athletics        | STR     |
| Deception        | CHA     |
| History          | INT     |
| Insight          | WIS     |
| Intimidation     | CHA     |
| Investigation    | INT     |
| Medicine         | WIS     |
| Nature           | INT     |
| Perception       | WIS     |
| Performance      | CHA     |
| Persuasion       | CHA     |
| Religion         | INT     |
| Sleight of Hand  | DEX     |
| Stealth          | DEX     |
| Survival         | WIS     |

---

## Backgrounds (2024)

16 backgrounds supported. Use `GET /options` for the full list. Each grants ability score bonuses, a starting feat, skill proficiencies, and tool proficiencies.

| Background  | Ability Scores    | Starting Feat                          | Skills                        | Tool                          |
| ----------- | ----------------- | -------------------------------------- | ----------------------------- | ----------------------------- |
| Acolyte     | INT, WIS, CHA     | Magic Initiate (Cleric, Druid, Wizard) | Insight, Religion             | Calligrapher's Supplies       |
| Artisan     | STR, DEX, INT     | Crafter                                | Investigation, Persuasion     | One artisan's tool (choice)   |
| Charlatan   | DEX, CON, CHA     | Skilled                                | Deception, Sleight of Hand    | Forgery Kit                   |
| Criminal    | DEX, CON, INT     | Alert                                  | Sleight of Hand, Stealth      | Thieves' Tools                |
| Entertainer | STR, DEX, CHA     | Musician                               | Acrobatics, Performance       | One musical instrument (choice)|
| Farmer      | STR, CON, WIS     | Tough                                  | Animal Handling, Nature       | Carpenter's Tools             |
| Guard       | STR, INT, CHA     | Alert                                  | Athletics, Perception         | One gaming set (choice)       |
| Guide       | DEX, CON, WIS     | Magic Initiate (Druid)                 | Stealth, Survival             | Cartographer's Tools          |
| Hermit      | CON, INT, WIS     | Magic Initiate (Druid)                 | Medicine, Religion            | Herbalism Kit                 |
| Merchant    | CON, INT, CHA     | Lucky                                  | Animal Handling, Persuasion   | Navigator's Tools             |
| Noble       | STR, INT, CHA     | Skilled                                | History, Persuasion           | One gaming set (choice)       |
| Sage        | CON, INT, WIS     | Magic Initiate (Cleric, Druid, Wizard) | Arcana, History               | Calligrapher's Supplies       |
| Sailor      | STR, DEX, WIS     | Tavern Brawler                         | Acrobatics, Perception        | Navigator's Tools             |
| Scribe      | DEX, INT, WIS     | Skilled                                | Investigation, Perception     | Calligrapher's Supplies       |
| Soldier     | STR, DEX, CON     | Savage Attacker                        | Athletics, Intimidation       | One gaming set (choice)       |
| Wayfarer    | DEX, WIS, CHA     | Lucky                                  | Insight, Stealth              | Thieves' Tools                |

---

## Species (2024)

10 species supported. Species do not grant ability score bonuses (backgrounds handle that in 2024 rules). Use `GET /options` for the full list.

| Species    | Speed  | Size            | Automatic Languages    | Additional Choices | Subspecies Required |
| ---------- | ------ | --------------- | ---------------------- | ------------------ | ------------------- |
| Dragonborn | 30 ft  | Medium          | Common, Draconic       | 1                  | Yes (10 ancestors)  |
| Dwarf      | 30 ft  | Medium          | Common, Dwarvish       | 1                  | No                  |
| Elf        | 30 ft  | Medium          | Common, Elvish         | 1                  | Yes (3 lineages)    |
| Gnome      | 30 ft  | Small           | Common, Gnomish        | 1                  | Yes (2 lineages)    |
| Goliath    | 35 ft  | Medium          | Common, Giant          | 1                  | Yes (6 ancestries)  |
| Halfling   | 30 ft  | Small           | Common, Halfling       | 1                  | No                  |
| Human      | 30 ft  | Medium          | Common                 | 2                  | No                  |
| Orc        | 30 ft  | Medium          | Common, Orc            | 1                  | No                  |
| Tiefling   | 30 ft  | Medium or Small | Common, Infernal       | 1                  | Yes (3 legacies)    |
| Aasimar    | 30 ft  | Medium or Small | Common, Celestial      | 1                  | No                  |

### Subspecies Detail

**Dragonborn** (choose ancestor): Black (Acid), Blue (Lightning), Brass (Fire), Bronze (Lightning), Copper (Acid), Gold (Fire), Green (Poison), Red (Fire), Silver (Cold), White (Cold)

**Elf** (choose lineage):

- Drow — Darkvision 120 ft, Dancing Lights, Faerie Fire (3), Darkness (5)
- High Elf — Detect Magic, Misty Step (3), Arcane Intellect
- Wood Elf — Druidcraft, Longstrider (3), Pass Without Trace (5), speed 35 ft

**Gnome** (choose lineage):

- Forest Gnome — Minor Illusion, Speak with Animals
- Rock Gnome — Mending, Prestidigitation, Tinker

**Goliath** (choose ancestry): Cloud's Jaunt, Fire's Burn, Frost's Chill, Hill's Tumble, Stone's Endurance, Storm's Thunder

**Tiefling** (choose legacy):

- Abyssal — Poison Spray, Ray of Sickness (3), Hold Person (5)
- Chthonic — Chill Touch, False Life (3), Ray of Enfeeblement (5)
- Infernal — Fire Bolt, Hellish Rebuke (3), Darkness (5)

---

## Classes

| Class     | Hit Die | HP at L1     | Saves     | Skill Choices                                                                                     | # Skills | Spells                                             | Subclass (2024)            |
| --------- | ------- | ------------ | --------- | ------------------------------------------------------------------------------------------------- | -------- | -------------------------------------------------- | -------------------------- |
| Barbarian | d12     | 12 + CON     | STR, CON  | Animal Handling, Athletics, Intimidation, Nature, Perception, Survival                           | 2        | None                                               | Path of the Berserker      |
| Bard      | d8      | 8 + CON      | DEX, CHA  | Any                                                                                               | 3        | 2 cantrips + 4 known                               | College of Lore            |
| Cleric    | d8      | 8 + CON      | WIS, CHA  | History, Insight, Medicine, Persuasion, Religion                                                  | 2        | 3 cantrips; prepare WIS mod + level/day            | Life Domain                |
| Druid     | d8      | 8 + CON      | INT, WIS  | Arcana, Animal Handling, Insight, Medicine, Nature, Perception, Religion, Survival                | 2        | 2 cantrips; prepare WIS mod + level/day            | Circle of the Land         |
| Fighter   | d10     | 10 + CON     | STR, CON  | Acrobatics, Animal Handling, Athletics, History, Insight, Intimidation, Perception, Survival      | 2        | None (unless Eldritch Knight)                      | Champion                   |
| Monk      | d8      | 8 + CON      | STR, DEX  | Acrobatics, Athletics, History, Insight, Religion, Stealth                                        | 2        | None                                               | Warrior of the Open Hand   |
| Paladin   | d10     | 10 + CON     | WIS, CHA  | Athletics, Insight, Intimidation, Medicine, Persuasion, Religion                                  | 2        | 2 known; prepare CHA mod + half level/day          | Oath of Devotion           |
| Ranger    | d10     | 10 + CON     | STR, DEX  | Animal Handling, Athletics, Insight, Investigation, Nature, Perception, Stealth, Survival         | 3        | 2 known                                            | Hunter                     |
| Rogue     | d8      | 8 + CON      | DEX, INT  | Acrobatics, Athletics, Deception, Insight, Intimidation, Investigation, Perception, Performance, Persuasion, Sleight of Hand, Stealth | 4 | None (unless Arcane Trickster) | Thief              |
| Sorcerer  | d6      | 6 + CON      | CON, CHA  | Arcana, Deception, Insight, Intimidation, Persuasion, Religion                                    | 2        | 4 cantrips + 2 known                               | Draconic Sorcery           |
| Warlock   | d8      | 8 + CON      | WIS, CHA  | Arcana, Deception, History, Intimidation, Investigation, Nature, Religion                         | 2        | 2 cantrips + 2 known (Eldritch Blast recommended)  | Fiend Patron               |
| Wizard    | d6      | 6 + CON      | INT, WIS  | Arcana, History, Insight, Investigation, Medicine, Religion                                       | 2        | 3 cantrips + 6 in spellbook; prepare INT mod + level/day | Evoker             |

Armor/weapon proficiencies are returned by `GET /options` and stored in the character sheet by the backend.

---

## Notes

- **Subspecies** are required for Dragonborn, Elf, Gnome, Goliath, and Tiefling.
- **2024 rules:** Species no longer grant ability score bonuses. Backgrounds do instead.
- **Subclasses** are typically chosen at level 3. They may be selected at creation if the player wants.
- **Background ability bonuses** are applied automatically by the backend. The player assigns base scores; the backend adds the chosen distribution.
- **Language choices** are validated by the backend. Invalid or duplicate choices return a 422 error.
- **Spells:** use `GET /spells` to look up available spells by class and level when helping the player choose.
- **JSONB fields** (`biography`, `feat_choices`, `prepared_spells`, `fighting_style`, `equipment`, `tool_proficiencies`) are stored as part of the character state object. They are not top-level schema-validated fields — include them nested in the character data sent to the backend.
