# Mystic Weave — Magic Rules

Version 2.0 — April 2026
Status: Canonical. Upload to GPT builder as a knowledge file.

**Rename note:** the magical field formerly called **Nature** is now **Druidry** to avoid collision with the mundane **Nature** knowledge group.

---

## Purpose

This file contains the GPT-facing rules for how magic works in Mystic Weave.

It defines:
- the three-layer magic access system (domain → field knowledge → spell application)
- magical fields as knowledge tags
- individual spells and rites as application tags
- the spell resolution threshold system
- access bands for safe, risky, and dangerous casting
- magical failure outcomes

Structured spell catalogs belong in JSON data files under `data/magic/`, not here.

Use this file together with:
- per-field spell files under `data/magic/`
- `data/tags/magic_fields.json`
- `world-rules.md`
- `engine.md`
- `combat_rules.md` when magic is used during conflict
- `progression_rules.md` for tag advancement adjudication

---

## Core Structure

Magic extends the existing competency system. No separate mana pool, spell slot system, or hidden casting economy is introduced.

Magic has three linked layers:

### Layer 1 — Domain Score (Gates Field Knowledge)

A character's domain score determines the maximum field knowledge tier available in fields governed by that domain.

| Domain Score | Maximum Field Knowledge Tier |
|---|---|
| 40 | T1 |
| 50 | T2 |
| 60 | T3 |
| 70 | T4 |
| 80 | T5 |

A character with Will 53 can advance Sacred, Warding, or Binding knowledge up to T2 but not T3. Raising Will to 60 makes T3 available to unlock.

Domain score gates the ceiling. It does not automatically grant the knowledge tier — the character must still earn the advancement through use per `progression_rules.md`.

### Layer 2 — Field Knowledge (Gates Spell Access)

Magical fields are broad areas of magical understanding, tracked as knowledge tags.

| Field Knowledge Tier | Spells Accessible |
|---|---|
| T1 | Tier 1 spells in that field |
| T2 | Tier 1–2 spells in that field |
| T3 | Tier 1–3 spells in that field |
| T4 | Tier 1–4 spells in that field |
| T5 | Tier 1–5 spells in that field |

Field knowledge governs what a character can safely attempt. Attempting a spell above the field tier is Dangerous Use regardless of application tier.

Field knowledge tiers advance through meaningful consequential use, per `progression_rules.md`. They do not consume AP.

### Layer 3 — Spell Application (Determines Success)

Individual spells are application tags. The application tier determines how reliably the caster succeeds when casting that specific spell.

Spell application tiers advance through repeated consequential use, per `progression_rules.md`. They do not consume AP.

See **Spell Resolution** below for the threshold table.

---

## Magical Fields

| Field | Primary Domain | Governs |
|---|---|---|
| Sacred | Will | Devotional practice, liturgy, purification, consecration, divine invocation |
| Warding | Will | Protective barriers, seals, anti-corruption protocols, ward maintenance |
| Binding | Will | Oaths, pacts, compulsions, sworn duties, and channeled authority with magical weight |
| Elemental | Endurance | Raw elemental channeling through sustained output |
| Druidry | Perception | Druidic and biome magic, ley-flow, living systems |
| Illusion | Presence | Constructed perception, false images, sensory manipulation |
| Runecraft | Intellect | Inscribed magical structures: runes, glyphs, sigils, permanent enchantment |
| Alchemy | Intellect | Magical compound preparation, transmutation, reagent work |
| Necromancy | Intellect | Death energy, undead interaction, life-force manipulation |

### Cross-Domain Rule

Some magical fields may roll through more than one plausible domain depending on the action and context.

Examples:
- Sacred may use **Will** for concentration or **Presence** for formal invocation
- Binding may use **Will** for oath endurance or **Presence** for command recognition
- Elemental may lean toward **Power** in aggressive output contexts

If two domains are equally plausible, use the lower score.

The cross-domain rule affects which domain is used for the spell roll's situational context. It does **not** affect which domain gates the field knowledge tier — that is always the field's primary domain.

---

## Spell Resolution

Spell rolls use a **fixed threshold** determined by the caster's application tier with that specific spell. This is a separate formula from the standard competency roll used for non-spell actions.

### Spell Threshold Table

| Application Tier | Target Number | Success Rate |
|---|---|---|
| T1 | 55 | 55% |
| T2 | 65 | 65% |
| T3 | 75 | 75% |
| T4 | 85 | 85% |
| T5 | 95 | 95% |

Roll d100 via `POST /roll`. Success if roll ≤ target.
Roll 1 = critical success.
Roll 100 = critical failure.

### Situational Modifiers

Situational conditions may shift the target by up to ±10.

| Condition | Modifier |
|---|---|
| Ideal conditions (calm, prepared, sanctified space, ritual support) | +5 |
| Standard conditions | +0 |
| Hostile conditions (active combat, environmental pressure, interruption) | −5 |
| Extreme conditions (catastrophic environment, active counterspell, grievous injury) | −10 |

A T3 caster under hostile conditions rolls against 75 − 5 = 70.
A T1 caster in ideal conditions rolls against 55 + 5 = 60.

### What Does Not Enter The Spell Roll

Domain score and field knowledge tier do **not** contribute to the spell target number. They gate access only.

The standard competency roll formula (`Domain + Knowledge Tier + Application Tier + Difficulty Modifier`) is used for non-spell contested actions. Spell rolls use the threshold table above.

### Magic-Adjacent Non-Spell Actions

Actions that involve magical knowledge but are not spell-casting — such as identifying a magical inscription, resisting a magical effect, analyzing an enchantment, or maintaining concentration under pressure — still use the standard roll formula with the relevant domain and tags.

---

## Access Model

Magic use follows three access bands.

### Safe Use

Use Safe Use when:
- the caster has the relevant field knowledge tag
- the caster has the specific spell application tag
- the spell's catalog tier does not exceed the caster's field knowledge tier

Adjudication:
- use the spell threshold table
- apply situational modifiers if relevant

### Risky Use

Use Risky Use when:
- the caster has the relevant field knowledge tag
- the caster does **not** have the specific spell application tag
- the attempted working is still within the caster's field knowledge tier ceiling

Adjudication:
- determine one final target by applying a **−10** access penalty to the spell threshold, then adjust for situational modifiers if relevant
- on failure, apply **Strain** before resolving narrative consequences

A character with Sacred T2 attempting a T2 spell they have never practiced: base threshold is 55 (T1 application assumed for untrained), adjusted to a final target of 45 before any situational modifier. Unreliable, as intended.

### Dangerous Use

Use Dangerous Use when:
- the caster lacks the relevant field knowledge tag entirely
- or the attempted working exceeds the field knowledge tier ceiling
- or the magic is forbidden, unstable, or clearly beyond the caster's established competence

Adjudication:
- determine one final target by applying a **−20** access penalty to the spell threshold, then adjust for situational modifiers if relevant
- on any failure degree, resolve using **Backlash** outcomes rather than ordinary failure narration

### Access Band Summary

| Band | Field Tag? | Spell Tag? | Within Ceiling? | Threshold Penalty |
|---|---|---|---|---|
| Safe | Yes | Yes | Yes | None |
| Risky | Yes | No | Yes | −10 |
| Dangerous | No, or over ceiling | — | — | −20 |

---

## Failure Model

Use these labels exactly in narration and adjudication:

- **Minor Miss**
- **Strain**
- **Backlash**
- **Catastrophic Failure**

### Minor Miss

Use for:
- Safe or Risky use
- partial failure, weak success, or reduced outcome

Results:
- the working weakens
- the effect partially resolves
- the spell fizzles, slips, or underperforms
- no lasting cost beyond reduced effect unless context demands otherwise

### Strain

Use for:
- Safe or Risky use failures where the magic does not fully misfire into backlash

Results may include:
- fatigue
- pain
- temporary instability
- lost time
- reduced magical control

The working fails, and the caster is impaired for the next sustained-magic roll until rest or stabilization.

### Backlash

Use for:
- any Dangerous Use failure
- or severe/critical failure in any band if the fiction warrants escalation

Apply one or more of the following:
- damage
- temporary condition or impairment
- corrupted effect
- wrong target
- inversion or misfire
- unwanted attention
- sacred offense
- environmental instability
- ward disturbance
- magical contamination

### Catastrophic Failure

Use for:
- roll 100 in Dangerous Use
- or clearly forbidden or catastrophic magical overreach

Results should be:
- permanent or extremely difficult to reverse
- character-scale or scene-scale world-altering
- never trivialized

---

## Spell Catalog Structure

Each magical field has a pyramid of spells:

| Tier | Spells Per Field | Character |
|---|---|---|
| T1 | 5 | Foundational tools — minor, practical, daily-use workings |
| T2 | 4 | Applied techniques — real tactical and situational value |
| T3 | 3 | Formal and decisive workings — scene-changing |
| T4 | 2 | Major site- or scene-shaping powers |
| T5 | 1 | Apex expression — mythic-scale capstone |

Total: 15 spells per field, 135 spells across 9 fields.

Each spell has a fixed tier. A T3 spell is always T3. It does not scale. The character's growth comes from improving their application tier with that spell (T1 → T5 mastery), not from the spell becoming more powerful.

Canonical spell data lives in per-field JSON files under `data/magic/`.

---

## GPT Spell Resolution Procedure

When a character attempts to cast a spell:

1. **Verify field access.** Does the caster have the field knowledge tag? If not → Dangerous Use.
2. **Verify tier access.** Is the spell's catalog tier within the caster's field knowledge tier? If not → Dangerous Use.
3. **Verify spell tag.** Does the caster have the specific spell application tag? If not → Risky Use. If yes → Safe Use.
4. **Determine application tier.** Look up the caster's application tier for this spell. If Risky Use (no tag), treat as T1.
5. **Look up base threshold** from the spell threshold table.
6. **Determine one final target** by applying the access-band penalty (none / −10 / −20) and then any situational modifier (±5 to ±10 based on conditions).
7. **Send final target to `POST /roll`.**
8. **Narrate outcome** using the failure model if the roll fails.

---

## GPT Magic Conduct Rules

1. **Magic extends existing competency logic.** No separate subsystem.
2. **Domain gates field knowledge.** Check the domain-gating table before allowing field advancement.
3. **Field knowledge gates spell access.** A caster cannot safely attempt spells above their field tier.
4. **Application tier determines success.** Use the threshold table, not the standard roll formula.
5. **Use the standard roll formula for non-spell magical actions** (identification, resistance, concentration, analysis).
6. **Use failure labels consistently.** Minor Miss, Strain, Backlash, and Catastrophic Failure are the canonical failure bands.
7. **Respect context.** Sacred, forbidden, unstable, communal, ritual, battlefield, and environmental contexts all affect how magic is narrated.
8. **Do not invent spells.** Reference the canonical spell data files before accepting or resolving a player-declared spell. Do not fabricate spells if structured data already exists.
9. **Do not invent extra infrastructure.** No mana pool, spell slot system, or hidden casting economy unless another rules file explicitly introduces it.

---

## Placeholder — Ritual Scaling

Placeholder.

This section will eventually define how the GPT should handle:
- multi-caster rites
- communal rituals
- long-duration sacred works
- complex ward maintenance
- formal ceremonial casting

---

## Placeholder — Magic in Combat

Placeholder.

This section will eventually define how spell interruption, casting under pressure, magical defense, and hostile magical exchange interact with combat resolution.

---

## Placeholder — Enchantment and Permanent Works

Placeholder.

This section will eventually define:
- long-term enchantment
- rune permanence
- magical crafting thresholds
- stable vs unstable magical objects

---

## Reference Files

- `data/tags/magic_fields.json` — canonical field definitions
- `data/magic/{field}.json` — per-field spell catalogs (sacred, warding, binding, elemental, druidry, illusion, runecraft, alchemy, necromancy)
- `world-rules.md` — broader world/system-facing rules (contains a summarized magic section that must stay in sync with this file)
- `combat_rules.md` — combat-facing interpretation when magic enters conflict
- `engine.md` — runtime system logic and adjudication guidance
- `progression_rules.md` — tag advancement adjudication rules

---

## Summary

Magic in Mystic Weave is governed by three layers: domain score gates field knowledge, field knowledge gates spell access, and spell application tier determines success through a fixed threshold table. Safe casting uses the threshold directly. Risky and Dangerous use apply penalties. Failure consequences escalate by access band. The standard competency roll formula is reserved for non-spell actions. No separate magic engine exists.