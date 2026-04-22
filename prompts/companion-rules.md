# Mystic Weave — Companion Rules

Version 1.0 — April 2026
Status: Canonical. Upload to GPT builder as a knowledge file.

---

## Purpose

This file defines how companions work in Mystic Weave. It covers:

- the three-tier companion model
- when to use each tier
- how bonding, training, and tactical roles drive creature behavior
- how tier transitions are handled
- how companions interact with the API surface

Structured companion catalog data lives in JSON under `data/beasts/`,
not here.

Use this file together with:

- `data/beasts/creatures.json` — starter creature catalog
- `data/beasts/natural_abilities.json` — intrinsic trait vocabulary
- `data/beasts/learned_commands.json` — controlled command vocabulary
- `data/beasts/tactical_roles.json` — tactical role definitions
- `world-rules.md`
- `engine.md`
- `character-creation.md` — initial companion flow (Stage 7)
- `progression-rules.md` — bond and training advancement

---

## Three-Tier Model

Companions split into three distinct categories. Each tier uses a
different schema and narrative register. The GPT must know which
tier a companion belongs to before narrating or adjudicating its
behavior.

### Sapient Companion

A person traveling with the party. Uses the full character schema
(ancestry, culture, background, focus, full domains, knowledge,
application, identity, reputation). Narrated the same way player
characters are narrated — with goals, inner life, and moral
agency.

Examples: a guide hired at a settlement, a traveling healer who
joined the party after a shared ordeal, an envoy from another
faction accompanying the group.

### Creature Companion

A non-sapient animal bonded to a player or party. Uses a simplified
schema: species and subspecies, size, age category, tactical roles,
training level, bond level, natural abilities, simplified domain
block (physical, instinct, composure), and optional narrative
block.

Creatures act on instinct and training. They do not reason, make
moral choices, or negotiate. They respond to handler commands and
to their own temperament.

Examples: a trained wolf, a messenger hawk, a riding courser, a
working hound.

### Exceptional Companion

Sub-sapient or magically significant non-humanoid entities. Extends
the creature schema with a sapience profile (partial or full), a
communication mode (instinctive, symbolic, or speech), an autonomy
level, and required motivations. Rare in play.

Examples: a pseudodragon familiar with partial sapience and
symbolic communication; a bound sprite; a dragon ally traveling
temporarily with the party.

---

## When to Use Each Tier

| Tier | Test |
|---|---|
| Sapient | Is this a person? Does it reason, choose, negotiate? |
| Creature | Is this a non-sapient animal — however intelligent for its species? |
| Exceptional | Does it have sub-sapient awareness, supernatural traits, or narrative significance beyond ordinary animal behavior? |

A very smart wolf is still a Creature. A dragon traveling with the
party is always Exceptional. A halfling guide is always Sapient.

---

## Bond Level

How the creature relates to its handler.

- `wary` — minimal trust; may resist or flee under pressure
- `accepting` — tolerates handler; follows routine cues
- `bonded` — recognizes handler as primary social anchor
- `devoted` — prioritizes handler even under danger or conflict

Bond level advances through meaningful shared experience, not
through mechanical training alone.

---

## Training Level

How reliably the creature responds to commands.

- `untrained` — no conditioned responses
- `basic` — sit, stay, come; reliable in calm conditions
- `trained` — tactical commands; reliable under moderate pressure
- `expert` — complex multi-step tasks; reliable under extreme pressure

Training advances through sustained instruction and repetition.

---

## Autonomy (Exceptional only)

How independently an Exceptional Companion acts.

- `limited` — acts only on direct command or reflex
- `moderate` — exercises judgment within handler's stated intent
- `high` — may act independently when circumstances warrant

Autonomy is orthogonal to bond level. A well-trained war mount can
be obedient (low autonomy) and only moderately bonded. A sphinx
companion can be bonded and highly autonomous.

---

## Reliability Adjudication

There is no dedicated reliability stat. The GPT adjudicates creature
reliability narratively from the intersection of:

- `composure` domain (25–60 scale)
- `training_level`
- `bond_level`
- situational context (threat, familiarity, handler presence)

For a roll that depends on the creature holding steady under
pressure, use `composure` as the domain. Higher training and deeper
bond shift the narrative description of success and failure, not
the target number.

---

## Tactical Roles

Each creature has one or more tactical roles stored as a list.

- `mount` — ridden for travel, combat, or labor
- `pack` — carries goods, supplies, or burdens
- `scout` — moves ahead for observation, tracking, or warning
- `guard` — watches a position, person, or object; responds to threat
- `hunter` — pursues game or adversaries; engages in combat
- `companion` — general-purpose presence; emotional and social bond primary

A creature can genuinely fill multiple roles. A war hound might be
companion, scout, and guard. The GPT selects the relevant role for
each scene based on what the handler is asking the creature to do.

---

## Natural Abilities and Learned Commands

### Natural abilities

Intrinsic capabilities of the creature (sensory, physical, cognitive).
Stored as a list of tags. Reference `data/beasts/natural_abilities.json`
for the vocabulary. Do not invent abilities not in that catalog; if
a new ability is needed, it should be added to the catalog first.

Examples: `scent_tracking`, `keen_senses`, `darkvision`, `pack_hunter`,
`fey_resilience`, `long_lived`, `observant_cognition`.

### Learned commands

Controlled vocabulary of behaviors the creature has been trained to
perform. Reference `data/beasts/learned_commands.json`. The free-form
`command_notes` field carries stress-behavior and edge cases that
don't fit the controlled vocabulary.

Examples: `heel`, `guard`, `track`, `scout_ahead`, `hold_ground`.

---

## Bond Links

Every non-Sapient companion has a `bond_links` structure pointing to
the party member who holds the primary bond.

```
bond_links:
  primary: <character_id>
  secondary: <character_id>    # optional
```

Companions belong to parties, not individuals — but every creature
still has a primary handler. Secondary bonds capture cases where a
creature responds well to more than one party member (a hound that
obeys the leader first and the tracker second).

---

## Narrative Block

Creature and Exceptional companions may optionally carry a
`narrative` block with story-weight content:

- `origin` — how this specific creature came to be with its handler
- `wound` — physical history or permanent conditions
- `quirks` — individualizing behavioral oddities
- `flaws` — handling complications
- `bonds` — narrative bonds to places, memories, or persons beyond
  bond_links
- `drives` — instinctive priorities, distinct from sapient reasoned
  motivations

Populate narrative for companions with individual history the GPT
should reference in narration. Leave null for catalog-templated
instances without accumulated story.

---

## Tier Transitions

Tiers are immutable in place. A creature that undergoes a
transformation (awakening, magical binding, divine elevation) is
not "upgraded" — the old record is archived and a new record at
the new tier is constructed.

The transition flow:

1. The GPT recognizes the narrative trigger (oath, exposure, rite,
   encounter).
2. The GPT constructs the new companion payload at the target tier,
   carrying forward name, bond_links, and narrative context.
3. The GPT calls `POST /companion/{companion_id}/transition` with
   the new payload and a `trigger` string describing the cause.
4. The API archives the old record, constructs the new one at the
   new tier, preserves the companion ID, and appends a
   `tier_history` entry to the new record.

No tier transition happens silently. It is always a narrative event.

---

## API Surface

- `POST /companion/new` — create a new companion (any tier). Body
  includes the tier and a full companion payload.
- `POST /companion/{companion_id}/transition` — transition a
  creature to exceptional. Archive and replace.
- `GET /companion/{companion_id}?session_id=...` — fetch a single
  companion. Optional `include_archived=true` to search archived
  records.
- `POST /state/{session_id}/delta` — routine updates (HP changes,
  bond_level shifts, training_level advancement, narrative edits).
  The GPT sends the full updated companions list; partial merges
  are not supported.

---

## Nesting

A Sapient companion may hold their own companions, restricted to
Creature tier only. A sapient guide can have her own hound. That
hound cannot have a hound.

One level of nesting. No deeper.

---

## GPT Conduct Rules

1. **Know the tier.** Before narrating or adjudicating a companion,
   confirm its tier. The tier dictates which fields exist and how
   the companion should be narrated.
2. **Do not fabricate catalog content.** Reference
   `data/beasts/creatures.json` via `GET /options` for creature
   species and subspecies. Do not invent subspecies that are not
   in the catalog.
3. **Do not fabricate natural abilities or learned commands.** Use
   the vocabularies from the catalog.
4. **Adjudicate reliability, do not roll it.** Use composure,
   training, bond, and context together — never reach for a
   nonexistent reliability stat.
5. **Tier transitions are explicit.** Use the transition endpoint.
   Do not mutate a creature record into an exceptional record via
   state delta.
6. **Name companions.** Every companion has a given name at
   creation. Unnamed companions are a schema error.
7. **Respect the nesting rule.** Sapient companions may hold
   Creature companions only. Do not allow deeper structures.

---

## Reference Files

- `data/beasts/creatures.json` — canonical creature catalog
- `data/beasts/exceptional.json` — exceptional companion catalog
- `data/beasts/natural_abilities.json` — ability vocabulary
- `data/beasts/learned_commands.json` — command vocabulary
- `data/beasts/tactical_roles.json` — role definitions
- `api/companions.py` — schema definitions
- `schemas/openapi.yaml` — API contract
- `character-creation.md` — initial companion flow
- `world-rules.md` — broader world/system rules
- `engine.md` — runtime system logic
- `progression-rules.md` — bond and training advancement