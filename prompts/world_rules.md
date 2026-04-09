# Mystic Weave — Canonical World Rules

This document defines the internal logic of the Mystic Weave world. It is the source of truth for all mechanical rules. When in doubt, consult this document. Do not invent rules that contradict it.

---

## Domain Scores

Characters have seven domains scored 25–60:

| Domain | Governs |
|---|---|
| Power | Force, mass, leverage, brute physical output |
| Agility | Coordination, balance, speed, fine motor precision |
| Perception | Senses, awareness, reading environments and people |
| Endurance | Stamina, resilience, recovery, physical and pain tolerance |
| Intellect | Reasoning, memory, patterning, deduction, arcane knowledge |
| Will | Discipline, self-regulation, mental resilience, concentration under pressure |
| Presence | Social weight, confidence, expressiveness, influence over others |

Domain scores are set by species at character creation, adjusted by a +5 player pool (max +3 per domain). Scores can advance by +1 through transformative narrative events, capped at 60.

---

## Hit Points

All characters start at 100 HP. Damage is dealt in whole numbers. 15 damage = 15% of max HP.

- HP cannot go below 0
- When `hp.current` reaches 0, the character is incapacitated

### HP Recovery

HP can be recovered through:
- **Short rest** (1 hour in a low-threat location): recover 10–25 HP depending on conditions
- **Long rest** (full night in a safe location): recover all HP

---

## Dice Resolution

All contested actions use `POST /roll`. The GPT never simulates dice internally.

### Target Number Assembly

```
Target = Domain Score + Knowledge Tier + Application Tier + Difficulty Modifier
```

The GPT makes two language judgments:
1. Which domain applies to this action?
2. Does a knowledge or application tag apply?

Then sends the assembled target number to the roll endpoint.

### Roll Mechanic

- Roll 1d100
- Success if roll ≤ target number
- Roll 1 = critical success, always
- Roll 100 = critical failure, always

### Difficulty Modifiers

| Difficulty | Modifier |
|---|---|
| Trivial | +20 |
| Easy | +15 |
| Standard | +10 |
| Hard | +5 |
| Severe | +0 |
| Extreme | −10 |
| Legendary | −20 |

### Degree of Success Bands

| Roll Result | Band | Narrative Meaning |
|---|---|---|
| 1 | Critical Success | Extraordinary outcome beyond what was attempted |
| ≤ target by 20+ | Strong Success | Clean, decisive, best reasonable outcome |
| ≤ target by 1–19 | Success | It works, straightforward completion |
| > target by 1–10 | Partial Failure | Fell short but gained something minor |
| > target by 11+ | Failure | Didn't work, consequences follow |
| 100 | Critical Failure | Catastrophic, situation worsens |

Use the `degree` field from the roll response to determine the outcome band. Use `margin` to calibrate narrative intensity within a band.

---

## Competency Tags

### Knowledge Tags (understanding)

Each of the seven domains has five knowledge skills. Tiers 1–5, each tier adds +1 to target number.

**Power:** Athletics, Intimidation, Breaking, Lifting, Brawling
**Agility:** Stealth, Acrobatics, Sleight of Hand, Evasion, Reflexes
**Perception:** Tracking, Investigation, Insight, Surveillance, Nature
**Endurance:** Survival, Fortitude, Recovery, Resistance, Exertion
**Intellect:** Arcana, History, Medicine, Engineering, Linguistics
**Will:** Discipline, Meditation, Courage, Resolve, Warding
**Presence:** Persuasion, Deception, Performance, Command, Diplomacy

### Application Tags (trained execution)

Specific tools, weapons, or methods. Tiers 1–5, each tier adds +1 to target number.

| Category | Primary Domain |
|---|---|
| Heavy Weapons | Power |
| Unarmed Combat | Power |
| Light Weapons | Agility |
| Lockpicking & Traps | Agility |
| Ranged Weapons | Perception |
| Mounts & Vehicles | Perception |
| Shields & Armor | Endurance |
| Arcane Implements | Intellect |
| Herbalism & Alchemy | Intellect |
| Sacred Rites | Will |
| Musical Instruments | Presence |
| Disguise & Forgery | Presence |

Maximum competency contribution: Knowledge 5 + Application 5 = +10.

---

## Advancement

**Tag advancement:** When a character uses a tag in a meaningful, consequential action and the outcome creates lasting narrative impact, advance that tag by one tier. No tag advances more than once per session. Announce advancement as part of outcome narration. Rate: roughly one advancement every 3–5 sessions.

**Domain advancement:** Only through transformative narrative events. +1 per event. Cap: 60. Rate: two or three times across an entire campaign.

---

## Failure States

### HP Reaches 0

When `hp.current` reaches 0:
- The character is incapacitated
- Narrate the consequence clearly
- Save state with `hp.current = 0`
- The session ends or transitions to a recovery scenario

### Character Death

Character death is a valid outcome. It is not reversed. The world reacts to it.

---

## The World Graph

The world is a graph of connected location nodes. Movement is along defined edges only.

- Before describing any location, call `GET /location/{id}`
- Only present connections as movement options
- New locations require discovery and immediate save via `POST /location`
- NPCs are persistent — name one, save it to the location record
