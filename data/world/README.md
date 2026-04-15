# data/world

Canonical structured runtime world data lives here. YAML under `data/world/` is the authoritative machine-facing layer for migrated world content.

Rules:
- use one YAML file per navigable location node
- keep hierarchy in fields (`region_id`, `settlement_id`, `district_id`, `parent_location_id`)
- keep connections pointed at stable IDs
- do not treat `prompts/world/` as canonical for migrated nodes
