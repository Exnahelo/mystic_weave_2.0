# Mystic Weave — Item Rules

Version 2.1 — April 2026
Status: Canonical. Upload to GPT builder as a knowledge file.

---

## Purpose

This file contains the GPT-facing rules for how items should be interpreted, selected, narrated, and applied during play.

It does **not** duplicate item catalogs. Structured item definitions live in JSON data files, one file per item, under `data/catalog/items/<category>/`.

Use this file together with:

* `data/catalog/items/ammunition/` — ammunition catalog
* `data/catalog/items/apparel/` — clothing and non-combat garments
* `data/catalog/items/armor/` — body armor
* `data/catalog/items/shield/` — shields
* `data/catalog/items/gear/` — tools, survival, magical trinkets, consumables
* `data/catalog/items/weapon/` — weapons
* `data/catalog/registries/` — controlled vocabularies (tags, knowledge, applications, magic fields, rarities, legality, market tags, subcategories)
* `combat-rules.md`
* `economy-rules.md`
* `mechanics-tables.md`
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
* legality
* value (in CD)
* ammunition compatibility
* knowledge/application structure where relevant
* consumable state and charges
* narrative effects
* magical tier and field where applicable

Do not invent alternate catalog entries when a listed item already exists.

If a needed item is not listed, the GPT may infer a nearest comparable only when:

* no listed equivalent exists
* the inference stays consistent with current item logic
* the item does not contradict established world or system rules

---

## Item Categories

Items are divided into six structural categories. Magical-ness is a property carried by `tier` and `magic_field` fields, not a separate category — a magical longsword is still `category: weapon`.

### Weapon

`data/catalog/items/weapon/`

* combat family (knowledge_tag: close_combat / melee / reach / ranged / mechanical / unconventional / martial_arts)
* specific weapon identity (application_tag)
* base damage (integer)
* handedness (one / two / versatile)

### Armor

`data/catalog/items/armor/`

* armor categories (light_armor / medium_armor / heavy_armor / unarmored)
* armor floor and ceiling (HP contribution range)
* mobility and protection framing

### Shield

`data/catalog/items/shield/`

* shield catalog
* canonical shield contribution (floor 5, ceiling 30)

### Ammunition

`data/catalog/items/ammunition/`

* compatible projectile resources
* standard and specialty ammunition
* recoverability judgments
* tag-based payload logic

### Apparel

`data/catalog/items/apparel/`

* clothing sets (common, work, travel, fine, ceremonial)
* footwear (turnshoes, boots, court shoes)
* handwear (gloves — non-combat, including bracers as decorative handwear)
* outerwear (cloaks)
* headwear

Apparel does not carry combat fields and does not fill the armor slot. A character wearing apparel and no armor is mechanically unarmored.

### Gear

`data/catalog/items/gear/`

* ordinary gear, tools, camp items, storage, travel equipment
* common tactical and social equipment
* cordage and rigging utility
* magical trinkets, foci, and consumables (carry `tier` and `magic_field` when magical)
* magical potions and single-use sacred items (`consumable: true, charges_max: 1`)

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

* one-use (`consumable: true`, `charges_max: null` or `1`)
* charge-based (`consumable: true`, `charges_max: N`)
* narratively recoverable
* expended on use
* only partially consumed in context

For non-ammunition consumables, assume that use normally reduces availability immediately unless the fiction strongly supports otherwise.

For ammunition, follow ammunition-specific rules from the ammunition catalog and `combat-rules.md`.

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

Use magical item tags, category, tier, magic field, and narrative effects to determine:

* what kind of action the item supports
* whether its magic is subtle, overt, sacred, arcane, or unstable
* whether use would be ordinary, regulated, suspicious, or politically sensitive

If a magical item creates a persistent world fact, update state.

### Magical Item Tier Framework

Items use a T0–T5 scale. Tier describes **what the item does** (mechanical impact and narrative weight), not **how it was made**.

| Tier | Character |
|---|---|
| T0 | Mundane items made from magical materials. No active magic. Baseline special without enchantment (silverwood bow, mithral dagger). |
| T1 | Minor magical effect. Utility or flavor; small situational benefit. |
| T2 | Meaningful magical effect. Can shift an encounter. |
| T3 | Strong magical effect. Clear strategic advantage; draws attention. |
| T4 | Major magical effect. Named or near-named; politically or narratively significant. |
| T5 | Legendary. One-of-a-kind outliers with mythic weight. Specific rules deferred. |

Tier semantics align with the T1–T5 pattern in `magic-rules.md` (minor utility at T1 through apex expression at T5). T0 extends the scale downward for material-only items that carry narrative specialness without magical effect.

Tier reflects **impact**, not input. An item enchanted by multiple spells or fields carries one tier, the tier of its overall effect on play. T0 (material-only) items fit the same scale.

### Magic Field

Magical items at T1 and above carry a `magic_field` from the nine canonical fields in `magic-rules.md`: sacred, warding, binding, elemental, druidry, illusion, runecraft, alchemy, necromancy.

T0 items may omit `magic_field` (they have no active magic). T5 mythic items whose magic does not originate in a single field may also omit it; treat such items as authored exceptions.

### What Tier Does Not Govern

Tier does not currently govern:

* who can craft an item at a given tier
* time, cost, or process of crafting
* activation rules (passive vs active vs triggered)
* charges, recharge, or stability beyond what the item record specifies
* whether items can be unmade, damaged, or decay

These belong to the enchantment-rules arc, not to the tier framework. Until that arc is authored, tier is a narrative and mechanical-impact descriptor only.

---

## Cultural Material Traditions

Some items in the catalog reflect distinct cultural craft traditions rather than purely mechanical differences. The GPT should narrate items in these traditions consistently with the worldbuilding behind them, even though the mechanical effects are already settled in the catalog.

### Feywood Composite Craft

Elven craft does not match human or dwarven traditions. Drakenvale-side and human cultures often solve a structural problem by adding more iron — more thickness, more rivets, more plate. The Feywood does not. Elven smiths and wardens have spent generations engineering around metal scarcity, building gear that uses less metal by relying on treated woods, layered hides, mineral washes, plant resins, and other Feywood materials in concert.

The result is gear that is lighter, balanced, durable, and extremely deliberate in its construction. It is not magically superior to mundane equivalents. It is exceptional craft, not an active power.

Three working tiers describe how Feywood items use material:

* **Ordinary use** — mundane materials, even where beautifully made. Wood, horn, bone, leather, woven fiber, bark-laminate, treated hide. Lesser traded metals where used at all. Most everyday Feywood items.
* **High craft** — items built around specially treated Feywood materials that reduce metal dependence. Silverbark Ash hafts, Ironroot shield cores, treated leather composites. Still mundane mechanically, but distinct in lore and construction. Items in this tier may be notable but should not be promoted to T0 by default.
* **Reserved works** — items whose identity centers on a magical material: recovered celestial metal (Elarith), Longbough wood, Witheroak ritual material, living Thornveil or Thornmere vinework, or Thornroot Stalker hide. These qualify for T0 (material-only) or T1+ (actively magical), per their catalog records.

When narrating Feywood items, prefer language that emphasizes craft economy and material harmony over "magic wood stronger than steel." An elven spear has a small metal point because the craft tradition reserves metal for where it matters; an elven longbow uses almost no metal at all; ranger leathers are layered composite, not steel-augmented hide. The catalog already encodes the mechanical effects — the GPT's job is to keep the narration consistent with the tradition.

### The Recovery Economy and the Elarith Reserve

The elves do not mine. Their metal comes from recovery: celestial-metal fragments scattered across the Hollow Crown by the Cataclysm, gathered patiently from riverbeds, lake margins, and impact-strewn ground over generations. The Feywood holds a generations-long reserve from this work, kept by elder houses, military orders, and ceremonial offices.

Recovered celestial metal is treated as sacred. It is reserved for heirlooms, ceremonial works, named weapons, and works of state meant to endure across generations. Ordinary Feywood goods do not use it. This is structural, not arbitrary — the reserve only stays viable because composite craft minimizes baseline metal use and Elarith is restricted to genuinely exceptional commissions.

The narrative implications:

* Items made with Elarith are not bought. They are inherited, awarded for proving, given through formal house relationship, or commissioned through institutional sanction.
* New celestial signs occasionally trigger sanctioned recovery expeditions. These are part recovery, part ritual, and part guardianship. What falls from the sky is not always safe to disturb.
* Elven characters wearing or carrying celestial-metal items signal something specific to other elves: house standing, military rank, ceremonial office, or a debt-of-honor relationship. Outsiders may not read the signal correctly, but elves do.
* Drakenvale's relationship to celestial material is monumental and central (the Heartmass, the Heartstone, the Stronghold). The Feywood's relationship is dispersed, recovered, and ceremonial. The two polities share a Cataclysm origin but parallel naming traditions for the same fragment-metal.

When a player attempts to acquire, trade, or commission an Elarith item, the GPT should treat the request as relationship-and-obligation rather than commerce. See `economy-rules.md` for the barter procedure and `data/catalog/crafting/materials.json` for the canonical material record.

### Naming Culture for Recovered Celestial Metal

The same material is named differently across cultures. The catalog stores `aliases` on the elarith material; the GPT should narrate the term that fits the speaker:

| Speaker | Term |
|---|---|
| Elves (everyday smithcraft) | Elarith |
| Elves (ceremonial, oath-context, formal) | Elyndral |
| Drakenvale (formal) | Heartfall — kin to the Heartmass core |
| Outsiders, working/folk usage | starvein, sky-iron, falling-iron |

A Heartwarden Captain at investiture says Elyndral. The same captain in their workshop says Elarith. A Drakenvale envoy says Heartfall. A human caravan trader says starvein. These are not interchangeable in formal contexts.

Cross-reference: `data/catalog/crafting/materials.json` is the canonical material record. The aliases listed there are the data; this section explains the cultural use.

---

## Magical Unarmored Rule

A magical garment may carry combat-armor function while remaining mechanically unarmored. Such items have:

* `category: armor`
* `application_tag: unarmored`
* `armor_floor > 0` and `armor_ceiling > 0` (provides HP contribution like normal armor)
* `tier: T1` or higher
* `magic_field` set

This pattern allows a warding robe to protect a wearer through HP contribution while still letting `martial_arts` knowledge tier reduce attacker thresholds (the unarmored evasion bonus from `combat-rules.md`).

Mundane garments cannot grant armor while remaining unarmored. Only magical items can do this. The catalog validator enforces this rule.

---

## Weapon and Armor Cross-Reference Rule

Weapons and armor do not resolve themselves through item data alone.

For all combat-facing interpretation, use item data together with `combat-rules.md`.

Specifically:

* weapon knowledge/application logic lives in combat rules plus weapon data
* armor and shield handling logic lives in combat rules plus armor and shield data
* ammunition handling lives in combat rules plus ammunition data

Do not rebuild combat interpretation inside this file.

---

## Economy Cross-Reference Rule

Item prices are data, but transaction handling is governed elsewhere.

Use:

* item JSON files for item-level value fields (`value_cd`)
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
5. **Let rarity, legality, and category influence access, scrutiny, and consequence.**
6. **Use notable items for narrative weight, not unconditional superiority.**
7. **Read tier and magic field for magical items; enforce magical-unarmored rule.**
8. **Update state when item use creates durable change.**
9. **Use economy and combat rules when item use crosses into those systems.**

---

## Placeholder — Crafting and Repair

Placeholder. Deferred to the enchantment-rules arc.

This section will eventually define how the GPT should handle:

* crafting inputs
* repair logic
* field repair vs workshop repair
* item degradation and restoration
* magical item maintenance, recharge, and unmaking

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

Until then, load is tracked by abstract band per `world-rules.md`, not by per-item weight.

---

## Reference Files

* `data/catalog/items/ammunition/` — ammunition catalog
* `data/catalog/items/apparel/` — clothing, footwear, handwear, and outerwear catalog
* `data/catalog/items/armor/` — body armor catalog
* `data/catalog/items/shield/` — shield catalog
* `data/catalog/items/gear/` — tools, survival, magical trinkets, consumables, foci
* `data/catalog/items/weapon/` — weapon catalog
* `data/catalog/registries/` — controlled vocabularies for tags, combat knowledge/applications, magic fields, rarities, legality, market tags, subcategories
* `combat-rules.md` — combat-facing handling of weapons, armor, ammunition
* `economy-rules.md` — buying, barter, pricing pressure, transaction state rules
* `magic-rules.md` — magical fields, spell access, casting resolution
* `mechanics-tables.md` — single-file reference for numerical tables
* `world-rules.md` — broader world/system-facing rules
* `engine.md` — runtime adjudication and system logic

---

## Summary

This file defines how the GPT should think about items. The catalogs provide the item facts, organized as one JSON file per item under `data/catalog/items/<category>/`. This file provides the interpretation rules: tool sufficiency, roll-tag fit, consumable handling, notable-item weight, magical tier framework, the magical-unarmored rule, and state consequences. Combat and economy interactions defer to their own rule files rather than being duplicated here.