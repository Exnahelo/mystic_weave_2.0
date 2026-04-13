# Mystic Weave — Economy Rules

Version 1.0 — April 2026
Status: Canonical. Upload to GPT builder as a knowledge file.

---

## Purpose

This file contains the GPT-facing rules for handling coin, barter, pricing context, and transaction state. Structured economic tables and lookup data belong in JSON data files, not here.

Use this file together with:

* `economy_currency.json`
* `character_starting_wealth.json`
* `economy_prices.json`
* `economy_regional_nodes.json`

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

Use the JSON price tables as baseline references. Do not invent arbitrary prices when a listed comparable exists.

---

## Barter Economy Rules

Use barter when the exchange centers on:

* magical goods
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

Coin should be narrated naturally by denomination, not as raw decimal gold.

Use these rules:

* amounts under 1 GD → narrate as CD or SD
* amounts from 1 to 99 GD → narrate as GD
* amounts 100 GD and above → narrate as PD when divisible cleanly by 10, otherwise GD
* never narrate a price as raw GD when a more natural denomination applies

The data layer may store values in CD for consistency. The GPT should still narrate them using natural denominations.

---

## Wealth Tier Rule

`wealth_tier` is persistent character context, not a live per-purchase calculator.

Use it to guide:

* what kind of spending feels trivial, meaningful, or painful
* how NPCs may read the character socially
* what level of reserves, comfort, or dependence makes sense in narration

Only update `wealth_tier` when a material change in long-term status occurs.

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

Use `economy_regional_nodes.json` to judge what is plausibly common, scarce, exported, imported, or unusually available in a region.

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

   * Use listed prices when available.
   * For unlisted goods, estimate from the nearest comparable item and remain session-consistent.

4. **Barter is narrative, not arithmetic.**

   * Do not reduce every meaningful exchange to coin-equivalent shop math.

5. **Context always matters.**

   * The same item may be ordinary in one node and scarce in another.

---

## Reference Files

* `economy_currency.json` — denomination data and conversion values
* `character_starting_wealth.json` — starting wealth tiers for character creation
* `economy_prices.json` — baseline price tables stored in CD
* `economy_regional_nodes.json` — regional availability and trade-node heuristics
* `world.md` — world-level social and economic context
* `groups.md` — SSTC and institutional trade context

---

## Summary

Use coin for ordinary trade. Use barter for meaningful or leverage-based exchange. Read price tables as baselines, not absolutes. Let region, scarcity, risk, and trust shape what is available and how it is valued. Always update economy state when a transaction occurs.
