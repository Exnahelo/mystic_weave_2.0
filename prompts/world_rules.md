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

Domain scores are set by ancestry base (280 total), culture bonus (10), background bonus (10), and player adjustment (10 points, max +5 per domain). Starting values are usually within ancestry baselines (commonly 25–60 before bonuses), but campaign progression can raise domains to 80 through AP spend.

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
**Perception:** Tracking, Investigation, Insight, Surveillance, Natural Lore
**Endurance:** Survival, Fortitude, Recovery, Resistance, Exertion
**Intellect:** Arcana, History, Medicine, Engineering, Linguistics
**Will:** Discipline, Meditation, Courage, Resolve, Focus
**Presence:** Persuasion, Deception, Performance, Command, Diplomacy

### Magical Fields (knowledge tag table)

Magical fields are knowledge tags and follow normal tier math (+1 per tier).
Canonical full specification: `prompts/magic_rules.md`.

| Field | Primary Domain | Governs |
|---|---|---|
| Sacred | Will | Devotional practice, liturgy, purification, consecration, divine invocation |
| Warding | Will | Protective barriers, seals, anti-corruption protocols, ward maintenance |
| Binding | Will | Oaths, pacts, compulsions, sworn duties, and channeled authority with magical weight |
| Elemental | Endurance | Raw elemental channeling through sustained output |
| Nature | Perception | Druidic and biome magic, ley-flow, living systems |
| Illusion | Presence | Constructed perception, false images, sensory manipulation |
| Runecraft | Intellect | Inscribed magical structures: runes, glyphs, sigils, permanent enchantment |
| Alchemy | Intellect | Magical compound preparation, transmutation, reagent work |
| Necromancy | Intellect | Death energy, undead interaction, life-force manipulation |

Cross-domain note: some fields can roll in more than one domain depending on context. Example: Sacred may roll Will for concentration or Presence for formal invocation; Binding may roll Will for oath endurance or Presence for command recognition. If two domains are equally plausible, use the lower score. Cross-domain does not change which domain gates field knowledge — that is always the primary domain.

Magical field knowledge tiers are gated by the field's primary domain score. See `prompts/magic_rules.md` for the domain-gating threshold table.

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

Magic uses three linked layers. Full specification: `prompts/magic_rules.md`.

### Layer 1 — Domain Score Gates Field Knowledge

| Domain Score | Maximum Field Knowledge Tier |
|---|---|
| 40 | T1 |
| 50 | T2 |
| 60 | T3 |
| 70 | T4 |
| 80 | T5 |

Domain score gates the ceiling only. Advancement through use still required.

### Layer 2 — Field Knowledge Gates Spell Access

| Field Knowledge Tier | Spells Accessible |
|---|---|
| T1 | Tier 1 spells in that field |
| T2 | Tier 1–2 spells |
| T3 | Tier 1–3 spells |
| T4 | Tier 1–4 spells |
| T5 | Tier 1–5 spells |

Attempting a spell above the field tier is Dangerous Use regardless of application tier.

### Layer 3 — Spell Application Determines Success

Spell rolls use a fixed threshold, NOT the standard competency roll formula.

| Application Tier | Target Number |
|---|---|
| T1 | 55 |
| T2 | 65 |
| T3 | 75 |
| T4 | 85 |
| T5 | 95 |

d100 roll-under via `POST /roll`. Roll 1 = critical success. Roll 100 = critical failure.
Situational modifiers: up to ±10 based on conditions.
Standard roll formula applies to non-spell magical actions (identification, resistance, concentration).

### Magical Fields (Knowledge Tags)

| Field | Primary Domain | Governs |
|---|---|---|
| Sacred | Will | Devotional practice, liturgy, purification, consecration, divine invocation |
| Warding | Will | Protective barriers, seals, anti-corruption protocols, ward maintenance |
| Binding | Will | Oaths, pacts, compulsions, sworn duties, and channeled authority with magical weight |
| Elemental | Endurance | Raw elemental channeling through sustained output |
| Nature | Perception | Druidic and biome magic, ley-flow, living systems |
| Illusion | Presence | Constructed perception, false images, sensory manipulation |
| Runecraft | Intellect | Inscribed magical structures: runes, glyphs, sigils, permanent enchantment |
| Alchemy | Intellect | Magical compound preparation, transmutation, reagent work |
| Necromancy | Intellect | Death energy, undead interaction, life-force manipulation |

Cross-domain note: some fields can roll in more than one domain depending on context. Example: Sacred may roll Will for concentration or Presence for formal invocation. If two domains are equally plausible, use the lower score. Cross-domain does not change which domain gates field knowledge — that is always the primary domain.

### Access Bands

| Band | Field Tag? | Spell Tag? | Within Ceiling? | Threshold Penalty |
|---|---|---|---|---|
| Safe | Yes | Yes | Yes | None |
| Risky | Yes | No | Yes | −10 |
| Dangerous | No, or over ceiling | — | — | −20 |

Risky Use: on failure, apply Strain before narrative consequences.
Dangerous Use: on any failure, use Backlash outcomes.

### Failure Model (Magic)

**Minor Miss** — Safe/Risky partial failure. Working weakens or fizzles. No lasting cost.

**Strain** — Safe/Risky failure. Fatigue, pain, temporary instability, lost time. Caster impaired until rest.

**Backlash** — Any Dangerous Use failure, or critical failure in any band. Damage, corrupted effect, wrong target, unwanted attention, sacred offense, environmental instability.

**Catastrophic Failure** — Roll 100 in Dangerous Use, or forbidden magic. Permanent, irreversible, character-scale consequences.

### Breath Weapon (Innate, Not Learned Magic)

Draconic breath is an innate species capability, not a learned spell. It does not use the spell threshold table. It does not require a magical field knowledge tag. Use `dragon_breath` as the application tag and resolve with the **standard competency roll formula** using Will or Power based on intent.

---

## Advancement

Progression adjudication is canonical in `prompts/progression_rules.md`.

Scene-boundary vocabulary for progression adjudication is canonical in `prompts/scene_structure.md`.

---

## Pacing (Lightweight Guidance State)

Pacing is descriptive scene-cadence guidance, not a separate subsystem. It does not override dice, location constraints, faction logic, or established consequences.

### Pacing Fields

- `tension` (0–10): current pressure level for scene intensity.
- `last_consequence_weight` (`local|situational|regional|campaign`): scale of the most recently resolved consequence.
- `turns_since_social_beat`: turns since a meaningful social interaction beat.
- `turns_since_discovery`: turns since a meaningful discovery/lore/reveal beat.
- `turn_count`: pacing-facing mirror of authoritative `world.turn`.

### Canonical Update Guidance

- Tension rises when outcomes escalate danger, urgency, or strategic pressure.
- Tension falls when outcomes materially stabilize safety, leverage, or immediate risk.
- Tension holds when pressure profile is broadly unchanged.
- Update `last_consequence_weight` at scene resolution using the existing consequence scale.
- Reset `turns_since_social_beat` to 0 when a meaningful social beat occurs; otherwise increment.
- Reset `turns_since_discovery` to 0 when a meaningful discovery beat occurs; otherwise increment.
- Synchronize `turn_count` with `world.turn` at save time.

Use pacing conservatively to avoid repetitive scene selection and to modulate cadence, not to force outcomes.

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

### Relationship Propagation Rules (Band Crossings)

Reputation propagation is a gameplay consequence layer, not flavor text. When standing crosses into a new band, faction posture and access should update for future scenes.

Apply propagation conservatively and faction-agnostically unless a faction has authored exceptions. Keep effects tied to the specific faction whose standing changed.

### Canonical Band Effects

- **Revered (61 to 100):** privileged access, proactive help, sensitive information access, reduced scrutiny, strong benefit of the doubt.
- **Respected (21 to 60):** easier introductions, routine cooperation, standard services/opportunities opened, moderate institutional trust.
- **Neutral (-20 to 20):** baseline access only, no special help, no automatic hostility.
- **Distrusted (-21 to -60):** guarded interactions, reduced access, higher scrutiny, refusals on sensitive requests.
- **Despised (-61 to -100):** denied access, active obstruction, and possible reporting/hostility depending on faction and context.

### Propagation Scope and Boundaries

Propagation may affect:
- service availability
- information access
- faction cooperation
- escort/sanction/authorization likelihood
- legal/social scrutiny
- which jobs, requests, or aid offers are available

Propagation does not require separate subsystem math. Do not create automatic cross-faction chain reactions unless explicitly authored.

### Threshold-Crossing Behavior

- Apply propagation when standing crosses from one band into another.
- Do not re-trigger the same unlock/lock consequence every turn while standing remains in the same band.
- On threshold crossing, update access and posture for future scenes.

### Faction-Agnostic Threshold Examples

- **Neutral -> Respected:** routine cooperation opens; trusted introductions become available.
- **Respected -> Revered:** sensitive access and proactive support become available.
- **Neutral -> Distrusted:** sensitive requests close; scrutiny and friction increase.
- **Distrusted -> Despised:** denial, expulsion, reporting, or active interference becomes likely by faction context.

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

- Before describing any location, call `GET /location/{location_id}`
- Only present connections as movement options
- New locations require discovery and immediate save via `POST /location`
- NPCs are persistent — name one, save it to the location record

---

## Economy Resolution Rules

Use `prompts/economy_rules.md` as the canonical economy/currency reference.

- Everyday purchases use coin when appropriate to context.
- High-value magical services, rare materials, relics, and sensitive information default to barter.
- Update `world.economy.coin` for coin transactions.
- Update `world.economy.trade_goods` and/or `world.economy.obligations` for barter outcomes.
- `coin` cannot go below 0.
- Keep `wealth_tier` stable across minor purchases; update only for material long-term status shifts.
