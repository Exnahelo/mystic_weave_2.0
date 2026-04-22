# Mystic Weave — Progression Rules

This document is the sole canonical source for progression adjudication.
Use it for AP earning, domain advancement, tag advancement, reward adjudication boundaries, and progression-related save timing.

Scene-boundary vocabulary is canonical in `prompts/scene-structure.md`.

---

## Core Separation Rule

AP adjudication and tag adjudication are separate.

- **AP** is awarded once per **resolved consequence chain** using the consequence scale.
- **Tag advancement** is awarded by **resolved scene**.
- A **multi-leg job or extended task** may yield **one AP award** while still containing **multiple tag-eligible scenes**.

The following terms are **not interchangeable**:
- beat
- encounter
- scene
- job / contract
- consequence chain

---

## Track 1 — Tags (Narrative, Use-Based)

- Tags do **not** consume AP.
- When a character uses a tag in a meaningful, consequential action and the outcome creates lasting narrative impact, that tag may advance by one tier.
- Tag advancement is adjudicated **per resolved scene**, not per beat, encounter, job, or consequence chain.
- No tag advances more than once per session.
- Maximum one tag advance per scene regardless of how many tags were used.
- The GPT selects the tag most central to the action. If multiple tags contributed equally, the player chooses.
- Tag tier cap is **T5**.

**Parent-cap rule for applications.** An application tag may not exceed the tier of its parent knowledge group. Exception: if an application was seeded above its parent at character creation (for example, a Focus granted the application at T2 while the parent knowledge is T1), the application does not regress, but it cannot advance further until the parent knowledge catches up or exceeds it.

This rule applies at adjudication time. Before advancing an application, verify that the parent would still be at or above the proposed application tier. If not, either advance the parent first (if the scene supports that) or select a different candidate.

Tags are not limited to those acquired at character creation. If a character demonstrates repeated meaningful use of a skill or technique not covered by an existing tag, the GPT may propose adding it at Tier 1.

- Newly proposed tags require **player confirmation before saving**.
- Do not save a newly added tag until the player confirms it.

---

## Track 2 — Domains (AP-Purchased)

- Domain increases are purchased with AP and may be applied to any domain.
- Domain score cap is **80**.
- Cost by target-score bracket:
  - Raising a domain to **25–60** costs **1 AP per point**.
  - Raising a domain to **61–70** costs **2 AP per point**.
  - Raising a domain to **71–80** costs **3 AP per point**.
- For multi-point increases that cross brackets, calculate AP point-by-point using the bracket of each resulting score.

If the player chooses to spend AP immediately at resolution time, that spend is part of the same progression adjudication sequence.

---

## Track 3 — AP Earning (Consequence Scale)

Award AP **once per resolved consequence chain**, after consequences are finalized.

| Consequence Scale | AP | One-sentence definition |
|---|---:|---|
| Local | 0 | The outcome affects only the immediate scene and creates no durable downstream pressure. |
| Situational | 1 | The outcome creates a meaningful short-term shift for the current objective, encounter, or nearby node. |
| Regional | 2 | The outcome reshapes conditions across multiple locations, factions, or travel paths in the active region. |
| Campaign | 4 | The outcome materially redirects major-arc stakes, long-horizon faction posture, or world-state trajectory. |

A multi-leg job or extended task may include multiple scenes, but it does **not** automatically generate multiple AP awards.

- If the legs belong to the same continuing consequence chain, award AP once when that chain resolves.
- If each leg is independently commissioned with independent stakes and resolves into separate consequence chains, adjudicate them separately.
- Sub-events within the same consequence chain do not grant additional AP.

---

## Reward Adjudication Boundary

Resolve the full reward package before any progression-related save.

The reward package may include:
- AP award
- AP spend
- tag advancement
- newly proposed tags
- any related advancement counter changes

Progression-related state is **not stable enough to save** until the reward package is settled.

---

## Progression Save Gate

No progression-related save occurs until the final reward package is settled.

- Do not save AP changes before AP adjudication is finalized.
- Do not save AP spend before the reward package is finalized.
- Do not save tag advancement before scene-resolution adjudication is finalized.
- Do not save newly added tags before player confirmation.
- If the player disputes the reward interpretation, do **not** commit disputed AP, disputed tag changes, or advancement counters.
- Other unrelated state may be saved only if the save payload does not modify AP, advancement counters, tag tiers, or newly proposed tags, and does not narratively imply that the reward ruling is settled.

---

## Operational Adjudication Order

When a scene or consequence chain resolves:

1. Determine whether the **scene** is resolved for tag-adjudication purposes.
2. Determine whether the **consequence chain** is resolved for AP-adjudication purposes.
3. Evaluate tag advancement separately from AP.
4. If AP is awarded and immediate AP spend is chosen, resolve that spend in the same progression adjudication sequence.
5. Ask for player confirmation if a new tag would be added.
6. If the player disputes the reward interpretation, pause progression-related save.
7. Save progression-related state only after the reward package is settled.
