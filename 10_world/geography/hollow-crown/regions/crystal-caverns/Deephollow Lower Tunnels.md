---
type: location
aliases:
  - The Lower Tunnels
tags:
  - drakenvale
  - crystal-caverns
  - underground
  - wilderness
  - dangerous
  - psionic
  - unmapped
vault_id: deephollow-lower-tunnels
region: hollow-crown
parent_location: crystal-caverns
status: locked
---

# Deephollow Lower Tunnels

The unmapped tunnel network beneath [[Deephollow]] extending into the deeper [[Crystal Caverns]]. The lower tunnels are not part of the city's operations — they are where the crystal veins go when the mining operations stop following them. The psionic resonance intensifies significantly in the lower sections. Long-term exposure without protection produces disorientation, hallucination, and in extreme cases permanent cognitive effects. The [[Deephollow|Deephollow Mining Authority]] has standing orders not to push new extraction beyond the marked lower boundary. Those orders are not always followed.

## Tags

- drakenvale
- crystal-caverns
- underground
- wilderness
- dangerous
- psionic
- unmapped

## Connected Nodes

- [[Deephollow]]
- [[Crystal Caverns]]

## Authoring Notes

This node is sparsely authored in source vault (single descriptive paragraph, no Scene Texture / Functions / Access sections). Source content is preserved verbatim above. Expansion can happen when a storyline requires the lower tunnels as a navigable destination rather than a hazard reference.

The location's wilderness character is canonical: this is not a city district, not a mapped zone, not a sanctioned exploration target. It is the threshold between [[Deephollow]]'s ordered subterranean civic life and the deep Crystal Caverns network's inhuman territory. Travelers who enter the lower tunnels are off-map and at their own risk.

The standing order against extraction beyond the marked boundary is the canonical authority position. The note "Those orders are not always followed" is a deliberate narrative hook — there are crews, individuals, and operations that push past the boundary anyway, for reasons ranging from greed to scholarly ambition to circumstances no one publicly admits. Specific incidents and characters can be authored at scene-construction time.

Source-vault frontmatter had `region_id: hollow_crown` (underscore) where every other source file uses `hollow-crown` (hyphen). Normalized here to `region: hollow-crown` for consistency with the rest of the user-vault frontmatter. Same upstream typo as `draconic_forge.md` from Refresh 8 — flagged again for upstream fix.

The connection to [[Deephollow]] comes from the source frontmatter's connections array. The connection to [[Crystal Caverns]] is added in this migration as the structural parent reference; the source's frontmatter listed only `deephollow` but the location is canonically inside the broader Crystal Caverns network.

The threshold from the lower tunnels into the deeper, less-understood Crystal Caverns territory is gradient, not stepped. There is no specific point at which a traveler "leaves" the Deephollow Lower Tunnels and "enters" the deep Crystal Caverns. The two regions are continuous; the distinction is one of degree (mapped vs. unmapped, mining-territory vs. wilderness, recoverable vs. unrecoverable).
