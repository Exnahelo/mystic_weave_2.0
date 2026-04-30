# Mystic Weave — Progression Rules

This document is the sole canonical source for progression adjudication.
Use it for tag advancement, AP earning, AP spend, and progression-related save timing.

Scene-boundary vocabulary is canonical in `prompts/scene-structure.md`.

---

## Core Model

Mystic Weave has three progression mechanics:

| Source | Trigger | Allocation |
|---|---|---|
| Tag advancement | Per-tier triggers in resolved scenes | The triggered tag |
| AP (fungible pool) | Tag-counter rollover OR awarded AP grant | Single pool, spendable on any domain |
| Domain spend | AP spend by player | Target domain, bracketed cost |

Tag advancement is adjudicated per **resolved scene**. AP earning is mechanical (the backend converts every 3 tag advances into 1 AP). Awarded AP is contract-bound and resolves when the contract resolves.

The terms **beat**, **encounter**, **scene**, **job**, and **contract** are not interchangeable. Use scene-structure vocabulary precisely.

---

## Track 1 — Tag Advancement

Tags are narrative and use-based. They do not consume AP. Tag tier cap is **T5**.

A tag may advance by one tier when the corresponding trigger fires in a resolved scene. **Maximum one tag advance per scene** across all layers; if multiple tags qualify, the player chooses.

The three layers have different triggers because they represent different things.

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

Magical fields advance under the same trigger structure as knowledge groups, applied to magical material. Field knowledge advances through understanding events about magic: studying a working, observing a master cast, reading a treatise, reflecting on a resolved magical encounter. Field tiers remain gated by domain score per `magic-rules.md`.

### Tag advancement boundaries

- One tag advance per resolved scene, across all layers combined.
- The GPT proposes the tag most central to the scene's resolution. If multiple tags qualify equally, the player chooses.
- New tags may be proposed at T1 if the character demonstrates repeated meaningful use of a skill not covered by an existing tag. **Newly proposed tags require player confirmation before saving.**
- Per-session tag advance caps are removed; the per-tier novelty test in the application trigger replaces that brake.

### Parent-cap rule

An application tag may not exceed the tier of its parent knowledge group.

Exception: if an application was seeded above its parent at character creation (for example, a Focus granted the application at T2 while the parent knowledge is T1), the application does not regress, but cannot advance further until the parent catches up.

The backend enforces this rule at write time. The GPT verifies the cap at adjudication time and either advances the parent first if the scene supports that, or selects a different candidate.

---

## Track 2 — AP (Fungible Pool)

AP lives in a single fungible pool — `points_available` on the character's advancement state. AP can be earned in two ways:

### Tag-counter rollover (mechanical)

Every tag tier advance increments a single `tag_counter`. When the counter reaches 3, it resets to 0 and the pool gains 1 AP. Knowledge, application, and field advances all count equally. The backend handles all counter math; the GPT does not compute it.

### Awarded AP (contract-bound)

Awarded AP is rare, pre-declared, and granted when a significant contract resolves.

**Rules:**

- **Pre-declared.** AP awards must be on the table before the work, as part of the contract or commitment. Retroactive AP awards are not permitted.
- **Failure default.** If the character fails to complete the contract, no AP is granted unless the contract specifies partial payout.

**Standing required.** Not every quest-giver can offer AP. AP awards come from forces with the standing or stake to genuinely shape a person:

- Council-level factions or institutional patrons of comparable weight
- Named figures of regional or higher significance acting in their capacity
- Oath-bound commitments and binding pacts
- World-imposed stakes (a god's task, a sworn duty, a binding magical contract)

Mortal-scale errands and routine commercial work pay coin and reputation, not AP. A hedge wizard offering 5 AP for a lost cat is not legitimate; the economy depends on this gate holding.

**Scale:**

| Commitment | Awarded AP |
|---|---:|
| Specific delicate task with real stake | 1 |
| Multi-leg mission of meaningful consequence | 2 |
| Regional-scale undertaking | 3 |
| Campaign-defining oath, pact, or arc commitment | 4 |

Higher awards are possible in extraordinary cases but should be authored explicitly, not formula-derived.

**Stacking.** Awarded AP does not replace coin, reputation, or favor. A Council contract pays all of them. Awarded AP is what makes a contract meaningful when the character no longer needs the coin or the reputation.

---

## Track 3 — Domain Spend

Domain points are purchased with AP from the fungible pool. Domain score cap is **80**.

| Target score bracket | AP cost per point |
|---|---:|
| 25–60 | 1 |
| 61–70 | 2 |
| 71–80 | 3 |

For multi-point increases that cross brackets, calculate AP point-by-point using the bracket of each resulting score. The backend handles bracket math.

**Spend timing.** The player may spend AP at any time outside an unresolved scene. If the player chooses to spend AP at scene resolution as part of the reward package, that spend is part of the same progression adjudication sequence.

---

## Reward Adjudication Boundary

Resolve the full reward package before any progression-related save.

The reward package may include:

- tag advancement
- newly proposed tags (requires player confirmation)
- tag-counter increments and AP rollover (mechanical, but reflected in the same save)
- awarded AP grant (if a contract resolved this scene)
- AP spend (if the player chooses to spend at resolution)

Progression-related state is **not stable enough to save** until the reward package is settled.

---

## Progression Save Gate

No progression-related save occurs until the final reward package is settled.

- Do not save tag advancement before scene-resolution adjudication is finalized.
- Do not save newly added tags before player confirmation.
- Do not save AP changes (rollover, awarded, or spent) before the reward package is finalized.
- If the player disputes any part of the reward interpretation, do not commit disputed elements.

Other unrelated state may be saved only if the save payload does not modify tag tiers, newly proposed tags, AP pool, tag counter, or domain scores, and does not narratively imply that the reward ruling is settled.

---

## Operational Adjudication Order

When a scene resolves:

1. Determine whether the **scene** is resolved for tag-adjudication purposes (per `scene-structure.md`).
2. Evaluate tag advancement triggers in order: application, knowledge, field. At most one fires.
3. If a contract or commitment resolved this scene and that contract specified an AP award, grant the awarded AP per the contract terms.
4. If the player chooses to spend AP at resolution, resolve that spend in the same sequence.
5. Ask for player confirmation if a new tag would be added.
6. If the player disputes any reward element, pause progression-related save.
7. Save progression-related state only after the reward package is settled.

The backend handles:

- tag-counter increment and rollover to AP
- parent-cap enforcement on application tier writes
- domain bracket cost math on AP spend

The GPT does not compute these. It announces what triggered, asks any required player choices, and submits the resolved reward package.