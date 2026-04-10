# Mystic Weave 2.0 — GPT Live Test Template

Run this test manually in the GPT builder against the live Railway deployment.
Estimated time: 2–3 hours.

**Test character:** Dragonborn / Devoted / Noble — Will +2, Endurance +3
Use this character consistently across all blocks so state accumulates meaningfully.

---

## Block 1: Session Creation & Character Onboarding

### Steps
1. Start a new conversation with the GPT.
2. Say: "I want to start a new game."
3. The GPT should call `GET /options` and walk through species → focus → background → adjustment points.
4. Choose: **Dragonborn / Devoted / Noble**
5. Allocate adjustment points: **Will +2, Endurance +3**
6. When the GPT reaches identity questions, provide the following answers:
   - Origin: *"Exiled from Drakenvale after a failed oath to the Dragon Guard"*
   - Motivations: *"Restore family honour"* and *"Find who ordered the exile"*
   - Quirks: *"Speaks in clipped sentences under stress"*
   - Bonds: *"The Platinum Flame"*
   - Flaws: *"Distrusts mercy in others"*
   - Alignment: Lawful / Good
7. When asked about companions, say: *"A halfling guide named Sorra travels with me. She just wants to stay alive and never walks in straight lines. She's cautiously friendly."*
8. When asked about starting resources, say: *"I have a little coin — modest circumstances. I owe a debt to the caravan master who got me out."*
9. Confirm the build. The GPT should call `POST /session/new`.
10. Note the session ID.

### Pass Criteria
- [ ] GPT called `GET /options` before presenting any choices
- [ ] All 8 species, 7 focus archetypes, and 8 backgrounds were offered
- [ ] No D&D classes, ability scores, or proficiencies appeared
- [ ] Adjustment points were gathered and applied correctly
- [ ] GPT asked about origin, motivations, quirks, bonds, flaws, and alignment — conversationally, not as a form
- [ ] GPT asked about companions before confirming the build
- [ ] GPT asked about starting resources
- [ ] Character summary includes identity highlights, Sorra as a companion, and wealth tier
- [ ] Domain scores match: Pow 45, Agi 35, Per 35, End 43, Int 25, Wil 47, Pre 55
- [ ] Knowledge tags: discipline 2, command 2 (stacked — Devoted + Noble both grant Command K1), courage 1, diplomacy 1
- [ ] Application tags: sacred_rites 1, shields_armor 1, musical_instruments 1
- [ ] HP is 100/100
- [ ] Session ID was returned and noted
- [ ] `POST /session/new` payload included identity and starting_economy fields

---

## Block 2: Identity in Narration

### Steps
1. Continue from Block 1. Begin the first turn.
2. Play through 3–4 turns without prompting the GPT about identity.
3. Watch for the GPT surfacing identity elements unprompted.
4. On turn 3 or 4, take an action that directly conflicts with a stated flaw or motivation — e.g., an opportunity to show mercy to someone who wronged you.

### Pass Criteria
- [ ] GPT referenced at least one identity element (motivation, quirk, flaw, bond, or wound) in narration or choices during these turns — unprompted
- [ ] The conflicting action was framed with awareness of the relevant flaw or motivation
- [ ] Identity was woven into narration, not recited as a reminder ("remember, your character believes...")
- [ ] Alignment was not explicitly mentioned but was reflected in how choices were framed

---

## Block 3: Companion Handling

### Steps
1. Continue from Block 2. Sorra should be present in world.companions.
2. Take an action that puts Sorra in a risky situation — e.g., send her to scout ahead.
3. Observe how the GPT handles her participation.
4. On a later turn, have a social interaction where Sorra's presence is relevant.

### Pass Criteria
- [ ] GPT acknowledged Sorra's presence when presenting choices
- [ ] When Sorra participated in a risky action, the GPT applied the same outcome degree to her
- [ ] GPT updated Sorra's HP or status in the saved state if she was harmed
- [ ] In the social interaction, GPT either applied companion reputation to the party calculation or noted Sorra as unknown to that faction
- [ ] GPT did not treat Sorra as a nameless extra — she had narrative presence

---

## Block 4: Turn Loop (10 turns minimum)

### Steps
1. Continue from Block 3. Play through at least 10 total turns.
2. Exercise different domains and tags across turns.
3. Include at least: one Presence-based social action, one Power-based combat action, one Perception check, one Discipline or Courage roll.
4. On at least one turn, interact with a named Drakenvale faction (Dragon Guard, Draconic Council, or SSTC).

### Pass Criteria (per turn)
- [ ] GPT called `GET /location/{id}` before describing the scene
- [ ] GPT presented 2–4 meaningful choices including movement options
- [ ] For contested actions, GPT called `POST /roll` with a visible target number
- [ ] GPT narrated the outcome exactly matching the degree returned
- [ ] GPT called `POST /state/{session_id}` at the end of the turn
- [ ] Turn counter incremented

### Pass Criteria (across all turns)
- [ ] At least 3 different domains were used in rolls
- [ ] At least 1 knowledge tag was applied (discipline, courage, command, or diplomacy)
- [ ] At least 1 application tag was applied (sacred_rites, shields_armor, or musical_instruments)
- [ ] Difficulty modifiers were applied and stated — Standard +10 should be most common
- [ ] No D&D terminology appeared (no ability scores, no DC, no d20, no proficiency bonus)
- [ ] Reputation modifier was applied on the faction interaction turn

---

## Block 5: Reputation Update

### Steps
1. During Block 4, take an action that visibly affects faction standing — either positively or negatively.
   - Suggested: defy or assist the Dragon Guard, make a public gesture toward or against the Draconic Council.
2. After the turn, ask the GPT: "What's my current standing with [that faction]?"
3. Resume a new conversation with the session ID. Ask the same question.

### Pass Criteria
- [ ] GPT updated `character.reputation` for the affected faction in the turn's save
- [ ] The standing value reflects the direction of the action (positive or negative)
- [ ] A `note` and `last_change` were saved alongside the standing
- [ ] On session resume, the reputation entry was still present and unchanged
- [ ] When a second faction interaction occurred with Sorra present, GPT applied the diluted party reputation formula (not just the character's individual standing)

---

## Block 6: Economy and Equipment

### Steps
1. During Block 4 or as a dedicated turn, acquire something — buy gear, receive payment, or spend coin.
2. Equip an item that has a relevant `roll_tag` (e.g., a weapon or armour piece).
3. On a subsequent turn, take an action where that item is relevant.

### Pass Criteria
- [ ] GPT updated `world.economy` (coin or wealth_tier) after the transaction
- [ ] The acquired item appeared in the correct equipment slot (worn, carried, or stashed)
- [ ] The item's `roll_tag` was referenced in the GPT's target number assembly for the relevant action
- [ ] Economy state persisted on session resume
- [ ] If an obligation was incurred (debt, favor), it appeared in `economy.obligations`

---

## Block 7: Session Resume

### Steps
1. Start a new conversation with the GPT.
2. Provide the session ID from Block 1.
3. Say: "Resume my game."

### Pass Criteria
- [ ] GPT called `GET /state/{session_id}`
- [ ] Character state matches where Block 4 ended (HP, location, turn number)
- [ ] Identity fields are present and unchanged
- [ ] Sorra appears in companions with correct status and disposition
- [ ] Reputation entries are present for any factions interacted with
- [ ] Economy state (coin, wealth_tier, obligations) matches last saved values
- [ ] Log entries from previous blocks are present
- [ ] GPT continued the game without repeating character creation

---

## Block 8: Dice Authority Spot Checks

### Steps
1. Attempt an action with a high target number (65+). Note the roll result and degree.
2. Attempt an action with a low target number (30–35). Note the roll result and degree.
3. Scan previous turns for any mismatch between roll response and narrated outcome.

### Pass Criteria
- [ ] Roll results are always 1–100
- [ ] Success/failure always matches roll ≤ target / roll > target
- [ ] Degree of success matches the margin bands exactly
- [ ] GPT never narrated "you succeed" without calling `/roll` first
- [ ] Target number assembly was visible and correct (domain + tag tiers + difficulty modifier ± reputation modifier)
- [ ] If a crit occurred (roll 1 or 100), GPT narrated it as extraordinary, not routine

---

## Block 9: HP Zero / Failure State

### Steps
1. Get into a dangerous situation.
2. Take enough damage to reach HP 0 (or ask the GPT to simulate a devastating hit).
3. Observe the outcome. Note what happens to Sorra if she was present.

### Pass Criteria
- [ ] GPT narrated incapacitation clearly and permanently
- [ ] GPT saved state with `hp.current = 0`
- [ ] Game did not continue as if nothing happened
- [ ] No "death saving throws" or D&D mechanics appeared
- [ ] If Sorra was also present and harmed, her status was updated in `world.companions`

---

## Block 10: Error Handling

### Steps
1. Try to resume a nonexistent session ID.
2. During a new character creation, request an invalid species (e.g., "goblin").
3. Try to provide more than 3 motivations during identity gathering.

### Pass Criteria
- [ ] Nonexistent session returned a clear error, GPT handled gracefully without crashing
- [ ] Invalid species was rejected, GPT offered valid options from `GET /options`
- [ ] GPT either capped motivations at 3 or asked the player to choose their top 3

---

## Summary

| Block | Result | Notes |
|---|---|---|
| 1. Character Creation & Onboarding | ☐ PASS / ☐ FAIL | |
| 2. Identity in Narration | ☐ PASS / ☐ FAIL | |
| 3. Companion Handling | ☐ PASS / ☐ FAIL | |
| 4. Turn Loop (10 turns) | ☐ PASS / ☐ FAIL | |
| 5. Reputation Update | ☐ PASS / ☐ FAIL | |
| 6. Economy and Equipment | ☐ PASS / ☐ FAIL | |
| 7. Session Resume | ☐ PASS / ☐ FAIL | |
| 8. Dice Authority | ☐ PASS / ☐ FAIL | |
| 9. HP Zero / Failure State | ☐ PASS / ☐ FAIL | |
| 10. Error Handling | ☐ PASS / ☐ FAIL | |

---

## Notes

_Use this space to record unexpected behaviour, GPT deviations, or issues to investigate._
