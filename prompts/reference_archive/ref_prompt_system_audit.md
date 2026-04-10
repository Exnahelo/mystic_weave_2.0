# Mystic Weave Prompt System Audit

Date: 2026-04-10  
Scope: Full review of prompt files for (1) missing `await`/wait semantics, (2) await/sequence quality, and (3) gameplay + instruction information gaps.

---

## Executive Summary

- **Literal `await` usage across `prompts/**/*.md`: 0 occurrences.**
- The system already has strong sequencing language ("Always call", "Before", "Do not"), especially in `engine.md`, but several critical checkpoints are still implicit rather than enforced.
- Primary risks are **instruction drift** and **cross-file canon conflicts**, not missing world content volume.

---

## Method

Reviewed:

- Core runtime prompts: `prompts/engine.md`, `prompts/character_creation.md`, `prompts/world_rules.md`
- Canon/lore references: `prompts/drakenvale_world.md`, `prompts/drakenvale_factions.md`, `prompts/drakenvale_organizations.md`, `prompts/drakenvale_geography.md`, `prompts/drakenvale_history.md`, `prompts/drakenvale_characters.md`, `prompts/drakenvale_biomes.md`
- Location data layer: `prompts/world/*.md` (spot-checked key nodes)
- Validation tooling: `scripts/validate_prompts.py`

Audit pattern:

1. Search for literal `await`
2. Identify mandatory sequencing language and API-order constraints
3. Find instruction ambiguity, contradiction, or unresolved stub handling
4. Classify into: Missing Await / Await Needs Improvement / Await Needs Clarification

---

## Findings by Category

## 1) Missing Await (missing explicit wait/confirm gates)

1. **No explicit player-confirmation waits for irreversible turns (outside character creation).**
   - `engine.md` defines turn flow but does not require explicit confirmation before high-cost commitments (major faction pledges, irreversible companion consequences, major economy commitments).

2. **No explicit API response validation checkpoint before proceeding.**
   - Endpoints are required, but runtime behavior for incomplete/partial API payloads is not formalized.

3. **No explicit canonical authority precedence section.**
   - Multiple files are "canonical" in wording; without precedence, cross-file conflict resolution is under-defined.

---

## 2) Await Needs Improvement (sequence exists but is too loose)

1. **State-write sequencing for complex turns is under-specified.**
   - `engine.md` requires changed fields be updated but does not define deterministic write order for multi-domain turns (combat + movement + economy + politics + companion updates).

2. **Risk adjudication tie-breaks are not explicit.**
   - Domain/tag selection is specified, but no explicit fallback for ambiguous multi-domain actions or multiple plausible tags.

3. **Party reputation computation is defined but lacks ambiguity handling.**
   - Formula is present, but fallback behavior for sparse/unknown data could be stricter.

---

## 3) Await Needs Clarification (intent likely to drift)

1. **Economy contradiction across files.**
   - `drakenvale_world.md`: internal economy is barter/no currency.
   - `drakenvale_factions.md`: internal economy includes coin transactions.

2. **Arcane Conservatory access contradiction.**
   - `drakenvale_factions.md`: criteria not formally defined.
   - `drakenvale_organizations.md`: access model is explicitly defined.

3. **Crisis protocol maturity mismatch.**
   - Design notes label some protocol areas as partial/open.
   - Factions doc presents a more finalized command/communications model.

4. **Stub policy is distributed and unevenly enforced.**
   - Some files explicitly say "do not invent", others imply or omit the policy.

5. **Design notes coexist with canonical files and can be misread if uploaded/consulted at runtime.**
   - `drakenvale_design_notes.md` is clearly marked internal, but overlap in subject matter increases risk if accidentally treated as runtime canon.

---

## Gameplay/Instruction Gap Analysis

### Gameplay Information Gaps

- **Crisis operations detail**: enough to narrate baseline incidents, but chain-of-command edge cases and escalation authority could still drift in high-pressure scenes.
- **Artifact governance lifecycle**: ownership, recall, disablement, and misuse response are implied but not systematized.
- **Stub organizations**: narratively useful but structurally thin (Sentinels, Envoys, Circle, Choir), which can create inconsistent gameplay expectations.

### Instruction Gaps

- **No single "conflict resolution protocol" for contradictory docs at runtime.**
- **No strict fallback behavior for API uncertainty** (e.g., partial location/state payloads).
- **No universal "unknown/stub response template" for model outputs** when users probe unfinished lore.

---

## Tooling Coverage Gaps (`scripts/validate_prompts.py`)

Current validator checks:

- Required file presence
- Minimum prompt length
- Marker presence
- Presence of world location files

Not currently validated:

- Required sequencing/await checkpoint language
- Canon authority/precedence marker
- Contradictory statements across canonical files
- Stub-policy marker consistency

---

## Recommended Remediation (Prioritized)

### Priority 0 — Runtime Safety

1. Add explicit **"Await/Validate" checkpoints** in `engine.md`:
   - Await endpoint response
   - Validate required fields
   - If invalid/incomplete, retry or narrate conservatively without irreversible updates

2. Add explicit **"Await player confirmation"** gates for irreversible choices.

3. Add a **"Canon Precedence" block** in runtime instructions.

### Priority 1 — Canon Consistency

4. Resolve economy contradiction (barter-only vs coin usage).
5. Resolve Arcane Conservatory access contradiction.
6. Align crisis protocol status between canonical docs and design notes.

### Priority 2 — Operational Determinism

7. Add deterministic state-write order for multi-change turns.
8. Add tie-break rules for ambiguous domain/tag adjudication.
9. Add standard handling for sparse/unknown faction reputation datasets.

### Priority 3 — Process Guardrails

10. Extend `validate_prompts.py` with structural checks for:
    - presence of await/checkpoint sections,
    - presence of canon precedence section,
    - warning markers for known contradiction pairs.

---

## Bottom Line

The prompt system is strong in core architecture and API-first discipline, but the next quality jump comes from formalizing **wait/validation semantics** and eliminating **cross-file canon ambiguity**. The most impactful work is not adding more lore volume; it is tightening execution rules and document precedence so gameplay stays deterministic under pressure.
