# Entity Registry Architecture

**Status:** PR 1 foundation. Runtime source of truth: `data/entities/`.

## Purpose

The entity registry is a role-based catalog for things that can appear in the
world as stable, addressable entities.

Before PR 1, related data was split across type-organized stores:

- companion stat blocks in `data/companions/creatures.json`
- Feywood fauna ecology in `data/environment/beasts/`
- Feywood flora ecology in `data/environment/flora/`

Those stores described overlapping beings from different viewpoints. The
registry consolidates them into one file per entity, joined by a shared `id`,
with optional facets for each role the entity can play.

---

## Directory layout

Entity files live under biome-grouped subdirectories:

```text
data/entities/<biome>/<id>.json
```

Templates live directly under `data/entities/` and start with `_` so loaders and
validators can skip them when reading authored entities.

---

## Schema reference

The canonical authoring examples are the JSON templates:

- `data/entities/_template_entity.json`
- `data/entities/_template_facet_ecology.json`
- `data/entities/_template_facet_creature_companion.json`

Every entity has a top-level identity block with these required fields: `id`,
`name`, `kind`, `biome`, `tags`, and `description`.

Every entity must also have at least one role facet. Facets are optional by
role, not by validity: an entity with no facets is incomplete.

---

## Facets

### `ecology`

The `ecology` facet describes the entity's place in a biome: environmental
authorship, food web references, zones, cultural role, canonical tier, harvest
status, and future scene-context systems. Fauna and flora can both carry it;
plants normally have this facet only.

`ecology.primary_diet` is a strict list of entity IDs. Non-entity ecological
inputs such as life stages, resource classes, and forage patterns live in
`ecology.primary_diet_categories` as free-form `snake_case` strings. Promoting
any such category to a first-class entity is a future authoring decision.

`ecology.harvest_status`, when present, is one of `wild`, `cultivated`,
`restricted`, `sacred`, or `unharvestable`. `ecology.canonical_tier` is one of
`primary` or `secondary`. `ecology.category` and `ecology.subcategory` are
`snake_case` strings, not closed enums.

### `creature_companion`

The `creature_companion` facet describes an entity that can participate in the
creature companion system. It carries the legacy companion fields except
`biome`, which is inherited from the top-level identity block.

### Future: `combat`

Reserved for encounter-facing mechanics. PR 1 does not author combat facets or
expose a new combat catalog.

### Future: `harvest`

Reserved for extractable materials, gathering rules, and economy-facing outputs.
PR 1 does not author harvest facets.

---

## Cross-reference rules

Entity IDs are global across `data/entities/` and must be `snake_case`. The
filename stem must match the entity `id`; the parent directory must match the
entity `biome`.

Ecology references use entity IDs, not display names. Values in
`ecology.primary_diet` and `ecology.primary_predators` must resolve to another
entity in the registry.

Zones in `ecology.zones` and top-level `tags` must be `snake_case`. There is no
canonical zone registry in PR 1, so validators check naming only.

---

## Loader behavior

`GET /catalog/creatures` remains the public creature catalog endpoint. It is a
filtered view over entities that have the `creature_companion` facet, preserving
the legacy response shape for existing clients and GPT tool contracts.

No `/catalog/entities` endpoint is introduced in PR 1.

---

## Migration history

Consolidated from `data/companions/creatures.json`,
`data/environment/beasts/`, `data/environment/flora/` in PR 1.

PR 2 is expected to move companion vocabulary registries into
`data/catalog/registries/`. Those registries remain unchanged in PR 1.