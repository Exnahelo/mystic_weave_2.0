# Mystic Weave — Progression Rules

This document is the sole canonical source for progression adjudication.
Use it for tag advancement, earned AP, awarded AP, domain spend, and progression-related save timing.

Scene-boundary vocabulary is canonical in `prompts/scene-structure.md`.

---

## Core Model

Mystic Weave has four progression sources, each with a distinct trigger:

| Source | Trigger | Allocation |
|---|---|---|
| Tag advancement | Layer-matched: technique, understanding, or domain push | The triggered tag |
| Earned AP | Every Nth tag advance in a domain | Locked to that domain |
| Domain push event | Pushed at a domain's outer envelope | Source domain (AP or direct point) |
| Awarded AP | Pre-declared contract reward | Free, player choice |

Tag advancement is adjudicated per **resolved scene**. AP earning has no scene-level adjudication — it is a mechanical consequence of tag advancement, computed by the backend. Awarded AP is contract-bound and resolves when the contract resolves.

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

### Domain push — core capability

A domain advances by one point when the character is **pushed at the domain's outer envelope** in a resolved scene. **All three** must be true:

1. The test demanded the **domain itself**, not a skill or technique riding on it.
2. The pressure **exceeded what the character has previously sustained** at this domain score.
3. The outcome was **earned** — succeeded under significant cost, or failed with consequence and recovery.

Examples by domain:

- **Power** — forced march carrying a wounded ally for hours after injury
- **Will** — held an oath under torture, magical compulsion, or moral pressure that should have broken it
- **Endurance** — survived deprivation, exposure, or sustained injury that would have killed someone weaker
- **Presence** — held a room of hostile or higher-status figures without losing footing
- **Perception** — read something true through conditions specifically designed or naturally suited to hide it
- **Intellect** — solved under genuine pressure a problem that demanded rigorous reasoning
- **Agility** — executed precision movement at the edge of what bodies can do

Domain pushes are rare by design. A character whose story does not push them does not grow domains through this trigger; they still grow via earned AP and awarded AP.

When a domain push triggers, the player chooses **one** of:
- **+1 AP in that domain** (banked for later spend)
- **+1 to that domain's score directly** (applied immediately, bypassing AP cost)

Not both. The direct point bypasses bracket cost.

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

## Track 2 — Earned AP

Earned AP is a mechanical consequence of tag advancement, not a separate adjudication.

**Rule:** Every **3 tag advances** within a domain earns **1 AP locked to that domain**.

- Each domain has its own counter and its own AP pool.
- Knowledge, application, and field tag advances all increment the counter equally.
- A tag's domain is the tag's primary domain. Cross-domain tags increment the **primary domain only**.
- The counter and pool are tracked in the backend. The GPT does not compute them; it announces tag advancement and the backend handles the rest.

Earned AP can only be spent on the domain it was earned in. A character who has played Power-heavy has Power-AP and can buy Power. They cannot redirect Power-AP into Presence.

This couples accomplishment to capability. A character grows in the directions they actually played.

---

## Track 3 — Awarded AP

Awarded AP is rare, pre-declared, and free-allocation across any domain.

### Rules

- **Pre-declared.** AP awards must be on the table before the work, as part of the contract or commitment. Retroactive AP awards are not permitted.
- **Free allocation.** Awarded AP can be spent on any domain, regardless of which trigger or contract earned it.
- **Failure default.** If the character fails to complete the contract, no AP is granted unless the contract specifies partial payout.

### Standing required

Not every quest-giver can offer AP. AP awards come from forces with the standing or stake to genuinely shape a person:

- Council-level factions or institutional patrons of comparable weight
- Named figures of regional or higher significance acting in their capacity
- Oath-bound commitments and binding pacts
- World-imposed stakes (a god's task, a sworn duty, a binding magical contract)

Mortal-scale errands and routine commercial work pay coin and reputation, not AP. A hedge wizard offering 5 AP for a lost cat is not legitimate; the economy depends on this gate holding.

### Scale

Awarded AP is scaled to the depth of commitment:

| Commitment | Awarded AP |
|---|---:|
| Specific delicate task with real stake | 1 |
| Multi-leg mission of meaningful consequence | 2 |
| Regional-scale undertaking | 3 |
| Campaign-defining oath, pact, or arc commitment | 4 |

Higher awards are possible in extraordinary cases but should be authored explicitly, not formula-derived.

### Stacking with other rewards

Awarded AP does not replace coin, reputation, or favor. A Council contract pays all of them. Awarded AP is what makes a contract meaningful when the character no longer needs the coin or the reputation.

---

## Track 4 — Domain Spend

Domain points are purchased with AP. Domain score cap is **80**.

| Target score bracket | AP cost per point |
|---|---:|
| 25–60 | 1 |
| 61–70 | 2 |
| 71–80 | 3 |

For multi-point increases that cross brackets, calculate AP point-by-point using the bracket of each resulting score. The backend handles bracket math.

### Spend sources

- **Earned AP** can only be spent on its source domain.
- **Awarded AP** can be spent on any domain.
- A domain spend may combine earned AP from that domain and awarded AP from any source.

### Spend timing

The player may spend AP at any time outside an unresolved scene. If the player chooses to spend AP at scene resolution as part of the reward package, that spend is part of the same progression adjudication sequence.

---

## Reward Adjudication Boundary

Resolve the full reward package before any progression-related save.

The reward package may include:

- tag advancement
- newly proposed tags (requires player confirmation)
- earned AP increments (mechanical, but reflected in the same save)
- domain push outcome (AP or direct point)
- awarded AP grant (if a contract resolved this scene)
- AP spend (if the player chooses to spend at resolution)

Progression-related state is **not stable enough to save** until the reward package is settled.

---

## Progression Save Gate

No progression-related save occurs until the final reward package is settled.

- Do not save tag advancement before scene-resolution adjudication is finalized.
- Do not save newly added tags before player confirmation.
- Do not save AP changes (earned, awarded, or spent) before the reward package is finalized.
- Do not save domain push outcomes before the player chooses AP-or-point.
- If the player disputes any part of the reward interpretation, do not commit disputed elements.

Other unrelated state may be saved only if the save payload does not modify tag tiers, newly proposed tags, AP pools, advancement counters, or domain scores, and does not narratively imply that the reward ruling is settled.

---

## Operational Adjudication Order

When a scene resolves:

1. Determine whether the **scene** is resolved for tag-adjudication purposes (per `scene-structure.md`).
2. Evaluate tag advancement triggers in order: application, knowledge, field, domain push. At most one fires.
3. If a domain push fires, ask the player to choose **+1 AP in that domain** or **+1 domain point directly**.
4. If a contract or commitment resolved this scene and that contract specified an AP award, grant the awarded AP per the contract terms.
5. If the player chooses to spend AP at resolution, resolve that spend in the same sequence.
6. Ask for player confirmation if a new tag would be added.
7. If the player disputes any reward element, pause progression-related save.
8. Save progression-related state only after the reward package is settled.

The backend handles:

- earned AP counter increments and threshold conversions to AP
- parent-cap enforcement on application tier writes
- domain bracket cost math on AP spend
- AP pool segregation by domain (earned vs. awarded)

The GPT does not compute these. It announces what triggered, asks any required player choices, and submits the resolved reward package.
