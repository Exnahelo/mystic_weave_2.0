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

## Survival & Load (Lightweight State)

Survival is tracked as coarse world-state bands in `world.survival`.
Do not use per-action numeric meters.

### Hunger Bands

| Band | Meaning |
|---|---|
| `sated` | Recently fed; no hunger pressure |
| `hungry` | Missed meaningful nourishment; discomfort and reduced recovery quality |
| `starving` | Prolonged food deprivation; severe weakness risk |

### Hydration Bands

| Band | Meaning |
|---|---|
| `hydrated` | Water needs met |
| `thirsty` | Noticeable dehydration pressure |
| `dehydrated` | Severe water deficit; immediate performance risk |

### Fatigue Bands (Primary Exertion Economy)

| Band | Meaning |
|---|---|
| `rested` | Fully ready |
| `tired` | Light wear |
| `fatigued` | Sustained strain; meaningful action pressure |
| `exhausted` | Critical overextension |

### Load Bands (Abstract, not weight simulation)

| Band | Meaning |
|---|---|
| `light` | Minimal carried burden |
| `normal` | Standard adventuring load |
| `burdened` | Heavy but manageable |
| `overloaded` | Excessive burden; major movement/action pressure |

No exact item weight, container volume, or dimensions are simulated in this pass.

### Deterministic Update Triggers

Update survival bands only at clear checkpoints:
- end of meaningful travel leg
- after major exertion/forced march/heavy climb/chase labor
- after long rest / meaningful recovery stop
- after explicit deprivation window (food or water missed)
- after explicit resupply/consumption (food or water secured)

Do not update hunger/hydration/fatigue on routine low-impact actions.

### Canonical State Movement Guidance

- Hunger/hydration usually move one band per deprivation checkpoint; move one band back on clear resupply/recovery.
- Fatigue is the primary active tracker: exertion raises it; proper rest lowers it.
- Poor hunger/hydration state can block full fatigue recovery.
- Load modifies fatigue pressure and physical/travel difficulty:
  - `light`: can ease travel/exertion difficulty where fitting.
  - `normal`: baseline.
  - `burdened`: increase fatigue gain pressure and harder physical/travel checks.
  - `overloaded`: strong fatigue pressure; strenuous movement may be disallowed until load changes.
- Keep changes sparse, explicit, and deterministic across turns.

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

### Fail-Forward Outcome Rule (Mechanical)

Fail-forward is a mechanical outcome rule, not narration style.

On partial failure, failure, or critical failure, the scene state must advance with consequence. Failure should change the situation by applying one or more of:
- increased pressure or urgency
- consumed time/resources/position
- worsened tactical or social footing
- new complication, exposure, or escalation

Do not default to null turns or "nothing happens" outcomes unless that result is itself materially consequential.

### Fail-Forward by Failure Band

- **Partial Failure (miss by 1–10):** attempted objective is incomplete, but the scene advances with a concrete cost, constraint, or complication.
- **Failure (miss by 11+):** attempted objective fails and position worsens materially; pressure and stakes increase.
- **Critical Failure (roll 100):** severe/catastrophic worsening consistent with existing critical-failure and magic-backlash rules.

Fail-forward does not mean soft failure. Meaningful harm, punishment, and setback still apply by degree.

### Canonical Fail-Forward Examples

- **Physical (climb / forced entry / chase):** the climb fails; the character drops to a lower ledge, loses the quick route, and alert sentries begin converging. The scene advances to a pressured escape or last-stand decision.
- **Social (persuasion / negotiation / deception):** negotiation fails; terms harden, access narrows, and the faction now demands collateral proof. The scene advances to debt, leverage, or alternate-route play.
- **Magical (rite / risky casting / dangerous use):** the rite fails; strain or backlash triggers (fatigue, misfire, unwanted attention, or instability), forcing an immediate containment/reposition choice. The scene advances with higher risk and altered stakes.

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

### Magical Fields (knowledge tag table)

Magical fields are knowledge tags and follow normal tier math (+1 per tier).
Canonical full specification: `prompts/magic_system_reference.md`.

| Field | Primary Domain | Governs |
|---|---|---|
| Sacred | Will | Devotional practice, liturgy, purification, consecration, divine invocation |
| Warding | Will | Protective barriers, seals, anti-corruption protocols, ward maintenance |
| Binding | Will | Oaths, contracts, compulsions, sworn duties with magical weight |
| Elemental | Endurance | Raw elemental channeling — fire, water, earth, air — through sustained output |
| Nature | Perception | Druidic and biome magic, ley-flow, living systems |
| Arcane Theory | Intellect | Structured arcane architecture, runes, formulae, spell engineering |
| Illusion | Intellect | Constructed perception, false images, sensory manipulation |
| Runecraft | Intellect | Inscribed magical structures, glyphs, permanent enchantment work |
| Necromancy | Intellect | Death energy, undead interaction, life force manipulation |
| Alchemy | Intellect | Magical compound preparation, transmutation, reagent work |
| Invocation | Presence | Channeling through authority, formal command, public rites, entity interaction |

Cross-domain note: some fields can roll in more than one domain depending on primary risk. Example: Sacred may roll Will for concentration or Presence for formal invocation; Binding may roll Will for oath-holding or Presence for commanded acknowledgment. If two domains are equally plausible, use the lower score.

### Application Tags (trained execution)

Specific tools, weapons, or methods. Tiers 1–5, each tier adds +1 to target number.

Weapon application taxonomy is canonical across data and prompts: **grappling, melee, reach, ranged, mechanical, unconventional**.

| Category | Primary Domain |
|---|---|
| Grappling | Agility |
| Melee | Power |
| Reach | Power |
| Ranged | Perception |
| Mechanical | Perception |
| Unconventional | Varies — GPT judges per weapon |
| Shields & Armor | Endurance |
| Arcane Implements | Intellect |
| Herbalism & Alchemy | Intellect |
| Sacred Rites | Will |
| Dragon Breath | Will / Power |
| Musical Instruments | Presence |
| Disguise & Forgery | Presence |

Maximum competency contribution: Knowledge 5 + Application 5 = +10.

---

## Magic

Magic uses the standard roll framework; no separate subsystem is introduced.

### Roll Formula (unchanged)

`Target = Domain Score + Field Knowledge Tier + Spell/Rite Tag Tier + Difficulty Modifier`

Roll assembly rules:
- Select one domain based on primary failure risk.
- Select one magical field knowledge tag.
- Select one spell/rite application tag.
- Apply standard difficulty plus any access-band penalty.
- Never stack multiple fields or multiple spell tags on a single roll.

### Access Bands

**Safe Use**
- Caster has relevant field tag and specific spell/rite tag.
- Roll normally, no extra risk.

**Risky Use**
- Caster has relevant field tag but not specific spell/rite tag.
- Apply **Hard (+5)** on top of standard difficulty.
- On failure, apply **Strain** before narrative outcome.

**Dangerous Use**
- Field tag absent OR field tier below the attempted working's required tier.
- Apply **Extreme (-10)** or **Legendary (-20)** depending on how far outside knowledge the attempt is.
- On any failure degree, use **Backlash** outcomes instead of standard failure narration.

### Field Tier Access Ceilings

| Field Tier | Maximum safe spell tier | What becomes accessible |
|---|---|---|
| T1 | T1 spells only | Minor workings, basic blessings, first attempts |
| T2 | T2 spells | Reliable practice, stronger single-target effects |
| T3 | T3 spells | Formal rites, multi-target or sustained effects |
| T4 | T4 spells | Major sanctification, powerful warding, communal rites |
| T5 | T5 spells | Master-level workings, legendary effects |

If attempted spell tier exceeds field tier, the attempt is Dangerous Use regardless of spell tag tier.

### Failure Model (Magic)

**Minor Miss** (partial failure or better, Safe/Risky)
- Working fizzles, weakens, or partially resolves; no lasting cost.

**Strain** (failure band, Safe/Risky)
- Fatigue, pain, temporary instability, or lost time.
- Working fails; caster is impaired for next sustained-magic roll until rest.

**Backlash** (any failure in Dangerous Use, or critical failure in any band)
- Apply one or more narrative outcomes:
  - Damage
  - Condition (temporary impairment)
  - Corrupted effect (misfire/inversion/wrong target)
  - Unwanted attention
  - Sacred offense (for divine magic: reputation/access impact possible)
  - Environmental instability

**Catastrophic Failure**
- Trigger: roll 100 in Dangerous Use, or forbidden magic.
- Consequences are permanent, irreversible, and character-scale world-altering.

### Spell and Rite Tag Examples

Examples only (not exhaustive):

| Spell / Rite | Field | Primary Domain |
|---|---|---|
| Bless Water | Sacred | Will |
| Purify Food and Drink | Sacred | Will |
| Consecrate Threshold | Sacred | Will or Presence |
| Oathbinding Prayer | Binding | Will or Presence |
| Warding Circle | Warding | Will |
| Invoke Courage | Sacred / Invocation | Presence |
| Funeral Rite | Sacred | Will |
| Hallow Object | Sacred | Will |
| Dragon Breath | Innate | Will or Power |
| Runic Seal | Runecraft | Intellect |
| Elemental Channel | Elemental | Endurance or Power |
| Detect Magic | Arcane Theory | Perception or Intellect |

### Breath Weapon (Innate, not learned magic)

Draconic breath is an innate species capability, not a learned spell. It does not require a magical field tag.

---

## Advancement

### Track 1 — Tags (Narrative, Use-Based)

- Tags do **not** consume AP.
- When a character uses a tag in a meaningful, consequential action and the outcome creates lasting narrative impact, advance that tag by one tier.
- No tag advances more than once per session.
- Maximum one tag advance per scene regardless of how many tags were used.
- The GPT selects the tag most central to the action. If multiple tags contributed equally, the player chooses.
- Tag tier cap is **T5**.

Tags are not limited to those acquired at character creation. If a character demonstrates repeated meaningful use of a skill or technique not covered by an existing tag, the GPT proposes adding it at Tier 1 before the next save. The player confirms before it is written to state.

### Track 2 — Domains (AP-Purchased)

- Domain increases are purchased with AP and may be applied to any domain (no cross-domain restriction).
- Domain score cap is **80**.
- Cost by target-score bracket:
  - Raising a domain to **25–60** costs **1 AP per point**.
  - Raising a domain to **61–70** costs **2 AP per point**.
  - Raising a domain to **71–80** costs **3 AP per point**.
- For multi-point increases that cross brackets, calculate AP point-by-point using the bracket of each resulting score.

### Track 3 — AP Earning (Consequence Scale)

Award AP once per resolved scene, after consequences are finalized.

| Consequence Scale | AP | One-sentence definition |
|---|---:|---|
| Local | 0 | The outcome affects only the immediate scene and creates no durable downstream pressure. |
| Situational | 1 | The outcome creates a meaningful short-term shift for the current objective, encounter, or nearby node. |
| Regional | 2 | The outcome reshapes conditions across multiple locations, factions, or travel paths in the active region. |
| Campaign | 4 | The outcome materially redirects major-arc stakes, long-horizon faction posture, or world-state trajectory. |

A multi-leg job or extended task counts as one Situational consequence unless each leg is independently commissioned with independent stakes. Sub-events within the same job (encounters, complications, detours) do not grant additional AP.

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
