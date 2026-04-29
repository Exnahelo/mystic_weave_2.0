# Mystic Weave — Economy Rules

Version 1.2 — April 2026
Status: Canonical. Upload to GPT builder as a knowledge file.

---

## Purpose

This file contains the GPT-facing rules for handling coin, barter, pricing context, and transaction state. Structured economic tables and lookup data belong in JSON data files, not here.

Use this file together with:

* `data/catalog/items/<category>/` — per-item catalog with `value_cd` per item (item-level prices)
* `data/economy/currency.json` — denomination data and conversion values
* `data/economy/prices.json` — baseline reference prices for services, lodging, food, transport, and other non-catalog purchases
* `data/economy/regional_nodes.json` — regional availability and trade-node heuristics
* `data/characters/starting_wealth.json` — starting wealth tiers for character creation
* `mechanics-tables.md` — currency narration ranges, wealth tier vocabulary
* `items-rules.md` — item interpretation and catalog usage

---

## Overview

Drakenvale operates on two parallel economic systems that coexist and complement each other.

**Coin economy** is used for everyday transactions, common goods, services, lodging, travel costs, and mundane materials. It is common in ordinary markets, practical exchanges, and SSTC-adjacent trade.

**Barter economy** is used for higher-value exchanges involving magical items, magical services, rare materials, specialized knowledge, information, relics, favors, and high-skill labor. Barter carries greater social weight than coin. A barter exchange is not just a price — it is a relationship.

Neither system is exclusive. Context determines which applies.

---

## Coin Economy Rules

Use coin for:

* ordinary food, lodging, tools, transport, and basic services
* routine marketplace purchases
* mundane goods with stable reference pricing
* purchases in SSTC-adjacent trade environments

For item purchases, the catalog `value_cd` field is the baseline price. For services and non-catalog purchases (meals, lodging, transport, professional fees), use `data/economy/prices.json`. Do not invent arbitrary prices when a listed comparable exists.

---

## Barter Economy Rules

Use barter when the exchange centers on:

* magical goods (especially T2 and above per items-rules.md tier framework)
* magical services
* rare or unstable materials
* relics or sacred objects
* specialized knowledge
* information with leverage value
* favors, obligations, oaths, or institutional access
* high-skill labor whose value is contextual rather than standardized

Barter should be narrated as negotiation, leverage, relationship, and obligation rather than as a fixed arithmetic quote.

---

## Barter Procedure

When a transaction is barter-appropriate:

1. Identify the exchange as barter rather than ordinary coin purchase.
2. Determine what each side actually values in context.
3. Negotiate in scene according to scarcity, leverage, status, urgency, and trust.
4. On agreement, update the relevant state fields:

   * `world.economy.trade_goods` for exchanged goods
   * `world.economy.obligations` for favors, debts, duties, or oaths
5. Do not mutate `coin` unless coin is explicitly included as part of the same deal.

---

## Narration Convention

Coin should be narrated naturally by denomination, not as raw decimal gold. The narration ranges table is in `mechanics-tables.md`; the rule:

* amounts under 1 GD → narrate as CD or SD
* amounts from 1 to 99 GD → narrate as GD
* amounts 100 GD and above → narrate as PD when divisible cleanly by 10, otherwise GD
* never narrate a price as raw GD when a more natural denomination applies

The data layer stores values in CD for consistency. The GPT narrates them using natural denominations.

---

## Wealth Tier Rule

`wealth_tier` is persistent character context, not a live per-purchase calculator.

Use it to guide:

* what kind of spending feels trivial, meaningful, or painful
* how NPCs may read the character socially
* what level of reserves, comfort, or dependence makes sense in narration

Only update `wealth_tier` when a material change in long-term status occurs.

Items in the catalog may carry `wealth_tier_floor` as a soft hint (items typical of or limited to characters at that tier and above). It is informational, not a hard gate.

---

## Price Context Rule

All listed prices are baseline settled-region values.

The GPT may adjust price pressure within reason when conditions justify it, including:

* remoteness
* danger
* scarcity
* monopoly control
* crisis conditions
* wartime or disruption
* high-trust or high-hostility environments

Use `data/economy/regional_nodes.json` to judge what is plausibly common, scarce, exported, imported, or unusually available in a region.

SSTC-connected nodes tend toward more stable market access and more reliable baseline pricing than isolated or dangerous regions.

---

## Regional Availability Guidance

Regional nodes are not just flavor. They should guide plausibility.

Examples:

* forge and metal goods are easier to source in Volcanic Highlands nodes
* crystal and resonance materials are easier to source through Deephollow
* rare herbs and restorative compounds are easier to source in wetland nodes
* food, timber, flora, fish, and stone are easier to source through the core supply villages
* highland travel goods, guides, and resupply are easier to source through Lastmark
* liminal, fey-adjacent, or threshold-trade goods are more plausible through Dracélune
* security-sensitive, ward-related, or low-trust corridor trade behaves differently near Greymantle and the Platinum Oath approach

The catalog's `market_tags` field on individual items signals which kinds of vendors typically stock or fence the item; cross-reference with regional context.

---

## Cultural Economic Traditions

Beyond regional availability, distinct cultures within the world operate on economic traditions that differ from baseline Drakenvale-side trade. The GPT should narrate transactions consistently with the originating culture, not collapse everything into ordinary coin commerce.

### The Feywood: Recovery Economy

The Feywood does not run on extraction. The elves do not mine. Their metal comes from a generations-long recovery tradition: celestial fragments scattered across the Hollow Crown by the Cataclysm, gathered patiently from riverbeds, impact-strewn ground, and exposed scars in the land. The Feywood holds a real and lasting reserve from this work, kept by elder houses, military orders, and ceremonial offices.

This produces a different kind of economy than coin trade:

* **Recovered celestial metal (Elarith) is not a commodity.** It is reserved for heirlooms, named weapons, ceremonial works, and commissions of state. No ordinary Feywood good uses it. No SSTC vendor stocks it. No coin price exists for it because no coin transaction is appropriate.
* **Composite craft makes baseline gear viable without metal abundance.** Most Feywood items use treated woods, layered hides, plant resins, and mineral washes — not as magic, but as engineering around scarcity. See the Feywood Composite Craft section in `items-rules.md`.
* **High-craft items can move through coin or barter** depending on what they are. A Silverbark Ash spear may be sold to an outsider through SSTC channels. A Heartwarden's vestments will not be.
* **Reserved works move through institutional relationship.** When a player wants an Elarith item — a moon blade, a Greenshield-Pattern sword, a Heartwarden's blade — coin will not buy it. Acquisition runs through proving, oath, house obligation, ceremonial commission, or a sanctioned expedition. This is barter at its strongest, with relationship and recognition as the medium.

When narrating elven goods, the GPT should default to barter framing for anything beyond ordinary craft, and should treat any attempt to "shop for" Elarith items as a category error. The character does not buy a moon blade. The character earns one, is given one, or returns home with one because something happened.

### Drakenvale and the Feywood: Parallel Origins

Both polities share a Cataclysm-event origin for celestial metal, but their relationships to it diverge:

* **Drakenvale** holds the Heartmass — the largest fragment, fused with platinum-veined heartrock, foundational to the Stronghold and the Heartstone. Drakenvale's relationship to celestial material is monumental, central, architectural, and political.
* **The Feywood** holds the rest — dispersed fragments recovered through patient gathering. Its relationship is diasporic, ceremonial, and oriented around heirlooms and named works.

These two polities are sovereign-equal allies. Neither party comments freely on the other's reserve. A Drakenvale envoy and a Feywood Heartwarden may meet without ever discussing where their respective celestial-metal stocks come from or how much remains. The mutual silence is not hostile; it is one of the things that keeps the alliance functional.

For naming conventions across speakers (Elarith / Elyndral / Heartfall / starvein), see the Naming Culture section in `items-rules.md`. The canonical material record is `data/catalog/crafting/materials.json`.

---

## Transaction State Rules

These are mandatory.

1. **Never narrate a transaction without updating state.**

   * coin changed → update `world.economy.coin`
   * goods exchanged → update `world.economy.trade_goods`
   * favor, debt, duty, or oath incurred → update `world.economy.obligations`

2. **Do not allow `coin` to go below 0.**

   * If the character cannot afford something, narrate denial, substitution, delay, partial payment, or barter alternatives.

3. **Do not invent arbitrary prices when reference data exists.**

   * For items: use catalog `value_cd`.
   * For services and non-catalog goods: use `data/economy/prices.json`.
   * For unlisted goods, estimate from the nearest comparable item and remain session-consistent.

4. **Barter is narrative, not arithmetic.**

   * Do not reduce every meaningful exchange to coin-equivalent shop math.

5. **Context always matters.**

   * The same item may be ordinary in one node and scarce in another.

---

## Reference Files

* `data/catalog/items/<category>/` — per-item catalog with `value_cd`, `wealth_tier_floor`, `market_tags`, `legality`
* `data/economy/currency.json` — denomination data and conversion values
* `data/economy/prices.json` — service and non-catalog reference prices, stored in CD
* `data/economy/regional_nodes.json` — regional availability and trade-node heuristics
* `data/characters/starting_wealth.json` — starting wealth tiers for character creation
* `mechanics-tables.md` — currency narration table, wealth tier vocabulary
* `items-rules.md` — item interpretation and catalog usage
* `world.md` — world-level social and economic context
* `groups.md` — SSTC and institutional trade context

---

## Summary

Use coin for ordinary trade. Use barter for meaningful or leverage-based exchange. Read catalog `value_cd` and prices.json as baselines, not absolutes. Let region, scarcity, risk, and trust shape what is available and how it is valued. Always update economy state when a transaction occurs.