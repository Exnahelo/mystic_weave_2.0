# Mystic Weave — Arc Rules

Version 1.0 — April 2026
Status: Canonical. Upload to GPT builder as a knowledge file.

---

## Purpose

This file contains the GPT-facing rules for how higher-level objectives are tracked, governed, and resolved in Mystic Weave.

Higher-level objectives include investigations, missions, expeditions, contracts, containment operations, diplomatic undertakings, and other pursued goals larger than one resolved scene.

It defines:

- the arc type system
- lifecycle states
- backend endpoint requirements
- formal-contract-only AP policy
- spawn-as-expected scope control
- closure, failure, and settlement procedures
- reward-channel enumeration at settlement

Use this file together with:

- `progression-rules.md` for AP, tag advancement, and progression save gates
- `engine.md` for turn-loop adjudication procedure
- `scene-structure.md` for scene-level vocabulary
- `pacing-rules.md` if present for pacing budget interaction
- `character-rules.md` for reputation, faction, and consequence propagation

---

## Core Principle

The backend is authoritative for arc structure. The narrator proposes; the backend validates and records.

When an event introduces a higher-level objective, the narrator must call `POST /arc/{session_id}/create` before continuing that narrative arc. Continuing without creating the arc is a structural error.

Lifecycle changes (`/transition`, `/spawn`, `/settle`) remain narrator-driven and are required at the moments described later in this document. Scene-level progression (`/progress`) is now handled automatically by the orchestrator when the narrator submits `arc_progressed_ids` via `POST /narrator/scene_resolved`; manual `/progress` calls remain available but are not the primary path.

The narrator does not have discretion to skip the lifecycle calls.

---

## Backend Authority

Arc envelope tracking — scenes used, locations visited, soft/hard cap conditions, phase-shift candidacy for emergent arcs — is computed by the backend and surfaced in `arc_envelope_status` on every scene-resolved response. The narrator does not count scenes, locations, or contributions manually. The orchestrator routes scene contributions to active arcs via `arc_progressed_ids`.

The narrator's role for arcs is judgment and lifecycle decisions: when to create, when to spawn vs replace vs merge, when to transition to closure paths, when to settle. The backend cannot judge whether institutional phase has begun or whether two scenes belong to the same consequence chain — those are creative decisions. The backend can validate that the structural conditions for a given lifecycle action are met.

---

## What Counts as an Arc-Shaped Event

An arc-shaped event is any fiction event that creates or meaningfully advances a goal larger than the immediate scene.

Typical creation events:

- a patron requests an investigation
- a faction offers a contract
- the player commits to an expedition
- an emergent mystery becomes a pursued goal
- a threat becomes a named containment objective
- a recovery, escort, infiltration, or surveillance operation is accepted
- an oath or binding pact defines future work
- a local problem is promoted into a structured undertaking

Typical progress events:

- a resolved scene produces evidence for an investigation
- a travel leg meaningfully advances an expedition
- a negotiation secures a required concession
- an encounter removes or changes an obstacle
- a discovery narrows the target
- a conflict resolves a mission leg
- a location is searched, mapped, infiltrated, cleansed, or secured for the arc

Typical transition events:

- the player accepts an available arc
- closure conditions become satisfied
- the objective becomes impossible
- the player abandons the work
- the arc reaches hard scope cap
- the arc is replaced by a successor
- a child arc merges into its parent

Typical spawn events:

- one investigation reveals a distinct sub-operation
- one mission crosses beyond its location budget
- the controlling faction pressure changes
- the immediate subtype changes
- a parent undertaking decomposes into separable legs
- a specific raid, parley, ritual, or rescue emerges from broader work

---

## Non-Arc Events

Not every scene creates an arc.

Do not create an arc for:

- a single throwaway obstacle
- incidental shopping
- ordinary travel with no higher-level commitment
- a scene-level dramatic question that fully resolves in the same scene
- flavor conversation without an objective
- routine recovery or resupply
- a rumor the player hears but does not pursue

If the player later chooses to pursue a rumor as a goal, create the arc then.

If the player declines a patron's offer, the narrator may create a `proposed` or `available` arc only if the offer remains structurally available in the world.

---

## Arc Types

There are five primary arc types, ordered by scope.

The type determines default budget envelopes and AP envelope limits.

The type is not a prestige label.

Choose the smallest type that honestly fits the objective.

### task_local

A single-location, single-objective task with limited consequences.

Examples:

- deliver a sealed letter across town
- find a missing tool in a known district
- escort someone through one local hazard
- resolve a contained household, shop, grove, or shrine problem

Default envelope:

- Stake scale: local
- Scene budget: 2 soft / 4 hard
- Location budget: 1 soft / 2 hard
- AP envelope: 0–1 if formal, 0 if emergent

Use this type when the objective has one main place, one main problem, and limited wider consequences.

Do not inflate a local task into a mission because the narration is interesting.

### contract_delicate

A formally tasked but contained matter requiring careful handling.

This is the classic delicate situation: a specific patron, a sensitive objective, and an expected return.

Examples:

- recover evidence without exposing the patron
- negotiate a single fraught handoff
- secure one person, item, or confession without public scandal
- handle a focused problem where tact matters as much as success

Default envelope:

- Stake scale: situational
- Scene budget: 4 soft / 6 hard
- Location budget: 2 soft / 3 hard
- AP envelope: exactly 1 if formal, 0 if emergent

Use this type when the structure is contained but politically, socially, or magically sensitive.

### mission_multi_leg

A multi-stage objective with several distinct beats.

Examples:

- investigate a suspect network across several scenes
- surveil a route, identify handlers, and recover proof
- locate a missing person through multiple leads
- perform a recovery mission with approach, obstacle, and extraction legs

Default envelope:

- Stake scale: situational
- Scene budget: 6 soft / 10 hard
- Location budget: 3 soft / 5 hard
- AP envelope: 1–2 if formal, 0 if emergent

Use this type when the objective has several meaningful legs but remains one coherent mission.

### undertaking_regional

A large arc affecting a region, multiple factions, or significant world state.

Examples:

- investigate corruption affecting a watershed
- contain a regional magical hazard
- broker peace among multiple factions
- dismantle a network with regional consequences

Default envelope:

- Stake scale: regional
- Scene budget: 10 soft / 16 hard
- Location budget: 4 soft / 7 hard
- AP envelope: 2–3 if formal, 0 if emergent

Use this type when the consequence map is regional, not merely local.

Expect this type to spawn child arcs.

### arc_campaign

A campaign-level arc spanning major character development, major world consequences, or multi-mission narratives.

Examples:

- fulfill a defining oath
- resolve a campaign-defining mystery
- confront a realm-shaping antagonist through multiple operations
- complete a multi-mission pact with lasting world-state consequences

Default envelope:

- Stake scale: campaign
- Scene budget: 16 soft / 24 hard
- Location budget: 6 soft / 12 hard
- AP envelope: 3–4 if formal, 0 if emergent

Use sparingly.

If a campaign arc starts absorbing every active problem, spawn child arcs instead.

---

## Subtypes

Subtype describes fictional shape, not reward scale.

Subtype is required at creation.

Allowed common subtypes:

- investigation
- recovery
- escort
- containment
- diplomatic
- expedition
- infiltration
- defense
- delivery
- ritual
- oath
- survival
- hunting
- political
- surveillance
- seizure

The subtype affects expected closure conditions and consequence patterns.

It does not directly change the AP envelope.

Use the nearest subtype when multiple apply.

If a broader investigation becomes a raid, spawn a seizure child arc rather than rewriting the parent subtype.

---

## Origin vs Phase

An arc has both an origin and a phase.

**Origin** is how the arc was first authored. It is set at creation and never changes.

- `formal` — created with explicit patron, objective, and expected return
- `emergent` — discovered or developed without formal tasking
- `derived` — spawned from another arc; inherits origin behavior from creation parameters

**Phase** is the arc's current operational character. It changes as play develops.

- *field phase* — the arc is unfolding through immediate action and discovery
- *institutional phase* — formal organizations, councils, patrons, or named authorities have engaged the matter
- *closure phase* — settlement, ruling, or conclusion is imminent

Origin is permanent. Phase is mutable. The two interact:

- A `formal` arc that begins in field phase remains AP-eligible regardless of phase changes
- An `emergent` arc that shifts to institutional phase is **required** to spawn a formal child arc if the formal-contract conditions are now met (patron, explicit objective, expected return)
- The parent emergent arc keeps its origin (history doesn't rewrite); the formal child captures the AP-eligible institutional work going forward
- An `emergent` arc that never reaches institutional phase remains AP-ineligible at settlement

Origin governs AP eligibility for the arc's own settlement. Phase governs whether a formal child should be spawned to own the institutional leg.

A derived child's AP eligibility is determined at the child's own creation, independent of the parent.

A patron-adjacent event is not automatically formal. Trust networks, family connections, social proximity, and noble status do not confer formal status. Formal status requires the three explicit conditions met at the child arc's creation.

---

## Phase Change Indicators

An emergent arc has shifted to institutional phase when one or more of the following structural conditions are met:

1. **Council, court, or formal review body** has accepted the matter under documented authority
2. **Named patron** (NPC or faction) has issued explicit tasking with declared scope
3. **Formal organization** (Heartwardens, Greenshields, Druids, Council, House intelligence body, etc.) has formally adopted the matter under their own chain of custody
4. **Documented mandate** has been issued (sealed letter, council ruling, signed contract, formal evidentiary log entry)
5. **Multiple formal organizations** have engaged the matter through a recognized handoff or joint review

When any of these conditions are met for an emergent arc, the narrator **must** spawn a formal child arc to own the institutional phase. The parent emergent arc continues to track the field-phase work; the formal child captures the AP-eligible institutional work.

The orchestrator surfaces phase-shift candidacy when an emergent arc crosses its soft cap. This is a *suggestion*, not a forced action — the narrator confirms whether the structural conditions above have actually been met before spawning. An emergent arc can pass its soft cap without triggering a phase change (e.g., long field investigation that hasn't yet reached institutional engagement).

The orchestrator suggestion appears in the `suggestions` list of the scene-resolved response, and the relevant arc's `arc_envelope_status` entry has `phase_shift_candidate: true`.

When spawning a formal child:

- The child must be created with `formal_contract_qualified: true`
- All three formal qualification fields must be present and accurate: `patron_npc_id` or `patron_faction`, `explicit_objective`, `expected_return`
- The child's AP envelope is determined at child creation per the formal arc rules
- `ap_ownership='child'` (the parent emergent has no AP envelope to partition)
- The child's `parent_arc_id` references the emergent parent

When **not** to spawn a formal child:

- The institutional engagement is incidental (a single formal NPC appearing in a scene without the matter being adopted)
- The matter is being delivered into authority for closure, not for ongoing institutional work (use settlement instead)
- The narrator has not yet confirmed the structural conditions in this section
- The arc has already settled

---

## Formal-Contract-Only AP

Only formal-contract-qualified arcs can award AP.

An arc is formal-contract-qualified only when all three are explicit at creation:

1. A patron is identified through `patron_npc_id` or `patron_faction`
2. An explicit objective is stated
3. An expected return or deliverable is named

The narrator must not infer formal status from social context alone.

The following do not confer formal status:

- introductions through trust networks
- family connections
- social proximity
- noble status of a related house
- being owed a favor
- discovering a problem near a patron's interests
- overhearing a need
- finding evidence before being tasked
- deciding privately to help

Emergent arcs may be created with `formal_contract_qualified: false`.

Emergent arcs cannot earn AP.

Emergent arcs can still earn:

- reputation
- coin or goods
- leverage
- obligations
- access
- items
- world-state changes
- tag advancement through resolved scenes

An emergent arc cannot be converted in place. Origin is permanent.

When an emergent arc reaches institutional phase (see Phase Change Indicators), spawn a formal child arc rather than re-authoring the parent.

The formal child captures AP-eligible institutional work going forward. The parent emergent arc continues tracking field-phase work and settles per emergent rules.

Do not retroactively mark already-completed emergent work as formal. Closed arcs are immutable.

If the institutional phase has fully resolved by the time the narrator recognizes the shift (e.g., council ruling already issued), the formal child may be created and immediately settled — but the AP-eligible work must have actually occurred during the formal child's existence, not before its creation.

---

## AP Ownership

AP ownership prevents one objective branch from paying AP multiple times.

At spawn, ownership must be clear.

Default expectations:

- formal parent + emergent child: parent retains AP ownership
- formal parent + formal child: explicitly partition ownership
- emergent parent: no AP exists to partition
- emergent child: `ap_ownership` should normally be `none` unless newly formalized by explicit patron tasking

Only one arc in a formal objective branch should own AP for the same work.

If a child owns AP, the parent must not also pay AP for that child's completed work.

If the parent owns AP, child settlements should use zero AP.

If unsure, keep AP on the parent and make child arcs structural only.

---

## Spawn-as-Expected

When an arc crosses meaningful structural boundaries, spawn a child arc rather than letting the parent sprawl.

Structural boundaries include:

- major location boundaries beyond the arc envelope
- a change in primary stake structure
- a change in principal faction pressure
- a shift from one subtype-shaped objective to another
- a distinct operation emerging from broader work
- a branch that can succeed or fail independently
- a new patron formally tasking a sub-objective

Spawned child arcs consume their own scene and location envelopes.

The parent remains open until its closure conditions are satisfied.

The parent may depend on child outcomes.

Spawning is not failure.

Spawning is the normal way to preserve bounded scope.

Example decomposition:

- Parent: undertaking_regional, `Heartwater corruption investigation`
- Child: mission_multi_leg, `basin reconnaissance`
- Child: mission_multi_leg, `Thornveil surveillance`
- Child: contract_delicate, `Greenlace seizure operation`

Each child has its own closure conditions.

The parent settles only after the required children settle or merge.

---

## Spawn vs Replace vs Merge

When a structural boundary is crossed during play, three responses exist. Picking the right one is what keeps the arc registry honest.

**Spawn (default).** A new bounded scope opens alongside the parent. Both arcs persist; both have their own closure conditions; the parent may depend on child outcomes but remains its own arc. Use spawn when the new work is distinct from the parent's path, when both could succeed independently, or when a patron formally tasks a sub-objective.

Test: *Are both arcs needed? Could either succeed without the other?* → if yes, spawn.

**Replace.** The original arc's objective has become moot, impossible, or fundamentally redirected, but a successor objective emerges from the same situation. The original arc closes with `replaced_by_successor`. A new arc takes its place. Use replace when the original closure conditions can no longer be met but a new shape of the same broad mandate is now in motion.

Test: *Has the original objective become unachievable, with a new objective emerging from the same situation?* → if yes, replace. Do not replace just because the path is harder; replace only when the original objective itself has shifted.

**Merge.** An emergent or distinct child arc turns out to be serving the parent's closure conditions rather than its own. The child closes with `merged_into_parent`; its progress and rewards apply to the parent. Use merge when an apparently-distinct thread is actually a sub-component of an existing arc, recognized only after work began.

Test: *Is this arc serving the parent's closure rather than its own?* → if yes, merge. Do not merge just because the arcs are related; merge only when one is genuinely subordinate.

When uncertain, default to spawn. Spawning preserves the most narrative state and the most bounded scope. Replace and merge each erase one arc's identity; that should require evidence, not convenience.

Boundary cases:

- New patron formally tasks a sub-objective → spawn (formal child of parent).
- Mid-investigation lead dies, but a different lead emerges → replace (failed lead → new lead).
- Emergent thread turns out to be solving the parent's actual problem → merge.
- Player pursues a side-objective that doesn't bear on the main arc → spawn (independent).
- Two arcs converge on the same outcome and one becomes redundant → merge the redundant one into the kept one.

---

## Lifecycle States

```text
proposed → available → in_progress → at_scope_cap → ready_to_close → complete
                                                  ↘                ↘
                                                   failed           failed
                       in_progress → ready_to_close → failed
                       in_progress → abandoned
                       in_progress → replaced_by_successor
                       in_progress → merged_into_parent
```

### proposed

The arc exists as a candidate.

It may not yet be player-facing.

Use when the backend needs to record a possible structured objective before it is offered.

### available

The arc is offered, discoverable, or available for acceptance.

Use for patron offers, posted contracts, known opportunities, or visible threats the player can choose to pursue.

### in_progress

The arc is active and consuming scope budget.

Use when the player has committed to the objective.

Resolved scenes within the arc call `/progress`.

### at_scope_cap

The hard cap has been reached.

Ordinary continuation is refused until transition.

The narrator must call `/transition` next.

Appropriate transitions include ready_to_close, failed, replaced_by_successor, or merged_into_parent depending on facts.

### ready_to_close

Closure conditions are satisfied.

The next required step is settlement.

Do not narrate rewards as final until `/settle` succeeds.

### complete

The arc closed successfully.

This is terminal.

Rewards and consequence events have been recorded.

### failed

The arc closed unsuccessfully.

This is terminal.

Failure may still produce consequences and non-AP rewards.

### abandoned

The player disengaged without satisfying closure.

This is terminal unless a later successor is created as a new arc.

### replaced_by_successor

The arc is closed because a successor owns forward progression.

This is terminal for the replaced arc.

Use when the objective fundamentally changes rather than merely spawning a child.

### merged_into_parent

A child arc contributes to parent settlement.

This is terminal for the child.

Use when the child did not produce independent terminal reward settlement but resolved a parent condition.

---

## Required Backend Calls

The following calls are mandatory when their triggers occur.

Failing to use them is a structural error.

The narrator manages arc lifecycle through a handful of explicit calls. Most arc activity during play is now driven by the orchestrator, which tracks scene contributions automatically.

### `POST /arc/{session_id}/{arc_id}/create`

Call when a higher-level objective is introduced. The narrator does not begin an arc narratively without first creating it. Required fields and validation are documented in the OpenAPI spec; the endpoint rejects malformed payloads with structured errors.

For emergent arcs: `formal_contract_qualified: false`. For formal arcs: include patron (`patron_npc_id` or `patron_faction`), `explicit_objective`, and `expected_return` — backend validates these at create time.

### `POST /arc/{session_id}/{arc_id}/progress`

**No longer required during normal play.** The orchestrator records arc-progression contributions via `arc_progressed_ids` in the `/narrator/scene_resolved` payload. Direct `/progress` calls remain available for legacy flows or admin work but are not the narrator's primary surface.

**Time-skip discipline still applies** at the orchestrator level: do not declare scene resolutions for waiting periods (NPC arrival, message reply, scheduled event). State that time passes and wait for the next meaningful trigger. `arc_progressed_ids` should be omitted from waiting-period scenes.

### `POST /arc/{session_id}/{arc_id}/transition`

Call when an arc moves through lifecycle states — typically when the orchestrator surfaces `arc_envelope_status[i].hard_cap_reached: true` (auto-transition to `at_scope_cap`) and the narrator must `/transition` to a closure path before continuing. The backend validates the transition matrix and rejects stale `from_state` values. For `ready_to_close`, closure conditions must be satisfied. For `failed`, authored failure conditions are checked; pass `force: true` only for unforeseen failure modes, not convenience.

### `POST /arc/{session_id}/{arc_id}/spawn`

Call when a structural boundary requires a child arc — including the emergent → formal phase shift per the Phase Change Indicators above. The orchestrator surfaces `phase_shift_candidate: true` for emergent arcs at soft cap; the narrator confirms the structural conditions before spawning.

Spawn children for separable work. Do not mutate a parent into a different shape simply because play expanded.

### `POST /arc/{session_id}/{arc_id}/settle`

Call when an arc resolves. Settlement enumerates all reward channels (outcome, awarded_ap, reputation_changes, coin_cd_awarded, coin_cd_forfeit, obligations_added, items_awarded, leverage_gained, notes); empty channels are explicit zeros or empty lists, not silent omissions. The endpoint enforces formal-contract eligibility for `awarded_ap > 0`.

---

## Settlement Validation Rules

The backend validates settlement.

The narrator must prepare payloads that respect these rules.

AP rules:

- `awarded_ap` must be 0 if outcome is `failed`
- `awarded_ap` must be 0 if the arc is not formal-contract-qualified
- `awarded_ap` must be within the arc AP envelope
- no partial AP on failure in v1
- AP ownership must not double-pay a parent/child branch

Reputation rules:

- deltas must stay within envelope bounds
- positive, negative, or mixed reputation may be appropriate
- faction propagation follows `character-rules.md`

Economy rules:

- coin awarded and coin forfeited are separate channels
- barter, obligations, and leverage are not the same as coin
- material rewards should be explicit

Parent/child rules:

- a parent cannot settle while AP-owning child arcs remain active
- children with parent-owned AP should settle with zero AP
- merged children contribute to parent closure rather than double-settling AP

---

## Closure Procedure

When an arc reaches objective completion:

1. Verify closure conditions are satisfied.
2. Call `/transition` with `to_state: ready_to_close`.
3. Pass required `world_flags` if closure conditions are flag-based.
4. Call `/settle` with actual reward result.
5. Narrate the settled result after backend success.
6. Save related state only after settlement succeeds.

Reward channels to enumerate:

- field tier advancement per `magic-rules.md`
- knowledge tag advancement per `progression-rules.md`
- application tag advancement per `progression-rules.md`
- tag-counter rollover AP if triggered by tag advancement
- awarded AP from arc settlement
- reputation changes
- coin, goods, items, or services
- leverage, evidence, access, or secrets
- obligations created, cleared, or worsened
- world-state consequences

Tag advancement remains scene-bound.

Awarded AP is arc-bound.

Do not collapse reward tracks into a single yes/no judgment.

Do not say "no further rewards" unless every channel has been considered.

---

## Failure Procedure

Failure is not zero-outcome.

Failed arcs cannot award AP in v1.

Failed arcs may still award or impose:

- reputation changes
- partial coin payment
- forfeited coin
- retained evidence
- leverage gained before failure
- obligations
- exposure penalties
- faction consequences
- future hooks

To transition to `failed`:

1. Check authored failure conditions.
2. If conditions are met, call `/transition` normally.
3. If conditions are not met but failure is necessary, call `/transition` with `force: true`.
4. If no failure conditions are authored, transition normally.
5. Call `/settle` with `outcome: "failed"` and `awarded_ap: 0`.

Always settle failed arcs.

Do not abandon the record because the fiction went badly.

---

## Abandonment Procedure

Use `abandoned` when the player disengages from an active arc without closure.

Abandonment is terminal for that record.

It may still produce world consequences.

If the same issue resurfaces later, create a successor arc rather than reopening the abandoned record unless backend policy explicitly supports reopening.

Abandoned arcs do not award AP.

Reputation or obligation consequences may still apply if fiction warrants.

---

## Scope-Cap Procedure

The hard cap is binding.

When `/progress` returns `auto_transitioned_to_at_scope_cap: true`:

1. Stop ordinary arc continuation.
2. Do not narrate another investigative or mission beat inside that arc.
3. Decide which structural transition fits the fiction.
4. Call `/transition`.
5. If the work needs to continue in a new shape, spawn or replace.

Allowed responses to hard cap include:

- close if conditions are satisfied
- fail if the arc exhausted its window
- replace with successor if the objective changed
- merge into parent if it was a child completing its contribution
- spawn a child if a separable branch should continue

Soft cap is advisory.

At soft cap, begin steering toward closure, spawn, or escalation.

Do not treat soft cap as permission to sprawl indefinitely.

---

## Relationship to Scenes

Each arc has a scene budget (soft cap, hard cap) determined by its `primary_type`. The orchestrator tracks resolved scenes per arc automatically and surfaces envelope status (`resolved_scenes_used`, `soft_cap_approaching`, `hard_cap_reached`, `phase_shift_candidate`) in the scene-resolved response. The narrator does not count scenes manually.

One resolved scene may advance more than one arc only if it genuinely changes each arc; list every advanced arc in `arc_progressed_ids`. Tag advancement is adjudicated at scene resolution; arc settlement is adjudicated at arc closure. These procedures may share a player-facing moment but remain separate mechanical channels.

When `soft_cap_approaching` becomes true, the orchestrator emits a closure suggestion (or for emergent arcs, a phase-shift suggestion — see Phase Change Indicators). When `hard_cap_reached` becomes true, the arc auto-transitions to `at_scope_cap`; the narrator must `/transition` to a closure path before continuing.

---

## Relationship to Pacing

Scene compression still applies. Routine travel or repeated low-novelty actions should not become extra resolved scenes merely to fill arc budget. Arc budget is not a quota; it is a maximum scope envelope. Do not declare scene resolutions for filler; do not omit `arc_progressed_ids` for a genuinely advanced arc just because an envelope is near cap.

---

## Narrator Checklist

At the start of a higher-level objective:

- Is this larger than one scene?
- Is there a patron?
- Is the objective explicit?
- Is the expected return explicit?
- Is the arc formal-contract-qualified?
- What is the smallest honest primary type?
- What subtype describes the fictional shape?
- What closure conditions are known?
- What failure conditions are known?
- Call `/create`.

After each resolved scene:

- Did the scene advance an active arc? List every advanced arc in `arc_progressed_ids` on the orchestrator payload — backend records progress and updates envelope status automatically.
- Read `arc_envelope_status` in the response: `hard_cap_reached` requires `/transition`; `phase_shift_candidate` requires evaluation against Phase Change Indicators and possibly `/spawn`; `soft_cap_approaching` is closure-time guidance.

When scope changes:

- Did location, faction, subtype, or stake structure change materially?
- Can this branch succeed or fail independently?
- Is it now a distinct operation?
- Call `/spawn` if yes.

At closure:

- Are closure conditions satisfied?
- Call `/transition` to `ready_to_close`.
- Enumerate every reward channel.
- Call `/settle`.
- Narrate the backend-approved result.

---

## When the Narrator Has No Choice

These are mandatory procedures:

- Arc-shaped event happens → call `/arc/{session_id}/create`
- Resolved scene advances an active arc → call `/progress`
- Arc state changes → call `/transition`
- Arc closes or fails → call `/settle`
- Arc scope changes meaningfully → call `/spawn`

When in doubt, prefer creating a bounded arc over untracked mission drift.

When scope expands, prefer spawning children over pushing one arc past its envelope.

When reward settlement occurs, enumerate every channel.

---

## Worked Example: Sylvara's Heartwater Investigation

Under the arc system, the Heartwater chain would be represented as one parent plus children.

Parent arc:

- type: undertaking_regional
- title: Heartwater corruption investigation
- patron: House Heartwood through Lethariel
- formal_contract_qualified: true
- ap_ownership: parent
- closure conditions: report delivered, evidence chain complete, faction state changed

Child 1:

- type: mission_multi_leg
- subtype: investigation
- title: Heartwater Basin reconnaissance
- ap_ownership: parent
- spawned when scope shifted to basin mapping

Child 2:

- type: mission_multi_leg
- subtype: surveillance
- title: Thornveil surveillance operation
- ap_ownership: parent
- spawned when basin evidence pointed at Thornveil-side pressure

Child 3:

- type: contract_delicate
- subtype: seizure
- title: Greenlace seizure operation
- ap_ownership: parent
- spawned when surveillance became a specific raid

When all required children settled or merged, the parent closure conditions evaluated.

The parent settlement could include AP, reputation changes, seized evidence leverage, obligations, and world-state consequences.

Total structure: four arc records, each scope-bounded and audit-traceable.

---

## Migration Note

Sylvara's existing play history, including the Heartwater chain and Thinwatch Spring, was completed before this system existed.

It remains untyped legacy.

Do not retroactively reconstruct old arcs.

New arcs created after Arc System v1 launch use this structure.