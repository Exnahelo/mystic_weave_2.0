# Prompt Restructure — Phase 1 Classification

Working notes for the prompt restructure (5.4.7 → 5.5.0). Records the
audit of `prompts/world-rules.md` against the rest of the prompt corpus,
the divergences from the brief's expected classification, and the design
decisions made before Phase 2.

This file is transient. Delete at the end of the restructure (the
resulting file structure is the documentation of where things ended up).

---

## Source

`prompts/world-rules.md`, 485 lines. Top-level sections:

1. Domain Scores (7–22)
2. Hit Points (25–37)
3. Survival & Load (40–103)
4. Dice Resolution (106–179)
5. Competency Tags (182–246)
6. Magic (249–330)
7. Advancement (332–336)
8. Pacing (340–362)
9. Reputation (366–446)
10. Failure States (449–461)
11. The World Graph (465–472)
12. Economy Resolution Rules (476–485)

## Classification table

| # | Section (lines) | Brief expected | Verified | Destination |
|---|---|---|---|---|
| 1 | Domain Scores (7–22) | CHARACTER-RULES | ✓ | character-rules.md |
| 2 | Hit Points (25–37) | CHARACTER-RULES | ✓ | character-rules.md |
| 3 | Survival & Load (40–103) | CHARACTER-RULES | ✓ | character-rules.md |
| 4 | Dice Resolution (106–179) | DUPLICATE | partial | top half DUPLICATE; Fail-Forward subsection (154–179) → character-rules.md as "Failure Outcomes" |
| 5 | Competency Tags (182–246) | DUPLICATE (progression-rules.md) | **✗** | CHARACTER-RULES; canonical 19-group taxonomy moves to character-rules.md |
| 6 | Magic (249–330) | DUPLICATE (magic-rules.md) | ✓ | drop; magic-rules.md canonical |
| 7 | Advancement (332–336) | DUPLICATE (progression-rules.md) | ✓ | drop; pointer-only |
| 8 | Pacing (340–362) | CHARACTER-RULES | ✓ | character-rules.md |
| 9 | Reputation (366–446) | CHARACTER-RULES | ✓ | character-rules.md |
| 10 | Failure States (449–461) | DUPLICATE (engine.md + arc-rules.md) | **✗** | CHARACTER-RULES; world-rules.md is the only authoritative source for HP=0/character death |
| 11 | The World Graph (465–472) | CHARACTER-RULES | ✓ | character-rules.md |
| 12 | Economy Resolution Rules (476–485) | DUPLICATE (economy-rules.md) | ✓ | drop; economy-rules.md canonical |

## Divergences and resolutions

### Competency Tags — option (a)

`progression-rules.md` covers tag *advancement* mechanics (triggers,
parent-cap, AP) but does not contain the canonical 19-knowledge-group
taxonomy. `mechanics-tables.md` lists group names with parenthetical
domain only — no governing-domain narrative or summary text. The
canonical 19 × Domain × Summary table only exists in `world-rules.md`.

**Resolved:** the canonical taxonomy moves to `character-rules.md`
(option a). Knowledge groups are part of character state structure (what
a character can have), separate from advancement mechanics (how those
things change). Domains and competency taxonomy live together in
character-rules.md. Progression-rules.md stays focused on triggers,
parent-cap, AP.

Rejected:
- (b) Move taxonomy to progression-rules.md — inflates a file that
  doesn't need taxonomy in scope.
- (c) Move taxonomy to mechanics-tables.md — that file is a fast-lookup
  index, not a canonical source. Putting the full table there would
  recreate the split-source-of-truth problem we're solving.

### Failure States — CHARACTER-RULES, not DUPLICATE

`engine.md` mentions HP=0 in one fragment ("Apply HP/state: 0 HP =>
incapacitated") on line 54, which is a runtime trigger pointer, not
canonical content. `arc-rules.md` has a Failure Procedure for arcs
(state `failed`), which is arc lifecycle, not character HP/death.

`world-rules.md` lines 449–461 ("HP Reaches 0", "Character Death") is
the only authoritative source for character-level failure handling.

**Resolved:** classify CHARACTER-RULES. Move into character-rules.md.

### Dice Resolution — split

Top half (formula, degree-of-success bands, difficulty modifiers) is
duplicated in `mechanics-tables.md` and `difficulty-rules.md`. Bottom
half (lines 154–179: "Fail-Forward Outcome Rule (Mechanical)",
"Fail-Forward by Failure Band", "Canonical Fail-Forward Examples") is
unique narration content not present elsewhere except a one-line summary
in engine.md.

**Resolved:** top half drops (DUPLICATE). Bottom half moves to
`character-rules.md` as a section called "Failure Outcomes" placed
immediately after "Failure States" — co-locating HP=0/death and
roll-failure handling, both forms of character-state failure at
different granularities.

Rejected: moving Fail-Forward into engine.md — engine.md is fighting
the 8000-byte cap for the Phase 8 arc gates. Fail-Forward is reference
material the GPT consults, not always-loaded.

## Final character-rules.md section order (Phase 2 scope)

1. Domain Scores
2. Hit Points
3. Survival & Load
4. Competency Tags (19-group taxonomy + Magical Fields parallel pointer to magic-rules.md)
5. Reputation
6. Pacing
7. The World Graph
8. Failure States (HP=0, character death)
9. Failure Outcomes (Fail-Forward rules and examples)

Magical Fields parallel table within Competency Tags reduces to a
pointer to `magic-rules.md` (which already holds the canonical Field ×
Primary Domain × Governs table). The internal duplication within
world-rules.md (lines 229–241 reappearing at 295–307) resolves when
world-rules.md is deleted in Phase 3.

## mechanics-tables.md pointer updates (Phase 3 scope)

Four-plus pointers in `mechanics-tables.md` currently cite
`world-rules.md`. Phase 3 plan:

| Pointer site | Current → New |
|---|---|
| Line 18 — Standard Roll Resolution canonical | `world-rules.md` → mechanics-tables.md self-canonical (formula + bands stay where they are; the file becomes canonical for these two paragraphs) |
| Line 228 — Reputation canonical | `world-rules.md` → `character-rules.md` |
| Line 295 — Survival Bands canonical | `world-rules.md` → `character-rules.md` |
| Line 456 — Pacing Fields canonical | `world-rules.md` → `character-rules.md` |
| Line 471 — Reference Files list | replace `world-rules.md` entry with `character-rules.md` |

The dice formula self-canonical exception is acceptable: alternative is
creating a new file or inflating an existing one for two paragraphs.
mechanics-tables.md gains canonical authority for the formula and
degree-of-success bands; difficulty-rules.md remains canonical for the
modifier ladder; character-rules.md remains free of dice mechanics.

## Phase 2 stop conditions (carried from brief)

- Content-completeness check passes (every CHARACTER-RULES section from
  Phase 1 present)
- No DUPLICATE content included
- Existing dedicated files (progression-rules.md, magic-rules.md,
  combat-rules.md, etc.) are not modified in Phase 2

## Working branch

`restructure/prompt-architecture`. Final merge to main happens after
Phase 9. Version bump 5.4.7 → 5.5.0 lands with that merge, not earlier.
