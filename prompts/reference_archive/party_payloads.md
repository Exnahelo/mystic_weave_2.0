# Party Payloads — POST /session/new

Five characters. Ability scores shown are **pre-background** (what you pass to the API).
Background bonuses are applied automatically by the backend.

---

## Notes on ability score math

Background bonuses applied to final scores shown on the sheet:

| Character | Background | Scores boosted | primary_score | Pre-bg adjustment |
| --- | --- | --- | --- | --- |
| Exnahelo | Noble | STR, INT, CHA | CHA (+2) | STR -1, INT -1, CHA -2 |
| Ranger | Guide | DEX, CON, WIS | WIS (+2) | DEX -1, CON -1, WIS -2 |
| Cleric | Guard | STR, INT, CHA | STR (+2) | STR -2, INT -1, CHA -1 |
| Wizard | Scribe | DEX, INT, WIS | INT (+2) | DEX -1, INT -2, WIS -1 |
| Rogue | Criminal | DEX, CON, INT | DEX (+2) | DEX -2, CON -1, INT -1 |

---

## GPT-side only (not stored in API at creation)

These fields exist on `CharacterModel` and can be saved by the GPT in subsequent
`POST /state/{session_id}` calls, but are not accepted by `POST /session/new`:

- Fighting style
- Weapon masteries
- Expertise skills
- Spells / cantrips (stored as `known_spells`, `prepared_spells`, `cantrips` on saves)
- Feat skill choices (Skilled)
- Languages granted by class features (Thieves' Cant, Orc/Sylvan from Ranger)

---

## 1 — Exnahelo Vindago (Paladin)

Noble: STR +1, INT +1, CHA +2 → pre-bg: STR 15, INT 7, CHA 14

```json
{
  "character_name": "Exnahelo Vindago",
  "class": "paladin",
  "species": "dragonborn",
  "subspecies": "draconic-ancestor-gold",
  "subclass": "ancients",
  "background": "noble",
  "ability_scores": {
    "STR": 15,
    "DEX": 10,
    "CON": 14,
    "INT": 7,
    "WIS": 10,
    "CHA": 14
  },
  "ability_score_method": "manual",
  "primary_score": "CHA",
  "skill_choices": ["athletics", "intimidation"],
  "language_choices": ["common-sign-language"],
  "species_choices": {},
  "equipment_choice": "equipment",
  "starting_location": "test-drakenvale-entry",
  "goal": "Gain an audience with the Draconic Council",
  "threat": "Suspicion from the Dragon Guard"
}
```

**Expected final scores:** STR 16, DEX 10, CON 14, INT 8, WIS 10, CHA 16
**HP:** 12 (d10 + CON mod +2)
**Backend auto-grants:** History, Persuasion (skills); skilled (feat); Dragonchess tool prof
**Languages auto-granted:** common, draconic + common-sign-language

---

## 2 — Ranger (Wood Elf)

Guide: DEX +1, CON +1, WIS +2 → pre-bg: DEX 15, CON 13, WIS 14

```json
{
  "character_name": "Ranger",
  "class": "ranger",
  "species": "elf",
  "subspecies": "elven-lineage-wood-elf",
  "subclass": "gloom-stalker",
  "background": "guide",
  "ability_scores": {
    "STR": 10,
    "DEX": 15,
    "CON": 13,
    "INT": 8,
    "WIS": 14,
    "CHA": 10
  },
  "ability_score_method": "manual",
  "primary_score": "WIS",
  "skill_choices": ["stealth", "perception", "athletics"],
  "language_choices": ["goblin"],
  "species_choices": {
    "keen_senses": "insight"
  },
  "equipment_choice": "equipment",
  "starting_location": "test-drakenvale-entry",
  "goal": "Gain an audience with the Draconic Council",
  "threat": "Suspicion from the Dragon Guard"
}
```

**Expected final scores:** STR 10, DEX 16, CON 14, INT 8, WIS 16, CHA 10
**HP:** 12 (d10 + CON mod +2)
**Backend auto-grants:** Stealth, Survival (skills); magic-initiate (feat); Cartographer's Tools
**Languages auto-granted:** common, elvish + goblin
**GPT-side only:** Orc and Sylvan (from class feature, not species — track narratively)

---

## 3 — Cleric (Goliath)

Guard: STR +2, INT +1, CHA +1 → pre-bg: STR 13, INT 9, CHA 9

```json
{
  "character_name": "Cleric",
  "class": "cleric",
  "species": "goliath",
  "subspecies": "giant-ancestry-stones-endurance",
  "subclass": "forge",
  "background": "guard",
  "ability_scores": {
    "STR": 13,
    "DEX": 10,
    "CON": 14,
    "INT": 9,
    "WIS": 16,
    "CHA": 9
  },
  "ability_score_method": "manual",
  "primary_score": "STR",
  "skill_choices": ["medicine", "insight"],
  "language_choices": ["common-sign-language"],
  "species_choices": {},
  "equipment_choice": "equipment",
  "starting_location": "test-drakenvale-entry",
  "goal": "Gain an audience with the Draconic Council",
  "threat": "Suspicion from the Dragon Guard"
}
```

**Expected final scores:** STR 15, DEX 10, CON 14, INT 10, WIS 16, CHA 10
**HP:** 12 (d8 + CON mod +2)
**Backend auto-grants:** Athletics, Perception (skills); alert (feat); Three-Dragon Ante tool prof
**Languages auto-granted:** common, giant + common-sign-language

---

## 4 — Wizard (High Elf)

Scribe: DEX +1, INT +2, WIS +1 → pre-bg: DEX 13, INT 15, WIS 11

```json
{
  "character_name": "Wizard",
  "class": "wizard",
  "species": "elf",
  "subspecies": "elven-lineage-high-elf",
  "subclass": "abjurer",
  "background": "scribe",
  "ability_scores": {
    "STR": 8,
    "DEX": 13,
    "CON": 14,
    "INT": 15,
    "WIS": 11,
    "CHA": 10
  },
  "ability_score_method": "manual",
  "primary_score": "INT",
  "skill_choices": ["arcana", "insight"],
  "language_choices": ["common-sign-language"],
  "species_choices": {
    "spellcasting_ability": "INT",
    "keen_senses": "survival"
  },
  "equipment_choice": "equipment",
  "starting_location": "test-drakenvale-entry",
  "goal": "Gain an audience with the Draconic Council",
  "threat": "Suspicion from the Dragon Guard"
}
```

**Expected final scores:** STR 8, DEX 14, CON 14, INT 17, WIS 12, CHA 10
**HP:** 9 (d6 + CON mod +2)
**Backend auto-grants:** Investigation, Perception (skills); skilled (feat); Calligrapher's Supplies
**Languages auto-granted:** common, elvish + common-sign-language

---

## 5 — Rogue (Halfling)

Criminal: DEX +2, CON +1, INT +1 → pre-bg: DEX 14, CON 13, INT 13

```json
{
  "character_name": "Rogue",
  "class": "rogue",
  "species": "halfling",
  "subspecies": null,
  "subclass": "soulknife",
  "background": "criminal",
  "ability_scores": {
    "STR": 10,
    "DEX": 14,
    "CON": 13,
    "INT": 13,
    "WIS": 12,
    "CHA": 10
  },
  "ability_score_method": "manual",
  "primary_score": "DEX",
  "skill_choices": ["acrobatics", "deception", "sleight-of-hand", "investigation"],
  "language_choices": ["common-sign-language"],
  "species_choices": {},
  "equipment_choice": "equipment",
  "starting_location": "test-drakenvale-entry",
  "goal": "Gain an audience with the Draconic Council",
  "threat": "Suspicion from the Dragon Guard"
}
```

**Expected final scores:** STR 10, DEX 16, CON 14, INT 14, WIS 12, CHA 10
**HP:** 10 (d8 + CON mod +2)
**Backend auto-grants:** Sleight of Hand, Stealth (skills); alert (feat); Thieves' Tools
**Languages auto-granted:** common, halfling + common-sign-language
**GPT-side only:** Thieves' Cant, Undercommon (class feature languages — track narratively)

---

## Known flags

- **Cleric subclass `forge`**: confirm it's in your `subclasses.json` after the merge.
- **Rogue skill_choices**: Criminal auto-grants Sleight of Hand and Stealth. Rogue gets 4 class skill choices — passing all 4 listed. `_build_skill_list` will deduplicate Sleight of Hand.
- **Ranger skill_choices**: Guide auto-grants Stealth and Survival. Passing Stealth in skill_choices anyway — deduplication handles it.
- **Wizard subclass `abjurer`**: confirm in `subclasses.json` after merge (you added it as `abjurer`).
