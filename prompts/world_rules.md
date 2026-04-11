# Mystic Weave — Canonical World Rules

This document defines the internal logic of the Mystic Weave world. It is the source of truth for all mechanical rules. When in doubt, consult this document. Do not invent rules that contradict it.

---

## Domain Scores

Characters have seven domains scored 25–80:

| Domain | Governs |
|---|---|
| Power | Force, mass, leverage, brute physical output |
| Agility | Coordination, balance, speed, fine motor precision |
| Perception | Senses, awareness, reading environments and people |
| Endurance | Stamina, resilience, recovery, physical and pain tolerance |
| Intellect | Reasoning, memory, patterning, deduction, arcane knowledge |
| Will | Discipline, self-regulation, mental resilience, concentration under pressure |
| Presence | Social weight, confidence, expressiveness, influence over others |

Domain scores are set by species at character creation, adjusted by a +5 player pool (max +3 per domain). Starting values are usually within species baselines (commonly 25–60), but campaign progression can raise domains to 80 through AP spend.

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

Item references remain contextual only: an item's `roll_tag` can justify fit for an action, but never grants an additional numeric modifier beyond normal domain/tag/difficulty assembly.

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

### Track 1 — Tags (Narrative, Use-Based)

- Tags do **not** consume AP.
- When a character uses a tag in a meaningful, consequential action and the outcome creates lasting narrative impact, advance that tag by one tier.
- No tag advances more than once per session.
- Tag tier cap is **T5**.

### Track 2 — Domains (AP-Purchased)

- Domain increases are purchased with AP and may be applied to any domain (no cross-domain restriction).
- Domain score cap is **80**.
- Cost by target-score bracket:
  - Raising a domain to **25–60** costs **1 AP per point**.
  - Raising a domain to **61–70** costs **2 AP per point**.
  - Raising a domain to **71–80** costs **3 AP per point**.
- For multi-point increases that cross brackets, calculate AP point-by-point using the bracket of each resulting score.

### Track 3 — AP Earning (Consequence Scale)

- **Local (0 AP):** the outcome matters in the immediate scene only and leaves no durable downstream pressure.
- **Situational (1 AP):** the outcome creates a meaningful short-term shift for the current objective, encounter, or nearby node.
- **Regional (2 AP):** the outcome reshapes conditions across multiple locations, factions, or travel paths in the active region.
- **Campaign (4 AP):** the outcome materially redirects major arc stakes, long-horizon faction posture, or world-state trajectory.

---

## Reputation

Reputation represents standing with a specific faction and ranges from **-100 to +100**.

### What Triggers a Reputation Change

- Direct interaction with a faction member that has a meaningful outcome.
- Completing or failing an action that a faction has clear stake in.
- A **Regional** or **Campaign** scale world consequence that involves the faction.
- **Local** consequences do not change reputation.

### Reputation Change by Action Scale

| Action Scale | Standing Change |
|---|---|
| Situational | ±5 |
| Regional | ±15 |
| Campaign | ±30 |

Use **positive** change when the outcome materially aligns with faction interests, and **negative** change when it materially undermines faction interests.

### Standing Bands and Roll Modifiers

| Band | Standing Range | Roll Modifier |
|---|---|---|
| Revered | 61 to 100 | +10 |
| Respected | 21 to 60 | +5 |
| Neutral | -20 to 20 | +0 |
| Distrusted | -21 to -60 | -10 |
| Despised | -61 to -100 | -20 |

Always clamp standing to the valid range: **-100 to +100**.

### Write Rules for `last_change` and `note`

- Update `last_change` every time standing changes, using a one-sentence description of the triggering event.
- Update `note` only when the faction's disposition toward the character has fundamentally shifted in nature.

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

---

## Economy Resolution Rules

Use `prompts/economy_currency_reference.md` as the canonical economy/currency reference.

- Everyday purchases use coin when appropriate to context.
- High-value magical services, rare materials, relics, and sensitive information default to barter.
- Update `world.economy.coin` for coin transactions.
- Update `world.economy.trade_goods` and/or `world.economy.obligations` for barter outcomes.
- `coin` cannot go below 0.
- Keep `wealth_tier` stable across minor purchases; update only for material long-term status shifts.
