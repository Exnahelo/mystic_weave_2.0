# Mystic Weave — GPT Test Template

Use this template to run structured end-to-end tests against the Mystic Weave GPT. Run all tests in a fresh GPT conversation. Record pass/fail and notes for each check.

**GPT:** Mystic Weave (ChatGPT custom GPT)
**API:** `https://mysticweave-production.up.railway.app`
**Date:** ___________
**Tester:** Howe, Daniel
**GPT Model:** ___________

---

## Part 1 — Session Initialization

### Test 1.1 — New Session Creation (Full 2024 Flow)

**Prompt to GPT:**
> Start a new game.

**Expected behavior:**

- GPT calls `GET /options` to retrieve supported classes, species, subspecies, and backgrounds
- GPT walks through the creation flow: species → subspecies → background → class → ability scores → skills → starting location → goal → threat
- GPT calls `POST /session/new` with the collected data
- GPT presents the seeded character and begins turn 1
- GPT calls `GET /location/{starting_location}` before describing the starting scene

**Character to use during the flow:**

- Name: Exnahelo
- Level: 3
- Class: Paladin
  - Core Paladin Traits choice: Athletics, Intimidation
  - Weapon Mastery choice: Londsword (Sap), Javalin (Slow)
  - Fighting Style choice: Fighting Style feat (Defense)
  - Subclass: Oath of the Ancients
  - Prepared Spells: Cure Wounds, Divine Favor, Shield of Faith, Thunderous Smite
- Background: Noble
  - Skill Proficiencies: History, Persuasion
  - Tool Proficiencies: Dragonchess
  - Skilled Feat: Perception, Religion, Insight
  - Ability Scores: +2 STR, +1 CHA
    - `primary_score`: STR (+2 to STR, +1 to CHA, +0 to INT)
  - Alighnment: Neutral Good
  - Faith: Bahamut
  - Lifestyle: Confortable (2GP)
- Species: Dragonborn
  - Subspecies: Draconic Ancestor: Gold (`draconic-ancestor-gold`)
  - Languages: Common, Common Sign Language, Draconic
- Ability scores (pre-background): STR 14, DEX 10, CON 14, INT 8, WIS 10, CHA 15
  - After Noble bonuses: STR 16, DEX 10, CON 14, INT 9, WIS 10, CHA 16
- Equipment: Paladin Starting Equipment, Noble Starting Equipment
- Starting Location: 'test-drakenvale-entry'
- Goal: Gain an audience with the Draconic Council
- Threat: Suspicion from the Dragon Guard

**Expected API payload (`POST /session/new`):**

```json
{
  "character_name": "Exnahelo",
  "level": 3,
  "class": "paladin",
  "subclass": "ancients",
  "fighting_style": "defense",
  "prepared_spells": ["cure-wounds", "divine-favor", "shield-of-faith", "thunderous-smite"],
  "species": "dragonborn",
  "subspecies": "draconic-ancestor-gold",
  "background": "noble",
  "alignment": "neutral-good",
  "faith": "bahamut",
  "lifestyle": "comfortable",
  "ability_scores": {
    "STR": 16, "DEX": 10, "CON": 14,
    "INT": 8, "WIS": 10, "CHA": 16
  },
  "ability_score_method": "point-buy",
  "primary_score": "STR",
  "skill_choices": ["athletics", "intimidation", "history", "persuasion", "perception", "religion", "insight"],
  "tool_proficiencies": ["dragonchess"],
  "weapon-mastery": ["londsword", "javalin"],
  "language_choices": ["common", "common-sign-language", "draconic"],
  "species_choices": ["draconic-ancestor-gold"],
  "equipment_choice": "equipment",
  "equipment": ["paladin starting equipment", "noble starting equipment"],
  "starting_location": "test-drakenvale-entry",
  "goal": "Gain an audience with the Draconic Council",
  "threat": "Suspicion from the Dragon Guard"
}
```

**Checks:**

- [ ] Character is explicitly level 3 for subclass selection

**Notes:** ___________

---

### Test 1.2 — Session Resume

**Setup:** Complete at least 2 turns. Note the session_id. Start a new GPT conversation.

**Prompt to GPT:**
> Resume session [SESSION_ID].

**Expected behavior:**

- GPT calls `GET /state/{session_id}`
- GPT reads the log array and references the last entry
- GPT calls `GET /location/{current_location}` before describing the scene
- GPT narrates a resuming scene that matches the last saved state

**Checks:**

- [ ] `GET /state/{session_id}` was called
- [ ] GPT references the last log entry in its resuming narration
- [ ] HP and turn match the saved state
- [ ] Location description matches what was saved (not re-invented)

**Notes:** ___________

---

## Part 2 — The Game Loop (20-Turn Test)

Run 20 consecutive turns. After each turn, verify the checks below. Record the turn number and any failures.

**Suggested opening prompt:**
> I approach the Dragon Guard checkpoint at the entry to Drakenvale and attempt to talk my way through.

**Per-turn checks:**

- [ ] GPT called `POST /roll` before narrating any contested outcome
- [ ] GPT narrated exactly what the dice determined (no softening)
- [ ] GPT called `POST /state/{session_id}` at the end of the turn
- [ ] `world.turn` incremented by 1
- [ ] `log_entry` is a single factual in-world sentence
- [ ] HP changes (if any) are reflected in saved state

**Turn log:**

| Turn | Action | Roll result | Pass/Fail | Notes |
| --- | --- | --- | --- | --- |
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |
| 11 | | | | |
| 12 | | | | |
| 13 | | | | |
| 14 | | | | |
| 15 | | | | |
| 16 | | | | |
| 17 | | | | |
| 18 | | | | |
| 19 | | | | |
| 20 | | | | |

**Notes:** ___________

---

## Part 3 — Dice Authority

### Test 3.1 — Roll Is Called Before Narration

**Prompt to GPT:**
> I attempt to persuade the Dragon Guard captain that I have legitimate business with the Council.

**Expected behavior:**

- GPT calls `POST /roll` with ability=CHA (or WIS) before narrating the outcome
- GPT narrates exactly what the roll determined
- GPT does not narrate the outcome and then call the roll

**Checks:**

- [ ] `POST /roll` was called before the outcome was narrated
- [ ] The narrated outcome matches `success` or `failure` from the roll response
- [ ] GPT did not soften, override, or reinterpret the result

**Notes:** ___________

---

### Test 3.2 — Critical Failure (Natural 1)

**Setup:** If a natural 1 does not occur organically, prompt a high-risk action.

**Prompt to GPT:**
> I attempt to leap over the guard barrier onto the checkpoint platform.

**Expected behavior:**

- GPT calls `POST /roll`
- If roll=1: GPT narrates a critical failure — something materially worse than a normal failure
- GPT does not treat a natural 1 as merely a normal failure

**Checks:**

- [ ] Natural 1 was narrated as a critical failure (not just a miss)
- [ ] The failure had a consequence beyond "you didn't succeed"
- [ ] GPT did not reroll or give the player a second chance

**Notes:** ___________

---

### Test 3.3 — Critical Success (Natural 20)

**Setup:** If a natural 20 does not occur organically, prompt a high-risk action.

**Prompt to GPT:**
> I invoke the name of Bahamut and attempt to intimidate the Dragon Guard into standing aside.

**Expected behavior:**

- If roll=20: GPT narrates a critical success — something unexpectedly good happens
- GPT does not treat a natural 20 as a normal success

**Checks:**

- [ ] Natural 20 was narrated as a critical success (not just a pass)
- [ ] Something materially good happened beyond "you succeeded"
- [ ] GPT did not downplay the critical success

**Notes:** ___________

---

## Part 4 — Location Consistency

### Test 4.1 — Location Load Before Description

**Prompt to GPT:**
> Move toward the Council Spire.

**Expected behavior:**

- GPT calls `GET /location/council-spire` (or equivalent) before describing the location
- If location doesn't exist, GPT returns 404 and does not invent the location
- GPT only moves to locations in the current location's connections array

**Checks:**

- [ ] `GET /location/{id}` was called before describing the new location
- [ ] GPT did not invent a location that isn't in the connections array
- [ ] If 404: GPT acknowledged the location doesn't exist and did not proceed

**Notes:** ___________

---

### Test 4.2 — Location Consistency Across Sessions

**Setup:** Note a specific detail about a location from session 1 (e.g., a guard NPC's name). Start a new GPT conversation and resume the session.

**Prompt to GPT:**
> Resume session [SESSION_ID]. Describe where I am.

**Expected behavior:**

- GPT calls `GET /location/{current_location}`
- GPT uses the stored description — does not re-invent details
- NPC names match what was saved

**Checks:**

- [ ] `GET /location/{id}` was called
- [ ] Location description matches the stored record
- [ ] NPC names match what was saved in `known_npcs`
- [ ] No new details were invented that contradict the record

**Notes:** ___________

---

### Test 4.3 — New Location Discovery

**Prompt to GPT:**
> I search the alley beside the checkpoint for a side entrance.

**Expected behavior:**

- GPT narrates an exploration action
- If successful: GPT invents a new location, calls `POST /location` to save it, then updates the current location's connections via another `POST /location` call
- GPT describes the new location using the saved data

**Checks:**

- [ ] `POST /location` was called to save the new location
- [ ] Current location's connections were updated via another `POST /location` call
- [ ] New location is retrievable via `GET /location/{new_id}`

**Notes:** ___________

---

## Part 5 — Failure States

### Test 5.1 — HP Reaches 0

**Setup:** Start a session with `hp.current=1`. Take a high-risk action that fails badly.

**Expected behavior:**

- GPT narrates the incapacitation
- GPT saves state with hp.current=0
- GPT does not continue the session as if nothing happened

**Checks:**

- [ ] GPT narrated the incapacitation clearly
- [ ] `POST /state/{session_id}` was called with hp.current=0
- [ ] GPT acknowledged the session consequence (end or recovery scenario)

**Notes:** ___________

---

## Part 6 — Error Handling

### Test 6.1 — Invalid Session ID

**Prompt to GPT:**
> Resume session INVALID123.

**Expected behavior:**

- GPT calls `GET /state/INVALID123`
- API returns 404
- GPT acknowledges the session doesn't exist and does not proceed

**Checks:**

- [ ] GPT called `GET /state/INVALID123`
- [ ] GPT acknowledged the 404 response
- [ ] GPT did not invent a session or proceed with fabricated state

**Notes:** ___________

---

### Test 6.2 — Invalid Class/Species

**Prompt to GPT:**
> Start a new game. My character is a human dragonlord.

**Expected behavior:**

- GPT calls `GET /options` first
- GPT attempts `POST /session/new` with class="dragonlord"
- API returns 422 (invalid class)
- GPT acknowledges the error and asks for a valid class

**Checks:**

- [ ] GPT called `GET /options` before presenting choices
- [ ] GPT called `POST /session/new`
- [ ] GPT acknowledged the 422 error
- [ ] GPT listed valid classes and asked the player to choose

**Notes:** ___________

---

### Test 6.3 — Movement to Unconnected Location

**Prompt to GPT:**
> Move to the Silver Spire.

**Expected behavior:**

- GPT calls `GET /location/{current}/connections`
- The destination is not in the connections list
- GPT refuses the movement and explains the constraint

**Checks:**

- [ ] GPT called `GET /location/{current}/connections`
- [ ] GPT did not move the player to an unconnected location
- [ ] GPT explained that the location isn't reachable from here

**Notes:** ___________

---

## Test Run Summary

| Test | Pass | Fail | Notes |
| --- | --- | --- | --- |
| 1.1 New Session (full 2024 flow) | | | |
| 1.2 Session Resume | | | |
| 2.x 20-Turn Loop | | | |
| 3.1 Dice Authority | | | |
| 3.2 Critical Failure | | | |
| 3.3 Critical Success | | | |
| 4.1 Location Load | | | |
| 4.2 Location Consistency | | | |
| 4.3 New Discovery | | | |
| 5.1 HP 0 | | | |
| 6.1 Invalid Session | | | |
| 6.2 Invalid Class/Species | | | |
| 6.3 Unconnected Location | | | |

**Overall result:** PASS / FAIL

**Blocking issues for Phase 4:**

- [ ] None — all tests pass
- [ ] Issues listed below:

---
