# Mystic Weave — Combat Rules

Version 1.1 — April 2026  
Status: Active rules scaffold. Expand as combat systems are finalized.

---

## Purpose

This file contains GPT-facing rules for combat interpretation, combat equipment handling, and future combat subsystems.

It is intentionally lighter than a full combat engine document. Use it as the current rule spine for equipment and as the placeholder shell for the rest of the combat system.

Structured equipment catalogs belong in JSON data files, not here.

Use this file together with:
- `data/items/weapon.json`
- `data/items/armor.json`
- `data/items/ammunition.json`
- `data/items/gear.json`
- `character-rules.md`
- `engine.md`

---

## Combat Equipment Rules

### Armor Rules

Armor affects mobility by category, not by hyper-detailed simulation.

- **Unarmored** — no Agility difficulty impact; some characters intentionally build around this state. Unarmored fighting is governed by the `martial_arts` knowledge group, not by a separate unarmored knowledge group.
- **Light armor** — no Agility difficulty impact under normal conditions
- **Medium armor** — GPT applies judgment; Agility difficulty may increase one step in demanding physical contexts
- **Heavy armor** — Agility difficulty increases one step as a baseline; two steps in demanding physical contexts

The GPT should interpret armor category first, then context. Do not invent granular penalties beyond what the system supports.

### Shield Rule

There is currently one shield entry in the catalog. Shield contributes to pre-combat HP through its floor and ceiling values just like armor does, with ceiling 30 and floor 5. Narrative descriptors of shield size or type may be mentioned by the narrator, but they do not affect mechanics.

### Weapon and Armor Knowledge and Application Rule

Combat operates on two linked layers:

- **Knowledge tag** — the broad family of combat use a character understands
- **Application tag** — the specific weapon, armor class, or technique a character becomes practiced with over time

The canonical knowledge tags for combat are:

- `close_combat` — short-range body-and-implement combat
- `melee` — standard one-handed and two-handed weapon combat
- `reach` — extended-reach weapon combat
- `ranged` — projectile combat (bows, thrown, sling)
- `mechanical` — engineered ranged combat (crossbows, rigged shot)
- `unconventional` — improvised, exotic, or non-standard weapon use
- `martial_arts` — disciplined unarmed combat traditions; includes unarmored fighting
- `armor` — armor and shield handling

The GPT should treat these as the primary handling categories for combat familiarity.

The application tag is the specific implement or class within the family. Weapon applications include items such as:

- knife
- dagger
- sword
- halberd
- shortbow
- light_crossbow
- whip

Armor knowledge groups (each with type-specific applications nested under it):

- `light_armor` — applications: `padded`, `leather`, `studded_leather`, `hide`
- `medium_armor` — applications: `chain_shirt`, `scale_mail`, `breastplate`
- `heavy_armor` — applications: `chain_mail`, `splint`, `plate`
- `shields` — applications: `shield` (additional shield types may be added later)

The `unarmored` application sits under the `martial_arts` knowledge group.

A character may understand an armor class through the knowledge group without being equally practiced in every specific armor type within it.

### Weapon Matching Rule

Match the weapon to its **knowledge tag** and **application tag** based on what it is and how it is being used.

Do not rely on name alone when context changes the function.

When an improvised or non-catalog item is used as a weapon, match it to the knowledge and application tags that best reflect how it is being employed. Catalog weapons carry fixed knowledge and application tags and are not reclassified mid-scene.

Examples:
- a net used to restrain rather than harm is unconventional / net
- a chain used as an improvised striking-control weapon is unconventional / chain

### Ammunition Rule

Ammunition is a damage modifier, not a proficiency layer. Standard ammunition contributes no bonus; special ammunition adds its `damage_modifier` value to the attack's damage when it lands.

Special ammunition is not recoverable. Standard ammunition recoverability is governed per-item by the catalog's `recoverable` field; the narrator should follow the field rather than improvise.

Use ammunition records to determine:
- what weapon the ammunition works with (`used_with`)
- whether the ammunition is standard or special (`ammo_class`)
- the damage modifier the ammunition contributes (`damage_modifier`)
- whether standard ammunition is recoverable in principle (`recoverable`)
- what tag-based narrative effect the ammunition carries, if any (`special_effect_tag`)

Tag-based effects continue to guide narration but do not produce hard mechanical outcomes beyond the damage modifier unless a later rules section defines them.

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

Combat uses backend-authoritative rolls and a fixed-threshold model that mirrors spell resolution. The narrator does not decide hit, damage, or HP outcomes independently — those are returned by the backend.

### Attack Sequence

An attack resolves in up to two rolls:

**Roll 1 — Does the attack land?**
- d100 roll-under against the attacker's weapon application tier threshold.
- Thresholds: T0=45, T1=55, T2=65, T3=75, T4=85, T5=95.
- The attacker's tier is read from their application tag for the specific weapon in use (e.g., `sword`, `shortbow`, `dagger`). If the character has no application tag for the weapon, treat as T0.
- **Nat 1:** critical hit. Skip to damage resolution with a 3× multiplier applied after all other calculation.
- **Nat 100:** fumble. Attack misses. Attacker takes 5–10 rebound damage (backend determines exact value). End of attack.
- **Miss:** attack ends, no damage.
- **Hit:** continue to Roll 2.

**Unarmored evasion modifier:** If the defender is unarmored, the attacker's Roll 1 threshold is reduced by (defender's `martial_arts` knowledge tier × 5). T5 martial_arts defender vs. T1 weapon attacker: 55 − 25 = 30.

**Roll 2 — How much damage?**
- Both attacker and defender roll d100. Higher is better for each side.
- Tie: damage = 0 (attack is deflected, dueling critical).
- Margin = attacker_roll − defender_roll.
- Raw damage = `max(0, weapon_base_damage × (1 + margin / 100))`.
  - If attacker wins (margin > 0), damage scales up.
  - If defender wins (margin < 0), damage is reduced. At margin −100, damage is 0.
- Add special ammunition damage_modifier if applicable.
- Apply critical multiplier from Roll 1 if the nat 1 crit fired (damage × 3).
- Apply defender's agility damage reduction: final damage × (1 − agility_tier × 0.10). T3 agility reduces damage by 30%.

Neither attacker nor defender adds any skill modifier to Roll 2. It is a raw d100 dueling roll.

### HP and Armor

Base HP = 100 for all characters.

Pre-combat HP is computed by the backend from:

```
max_hp = 100 + armor_contribution + shield_contribution
armor_contribution = armor_floor + (armor_ceiling − armor_floor) × (armor_tier / 5)
shield_contribution = shield_floor + (shield_ceiling − shield_floor) × (shield_tier / 5)
```

Where:
- `armor_floor` and `armor_ceiling` are from the worn armor's catalog entry.
- `armor_tier` is the character's **knowledge group** tier for the armor class in use — read from `character.knowledge.{light_armor|medium_armor|heavy_armor}.tier`. T0 if untrained. (The application tier of the specific armor type — `padded`, `chain_shirt`, `plate`, etc. — is parent-cap'd to the group tier and available for narrative texture, but `armor_tier` for HP computation is the group tier.)
- `shield_floor` and `shield_ceiling` are from the shield catalog entry (5 and 30).
- `shield_tier` is the character's knowledge group tier for `shields` — read from `character.knowledge.shields.tier`. T0 if untrained. Omit the entire shield contribution if no shield is equipped.
- Unarmored contributes no HP (floor=0, ceiling=0). Unarmored defense is evasion-based, applied to Roll 1 instead via the `martial_arts` knowledge tier (the `unarmored` application sits under `martial_arts`).

### Dual Wielding

If the character attacks with a weapon in their off-hand, that attack uses half of the weapon's base damage (rounded down). Roll 1 is unchanged. Dominant-hand attacks use full base damage normally.

The system does not currently enforce which hand holds which weapon beyond this rule; the narrator may describe dual-wield sequences but backend damage calculation is per-attack and uses the declared weapon's full or halved base damage accordingly.

### Critical Hit (Nat 1 on Roll 1)

Critical hit skips Roll 2's normal computation and applies a flat 3× multiplier to the weapon's base damage. Special ammunition damage modifier is added after the multiplier. Agility damage reduction still applies.

### Fumble (Nat 100 on Roll 1)

Attack misses. Attacker takes between 5 and 10 rebound damage as determined by the backend. No Roll 2 occurs. Agility reduction does not apply to rebound damage.

### What The Narrator Does Not Do

- The narrator does not decide whether an attack hits. `POST /roll` (or the combat resolution endpoint, when introduced) decides.
- The narrator does not decide damage values. The backend returns them.
- The narrator does not modify HP. The backend updates it.
- The narrator does not invent crit effects beyond the 3× multiplier.
- The narrator does not apply situational modifiers to combat rolls. Situational modifiers are not in combat v1.0.

The narrator describes the action, the impact, and the consequences. The numbers come from the backend.

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

---

## Reference Files
- `data/items/weapon.json` — authoritative weapon catalog
- `data/items/armor.json` — authoritative armor and shield catalog
- `data/items/ammunition.json` — authoritative ammunition catalog
- `data/items/gear.json` — broader gear and mundane equipment catalog
- `character-rules.md` — character/system-facing rules outside combat-specific handling
- `engine.md` — broader runtime logic and system interpretation

---

## Summary

Combat v1.0 defines backend-authoritative resolution using two rolls per attack, fixed-threshold hit mechanics mirrored from magic spell resolution, a contested-roll damage model with agility-based reduction, and pre-combat HP derived from armor and shield floor/ceiling values combined with skill tier. Ammunition is a damage modifier, not a proficiency layer. Weapon and armor knowledge follows the canonical taxonomy: `close_combat`, `melee`, `reach`, `ranged`, `mechanical`, `unconventional`, `martial_arts`, `light_armor`, `medium_armor`, `heavy_armor`, and `shields` as knowledge groups, with type-specific armor applications nested under each armor class (e.g., `padded`/`leather`/`studded_leather`/`hide` under `light_armor`). The `unarmored` application sits under `martial_arts`. Additional combat subsystems (positioning, magic in combat, mounted combat, etc.) remain placeholders for future canonization.
