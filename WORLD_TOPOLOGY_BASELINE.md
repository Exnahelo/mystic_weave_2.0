# World Topology Baseline — 2026-04-11

Post-audit baseline for `prompts/world/*.md` connection reciprocity after the expanded settlement/location pass.

## Scope

Audit performed against all current world location files under `prompts/world/`.

Current scan totals:
- 46 location files with `id` + `connections`
- 21 non-reciprocal in-map links
- 7 off-map placeholder exits

## Reciprocity decision summary

### Corrected to two-way (historical reference)
- `stronghold-of-drakenvale` ↔ `volcanic-highlands`
  - Reason: this is a navigable regional route within the current playable map and should be traversable in both directions for consistency.

### Intentionally one-way (current)

#### Hidden / gated sanctums
- `eryndors-lair` → `sacred-pools`
- `eryndors-lair` → `platinum-heart`
- `platinum-oath-monastery` → `rift-of-discord-edge`
- `platinum-oath-monastery` → `greymantle`

Reason:
- These preserve discovery/security gating for sensitive spaces (hidden lair and restricted monastery). Inbound links from public nodes are intentionally omitted.

#### Directional logistics/spoke links (accepted for now)
- `dewhollow` → `dracelune`
- `brackenmoor` → `dracelune`
- `mirefall` → `dracelune`
- `silvercut` → `dracelune`
- `thornveil` → `dracelune`
- `scalemere` → `dracelune`
- `ashfield` → `stronghold-of-drakenvale`
- `ashfield-fields` → `stronghold-of-drakenvale`
- `stonemark` → `stronghold-of-drakenvale`
- `lastmark` → `stronghold-of-drakenvale`
- `zarkharath` → `stronghold-of-drakenvale`
- `deephollow` → `stronghold-of-drakenvale`
- `deephollow` → `zarkharath`
- `volcanic-highlands-trail` → `stronghold-of-drakenvale`
- `rift-of-discord-edge` → `shadowed-hollows-approach`
- `greymantle` → `mirefall`
- `stonemark-deep-cuts` → `deephollow-lower-tunnels`

Reason:
- These currently model outbound trade/travel emphasis and hub routing. Keep as-authored unless design intent changes to fully bidirectional traversal everywhere.

## Off-map / placeholder exits retained

These links currently point beyond the explicitly authored local map and are retained as intentional external stubs rather than reciprocity defects:

- `dracelune` → `feywood-glade-border`
- `dewhollow` → `feywood-glade-border`
- `thornveil` → `feywood-glade-border`
- `volcanic-highlands` → `draconic-grasslands`
- `ashfield-fields` → `draconic-grasslands-edge`
- `shadowed-hollows-approach` → `shadowed-hollows-proper`
- `platinum-oath-monastery` → `platinum-oath-approach`

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

After the 2026-04-11 expanded-location audit:
- hidden/gated one-way links remain intentional
- directional hub/spoke one-way links are currently accepted design (documented above)
- seven off-map placeholder exits remain intentional until destination files are authored