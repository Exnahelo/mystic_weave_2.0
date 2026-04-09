# Mystic Weave — Canonical World Rules

This document defines the internal logic of the Mystic Weave world. It is the source of truth for all mechanical rules. When in doubt, consult this document. Do not invent rules that contradict it.

---

## Ability Scores

Characters have six standard D&D 5e ability scores: STR, DEX, CON, INT, WIS, CHA. Scores range from 1–30. At level 1, scores are set using the standard array (15, 14, 13, 12, 10, 8) assigned by the player, then modified by the chosen background (+2/+1/+1).

Ability scores inform narrative bias and determine dice modifiers. They do not run mechanical calculations during gameplay beyond what the `/roll` endpoint handles.

---

## Hit Points

HP represents the character's capacity to absorb damage and keep fighting.

- **Starting HP** = hit die maximum + CON modifier (standard 5e level 1 rule)
- HP cannot go below 0
- When `hp.current` reaches 0, the character is incapacitated

### HP Loss

HP is reduced when the character takes damage from a failed save, a successful enemy attack, or a hazard. The amount is determined narratively based on the threat level and roll margin.

### HP Recovery

HP can be recovered through:
- **Short rest** (1 hour in a low-threat location): spend hit dice to recover HP
- **Long rest** (full night in a safe location): recover all HP

---

## Proficiency

Characters are proficient in skills, weapons, and armor listed in their class and background. Proficiency adds the proficiency bonus (+2 at level 1) to relevant ability checks and saving throws.

When calling `POST /roll`, set `proficient: true` if the character is proficient in the relevant skill or weapon.

---

## Dice Resolution

All contested actions use `POST /roll`. The GPT never simulates dice internally.

**Standard check:**
- Roll 1d20 + ability modifier + proficiency bonus (if proficient)
- Compare to DC (Difficulty Class)
- `success: true` if total ≥ DC

**Critical results:**
- Natural 1 = critical failure, regardless of modifiers
- Natural 20 = critical success, regardless of DC

**Difficulty Classes:**
| Difficulty | DC |
| --- | --- |
| Very Easy | 5 |
| Easy | 10 |
| Medium | 15 |
| Hard | 20 |
| Very Hard | 25 |
| Nearly Impossible | 30 |

---

## Failure States

### HP Reaches 0

When `hp.current` reaches 0:
- The character is incapacitated
- Narrate the consequence clearly — the character cannot continue the expedition
- Save state with `hp.current = 0`
- The session ends or transitions to a recovery scenario

### Character Death

Character death is a valid outcome. It is not reversed. The world reacts to it.

---

## The World Graph

The world is a graph of connected location nodes. Movement is along defined edges only.

- The player can only move to locations listed in the current location's `connections` array
- New locations are discovered through explicit exploration actions
- Discovered locations must be saved immediately via `POST /location`
- The GPT cannot invent geography mid-session without saving it

---

## Location Consistency

Locations are stored in Postgres. The GPT reads location data before describing any place.

- The GPT may add sensory flavor but may not contradict any field in the record
- If a new detail is invented (NPC name, building), it must be saved back via `POST /location`
- NPC names, descriptions, and relationships are persistent once saved

---

## NPC Persistence

NPCs are persistent once named. If the GPT names an NPC, it must:
1. Add the NPC's identifier to the location's `known_npcs` array
2. Save the updated location via `POST /location`

NPCs do not change between sessions unless the world state changes.

---

## Narrative Principles

- **Failure moves the world forward.** Failed actions change the situation — they do not reset it.
- **Consistency over creativity.** Logical consistency beats narrative immersion.
- **No premature complexity.** No factions, inventories, spell slots, or combat subsystems until explicitly added.
- **The dice are authoritative.** The GPT narrates results; it does not override them.
