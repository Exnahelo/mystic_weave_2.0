# Mystic Weave — Magic Rules

Version 1.0 — April 2026  
Status: Canonical. Upload to GPT builder as a knowledge file.

---

## Purpose

This file contains the GPT-facing rules for how magic works in Mystic Weave.

It defines:
- magical fields as knowledge tags
- individual spells and rites as application tags
- access bands for safe, risky, and dangerous casting
- magical failure outcomes
- the roll structure used when adjudicating magic

Structured spell catalogs belong in JSON data files, not here.

Use this file together with:
- `magic_spells.json` or the current spell data files
- `world_rules.md`
- `engine.md`
- `combat_rules.md` when magic is used during conflict

---

## Core Structure

Magic extends the existing competency system. No separate magic infrastructure is introduced.

Magic has two linked layers:

### Magical Fields (Knowledge Tags)

Magical fields are broad areas of magical understanding.

- Use normal knowledge tier math (T1–T5, +1 per tier)
- Field tier determines what can be attempted safely
- Field knowledge reflects understanding, training, and safe access

### Individual Spells and Rites (Application Tags)

Spells and rites are specific practiced workings within a field.

- Use normal application tier math (T1–T5, +1 per tier)
- Improve through repeated consequential use, same as other application tags
- A caster may understand a field broadly without being equally practiced in every spell within it

---

## Magical Fields

| Field | Primary Domain | Governs |
|---|---|---|
| Sacred | Will | Devotional practice, liturgy, purification, consecration, divine invocation |
| Warding | Will | Protective barriers, seals, anti-corruption protocols, ward maintenance |
| Binding | Will | Oaths, contracts, compulsions, sworn duties with magical weight |
| Elemental | Endurance | Raw elemental channeling through sustained output |
| Nature | Perception | Druidic and biome magic, ley-flow, living systems |
| Arcane Theory | Intellect | Structured arcane architecture, runes, formulae, spell engineering |
| Illusion | Intellect | Constructed perception, false images, sensory manipulation |
| Runecraft | Intellect | Inscribed magical structures, glyphs, permanent enchantment work |
| Necromancy | Intellect | Death energy, undead interaction, life-force manipulation |
| Alchemy | Intellect | Magical compound preparation, transmutation, reagent work |
| Invocation | Presence | Channeling through authority, formal command, public rites, entity interaction |

### Cross-Domain Rule

Some magical fields may roll through more than one plausible domain depending on the action and risk.

Examples:
- Sacred may use **Will** for concentration or **Presence** for formal invocation
- Binding may use **Will** for oath endurance or **Presence** for command recognition
- Elemental may sometimes lean toward **Power** in aggressive output contexts if the broader rules allow it

If two domains are equally plausible, use the lower score.

---

## Access Model

Magic use follows three access bands.

### Safe Use

Use Safe Use when:
- the caster has the relevant field knowledge tag
- the caster has the specific spell or rite application tag
- the spell tier does not exceed the field tier’s safe ceiling

Adjudication:
- roll normally

### Risky Use

Use Risky Use when:
- the caster has the relevant field knowledge tag
- the caster does **not** have the specific spell or rite application tag
- the attempted working is still within the caster’s field access ceiling

Adjudication:
- apply **Hard** difficulty on top of the base difficulty
- on failure, apply **Strain** before resolving narrative consequences

### Dangerous Use

Use Dangerous Use when:
- the caster lacks the relevant field knowledge tag entirely
- or the attempted working exceeds the field tier’s safe access ceiling
- or the magic is forbidden, unstable, or clearly beyond the caster’s established competence

Adjudication:
- apply **Extreme** or **Legendary** difficulty depending on how far beyond safe access the attempt is
- on any failure degree, resolve using **Backlash** outcomes rather than ordinary failure narration

---

## Field Tier Access Ceilings

| Field Tier | Maximum Safe Spell Tier | What becomes safely accessible |
|---|---|---|
| T1 | T1 | Minor workings, first blessings, basic practical magic |
| T2 | T2 | Reliable practice, stronger single-target effects |
| T3 | T3 | Formal rites, sustained effects, multi-target workings |
| T4 | T4 | Major sanctification, stronger warding, communal rites |
| T5 | T5 | Master-level workings, legendary magical effects |

Attempting a spell above the field tier is Dangerous Use even if the application tag is high.

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

## Breath Weapon

### Breath Weapon (Innate, Separate from Learned Magic)

Draconic breath is innate species capability, not a learned spell.

Rules:
- no magical field knowledge tag is required
- use `dragon_breath` as the application tag
- use **Will** or **Power** based on intent and the broader action framing

This is separate from learned magical practice.

---

## Roll Formula

`Target = Domain Score + Field Knowledge Tier + Spell/Rite Tag Tier + Difficulty Modifier`

The GPT should select:

1. one domain
2. one field knowledge tag
3. one spell or rite application tag
4. base difficulty plus any access-band adjustment

Never stack multiple field tags or multiple spell tags on a single roll.

---

## Spell Data Authority

Canonical spell names, tiers, and structured spell definitions belong in spell data files.

The GPT should always reference the authoritative spell data before accepting or resolving a player-declared spell tag.

Do not invent canonical spells if structured spell data already exists.

---

## GPT Magic Conduct Rules

1. **Use the normal competency system first.**  
   Magic extends existing knowledge/application logic rather than replacing it.

2. **Field knowledge governs safety.**  
   Spell familiarity alone is not enough if the caster lacks the field.

3. **Application tags govern practiced precision.**  
   Knowing a field does not mean automatic fluency in every spell.

4. **Do not invent extra infrastructure.**  
   No separate mana pool, spell slot system, or hidden casting economy should be added unless another rules file explicitly introduces it.

5. **Use failure labels consistently.**  
   Minor Miss, Strain, Backlash, and Catastrophic Failure are the canonical failure bands.

6. **Respect context.**  
   Sacred, forbidden, unstable, communal, ritual, battlefield, and environmental contexts all affect how magic is narrated.

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

- `magic_spells.json` or current spell data files — canonical spell catalog
- `world_rules.md` — broader world/system-facing rules
- `combat_rules.md` — combat-facing interpretation when magic enters conflict
- `engine.md` — runtime system logic and adjudication guidance

---

## Summary

Magic in Mystic Weave is not a separate engine. It is an extension of the existing competency system through magical fields as knowledge tags and spells or rites as application tags. Safe access depends on field knowledge, practiced casting depends on application tags, and failure consequences escalate according to access band and context.