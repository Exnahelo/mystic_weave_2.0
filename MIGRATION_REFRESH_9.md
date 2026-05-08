# MIGRATION_REFRESH_9

**Type:** Refresh (underworld closure — new authoring + source-rebuild)
**Scope:** Underworld geography under the Hollow Crown — Beneath the Southern Dark Quadrant region + Temple of Mordrax + Crystal Caverns region + Deephollow + Deephollow Lower Tunnels
**Notes shipped:** 5 entity notes
**Source vault:** `Exnahelo/mystic_weave_2.0`, branch `main`, paths under `prompts/world_vault/hollow_crown/underworld/`

---

## Summary

Closes the underworld branch of the Hollow Crown's geography under the (b) topology decision: the Underworld is treated as a category, not a path-tree wrapper. The two underworld regions (Beneath the Southern Dark Quadrant, Crystal Caverns) sit as siblings to surface regions under `regions/` directly, mirroring how Refresh 7 handled the Alpine Peaks. No `Underworld.md` index file is created.

This refresh resolves the orphaned-parent state of [[Varethyn's Lair]] from Refresh 8 — Crystal Caverns is now authored at the path the Lair already pointed to. No move needed for the Lair note itself.

---

## Notes inventory

### NEW (5 notes)

| Note | Path | Source |
|---|---|---|
| Beneath the Southern Dark Quadrant | `regions/beneath-southern-dark-quadrant/Beneath the Southern Dark Quadrant.md` | **Synthesized** — no source region-zone root file exists; `beneath_southern_dark_quadrant/` folder in source contains only `temple_of_mordrax.md`. Synthesis draws on Temple content + project canon (`world.md`, `history.md`). |
| Temple of Mordrax | `regions/beneath-southern-dark-quadrant/Temple of Mordrax.md` | **Source-rebuilt** — verbatim/near-verbatim from rich source file (137 lines). All sections preserved: Scene Texture, Historical Weight, Contemporary Significance, Access, Authoring Notes. |
| Crystal Caverns | `regions/crystal-caverns/Crystal Caverns.md` | **Source-rebuilt with adjacent-source expansion** — single rich descriptive paragraph from `crystal_caverns.md` plus scene-texture material drawn from [[Deephollow]], [[Deephollow Lower Tunnels]], and [[Varethyn's Lair]] sources to fill out Scene Texture / The Observer / Access sections. All expansions stay within source canon. |
| Deephollow | `regions/crystal-caverns/Deephollow.md` | **Source-rebuilt with truncation gap** — full source content through "...the backbone of any sanctioned underground" preserved. **Source file ends mid-sentence**; gap explicitly flagged in body and authoring notes. |
| Deephollow Lower Tunnels | `regions/crystal-caverns/Deephollow Lower Tunnels.md` | **Source-rebuilt** — minimal source content (single paragraph). |

### Status transitions

All 5 notes authored at `status: locked` directly (new authoring, not transitioning from `working`).

---

## The Deephollow source-vault truncation

**This is the most consequential issue surfaced in Refresh 9 and worth recording explicitly.**

The source-vault file `prompts/world_vault/hollow_crown/underworld/crystal_caverns/deephollow/deephollow.md` is **104 lines, ending mid-sentence at "...the backbone of any sanctioned underground" with no trailing newline.** Verified by reading via direct filesystem access against the local clone (not via the GitKraken MCP read tool, which returns the same content but via a path that initially looked like API-side truncation). The file is genuinely incomplete in source.

What was captured: full Description + Scene Texture + Districts and Layout + Functions + Access and the Cavern Network + The Deep Marshal + The Assay Master + the opening sentence of The Guild of Underdelvers section. ~95% of the file's content is intact and migrated.

What is missing in source (and therefore not migrated):
- Closing sentences of the Guild of Underdelvers paragraph (begins describing membership and Vault-tier headquarters; cuts off describing what Guild members "form the backbone of any sanctioned underground" — likely "expedition" or "operation")
- Any sections that would follow Guild of Underdelvers — likely an Authoring Notes section (consistent with every other authored source file in the underworld batch), possibly additional sections

User-vault Deephollow note flags this directly in the body (with bracketed annotation at the truncation point) and in the Authoring Notes section. The note is usable in current form; should be refreshed when source is completed upstream.

---

## Source-vault discoveries (file-tree audit)

This refresh's tooling shift from GitKraken-MCP-only to local-filesystem access (via shallow clone in container) revealed several structural facts about the source vault that were not visible through file-by-file reads:

### 1. Beneath the Southern Dark Quadrant has no region-zone root file

The source-vault folder `underworld/beneath_southern_dark_quadrant/` contains exactly one file: `temple_of_mordrax.md`. There is no `southern_dark_quadrant.md` or `beneath_southern_dark_quadrant.md` region-zone root. The user-vault region note for this sub-region is fully synthesized — flagged in the note's own Authoring Notes section.

### 2. Deephollow has its own folder; Lower Tunnels does not

The source layout:

```
underworld/crystal_caverns/
├── crystal_caverns.md
├── deephollow_lower_tunnels.md         (sibling file)
└── deephollow/
    └── deephollow.md                   (nested)
```

Inconsistent. Deephollow gets its own folder (suggesting future expansion plans for districts, sub-locations, or specific NPC files), but Deephollow Lower Tunnels — which is canonically a child of Deephollow — sits as a sibling to the `deephollow/` folder rather than inside it. Same pattern of file-tree-vs-canonical-parent mismatch as Refresh 8's Varethyn's Lair (file at `underworld/varethyns_lair.md`, canonical parent `crystal-caverns`).

User-vault placement honors canonical parent, not source-vault file-tree position.

### 3. region_id underscore typo recurs

`deephollow_lower_tunnels.md` source frontmatter has `region_id: hollow_crown` (underscore) where every other source file uses `hollow-crown` (hyphen). Normalized in this migration. Second occurrence of the same typo (Refresh 8 caught it in `draconic_forge.md`). Worth a single upstream sweep.

---

## Frontmatter normalization (applied to all source-derived notes)

Same rules as Refresh 8:

| Source field | User-vault field | Transformation |
|---|---|---|
| `id` | `vault_id` | dashed-form preserved |
| `name` | (dropped, in H1) | — |
| `type` | `type` | normalized: `region_zone` → `region`; `sealed-site` → `location` (with `sealed-site` preserved as tag); `wilderness` → `location` (with `wilderness` preserved as tag); `settlement` → `settlement` |
| `region_id` | `region` | underscore → hyphen where applicable |
| `parent_location_id` | `parent_location` | dashed-form preserved |
| `connections` | (dropped from frontmatter) | translated to inline wikilinks + `## Connected Nodes` section |
| `tags` | `tags` | preserved, with type-distinction tags added where source `type` was a special category (e.g., `sealed-site` tag added to Temple of Mordrax) |
| `known_npcs` | (dropped) | NPCs surfaced via inline wikilinks in body |
| `threat_level` | (dropped) | mechanical/runtime field |
| `discovered` | (dropped) | mechanical/runtime field; structural intent preserved via prose in Access sections where applicable |

---

## Topology decisions

### (b) topology — underworld as category, not path wrapper

Per pre-build agreement: underworld regions sit as siblings to surface regions under `regions/`, with no `regions/underworld/` wrapper folder and no `Underworld.md` category index file. Mirrors Refresh 7's surface treatment (Alpine Peaks at `regions/alpine-peaks/` directly, not under `regions/surface/`).

### Discovery-gating preserved (from Refresh 8)

Crystal Caverns does NOT list [[Varethyn's Lair]] in its Connected Nodes. Only the Lair side asserts the outbound edge. Obsidian backlinks will surface the relationship in the graph, but the Crystal Caverns note offers no surface signal of the Lair's existence.

This rule is explicit in Crystal Caverns' Authoring Notes for future authoring reference.

### Underworld region separation

[[Beneath the Southern Dark Quadrant]] and [[Crystal Caverns]] are canonically NOT connected. The two underworld regions are isolated from each other by natural rock barriers — the Temple's siting has been effectively isolated from the broader cavern network since before the realm's founding. Both region notes carry this rule in their authoring notes; any future storyline involving subterranean travel between them requires explicit narrative justification.

### Reciprocal forward-references

Outgoing wikilinks to nodes not yet authored:

- [[Shadowed Hollows]] (and "Shadowed Hollows Proper" from Temple source) — the corrupted surface zone above the Temple. Surface forward-reference. Reciprocal connection to Temple of Mordrax should be established when the Shadowed Hollows region is authored.
- [[Temperate Forest]] — surface region with cavern-system access mentioned in source. Reciprocal connection to Crystal Caverns should be established when authored.
- [[Stronghold of Drakenvale]] (already authored in Refresh 8) — Crystal Caverns canonically lists "cave systems under the Stronghold" as an access path. The Stronghold's Connected Nodes did not list Crystal Caverns in Refresh 8; this is a topology gap that should be reconciled in a future topology pass — Crystal Caverns is an outbound from Stronghold but the Stronghold note does not show this. Same applies to [[Zarkharath]] and Deephollow's trade route.

These are all expected forward-references in a multi-batch migration; calling them out so the topology pass at the end of geography migration catches them.

---

## Wikilinks introduced

### Resolved within this batch

`[[Beneath the Southern Dark Quadrant]]`, `[[Temple of Mordrax]]`, `[[Crystal Caverns]]`, `[[Deephollow]]`, `[[Deephollow Lower Tunnels]]`

### Resolved against existing notes (Refreshes 1–8)

`[[Hollow Crown]]`, `[[Stronghold of Drakenvale]]`, `[[Amethyst Vault]]` (referenced in Crystal Caverns context), `[[Varethyn of the Amethyst Gaze]]`, `[[Varethyn's Lair]]`, `[[Mordrax]]`, `[[Solveris]]`, `[[Vindrael]]`, `[[Heartstone]]`, `[[Discordant War]]`, `[[Oath of the Fallen]]`, `[[Wardens]]`, `[[Vigil]]`, `[[Platinum Oath Monastery]]`, `[[Arcane Conservatory]]`, `[[Administrative Quarter]]`, `[[Draconic Council]]`, `[[Age of Harmony]]`, `[[Central Draconic Grasslands]]`, `[[Lastmark]]` (referenced indirectly through trade-context), `[[Zarkharath]]`, `[[Infernal Forge]]`, `[[War of the Fallen]]`, `[[Mordraxian Rebels]]`, `[[Dark Hold]]`, `[[Greymantle]]`

(Spot-check during apply review. Anything that doesn't resolve adds to the unresolved list for a future batch.)

### Unresolved — forward-references for future batches

| Wikilink | Resolves in / Type |
|---|---|
| `[[Shadowed Hollows]]` | future Hollow Crown surface dark-quadrant batch |
| `[[Temperate Forest]]` | future Hollow Crown surface forest batch |
| `[[Deep Marshal]]` | Tier-3 generative role — future role-stub batch |
| `[[Assay Master]]` | Tier-3 generative role — future role-stub batch |
| `[[Guild of Underdelvers]]` | future groups/factions batch |

---

## Realm-note patch

The realm note `10_world/geography/hollow-crown/Drakenvale.md` may need additions to its Major places section to reference the underworld additions. Since this bundle's repo-scope rules don't permit reading the user vault's working tree, the patch is documented here as a manual step rather than auto-patched.

### What to consider adding (manual review against current Drakenvale.md)

If the Major places section has an underworld/subterranean subsection, or if it's currently flat:

| Entity | Path |
|---|---|
| Beneath the Southern Dark Quadrant | `regions/beneath-southern-dark-quadrant/Beneath the Southern Dark Quadrant.md` |
| Temple of Mordrax | `regions/beneath-southern-dark-quadrant/Temple of Mordrax.md` |
| Crystal Caverns | `regions/crystal-caverns/Crystal Caverns.md` |
| Deephollow | `regions/crystal-caverns/Deephollow.md` |
| Deephollow Lower Tunnels | `regions/crystal-caverns/Deephollow Lower Tunnels.md` |

If the realm note uses bare `[[Wikilinks]]`, no path edit is needed — Obsidian will resolve by filename. If paths are encoded explicitly, edit accordingly. Skip if the realm note's Major places section doesn't include underworld content at all (in which case the question is whether to add it now or defer to a topology pass).

---

## Apply commands

From the vault root:

```bash
# 1. Unzip the bundle in place (no overwrites — all 5 notes are new authoring)
unzip -o MIGRATION_REFRESH_9.zip

# 2. Manual: review Drakenvale.md and add underworld entries to Major places
#    if appropriate. Skip if not relevant to current realm-note structure.

# 3. Verify
find 10_world/geography/hollow-crown/regions -name "*.md" | sort

# 4. Commit
git add 10_world/
git commit -m "Refresh 9: author underworld geography — Beneath the Southern Dark Quadrant + Temple of Mordrax + Crystal Caverns + Deephollow + Deephollow Lower Tunnels; resolve Varethyn's Lair orphaned-parent state"
git push
```

`unzip -o` from Terminal, not Finder. The flag forces overwrite, but in this bundle every file is new (no overwrites needed) — `-o` is just defensive.

---

## Reconcile rule audit

| Rule | Application |
|---|---|
| Source vault wins on content where richer | Applied to Temple of Mordrax (verbatim), Deephollow (verbatim through truncation point). Crystal Caverns, Deephollow Lower Tunnels carry source content + minimal expansion. |
| Synthesize from constituents + project canon when source is sparse or absent | Applied to Beneath the Southern Dark Quadrant region root (no source) and Crystal Caverns Scene Texture / The Observer / Access sections (source had only one descriptive paragraph). All synthesis flagged in the notes' own Authoring Notes. |
| User vault wins on alias/path/frontmatter conventions | Applied — `type`, `aliases`, `tags`, `vault_id`, `region`, `parent_location`, `status` all follow user-vault convention. Source-vault frontmatter fields normalized or dropped. |
| Translate source `connections` arrays into inline wikilinks + Connected Nodes section | Applied throughout. |
| Mechanical fields out of scope | `threat_level` and `discovered` dropped from all notes. Discovery-gating for Temple of Mordrax (canonically `discovered: false`) preserved through prose in Access section. |
| Discovery-gated topology preserved (Refresh 8 rule for Varethyn's Lair) | Applied — Crystal Caverns does not list Varethyn's Lair in its Connected Nodes. |

---

## What this refresh does NOT do

- Does not author [[Shadowed Hollows]], [[Temperate Forest]], or any other surface region forward-referenced from the underworld notes.
- Does not author the Tier-3 generative roles ([[Deep Marshal]], [[Assay Master]]) introduced as wikilinks.
- Does not author [[Guild of Underdelvers]] as a faction node.
- Does not patch [[Stronghold of Drakenvale]]'s Connected Nodes to add reciprocal edges to [[Crystal Caverns]] (topology gap noted; reconcile in a future topology pass).
- Does not patch [[Zarkharath]] for the trade-route edge to [[Deephollow]] (same — future topology pass).
- Does not patch the realm note `Drakenvale.md` directly — manual step deliberately.
- Does not address the Deephollow source-vault truncation upstream — flagged for upstream fix.
- Does not address the `region_id: hollow_crown` underscore typo upstream — flagged for upstream fix.
- Does not touch any 2.0 implementation, prompt files, or registries (out of scope for this project).

---

## Tooling note (process improvement)

This refresh switched read tooling mid-stream from `repository_get_file_content` (GitKraken MCP) to local-filesystem access via `git clone` + `view`/`bash_tool`. The MCP tool was returning what looked like truncation on Deephollow and hard failures on filename guesses for the southern-dark-quadrant root. Switching to filesystem access immediately resolved both: directory listings settled the file tree once, and full file content dropped out without the 4KB-or-so truncation cap the MCP tool seemed to be enforcing on the largest source file.

For future refreshes: clone first (`git clone --depth 1 https://github.com/Exnahelo/mystic_weave_2.0.git`), then `view` and `bash_tool` against the local clone. The MCP tool is fine for spot-reads of small files but not appropriate for the largest source files or for tree exploration. The user explicitly flagged this earlier in the conversation; recording here for procedural memory.
