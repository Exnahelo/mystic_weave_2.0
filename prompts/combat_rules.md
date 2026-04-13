# Mystic Weave — Combat Rules

Version 1.0 — April 2026  
Status: Active rules scaffold. Expand as combat systems are finalized.

---

## Purpose

This file contains GPT-facing rules for combat interpretation, combat equipment handling, and future combat subsystems.

It is intentionally lighter than a full combat engine document. Use it as the current rule spine for equipment and as the placeholder shell for the rest of the combat system.

Structured equipment catalogs belong in JSON data files, not here.

Use this file together with:
- `items-weapons.json`
- `items-armor.json`
- `items-ammunition.json`
- `items-mundane.json`
- 'items-notable.json'
- `world_rules.md`
- `engine.md`

---

## Combat Equipment Rules

### Armor Rules

Armor affects mobility by category, not by hyper-detailed simulation.

- **Unarmored** — no Agility difficulty impact; some characters intentionally build around this state
- **Light armor** — no Agility difficulty impact under normal conditions
- **Medium armor** — GPT applies judgment; Agility difficulty may increase one step in demanding physical contexts
- **Heavy armor** — Agility difficulty increases one step as a baseline; two steps in demanding physical contexts

The GPT should interpret armor category first, then context. Do not invent granular penalties beyond what the system supports.

### Shield Rule

A shield is a single catalog entry. Size and type are narrative descriptors handled at runtime rather than separate item classes unless later rules say otherwise.

Use common sense:
- a tower shield impedes movement more than a buckler
- a buckler imposes less practical burden than a full body-covering shield
- shield narration should reflect described size, handling, and context

### Weapon Knowledge and Application Rule

Weapons operate on two linked layers:

- **Knowledge tag** — the broad family of weapon use a character understands
- **Application tag** — the specific weapon a character becomes practiced with over time

The current weapon knowledge tags are:
- grappling
- melee
- reach
- ranged
- mechanical
- unconventional

The GPT should treat these as the primary handling categories for weapon familiarity.

The application tag is the actual weapon itself, such as:
- knife
- dagger
- sword
- halberd
- shortbow
- light_crossbow
- whip

A character may understand a weapon family through knowledge without being equally practiced in every application within that family.

### Weapon Matching Rule

Match the weapon to its **knowledge tag** and **application tag** based on what it is and how it is being used.

Do not rely on name alone when context changes the function.

When a weapon could plausibly overlap categories, use the category that best reflects how it is being employed in the moment.

Examples:
- a knife used in tight close-quarters fighting is grappling / knife
- a net used to restrain rather than harm is unconventional / net
- a chain used as an improvised striking-control weapon is unconventional / chain

### Ammunition Rule

Ammunition is treated as a compatible resource, not as a knowledge/application proficiency object.

Use ammunition records to determine:
- what weapon it works with
- whether it is standard or special ammunition
- whether it is narratively recoverable
- whether it is treated as expended or scene-recoverable
- what tag-based special effect it carries, if any

For ordinary ammunition, recovery is contextual. A fired arrow or bolt is not always permanently lost, but it is not automatically reusable either. The GPT should judge based on terrain, impact, breakage, urgency, and scene outcome.

Special ammunition should be interpreted through its tags and `special_effect_tag`, not through invented hard mechanics unless later rules define them.

### Equipment Catalog Authority

The item catalogs are authoritative for:
- names
- prices
- equipment categories
- knowledge/application structure for weapons and armor
- ammunition compatibility

Do not invent alternate catalog entries when a listed item already exists.

---

## Combat Resolution

Placeholder.

This section will eventually define how the GPT should interpret attack flow, resolution sequencing, contested actions, consequences, and failure states.

---

## Damage and Harm

Placeholder.

This section will eventually define harm interpretation, injury pressure, recovery framing, and any distinctions between superficial harm, serious wounds, and incapacitation.

---

## Positioning, Range, and Reach

Placeholder.

This section will eventually define how the GPT should reason about distance, engagement range, reach advantage, movement pressure, and environmental control in combat scenes.

---

## Improvised Combat and Environmental Violence

Placeholder.

This section will eventually define how the GPT should handle improvised weapons, terrain-based harm, falling, fire, collapsing structures, and similar non-catalog combat factors.

---

## Magic in Combat

Placeholder.

This section will eventually define how spell use, magical interruption, magical defense, and hazardous casting interact with the combat system.

---

## Social and Psychological Pressure in Combat

Placeholder.

This section will eventually define fear, intimidation, surrender pressure, morale collapse, hesitation, and similar non-physical combat dynamics.

---

## Mounted and Large-Creature Combat

Placeholder.

This section will eventually define mounted combat, large-body reach problems, mobility differences, and how unusual combat scales should be interpreted.

---

## GPT Combat Conduct Rules

Until fuller combat rules are finalized, follow these principles:

1. **Use existing system categories before improvising new ones.**
2. **Read equipment through the item data files, not old archived reference prose.**
3. **Apply context-sensitive judgment, but do not invent unsupported subsystems.**
4. **Treat knowledge/application as meaningful for weapons and armor, but not for ammunition.**
5. **When uncertain, stay consistent with prior session interpretation rather than escalating complexity mid-scene.**

---

## Reference Files

- `items-weapons.json` — authoritative weapon catalog
- `items-armor.json` — authoritative armor and shield catalog
- `items-ammunition.json` — authoritative ammunition catalog
- `items-mundane.json` — broader mundane equipment catalog
- 'items-notable.json'
- `world_rules.md` — world/system-facing rules outside combat-specific handling
- `engine.md` — broader runtime logic and system interpretation

---

## Summary

For now, this file defines how the GPT should interpret combat equipment and preserves a clean place to grow the rest of the combat system. Weapon and armor handling should follow knowledge/application logic. Ammunition should be treated as a compatible resource with narrative recoverability. Additional combat subsystems should be added here as they are canonized.
