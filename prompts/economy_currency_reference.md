# Mystic Weave — Economy & Currency Reference

Version 1.0 — April 2026
Status: Canonical. Upload to GPT builder as a knowledge file.

---

## Overview

Drakenvale operates on two parallel economic systems that coexist and complement each other.

**Coin economy** — used for everyday transactions, common goods, services, lodging, weapons, and mundane materials. Operated through the Silver Scale Trading Company (SSTC) for external trade. Used freely outside Drakenvale and in SSTC-adjacent commerce inside the valley.

**Barter economy** — used for high-value exchanges involving magical items, magical services, rare materials, specialized knowledge, information, relics, and high-skill labor. Barter is considered more prestigious and carries more social weight than coin. A barter transaction is a relationship; a coin transaction is a convenience.

Neither system is exclusive. A healing potion might be purchased with coin at an SSTC outpost or bartered for a favor at the Platinum Heart. Context determines which applies.

---

## Currency — The Drake System

All coin is denominated in Drakes. The gold Drake (GD) is the standard reference unit. Prices are calibrated on a gold-decimal scale even when narrated as copper/silver/platinum.

### Denominations

| Coin | Abbreviation | Value in GD | Shorthand |
|---|---|---|---|
| Copper Drake | CD | 0.01 GD | 1 CD = one hundredth of a gold |
| Silver Drake | SD | 0.10 GD | 1 SD = one tenth of a gold |
| Gold Drake | GD | 1.00 GD | Standard reference unit |
| Platinum Drake | PD | 10.00 GD | High-value transactions |

### Narration Convention

- Amounts under 1 GD → CD or SD
- Amounts 1–99 GD → GD
- Amounts 100 GD+ → PD where the amount divides cleanly by 10, otherwise GD
- Never express an amount as raw GD when a more natural denomination applies

---

## Starting Coin by Wealth Tier

Starting coin is set at session creation based on the character's wealth tier.

| Wealth Tier | Starting Coin (target fiction) | CD stored (integer) | What It Represents |
|---|---|---|---|
| Destitute | 0.50 GD | 50 CD | A handful of coppers. No financial safety net. |
| Modest | 5.00 GD | 500 CD | Working class. Can cover food and shelter short-term. |
| Comfortable | 40.00 GD | 4000 CD | Skilled professional or minor noble. Some savings. |
| Wealthy | 150.00 GD | 15000 CD | Minor merchant, landowner, or officer. Meaningful reserves. |
| Affluent | 500.00 GD | 50000 CD | Significant wealth. Rarely carries coin directly — uses credit, agents, or barter. |

---

## Price Reference — Coin Economy

Prices are baseline for a typical settled region. Remote locations, dangerous routes, or scarcity may increase prices. SSTC-adjacent markets trend toward baseline. Drakenvale internal markets trend toward barter for anything above common goods.

### Consumables

| Item | Price |
|---|---|
| Loaf of bread | 2 CD |
| Mug of ale | 4 CD |
| Trail rations (1 day) | 5 CD |
| Meal (basic, inn or tavern) | 8 CD |
| Candle | 1 CD |
| Oil flask | 1 SD |
| Soap | 2 CD |

### Lodging & Services

| Item | Price |
|---|---|
| Poor inn bed (common room floor) | 5 CD |
| Decent private room | 2 GD |
| Stable fee (per night) | 5 CD |
| Meal + decent room (together) | 2.08 GD |
| Wagon passage (long trip) | 5 GD |
| Day laborer hire (1 day) | 5 SD |
| Skilled guide (1 day) | 2 GD |
| Blacksmith repair (simple tool) | 1 GD |
| Healer visit (minor wound) | 2 GD |

### Basic Gear

| Item | Price |
|---|---|
| Torch | 1 SD |
| Bedroll | 5 SD |
| Blanket | 3 SD |
| Waterskin | 2 SD |
| Sack | 5 CD |
| Backpack | 3 SD |
| Rope (50 ft) | 1 GD |
| Lantern | 5 SD |
| Lock (simple) | 1 GD |

### Tools & Kits

| Item | Price |
|---|---|
| Hammer | 5 SD |
| Shovel | 1 GD |
| Cooking pot | 5 SD |
| Sewing kit | 2 SD |
| Fishing kit | 8 SD |
| Crowbar | 2 SD |

### Weapons

| Item | Price |
|---|---|
| Dagger | 2 GD |
| Spear | 1 GD |
| Shortsword | 8 GD |
| Longbow | 15 GD |

### Armor

| Item | Price |
|---|---|
| Leather armor | 10 GD |
| Chain shirt | 50 GD |
| Plate armor | 150 PD (1,500 GD) |

### Animals & Transport

| Item | Price |
|---|---|
| Mule | 8 GD |
| Riding horse | 7 PD (70 GD) |
| Cart | 15 GD |

---

## Barter Economy

Barter applies to magical goods, specialized knowledge, information, relics, and high-skill magical services. It is not tracked as a coin price — it is a narrative negotiation reflected in `trade_goods` and `obligations` in state.

### How Barter Works

1. The GPT identifies the exchange as barter-appropriate based on the nature of goods/services involved.
2. Parties negotiate in-scene. Counterparties act according to status, scarcity, and leverage.
3. On agreement, update `world.economy.trade_goods` (add/remove goods) and `world.economy.obligations` (add/remove duties/favors).
4. Do not mutate `coin` unless coin is explicitly part of the same deal.

---

## Economy Rules for the GPT (Non-Negotiable)

1. **Never narrate a transaction without updating state.**
   - coin changed → update `world.economy.coin`
   - goods exchanged → update `world.economy.trade_goods`
   - favor/debt/oath incurred → update `world.economy.obligations`

2. **Use this price reference.** Do not invent arbitrary prices. For unlisted goods, estimate from nearest comparable baseline and remain session-consistent.

3. **`coin` cannot go below 0.** If the player cannot afford something, narrate denial, alternatives, or barter paths.

4. **Narrate coin using denomination thresholds (mandatory).** Amounts under 1 GD → CD or SD. Amounts 1–99 GD → GD. Amounts 100 GD+ → PD where the amount divides cleanly by 10, otherwise GD. Never express an amount as raw GD when a more natural denomination applies.

5. **Barter is narrative, not arithmetic.** Do not expose calibration ranges as shop quotes.

6. **`wealth_tier` is persistent context, not a per-purchase calculator.** Update only for material status shifts.

7. **Prices scale with context.** Remote, dangerous, scarce, monopolized, or crisis conditions can shift baseline within reason.
