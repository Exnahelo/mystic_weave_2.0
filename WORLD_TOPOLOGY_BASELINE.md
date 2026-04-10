# World Topology Baseline — 2026-04-10

Post-audit baseline for `prompts/world/*.md` connection reciprocity.

## Scope

Audit performed against all current world location files under `prompts/world/`.

## Reciprocity decision summary

### Corrected to two-way
- `stronghold-of-drakenvale` ↔ `volcanic-highlands`
  - Reason: this is a navigable regional route within the current playable map and should be traversable in both directions for consistency.

### Intentionally one-way
- `eryndors-lair` → `sacred-pools`
- `eryndors-lair` → `platinum-heart`

Reason:
- Eryndor's sanctum is intentionally undiscovered (`discovered: false`) and should not become exposed as a normal movement option from public or semi-public sacred locations.
- The outbound links preserve authorial logic for where the sanctum sits physically, while the missing inbound links preserve discovery gating and avoid accidental player-facing disclosure.

## Off-map / placeholder exits retained

These links currently point beyond the explicitly authored local map and are retained as intentional external stubs rather than reciprocity defects:

- `dracelune` → `feywood-glade-border`
- `volcanic-highlands` → `draconic-grasslands`

Guidance:
- Treat these as outward-facing world-edge exits until those destination files are authored.
- When those destinations are added, add reciprocal links unless the new content explicitly requires one-way traversal.

## Future content update rules

When adding or revising `prompts/world/*.md`:
1. Default all navigable in-map routes to reciprocal links.
2. If a link is intentionally one-way, document the reason in the PR or release note.
3. Hidden lairs, sealed spaces, and discovery-gated sanctums should not expose inbound links from public locations unless that reveal is intentional.
4. Off-map placeholders are allowed, but should be called out explicitly in release notes until the connected destination exists.

## Baseline result

After the 2026-04-10 correction:
- one normal in-map reciprocity defect was fixed
- hidden-lair one-way links remain intentional
- two off-map placeholder exits remain intentional until expanded world content is authored