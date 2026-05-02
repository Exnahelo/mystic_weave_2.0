# Mystic Weave — Scene Structure

This document defines pacing units and reward-adjudication units.
Use these terms exactly. Do not treat them as interchangeable.

---

## Beat

A **beat** is a small unit of interaction, revelation, or action inside a larger sequence.
A beat may change tone, pressure, or information, but does not by itself define reward timing.

## Encounter

An **encounter** is a bounded challenge, exchange, or pressure event.
Examples: a negotiation, an ambush, a chase, a ritual interruption, a guarded checkpoint.
An encounter may be only part of a larger scene.
A single encounter may itself be a full scene if it has its own immediate objective, continuous pressure, and clear local resolution.

## Scene

A **scene** is a coherent unit of play with one immediate focus, one continuous situation, and one local dramatic question.
A scene may contain multiple beats and may include one or more encounters if they remain part of the same continuous situation.

## Resolved Scene

A **resolved scene** is a scene whose immediate dramatic question has been answered clearly enough to adjudicate local outcome.
Once a scene is resolved, tag advancement may be adjudicated.

## Job / Contract

A **job** or **contract** is a higher-level objective that may span multiple scenes, locations, and encounters.
A job is not automatically one scene.
A job may contain several resolved scenes.

Higher-level scope governance — when an arc crosses its scene budget, when scope expands, when missions decompose into multi-leg objectives — is handled by the arc system. See `arc-rules.md`. Scene-level pacing remains as documented here.

## Consequence Chain

A **consequence chain** is the full linked sequence of outcomes that belongs to one continuing stake structure.
A consequence chain may span multiple scenes.
Once the chain's consequences are settled, AP may be adjudicated.

---

## Boundary Rules

### When multiple beats are still one scene

Multiple beats are still one scene if they all remain inside the same immediate situation and the same local dramatic question.
Examples:
- negotiating, then producing evidence, then reacting to a counteroffer in one uninterrupted audience
- sneaking through a checkpoint, hiding, then bluffing the same patrol in one continuous infiltration sequence
- climbing, slipping, and making a final pull to the same ledge in one continuous obstacle sequence

### When an encounter is not a new scene

An encounter is not a new scene if it is only one phase of the same ongoing local situation.
Do not split a scene merely because pressure changes.

### When a new scene starts

A new scene starts when at least one of the following changes clearly:
- the immediate objective
- the governing local question
- the active situation or location context
- the main participants or pressure structure
- the action has clearly transitioned out of the prior resolved situation

### When routine travel / guard duty / repeated low-novelty action should be compressed

Compress routine or low-novelty action instead of treating each repetition as a new scene.
Examples:
- uneventful travel legs
- routine guard rotations
- repeated scanning, waiting, or camp maintenance
- repeated low-variation labor without a new dramatic question

Compression is preferred unless a new meaningful decision, threat, discovery, or consequence boundary appears.

### When multiple scenes may still belong to one AP consequence chain

Multiple scenes may still belong to one AP consequence chain if they are all contributing to the same unresolved higher-stakes outcome.
Examples:
- several job legs serving one contract outcome
- infiltration, negotiation, and extraction all tied to one continuing commissioned objective
- a pursuit across several locations where the larger stakes are not settled until the final capture, escape, or loss

In these cases:
- tag advancement may be adjudicated per resolved scene
- AP waits until the consequence chain resolves

---

## Log Entry Discipline

The `log_entry` is for narrative state, not state already tracked in structured fields. Character HP, equipment, coin, AP, tag tiers, and calendar are read directly from their dedicated fields; do not narrate them again in the log.

**Include in the log:**
- new discoveries
- decisions that changed direction
- major NPC conversations
- confirmed links between people, places, or factions
- escalations
- handoffs to authorities
- closures of active arcs
- newly opened live threads

**Exclude from the log:**
- calendar or time corrections
- inventory normalizations or purchases
- coin totals and spend
- AP awards, tag advancement, point increases
- "state correction" lines that do not change the fiction
- routine rest, eat, or trance beats unless they matter to pacing
- blow-by-blow combat unless the fight changes the arc

Per-arc beats belong on the Arc record via `/arc/.../progress` or `/arc/.../transition`, not the global log. The global `log_entry` is for non-arc narrative state and arc-level outcomes (closure summaries, transitions visible to the wider world).

Use typed log entries when they apply: `closure_summary` for arc closures (with structured payload), `compression` for synthesizing prior beats, `narrative_non_arc` for narrative beats outside any active arc, `world_change` for durable world state changes.

When in doubt, ask: would another instance of the narrator, reading this log fresh tomorrow, need this entry to know what is going on in the story? If no — exclude. If the answer is in a structured field — exclude.

---

## Companion Role Preservation

When the player gives multi-vector commands assigning distinct roles to characters or companions (for example: "Dusk scouts wide, Serel covers, Sylvara advances on the line"), the narration must resolve each vector separately. Compressing distinct tactical roles into one blended maneuver erases player tactics and reduces companions to "better tracking attached to the player."

A multi-vector command is identifiable by:

- explicit role-per-actor assignment ("Dusk does X, you do Y, Serel does Z")
- spatial separation requested ("Dusk flanks while you press the line")
- distinct timing or trigger requested ("hold here, signal them in when X happens")

When such a command is received:

- Each named actor's vector resolves separately in the narration.
- Distinct rolls or reads are made when each vector requires one.
- The outcome describes what each vector produced, not just what the player observed.
- Companions used as autonomous tactical assets ("Dusk gets ahead, comes around the blind") are not flattened into "you and Dusk move together."

If a single roll is genuinely sufficient for a coordinated action, say so — do not invent multiple rolls where the player asked for one. The rule is: respect the structure the player set, do not override it.
