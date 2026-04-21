# Mystic Weave — Item Rules

Version 1.0 — April 2026
Status: Canonical. Upload to GPT builder as a knowledge file.

---

## Purpose

This file contains the GPT-facing rules for how items should be interpreted, selected, narrated, and applied during play.

It does **not** duplicate item catalogs. Structured item definitions live in JSON data files.

Use this file together with:

* `data/items/ammunition.json`
* `data/items/apparel.json`
* `data/items/armor.json`
* `data/items/gear.json`
* `data/items/magical.json`
* `data/items/notable.json`
* `data/items/weapons.json`
* `combat-rules.md`
* `economy-rules.md`
* `world-rules.md`
* `engine.md`

---

## Item Catalog Authority

The JSON item files are authoritative for:

* item names
* item categories
* tags
* roll tags
* rarity
* price fields
* ammunition compatibility
* knowledge/application structure where relevant
* consumable state
* narrative effects

Do not invent alternate catalog entries when a listed item already exists.

If a needed item is not listed, the GPT may infer a nearest comparable only when:

* no listed equivalent exists
* the inference stays consistent with current item logic
* the item does not contradict established world or system rules

---

## Item Categories

The current item data is divided into seven catalog groups.

### Ammunition

Use `data/items/ammunition.json` for:

* compatible projectile resources
* standard and specialty ammunition
* recoverability judgments
* tag-based payload logic

### Apparel

Use `data/items/apparel.json` for:

* clothing sets (common, work, travel, fine, ceremonial)
* footwear (turnshoes, boots, court shoes)
* handwear (gloves — non-combat)
* outerwear (cloaks)

### Armor

Use `data/items/armor.json` for:

* unarmored state
* armor categories
* shields
* armor knowledge/application structure
* mobility and protection framing

### Magical

Use `data/items/magical.json` for:

* standard magical items
* reusable arcane, sacred, or utility magic gear
* magical consumables not elevated to notable-item status

### Gear

Use `data/items/gear.json` for:

* ordinary gear
* tools
* camp items
* storage
* travel equipment
* common tactical and social equipment
* cordage (twine, waxed line, cord) alongside rope and rigging utility

### Notable

Use `data/items/notable.json` for:

* named or setting-significant items
* rarer gear with stronger narrative identity
* items whose use may attract visibility, consequence, or political interest

### Weapons

Use `data/items/weapons.json` for:

* weapon knowledge/application handling
* primary combat family matching
* specific weapon identity
* ordinary priced weapon catalog entries

---

## Tool Sufficiency Rule

When a character attempts a skilled task, assess whether their carried items provide a logical means to accomplish it.

* If the core requirement is present, proceed normally.
* If the item meaningfully helps but is not strictly required, the item may justify a cleaner, safer, or more plausible attempt.
* If a critical non-substitutable item is absent, the attempt fails before a roll is called.
* If improvised substitutes are plausible, allow them only with appropriate narrative cost, reduced reliability, or increased difficulty.

Do not treat every item as a numeric bonus. Items primarily determine plausibility, access, positioning, and fictional permission.

---

## Roll Tag Rule

`roll_tag` indicates contextual fit, not an automatic numerical bonus.

Use `roll_tag` to determine:

* whether the item clearly belongs in the scene
* whether it supports the kind of action being attempted
* whether it meaningfully improves fictional positioning
* whether a task is credible without improvisation

An item with a matching `roll_tag` supports the attempt. It does not replace:

* domain selection
* knowledge/application selection
* difficulty judgment
* consequence handling

---

## Consumables Rule

Consumables are expended according to their item logic and scene outcome.

Use the item data to determine whether a consumable is:

* one-use
* charge-based
* narratively recoverable
* expended on use
* only partially consumed in context

For non-ammunition consumables, assume that use normally reduces availability immediately unless the fiction strongly supports otherwise.

For ammunition, follow ammunition-specific rules from `data/items/ammunition.json` and `combat-rules.md`.

---

## Durable Items Rule

Durable items are not automatically consumed, but they are still subject to fiction.

A durable item may become:

* broken
* damaged
* lost
* disarmed
* confiscated
* dropped
* exhausted in practical usefulness for the current scene

If an item suffers meaningful change, reflect that in state when relevant.

---

## Notable Item Rule

Notable items are not just stronger gear. They carry narrative identity.

Use notable items to introduce:

* visibility
* institutional recognition
* political consequence
* obligation
* access pressure
* heightened narrative weight

Avoid treating notable items as flat power multipliers.

A notable item should usually do one or more of the following:

* justify a stronger fictional position
* enable a rarer kind of attempt
* alter social or institutional response
* create consequence when revealed or used openly

---

## Magical Item Rule

Magical items should remain legible and bounded.

Do not narrate magical items as unconditional solutions unless another rule explicitly permits it.

Use magical item tags, category, and narrative effects to determine:

* what kind of action the item supports
* whether its magic is subtle, overt, sacred, arcane, or unstable
* whether use would be ordinary, regulated, suspicious, or politically sensitive

If a magical item creates a persistent world fact, update state.

---

## Weapon and Armor Cross-Reference Rule

Weapons and armor do not resolve themselves through item data alone.

For all combat-facing interpretation, use item data together with `combat-rules.md`.

Specifically:

* weapon knowledge/application logic lives in combat rules plus weapon data
* armor and shield handling logic lives in combat rules plus armor data
* ammunition handling lives in combat rules plus ammunition data

Do not rebuild combat interpretation inside this file.

---

## Economy Cross-Reference Rule

Item prices are data, but transaction handling is governed elsewhere.

Use:

* item JSON files for item-level value fields
* `economy-rules.md` for transaction logic, barter, price pressure, and state updates

Do not narrate item purchase, sale, barter, or trade without following economy rules.

---

## Inventory and State Rule

If an item changes the world, inventory, or access condition in a durable way, update state.

This includes:

* acquiring or losing an item
* expending a consumable
* breaking or damaging a notable object
* placing or leaving equipment at a location
* using an item to create a persistent environmental change
* turning an item into an obligation, symbol, or recognized credential

If the effect is temporary and scene-local, state updates may be unnecessary unless another rule requires them.

---

## GPT Item Conduct Rules

1. **Read the catalogs first.** Do not invent duplicates of listed items.
2. **Treat items as contextual support, not free bonuses.**
3. **Use roll tags for fit, not automatic math.**
4. **Apply tool sufficiency before calling for a roll.**
5. **Let rarity and category influence access, scrutiny, and consequence.**
6. **Use notable items for narrative weight, not unconditional superiority.**
7. **Update state when item use creates durable change.**
8. **Use economy and combat rules when item use crosses into those systems.**

---

## Placeholder — Crafting and Repair

Placeholder.

This section will eventually define how the GPT should handle:

* crafting inputs
* repair logic
* field repair vs workshop repair
* item degradation and restoration
* magical item maintenance

---

## Placeholder — Loot Generation

Placeholder.

This section will eventually define how the GPT should handle:

* loot rarity
* encounter-appropriate rewards
* faction gear patterns
* region-weighted drops
* notable item placement discipline

---

## Placeholder — Encumbrance and Carry Logic

Placeholder.

This section will eventually define how the GPT should reason about:

* carried load
* pack limits
* access speed
* stowed vs ready items
* practical inventory burden

---

## Reference Files

* `data/items/ammunition.json` — ammunition catalog and specialty payload data
* `data/items/apparel.json` — clothing, footwear, handwear, and outerwear catalog
* `data/items/armor.json` — armor and shield catalog
* `data/items/gear.json` — ordinary gear, tools, storage, camp items, and cordage catalog
* `data/items/magical.json` — standard magical item catalog
* `data/items/notable.json` — named and setting-significant item catalog
* `data/items/weapons.json` — weapon catalog and combat-family item data
* `combat-rules.md` — combat-facing handling of weapons, armor, and ammunition
* `economy-rules.md` — buying, barter, pricing pressure, and transaction state rules
* `world-rules.md` — broader world/system-facing rules
* `engine.md` — runtime adjudication and system logic

---

## Summary

This file defines how the GPT should think about items. The catalogs provide the item facts. This file provides the interpretation rules: tool sufficiency, roll-tag fit, consumable handling, notable-item weight, and state consequences. Combat and economy interactions should defer to their own rule files rather than being duplicated here.
