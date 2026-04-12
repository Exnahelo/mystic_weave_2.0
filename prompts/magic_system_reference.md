# Mystic Weave — Magic System Reference (Full Specification)

Magic extends existing competency mechanics. No separate infrastructure is introduced.
This is the canonical full specification for magical fields, spell/rite handling,
access bands, and magical failure outcomes.

---

## Core Structure

Magic has two tracks that work together:

### Magical Fields (Knowledge Tags)
- Broad areas of magical understanding.
- Use normal knowledge tier math (T1–T5, +1 per tier).
- Field tier determines what can be attempted safely.

### Individual Spells and Rites (Application Tags)
- Specific practiced workings inside a field.
- Use normal application tier math (T1–T5, +1 per tier).
- Improve through repeated consequential use, same as other application tags.

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

Cross-domain note:
- Some fields naturally cross domains by action risk.
- Example: Sacred may roll Will (concentration) or Presence (formal invocation).
- Example: Binding may roll Will (oath endurance) or Presence (commanded acknowledgment).
- If two domains are equally plausible, use the lower score.

---

## Access Model

Use this section in parity with `prompts/world_rules.md` Access Bands.

### Safe Use
- Caster has the relevant field knowledge tag and the specific spell/rite application tag.
- Roll normally.

### Risky Use
- Caster has the relevant field knowledge tag but not the specific spell/rite tag.
- Apply a **Hard** difficulty modifier on top of standard difficulty.
- On failure, apply **Strain** before narrative outcome.

### Dangerous Use
- Field tag absent entirely, or field tier below what the working requires.
- Apply **Extreme** or **Legendary** depending on distance beyond knowledge.
- On any failure degree, use **Backlash** outcomes instead of standard failure narration.

---

## Field Tier Access Ceilings

| Field Tier | Maximum safe spell tier | What becomes accessible |
|---|---|---|
| T1 | T1 spells only | Minor workings, basic blessings, first attempts |
| T2 | T2 spells | Reliable practice, stronger single-target effects |
| T3 | T3 spells | Formal rites, multi-target or sustained effects |
| T4 | T4 spells | Major sanctification, powerful warding, communal rites |
| T5 | T5 spells | Master-level workings, legendary effects |

Attempting above field tier is Dangerous Use even if spell tag tier is high.

---

## Failure Model

Use these labels exactly in narration and adjudication: Minor Miss, Strain,
Backlash, Catastrophic Failure.

### Minor Miss (Safe/Risky, partial failure or better)
- Working weakens, fizzles, or partially resolves.
- No lasting cost beyond reduced effect.

### Strain (Safe/Risky, failure band)
- Fatigue, pain, temporary instability, or lost time.
- Working fails; caster is impaired for the next sustained-magic roll until rest.

### Backlash (Dangerous any failure, or critical failure in any band)
Apply one or more outcomes:
- Damage
- Condition (temporary impairment)
- Corrupted effect (misfire/inversion/wrong target)
- Unwanted attention
- Sacred offense (for divine magic, reputation/access impact possible)
- Environmental instability

### Catastrophic Failure
- Roll 100 in Dangerous Use, or forbidden magic attempt.
- Consequences are permanent, irreversible, and character-scale world-altering.

---

## Breath Weapon (Innate, Separate from Learned Magic)

- Draconic breath is innate species capability, not a learned spell.
- No magical field tag is required.
- Uses `dragon_breath` application tag with Will or Power based on intent.

---

## Roll Formula (Unchanged)

`Target = Domain Score + Field Knowledge Tier + Spell/Rite Tag Tier + Difficulty Modifier`

The GPT selects:
1. One domain (primary failure risk)
2. One field knowledge tag
3. One spell/rite application tag
4. Standard difficulty plus access-band adjustment

Never stack multiple field tags or multiple spell tags on one roll.

---

## Spell and Rite Tag Examples

Canonical spell names and tier structures live in `data/spells.json`; always reference that file before accepting player-declared spell tags.

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
