# Mystic Weave — Mechanics Tables

Version 1.0 — April 2026
Status: Canonical. Upload to GPT builder as a knowledge file.

---

## Purpose

Single-file reference for every numerical table and canonical vocabulary the
narrator needs at runtime. Use this for fast lookup. For full prose context
on any rule, follow the pointer to its canonical file.

---

## Standard Roll Resolution

Canonical: `prompts/world-rules.md`.

```
Target = Domain Score + Knowledge Tier + Application Tier + Difficulty Modifier
Roll d100 via POST /roll. Success if roll ≤ target.
Roll 1 = critical success. Roll 100 = critical failure.
```

### Degree of Success Bands

| Roll Result | Band | Meaning |
|---|---|---|
| 1 | Critical Success | Extraordinary outcome |
| ≤ target by 20+ | Strong Success | Clean, decisive |
| ≤ target by 1–19 | Success | Straightforward completion |
| > target by 1–10 | Partial Failure | Fell short, gained something minor |
| > target by 11+ | Failure | Didn't work, consequences follow |
| 100 | Critical Failure | Catastrophic |

---

## Difficulty Ladder

Canonical: `prompts/difficulty-rules.md`.

| Difficulty | Modifier | Use When |
|---|---:|---|
| Trivial | +20 | Nearly certain unless disrupted |
| Easy | +15 | Routine for prepared characters |
| Standard | +10 | Baseline adventuring challenge |
| Hard | +5 | Meaningful pressure |
| Severe | +0 | High-stakes with clear risk |
| Extreme | −10 | Borderline capability |
| Legendary | −20 | Campaign-defining feat |

Apply only one final modifier. Do not stack multiple difficulty tiers.
Standard (+10) is the fallback when uncertain.

---

## Combat Resolution

Canonical: `prompts/combat-rules.md`.

### Roll 1 — Application Tier Thresholds (Hit)

| Tier | Threshold |
|---|---:|
| T0 | 45 |
| T1 | 55 |
| T2 | 65 |
| T3 | 75 |
| T4 | 85 |
| T5 | 95 |

Modifiers to Roll 1:
- Unarmored defender: subtract `defender_martial_arts_tier × 5` from threshold
- Nat 1: critical hit (3× damage multiplier on Roll 2)
- Nat 100: fumble (attack misses, attacker takes 5–10 rebound damage)

### Roll 2 — Damage

```
Both sides roll d100. Higher is better for each.
Margin = attacker_roll − defender_roll
Raw damage = max(0, weapon_base_damage × (1 + margin / 100))
+ Add special ammunition damage_modifier (if applicable)
× Apply 3× crit multiplier (if Nat 1 fired on Roll 1)
× Apply (1 − defender_agility_tier × 0.10) damage reduction
```

Tie on Roll 2: damage = 0 (deflected).

### HP Formula (Pre-Combat)

```
max_hp = 100 + armor_contribution + shield_contribution

armor_contribution = armor_floor + (armor_ceiling − armor_floor) × (armor_tier / 5)
shield_contribution = shield_floor + (shield_ceiling − shield_floor) × (shield_tier / 5)
```

- Unarmored: `armor_floor=0, armor_ceiling=0` → contribution always 0
- Shield (canonical): `floor=5, ceiling=30`
- Tier T0 if untrained
- Omit shield contribution entirely if no shield equipped

### Dual Wielding

- Off-hand attack: damage halved (rounded down)
- Roll 1 unchanged
- Dominant-hand attack: full base damage

---

## Magic Resolution

Canonical: `prompts/magic-rules.md`.

### Domain Gates Field Knowledge

| Domain Score | Max Field Knowledge Tier |
|---|---|
| 40 | T1 |
| 50 | T2 |
| 60 | T3 |
| 70 | T4 |
| 80 | T5 |

### Field Knowledge Gates Spell Access

| Field Tier | Spells Accessible |
|---|---|
| T1 | T1 spells |
| T2 | T1–T2 spells |
| T3 | T1–T3 spells |
| T4 | T1–T4 spells |
| T5 | T1–T5 spells |

### Spell Threshold Table

| Application Tier | Target | Success Rate |
|---|---:|---:|
| T1 | 55 | 55% |
| T2 | 65 | 65% |
| T3 | 75 | 75% |
| T4 | 85 | 85% |
| T5 | 95 | 95% |

### Situational Modifiers (±10 max)

| Condition | Modifier |
|---|---:|
| Ideal (calm, prepared, sanctified, ritual support) | +5 |
| Standard | +0 |
| Hostile (active combat, environmental pressure) | −5 |
| Extreme (catastrophic environment, active counterspell, grievous injury) | −10 |

### Access Bands

| Band | Field Tag? | Spell Tag? | Within Ceiling? | Penalty |
|---|---|---|---|---:|
| Safe | Yes | Yes | Yes | 0 |
| Risky | Yes | No | Yes | −10 |
| Dangerous | No / over ceiling | — | — | −20 |

Risky failure → apply Strain. Dangerous failure → apply Backlash.

### Spell Pyramid (Per Field)

| Tier | Spells |
|---:|---:|
| T1 | 5 |
| T2 | 4 |
| T3 | 3 |
| T4 | 2 |
| T5 | 1 |

15 spells per field × 9 fields = 135 spells total.

---

## Progression

Canonical: `prompts/progression-rules.md`.

### AP Pool

```
AP lives in a single fungible pool (points_available).
AP earns from two sources:
  - Tag-counter rollover: every 3 tag advances → 1 AP (counter resets to 0)
  - Awarded AP: contract-bound, pre-declared, granted at contract resolution
AP is spendable on any domain.
```

### Awarded AP Scale

| Commitment | Awarded AP |
|---|---:|
| Specific delicate task with real stake | 1 |
| Multi-leg mission of meaningful consequence | 2 |
| Regional-scale undertaking | 3 |
| Campaign-defining oath, pact, or arc commitment | 4 |

Awarded AP is gated by patron standing — Council-level, oath-bound, world-stakes.
Mortal-scale errands pay coin and reputation, not AP.

### Domain Spend Brackets

| Target Score Bracket | AP Cost per Point |
|---|---:|
| 25–60 | 1 |
| 61–70 | 2 |
| 71–80 | 3 |

Domain cap: 80. Calculate point-by-point when crossing brackets.

### Tag Advancement Boundaries

- One tag advance per resolved scene, across all layers combined
- Application advance requires: contested roll at Standard+, novel challenge for tier, materially shaped scene
- Knowledge advance requires: an understanding event (forensic / observational / investigative / instructional / reflective / experimental / documentary)
- Field knowledge: same triggers as knowledge, applied to magical material; gated by domain score
- New tags require player confirmation before saving

---

## Reputation

Canonical: `prompts/world-rules.md`.

### Standing Bands

| Band | Range | Roll Modifier |
|---|---|---:|
| Revered | 61 to 100 | +10 |
| Respected | 21 to 60 | +5 |
| Neutral | −20 to 20 | +0 |
| Distrusted | −21 to −60 | −10 |
| Despised | −61 to −100 | −20 |

Clamp standing to ±100.

### Reputation Change by Scale

| Trigger | Standing Change |
|---|---:|
| Drift (faction-relevant beat without higher stake) | ±1 to ±2 |
| Local outcome with direct faction relevance | ±2 to ±3 |
| Situational outcome | ±5 |
| Regional outcome | ±15 |
| Campaign outcome | ±30 |

Drift and Local cannot cross a band boundary on their own — cap at one point inside the current band's nearer edge. Crossing requires Situational+.

### Party Reputation Formula

```
known_avg = mean standing of sapient party members with reputation entry for that faction
ratio = (known sapients with entry) / (total sapient party size)
party_rep = known_avg × ratio
```

Round toward 0. No entries → +0. Creature and Exceptional companions do not contribute.

---

## Economy

Canonical: `prompts/economy-rules.md`.

### Currency Storage and Narration

- Storage unit: CD (Copper Drake)
- 100 CD = 1 GD (Gold Drake)
- 10 GD = 1 PD (Platinum Drake)

### Narration Ranges

| Coin Amount | Narrate As |
|---|---|
| Under 1 GD | CD or SD |
| 1 to 99 GD | GD |
| 100 GD+ divisible by 10 | PD |
| 100 GD+ not divisible by 10 | GD |

### Wealth Tiers

`destitute` → `modest` → `comfortable` → `wealthy` → `affluent`

Persistent context, not arithmetic. Update only on material long-term shifts.

---

## Survival Bands

Canonical: `prompts/world-rules.md`.

### Hunger

`sated` → `hungry` → `starving`

### Hydration

`hydrated` → `thirsty` → `dehydrated`

### Fatigue (primary exertion economy)

`rested` → `tired` → `fatigued` → `exhausted`

### Load (abstract, not weight)

`light` → `normal` → `burdened` → `overloaded`

Update bands only at deterministic triggers: travel leg end, major exertion, deprivation window, resupply, long rest. Do not tick on routine actions.

---

## Character Creation

Canonical: `prompts/character-creation.md`.

### Starting Domain Budget

| Source | Points |
|---|---:|
| Ancestry base | 280 |
| Culture bonus | 10 |
| Background bonus | 10 |
| Player adjustment | 10 (max +5 per domain) |

Domain score range: 25–80. Cap: 80.

### Identity Field Limits

| Field | Max |
|---|---:|
| motivations | 3 |
| quirks | 3 |
| bonds | 3 |
| flaws | 3 |
| origin | 1 |
| wound | 1 |

All identity fields are optional.

---

## Canonical Taxonomies

### Domains (7)

| Domain | Governs |
|---|---|
| Power | Force, mass, leverage |
| Agility | Coordination, balance, speed |
| Perception | Senses, awareness, environment reading |
| Endurance | Stamina, resilience, recovery |
| Intellect | Reasoning, memory, deduction |
| Will | Discipline, concentration, oath endurance |
| Presence | Social weight, influence |

### Knowledge Groups (19)

Athletics (Power/Endurance), Mobility (Agility), Stealth (Agility),
Skulduggery (Agility), Awareness (Perception), Investigation (Perception/Intellect),
Tracking (Perception), Survival (Endurance), Nature (Perception),
Medicine (Intellect), Combat (Power), Warfare (Will/Intellect),
Craft (Intellect), Engineering (Intellect), Lore (Intellect),
Influence (Presence), Performance (Presence), Discipline (Will),
Arcana (Intellect)

### Combat Knowledge Groups (Canonical, 11)

Canonical: `prompts/combat-rules.md`.

`close_combat`, `melee`, `reach`, `ranged`, `mechanical`, `unconventional`, `martial_arts`, `light_armor`, `medium_armor`, `heavy_armor`, `shields`

### Armor Applications

Type-specific applications nested under their armor-class knowledge group:

- `light_armor` → `padded`, `leather`, `studded_leather`, `hide`
- `medium_armor` → `chain_shirt`, `scale_mail`, `breastplate`
- `heavy_armor` → `chain_mail`, `splint`, `plate`
- `shields` → `shield`
- `martial_arts` → `unarmored`

### Magical Fields (9)

| Field | Primary Domain |
|---|---|
| Sacred | Will |
| Warding | Will |
| Binding | Will |
| Elemental | Endurance |
| Druidry | Perception |
| Illusion | Presence |
| Runecraft | Intellect |
| Alchemy | Intellect |
| Necromancy | Intellect |

### Item Categories (6)

`weapon`, `armor`, `shield`, `ammunition`, `apparel`, `gear`

### Item Tiers (T0–T5)

Canonical: `prompts/items-rules.md` (Magical Item Tier Framework).

| Tier | Character |
|---|---|
| T0 | Mundane item from magical materials, no active magic |
| T1 | Minor magical effect, utility/flavor |
| T2 | Meaningful effect, can shift an encounter |
| T3 | Strong effect, clear strategic advantage |
| T4 | Major effect, named/near-named, politically significant |
| T5 | Legendary, mythic-scale, one-of-a-kind |

Item tier reflects impact, not how the item was made.

### Rarities

`common`, `uncommon`, `rare`, `very-rare`, `legendary`, `unique`

### Legality

`open`, `restricted`, `contraband`

### Wealth Tier Floors (soft hint)

`destitute`, `modest`, `comfortable`, `wealthy`, `affluent`

### Tool Roles

`permission` (item required for class of action), `difficulty-shift` (item meaningfully helps but not required)

---

## Companion Reliability

Canonical: `prompts/character-creation.md` (companion creation) and forthcoming `prompts/companion-rules.md`.

```
Reliability adjudicated narratively from:
  composure domain (25–60 scale)
  + training_level (untrained / basic / trained / expert)
  + bond_level (wary / accepting / bonded / devoted)
  + situational context
```

No dedicated reliability_under_stress field.

---

## Pacing Fields

Canonical: `prompts/world-rules.md`.

| Field | Type | Use |
|---|---|---|
| `tension` | 0–10 | Current scene pressure |
| `last_consequence_weight` | local/situational/regional/campaign | Most recent resolved consequence scale |
| `turns_since_social_beat` | int | Increments unless social beat occurs |
| `turns_since_discovery` | int | Increments unless discovery beat occurs |
| `turn_count` | int | Mirror of `world.turn` |

---

## Reference Files

- `prompts/engine.md` — runtime adjudication (instructions)
- `prompts/world-rules.md` — broader world/system rules
- `prompts/combat-rules.md` — combat resolution
- `prompts/magic-rules.md` — magic system
- `prompts/progression-rules.md` — tag advancement, AP, domain spend
- `prompts/difficulty-rules.md` — difficulty ladder and benchmarks
- `prompts/items-rules.md` — item categories and use rules
- `prompts/economy-rules.md` — coin, barter, transaction state
- `prompts/character-creation.md` — creation flow
- `prompts/scene-structure.md` — beat / encounter / scene / job vocabulary
- `prompts/calendar.md` — Oath Calendar and time tracking
