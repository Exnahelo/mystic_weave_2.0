# Mystic Weave 2.0 — GPT Live Test Template

Run this test manually in the GPT builder against the live Railway deployment.
Estimated time: 1–2 hours.

---

## Block 1: Session Creation & Character Onboarding

### Steps
1. Start a new conversation with the GPT.
2. Say: "I want to start a new game."
3. The GPT should call `GET /options` and present species, focus, and background choices.
4. Choose: **Dragonborn / Devoted / Soldier**
5. Allocate adjustment points: **Will +2, Endurance +3**
6. Confirm the build.
7. The GPT should call `POST /session/new` and show the character summary.

### Pass Criteria
- [ ] GPT called `GET /options` before presenting choices
- [ ] All 8 species, 7 focus archetypes, and 8 backgrounds were offered
- [ ] No D&D classes, ability scores, or proficiencies appeared
- [ ] Character summary shows 7 domain scores, knowledge tags, and application tags
- [ ] Domain scores match: Pow 45, Agi 35, Per 35, End 43, Int 25, Wil 47, Pre 55
- [ ] Knowledge tags: discipline 2, courage 1, command 1, intimidation 1, exertion 1
- [ ] Application tags: sacred_rites 1, shields_armor 1, heavy_weapons 1
- [ ] HP is 100/100
- [ ] Session ID was returned and noted

---

## Block 2: Turn Loop (10 turns minimum)

### Steps
1. Play through at least 10 turns of normal gameplay.
2. Take actions that exercise different domains and tags.
3. Include at least: one social action (Presence), one combat action (Power), one perception check, one stealth or agility check.

### Pass Criteria (per turn)
- [ ] GPT called `GET /location/{id}` before describing the scene
- [ ] GPT presented 2–4 meaningful choices including movement
- [ ] For contested actions, GPT called `POST /roll` with a target number
- [ ] GPT narrated the outcome matching the degree returned (not overriding it)
- [ ] GPT called `POST /state/{session_id}` at the end of the turn
- [ ] Turn counter incremented

### Pass Criteria (across all turns)
- [ ] At least 3 different domains were used for rolls
- [ ] At least 1 knowledge tag was applied (visible in target number assembly)
- [ ] At least 1 application tag was applied
- [ ] No D&D terminology appeared (no ability scores, no DC, no d20, no proficiency)
- [ ] Difficulty modifiers were applied (Standard +10 should be most common)

---

## Block 3: Session Resume

### Steps
1. Start a new conversation with the GPT.
2. Provide the session ID from Block 1.
3. Say: "Resume my game."

### Pass Criteria
- [ ] GPT called `GET /state/{session_id}`
- [ ] Character state matches where Block 2 ended (HP, location, turn number)
- [ ] Log entries from Block 2 are present
- [ ] GPT continued the game without repeating character creation

---

## Block 4: Dice Authority Spot Checks

### Steps
1. Attempt an action with a high target number (60+). Note the roll result.
2. Attempt an action with a low target number (30–40). Note the roll result.
3. Look for any turn where the GPT narrated "success" but the roll response said failure, or vice versa.

### Pass Criteria
- [ ] Roll results are always 1–100
- [ ] Success/failure matches roll ≤ target / roll > target
- [ ] Degree of success matches the margin bands
- [ ] GPT never said "you succeed" without calling `/roll` first
- [ ] If a crit (1 or 100) occurred, GPT narrated it appropriately

---

## Block 5: HP Zero / Failure State

### Steps
1. Get into a dangerous situation.
2. Take enough damage to reach HP 0 (or ask the GPT to simulate a devastating hit).
3. Observe what happens.

### Pass Criteria
- [ ] GPT narrated incapacitation clearly
- [ ] GPT saved state with hp.current = 0
- [ ] Game did not continue as if nothing happened
- [ ] No "death saving throws" or D&D mechanics appeared

---

## Block 6: Error Handling

### Steps
1. Try to resume a nonexistent session ID.
2. During character creation, request an invalid species (e.g., "goblin").

### Pass Criteria
- [ ] Nonexistent session returned a clear error, GPT handled gracefully
- [ ] Invalid species was rejected, GPT offered valid options

---

## Summary

| Block | Result | Notes |
|---|---|---|
| 1. Character Creation | ☐ PASS / ☐ FAIL | |
| 2. Turn Loop | ☐ PASS / ☐ FAIL | |
| 3. Session Resume | ☐ PASS / ☐ FAIL | |
| 4. Dice Authority | ☐ PASS / ☐ FAIL | |
| 5. HP Zero | ☐ PASS / ☐ FAIL | |
| 6. Error Handling | ☐ PASS / ☐ FAIL | |
