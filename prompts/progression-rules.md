# Mystic Weave — Progression Rules

This document is the canonical narrator-facing source for progression
adjudication: when tag advances trigger, what counts as an understanding
event, and what makes an arc AP-eligible. Backend handles validation,
counter rollover, and spend math.

Scene-boundary vocabulary is canonical in `prompts/scene-structure.md`.

---

## Core Model

Mystic Weave has three progression mechanics:

| Source | Trigger | Allocation |
|---|---|---|
| Tag advancement | Per-tier triggers in resolved scenes | The triggered tag |
| AP (fungible pool) | Tag-counter rollover OR awarded AP grant | Single pool, spendable on any domain |
| Domain spend | AP spend by player | Target domain, bracketed cost |

Tag advancement is adjudicated per **resolved scene**. AP earning is mechanical (the backend converts every 3 tag advances into 1 AP). Awarded AP is arc-bound and reserved for formal-contract-qualified arcs.

The terms **beat**, **encounter**, **scene**, **job**, and **contract** are not interchangeable. Use scene-structure vocabulary precisely.

---

## Backend Authority

Progression validation and commit are backend-authoritative. The narrator's role is judgment and proposal:

- **Judgment** — did the trigger fire? Is this scene worth a tag advance? Which tag fits?
- **Proposal** — submit scene actions and (optionally) one proposed tag advance via `POST /narrator/scene_resolved`.

The backend handles structural validation, parent-cap enforcement, registry classification, counter rollover, AP earning, and atomic commit. The orchestrator returns ranked candidates with explicit/implicit/contextual fit so the narrator can see strongest-fit candidates and self-correct on subsequent scenes if a stronger match was omitted.

Direct calls to `/progression/scan` and `/progression/commit` exist in the full API for testing and admin work but are not the primary narrator path. Use the orchestrator.

Maximum one tag advance per resolved scene; the backend enforces this via the scene-record `tag_advance_committed` flag. Parent-cap (an application's tier may not exceed its parent group; a spell mastery may not exceed its parent field) is structurally enforced at model construction. AP-counter rollover (every 3 advances → +1 AP) and bracket-cost math on domain spend are computed by the backend; the narrator does not author these values.

---

## Tag advancement boundaries

- One tag advance per resolved scene, across all layers combined (backend-enforced).
- The narrator proposes the tag most central to the scene's resolution. If multiple tags qualify equally, the player chooses.
- New tags may be proposed at T1 if the character demonstrates repeated meaningful use of a skill not covered by an existing tag. **Newly proposed tags require player confirmation before submitting via the orchestrator.**

---

## Track 1 — Tag Advancement

Tags are narrative and use-based. They do not consume AP. Tag tier cap is **T5**.

A tag may advance by one tier when the corresponding trigger fires in a resolved scene. The three layers have different triggers because they represent different things.

### Application — technique

An application advances when, in a single resolved scene, **all three** are true:

1. The character made at least one **contested roll** using that application at Standard difficulty or harder. Trivial and Easy rolls do not count.
2. The situation presented a **meaningfully new challenge** for that application — a class of opponent, environment, condition, or stakes the character has not previously cleared at the current tier.
3. The outcome **materially shaped the scene**. Success or fail-forward changed what happens next; a flat null beat does not qualify.

The novelty test (criterion 2) is **per-tier**. Once an application advances from T1 to T2 by clearing a class of challenge, that class no longer qualifies for further advancement until the character encounters a context that pressures T2 specifically. This produces natural diminishing returns — repetition stops paying without an explicit counter.

### Knowledge — understanding

A knowledge group advances when the character engages in an **understanding event** within that domain — pulling signal from raw material and constructing something they did not have before. Forms include but are not limited to:

- **Forensic** — examined evidence, tracks, wounds, ruins, documents, or aftermath and inferred something non-obvious
- **Observational** — watched a practitioner, system, or phenomenon closely enough to extract pattern
- **Investigative** — followed a chain of inference across a scene to a conclusion that was not given
- **Instructional** — received direct teaching from someone who knows more
- **Reflective** — integrated a major resolved experience into a clearer model than before
- **Experimental** — tested a hypothesis against the world and updated based on the result
- **Documentary** — extracted information from preserved sources: text, oral tradition, recorded testimony

The qualifier across all forms: the character ended the scene understanding something they did not understand walking in, and the understanding was **earned through engagement**, not handed over as exposition.

A bystander overhearing a fact does not qualify. A character working through it does. Knowledge does **not** grow from repeated practice; that is what application is for.

### Field — magical understanding

Magical fields advance under the same trigger structure as knowledge groups, applied to magical material: studying a working, observing a master cast, reading a treatise, reflecting on a resolved magical encounter. Field tiers remain gated by domain score per `magic-rules.md`.

---

## Track 2 — Awarded AP (arc-bound)

Awarded AP is arc-bound and reserved for formal-contract-qualified arcs. It resolves through `POST /arc/{arc_id}/settle` when an arc transitions to `complete`. Emergent arcs cannot earn AP — see `arc-rules.md` for the full arc system procedure including origin/phase rules.

**Rules:**

- **Pre-declared through arc creation.** AP awards must be within the arc's formal reward envelope before the work. Retroactive AP awards are not permitted.
- **Failure default.** Failed arcs grant 0 AP. Non-AP consequences still settle.

**Formal provenance required.** Not every quest-giver can offer AP. AP requires explicit patron, objective, and expected return at arc creation. The patron or stake should be weighty enough to genuinely shape a person:

- Council-level factions or institutional patrons of comparable weight
- Named figures of regional or higher significance acting in their capacity
- Oath-bound commitments and binding pacts
- World-imposed stakes (a god's task, a sworn duty, a binding magical contract)

Mortal-scale errands, emergent discoveries, and routine commercial work pay coin, reputation, access, leverage, or items, not AP.

**Scale:**

| Commitment | Awarded AP |
|---|---:|
| Specific delicate task with real stake | 1 |
| Multi-leg mission of meaningful consequence | 2 |
| Regional-scale undertaking | 3 |
| Campaign-defining oath, pact, or arc commitment | 4 |

Higher awards are possible in extraordinary cases but should be authored explicitly.

**Stacking.** Awarded AP does not replace coin, reputation, favor, items, leverage, or obligations. Arc settlement enumerates each reward channel independently.

---

## Track 3 — Domain Spend

Domain points are purchased with AP from the fungible pool. Domain score cap is **80**. Bracket-cost math is computed by `POST /character/{session_id}/spend_ap`; narrator does not author cost in payloads.

**Spend timing.** The player may spend AP at any time outside an unresolved scene.
