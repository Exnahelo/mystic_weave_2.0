# World Data Policy

Authoritative policy for canonical world content: structured YAML under
`data/world/` and its Obsidian-friendly markdown mirror under
`prompts/world_vault/`. Paired with `docs/conventions.md` (naming) and
enforced in CI.

## Scope

Two paths:

- `data/world/**/*.yaml` — canonical structured runtime world data
- `prompts/world_vault/**/*.md` — 1:1 markdown mirror

Every YAML file under `data/world/` has a markdown mirror at the same
relative path under `prompts/world_vault/`. The pair represents a single
canonical node.

## Invariants

### Stem↔id

For every world YAML file and every vault markdown mirror:

    Path(file).stem == data["id"].replace("-", "_")

Holds in both directions. A rename of either surface must update the other
in the same commit. IDs are stable across history; filenames follow them.

### YAML↔Markdown mirror

- Same relative path, same stem, different extension.
- Frontmatter `id:` equals YAML `id:`.
- Canonical fields (`name`, `type`, `description`, `connections`,
  `known_npcs`, `tags`, `threat_level`, `discovered`) stay in sync.
  Any edit to one lands in the other in the same commit.

### Tag hygiene

Tags appear in YAML `tags:` and, for mirrors, in frontmatter `tags:` plus
the `## Tags` markdown section.

- **Case**: `kebab-case` only. No `snake_case`, no mixed case.
- **No authoring-meta tags** in canonical content: `canonical`,
  `canonical-realm`, `placeholder`, `TODO`, `draft`.
- **No duplicates** within a single file's tag list.
- **Frontmatter↔body sync** (markdown only): the set of tags in frontmatter
  equals the set in the `## Tags` section. Order may differ.

## Validator ownership

| Validator | Owns |
|---|---|
| `scripts/validate_naming.py` | filesystem path case rules (delegated to `docs/conventions.md`) |
| `scripts/validate_data_files.py` | stem↔id for world YAML, tag hygiene for world YAML |
| `scripts/validate_prompts.py` | stem↔id for vault MD, tag hygiene for vault MD, frontmatter↔body sync |

## CI enforcement

All three validators run in `.github/workflows/ci.yml` on every PR and every
push to `main`. Failure blocks merge.

## Revision policy

Changes to invariants require an update to this file first on its own commit,
then the content/schema changes that follow. Never land an invariant change
and the content change it enables in the same commit — it destroys the audit
trail.