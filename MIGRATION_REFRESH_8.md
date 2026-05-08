# MIGRATION_REFRESH_8

**Type:** Refresh (reconcile-in-place + structural relocation)
**Scope:** Drakenvale City + Stronghold cluster + Varethyn's Lair
**Notes touched:** 12 entity notes + 1 realm-note patch + old `locations/` cleanup
**Source vault:** `Exnahelo/mystic_weave_2.0`, branch `main`, paths under `prompts/world_vault/hollow_crown/`

---

## Summary

Reconciles the Drakenvale City + Stronghold cluster (1 city + 1 fortress + 8 fortress sub-locations) from rich source-vault authoring into the user vault, simultaneously fixing structural placement: the cluster moves out of the flat `10_world/geography/hollow-crown/locations/` folder and into properly-scoped region/settlement subfolders under `regions/central-draconic-grasslands/`. A new region root note is authored for the Central Draconic Grasslands, synthesized from a sparse source stub plus project canon. Varethyn's Lair is reconciled in place at its existing path; source canonically places it under Crystal Caverns, not the Stronghold cluster.

All 11 source-derived notes have status `working` → `locked` after reconciliation. The new region root is authored at `locked` directly.

---

## Notes inventory

### NEW

| Note | Path |
|---|---|
| Central Draconic Grasslands | `10_world/geography/hollow-crown/regions/central-draconic-grasslands/Central Draconic Grasslands.md` |

Synthesized from the sparse source stub (`prompts/world_vault/hollow_crown/surface/central_draconic_grasslands/central_draconic_grasslands.md`, which contained only description + tags + boilerplate authoring note) plus constituent location summaries authored in this batch and project canon already present in `world.md` / `geography.md`. Shape: lead paragraph, Geographic Role, Constituent Locations (authored vs forward-referenced), Tags, Connected Nodes, Authoring Notes.

### MOVED + RECONCILED (10 notes)

All moved from `10_world/geography/hollow-crown/locations/` into properly-scoped paths. Bodies fully rebuilt from source-vault content (Scene Texture, Functions, Access, Authoring Notes sections preserved verbatim or near-verbatim from source; minor smoothing only for inline wikilink integration). Frontmatter normalized to user-vault convention.

| Note | New path |
|---|---|
| Drakenvale City | `regions/central-draconic-grasslands/Drakenvale City.md` |
| Stronghold of Drakenvale | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Stronghold of Drakenvale.md` |
| Draconic Hall | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Draconic Hall.md` |
| Platinum Heart | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Platinum Heart.md` |
| Amethyst Vault | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Amethyst Vault.md` |
| Arcane Conservatory | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Arcane Conservatory.md` |
| Aeries | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Aeries.md` |
| Administrative Quarter | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Administrative Quarter.md` |
| Draconic Forge | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Draconic Forge.md` |
| Sacred Pools | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Sacred Pools.md` |

### RECONCILED IN PLACE (1 note)

| Note | Path |
|---|---|
| Varethyn's Lair | `10_world/geography/hollow-crown/regions/crystal-caverns/Varethyn's Lair.md` (unchanged) |

Source canonically places Varethyn's Lair under Crystal Caverns (`parent_location_id: crystal-caverns`; description: "carved into a natural amethyst-laced chamber **deep within the Crystal Caverns**"). The existing user-vault placement is therefore structurally correct. Body content and frontmatter rebuilt from source. The Lair remains "orphaned" structurally in the sense that the Crystal Caverns region/parent note is not yet authored — that's a future-batch concern, not a Refresh 8 concern.

---

## Frontmatter normalization (applied to all 11 source-derived notes)

Source-vault → user-vault field translations:

| Source field | User-vault field | Transformation |
|---|---|---|
| `id` | `vault_id` | dashed-form preserved |
| `name` | (dropped, name is in H1) | — |
| `type` | `type` | normalized: `lair` → `location` |
| `region_id` | `region` | normalized: `hollow_crown` (underscore, in source `draconic_forge.md` only) → `hollow-crown` (hyphen) for consistency |
| `settlement_id` | (dropped — redundant with `parent_location` for sub-locations) | — |
| `parent_location_id` | `parent_location` | dashed-form preserved |
| `connections` | (dropped from frontmatter) | translated to inline `[[Wikilinks]]` and a `## Connected Nodes` section |
| `tags` | `tags` | preserved |
| `known_npcs` | (dropped from frontmatter) | NPCs surfaced via inline wikilinks in body |
| `threat_level` | (dropped) | mechanical/runtime field; out of scope for migration per project rules |
| `discovered` | (dropped) | mechanical/runtime field; structural intent preserved via `discovery-gated` tag and prose in Access sections where applicable |

Status: `working` → `locked` for all 10 reconciled notes; `locked` directly for new region root and Varethyn's Lair.

---

## Surfaced inconsistencies (source-vault)

1. **`draconic_forge.md` frontmatter uses `region_id: hollow_crown` (underscore)** where every other source file uses `hollow-crown` (hyphen). Normalized to hyphen in this refresh; flagged here for upstream source-vault fix.

2. **Varethyn's Lair source path lives at `prompts/world_vault/hollow_crown/underworld/varethyns_lair.md`** — directly in `underworld/`, sibling to `underworld.md`, NOT nested under `underworld/crystal_caverns/` despite the lair's `parent_location_id` being `crystal-caverns` and its description placing it "deep within the Crystal Caverns." This is a source-vault file-path / canonical-structure mismatch (file lives at one level of nesting, but the canonical parent is one level deeper). Not corrected in this refresh — file location in source is upstream concern.

---

## Topology decisions

### Two-way edges (per source authoring notes)

The Drakenvale City source's Authoring Notes explicitly say prior one-way hub/spoke links routing directly to `stronghold-of-drakenvale` should be replaced with two-way edges between `drakenvale-city` and adjacent nodes. Honored:

- Drakenvale City ↔ Ashfield (southeastern agricultural road)
- Drakenvale City ↔ Draconic Grasslands Edge (eastern civic road)
- Drakenvale City ↔ Southern Lake (continuous lakefront)
- Drakenvale City ↔ Sacred Pools (base plaza)
- Drakenvale City ↔ Stronghold of Drakenvale (ceremonial ascent)
- Drakenvale City ↔ Hall of Scales, Scalemere, Stonemark, Crystalhaven (civic/trade adjacencies)

Sacred Pools ↔ Platinum Heart, Drakenvale City, Southern Lake — all two-way per source.

### Discovery-gated topology (one-way outbound from Lair only)

Source authoring note for Varethyn's Lair: "Neither `amethyst-vault` nor `crystal-caverns` should list `varethyns-lair` in their outbound connections."

Honored:

- Varethyn's Lair → Amethyst Vault (listed in Lair's Connected Nodes)
- Varethyn's Lair → Crystal Caverns (listed in Lair's Connected Nodes)
- Amethyst Vault → Varethyn's Lair: **NOT** listed in Vault's Connected Nodes
- Crystal Caverns → Varethyn's Lair: **NOT** listed (Crystal Caverns parent not yet authored, but the rule is set for when it is)

Stronghold of Drakenvale parent: Varethyn's Lair intentionally NOT in its connections list, preserving discovery-gating from the surface side.

Obsidian backlinks will surface the relationship in the graph regardless. Only the Lair side asserts the outbound edge in its Connected Nodes section.

---

## Wikilinks introduced

### Resolved within this batch (resolve to notes authored in Refresh 8)

`[[Drakenvale City]]`, `[[Stronghold of Drakenvale]]`, `[[Draconic Hall]]`, `[[Platinum Heart]]`, `[[Amethyst Vault]]`, `[[Arcane Conservatory]]`, `[[Aeries]]`, `[[Administrative Quarter]]`, `[[Draconic Forge]]`, `[[Sacred Pools]]`, `[[Varethyn's Lair]]`, `[[Central Draconic Grasslands]]`

### Resolved against existing notes (Refreshes 1–7)

`[[Hollow Crown]]`, `[[Alpine Peaks]]`, `[[Lastmark]]`, `[[Eryndor the Radiant]]`, `[[Zarkeros the Inferno]]`, `[[Varethyn of the Amethyst Gaze]]`, `[[Solveris]]`, `[[Mordrax]]`, `[[Vindrael]]`, `[[Codex of Remembrance]]`, `[[Dragon Guard]]`, `[[Wardens]]`, `[[Platinum Acolytes]]`, `[[Accord]]`, `[[Discordant War]]`, `[[Oath of the Fallen]]`, `[[Oath of Scales]]`, `[[Trial of Wings]]`, `[[Conclave]]`, `[[Heartmass]]`, `[[Heartstone]]`, `[[Platinum Flame]]`, `[[Age of Harmony]]`, `[[Platinum Oath Monastery]]`, `[[Zarkharath]]`, `[[Infernal Forge]]`, `[[Northeastern Volcanic Highlands]]`, `[[Deephollow]]`, `[[Feywood]]`, `[[Shadowed Hollows]]`

(Spot-check these against your vault — any that don't yet resolve get added to the unresolved list below for next batch.)

### Unresolved — forward-references for future batches

| Wikilink | Resolves in / Type |
|---|---|
| `[[Southern Lake]]` | future Hollow Crown surface waterbody batch |
| `[[Ashfield]]` | future Hollow Crown surface settlement batch (agricultural belt) |
| `[[Ashfield Fields]]` | future Hollow Crown surface batch |
| `[[Draconic Grasslands Edge]]` | future Hollow Crown surface region/edge batch |
| `[[Hall of Scales]]` | future Hollow Crown surface settlement batch |
| `[[Scalemere]]`, `[[Stonemark]]`, `[[Crystalhaven]]` | future Hollow Crown surface settlement batches |
| `[[Crystal Caverns]]` | future Hollow Crown underworld batch (parent for Varethyn's Lair) |
| `[[Kaerys Emberclaw]]`, `[[Tazrik Flameweaver]]`, `[[Lethira Vale]]`, `[[Ardrynn the Measured]]`, `[[Serevane]]` | future NPC migration batches |
| `[[Lead Artisan of the Circle]]`, `[[Director of the Sapphire Choir]]`, `[[High Acolyte of the Platinum Flame]]`, `[[Arch-Scholar of the Conservatory]]`, `[[Chief Steward of the Quarter]]`, `[[Master Smith of the Draconic Forge]]`, `[[Attending Acolyte of the Pools]]` | Tier-3 generative NPC role notes — future role-stub batch |
| `[[Silver Scale Trading Company]]`, `[[Circle of Artisans]]`, `[[Sapphire Choir]]`, `[[Silver Wing Envoys]]`, `[[Sapphire Sentinels]]` | future groups/factions migration batches |

---

## Realm-note patch — `Drakenvale.md`

The realm note at `10_world/geography/hollow-crown/Drakenvale.md` references "Major places" with paths or wikilinks pointing into the old `locations/` flat folder. After Refresh 8's moves, these references need updating.

**This bundle does NOT include a patched `Drakenvale.md`.** The realm note's full content was not read during this refresh (out-of-scope per repo access rules — only `prompts/world_vault/**` is in scope, which is the source vault, not the user vault). You'll need to apply the patch manually.

### What to update

Find the Major places section. For each of these 11 entities, update any path references or wikilink targets:

| Entity | Old path/link | New path |
|---|---|---|
| Drakenvale City | `locations/Drakenvale City.md` (or wikilink `[[Drakenvale City]]` resolving there) | `regions/central-draconic-grasslands/Drakenvale City.md` |
| Stronghold of Drakenvale | `locations/Stronghold of Drakenvale.md` | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Stronghold of Drakenvale.md` |
| Draconic Hall | `locations/Draconic Hall.md` | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Draconic Hall.md` |
| Platinum Heart | `locations/Platinum Heart.md` | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Platinum Heart.md` |
| Amethyst Vault | `locations/Amethyst Vault.md` | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Amethyst Vault.md` |
| Arcane Conservatory | `locations/Arcane Conservatory.md` | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Arcane Conservatory.md` |
| Aeries | `locations/Aeries.md` | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Aeries.md` |
| Administrative Quarter | `locations/Administrative Quarter.md` | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Administrative Quarter.md` |
| Draconic Forge | `locations/Draconic Forge.md` | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Draconic Forge.md` |
| Sacred Pools | `locations/Sacred Pools.md` | `regions/central-draconic-grasslands/stronghold-of-drakenvale/Sacred Pools.md` |
| Central Draconic Grasslands (NEW — add to Major places if absent) | — | `regions/central-draconic-grasslands/Central Draconic Grasslands.md` |

Note: if the realm note uses bare `[[Wikilinks]]` rather than relative paths, Obsidian will resolve them by filename regardless of path, and no edit is needed unless the wikilink text itself was wrong. The patch only matters if the realm note encodes paths explicitly. Check before editing.

---

## Apply commands

From the vault root:

```bash
# 1. Unzip the bundle in place (overwrites existing draft notes at locations/)
unzip -o MIGRATION_REFRESH_8.zip

# 2. Remove the old flat locations folder (notes are now at regions/...)
rm -rf 10_world/geography/hollow-crown/locations/

# 3. Manual: edit 10_world/geography/hollow-crown/Drakenvale.md per the
#    "Realm-note patch" section above. Skip if Major places uses bare
#    [[Wikilinks]] without path qualifiers.

# 4. Verify
find 10_world/geography/hollow-crown -name "*.md" | sort

# 5. Commit
git add 10_world/
git commit -m "Refresh 8: reconcile Drakenvale City + Stronghold cluster + Varethyn's Lair from source vault; relocate from flat locations/ to region-scoped paths"
git push
```

The `unzip -o` flag forces overwrite. Run from a Terminal session, not Finder; macOS Finder's Archive Utility does not honor the `-o` flag and may dump files into a single nested folder rather than merging into the existing tree.

---

## Reconcile rule audit

| Rule | Application |
|---|---|
| Source vault wins on content where richer | Applied — full Scene Texture, Functions, Access, Authoring Notes preserved verbatim or near-verbatim from source for all 11 source-derived notes. |
| User vault wins on alias/path/frontmatter conventions | Applied — `type:`, `aliases:`, `tags:`, `vault_id:`, `region:`, `parent_location:`, `status:` follow user-vault convention; `id`, `name`, `connections`, `known_npcs`, `threat_level`, `discovered` dropped or translated. |
| Translate source `connections` arrays into inline wikilinks + Connected Nodes section | Applied throughout. |
| Status `working` → `locked` after reconciliation | Applied to all 11 source-derived notes; new region root authored at `locked` directly. |
| Preserve user-vault-only content draft notes contain that source lacks | **Not applied** — per pre-build agreement (option 2 from restate), source-rebuild trusted; spot-check during apply review. Source was assessed as "substantially richer" than user-vault drafts in your audit, suggesting drafts were thin scaffolds. |
| Mechanical fields out of scope | Applied — `threat_level` and `discovered` dropped from frontmatter. Discovery-gating preserved structurally (Varethyn's Lair) via `discovery-gated` tag and prose in Access section. |

---

## What this refresh does NOT do

- Does not author the Crystal Caverns parent / region note. Varethyn's Lair sits at `regions/crystal-caverns/` under an unauthored parent, same as before this refresh.
- Does not author any of the forward-referenced settlements (Ashfield, Hall of Scales, Scalemere, Stonemark, Crystalhaven, etc.).
- Does not author any of the named NPCs or generative role notes referenced via wikilinks.
- Does not patch the realm note (`Drakenvale.md`) directly — that's a manual step, deliberately scoped narrowly.
- Does not touch any 2.0 implementation, prompt files, or registries (out of scope for this project).
