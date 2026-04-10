# Mystic Weave — Magic System Reference

This document defines how magic is adjudicated at runtime. It extends `prompts/world_rules.md` and must not override core roll math.

## Core Resolution Rule

All magical actions use the same roll framework:

`Target = Domain Score + Knowledge Tier + Application Tier + Difficulty Modifier`

Runtime constraints:
- Select exactly **one** domain.
- Select at most **one** knowledge tag and **one** application tag.
- Do not stack multiple knowledge or multiple application tags.
- If uncertain whether a tag applies, do not apply it.

## Domain Mapping for Magic Use

Use the domain that best matches failure risk, not flavor text.

| Domain | Use for magical actions where primary risk is... |
|---|---|
| Intellect | Incorrect arcane theory, bad runic structure, unstable spell architecture |
| Will | Loss of control, concentration break, psychic/spiritual overload, ward maintenance |
| Presence | Channeling through authority/oath/social force, public rites, commanding entities |
| Perception | Reading magical signatures, tracking ley-flow, spotting distortions/curses |
| Endurance | Sustained channeling under pain/fatigue/environmental pressure |
| Agility | Precision gesture sequences, fast reactive casting in motion |
| Power | High-force channeling where raw output and containment are the key risk |

Tie-break rule: if two domains are equally plausible, choose the lower domain score.

## Magic-Relevant Knowledge Tags

These are existing canonical knowledge tags applied to magical contexts:

- **Arcana (Intellect):** theory, schools, spell structure, magical diagnostics
- **History (Intellect):** old rites, legacy wards, historical spellcraft conventions
- **Engineering (Intellect):** runic constructs, magical devices, containment frameworks
- **Linguistics (Intellect):** true names, dead tongues, binding syntax
- **Warding (Will):** barriers, seals, anti-corruption protocols
- **Discipline (Will):** controlled channeling, suppression of backlash
- **Meditation (Will):** stabilizing focus for long/complex rituals
- **Insight (Perception):** reading intent/signature in intelligent magic phenomena
- **Nature (Perception):** druidic/biome magic, ley-flow tied to terrain
- **Command (Presence):** formal invocation through recognized authority structures

## Magic-Relevant Application Tags

These are existing application tags used for magical execution:

- **Arcane Implements (Intellect):** staves, foci, attuned tools, precision channeling
- **Herbalism & Alchemy (Intellect):** reagents, catalysts, stabilizers, ritual compounds
- **Sacred Rites (Will):** consecration, purification, oaths, divine-liturgical frameworks
- **Musical Instruments (Presence):** resonance-based casting, cadence-bound rituals

Item `roll_tag` handling remains canonical: matching `roll_tag` is contextual legitimacy, not extra numeric bonus.

## Effect-Scale Difficulty Ladder (Magic)

Use this ladder when calibrating magical effect scale. Then adjust for environment, time pressure, opposition, and instability.

| Effect Scale | Typical Scope | Base Difficulty |
|---|---|---|
| Minor utility | Light, spark, brief illusion, harmless cantrip-like effect | Easy (+15) |
| Controlled practical | Reliable single-target utility, minor ward, short-range detection | Standard (+10) |
| Tactical field use | Combat-relevant cast, active counterspell, fast ritual under pressure | Hard (+5) |
| Major ritual | Multi-step rite, broad area influence, durable magical alteration | Severe (+0) |
| High-risk arcana | Forbidden/volatile energies, unstable bindings, hostile ley interference | Extreme (-10) |
| Legendary working | Valley-scale shifts, mythic wards, ancient relic-grade effects | Legendary (-20) |

## Consequence Guidance for Magical Failure

Use roll `degree` + narrative logic; preserve world continuity.

- **Partial failure:** diminished effect, short duration, visible strain, costly side effect
- **Failure:** intended effect fails; introduces immediate complication or exposure
- **Critical failure:** backlash, corruption spread, shattered focus, collateral narrative consequence

Never retcon magical outcomes. Save durable magical changes to state/location records.
