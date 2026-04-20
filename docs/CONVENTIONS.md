# Naming Conventions

Authoritative reference for naming identifiers in this repository. When a naming question arises, match the identifier's **category**, not the file it appears in.

## The table

| Category | Case | Example |
|---|---|---|
| Python modules, packages, files | `snake_case` | `scene_context.py`, `api/routes/session.py` |
| Python functions, methods, variables | `snake_case` | `build_scene_context()`, `session_id` |
| Python classes | `PascalCase` | `CharacterModel`, `NewSessionRequest` |
| Python constants | `UPPER_SNAKE_CASE` | `DATABASE_URL` |
| JSON / YAML object keys | `snake_case` | `character_name`, `wealth_tier`, `parent_location_id` |
| Directory names | `snake_case` | `stronghold_of_drakenvale/`, `hollow_crown/` |
| Data / world filenames (`.yaml`, `.md`) | `snake_case` | `stronghold_of_drakenvale.yaml` |
| Canonical IDs and slugs (content) | `kebab-case` | `stronghold-of-drakenvale`, `eryndors-lair` |
| Tags | `kebab-case` | `alpine-peaks`, `dragon-guard` |
| URL path segments | `kebab-case` | `/location/{location_id}` |
| URL / query parameters | `snake_case` | `?session_id=abc` |
| Environment variables | `UPPER_SNAKE_CASE` | `DATABASE_URL`, `RAILWAY_GIT_COMMIT_SHA` |
| Database tables and columns | `snake_case` | `game_states`, `session_id` |
| Git branches | `kebab-case` | `chore/naming-conventions`, `feat/scene-endpoint` |
| Markdown documentation files | `kebab-case` | `operational-runbook.md` |

## The core rule

**Filesystem paths are `snake_case`. Content identifiers are `kebab-case`.**

This creates a predictable, one-directional transformation between a file and its ID:

```
filename stem:  stronghold_of_drakenvale
content id:     stronghold-of-drakenvale
transform:      stem == id.replace("-", "_")
```

A YAML source and its Markdown mirror therefore share a stem:

```
data/world/.../stronghold_of_drakenvale.yaml        →  id: stronghold-of-drakenvale
prompts/world_vault/.../stronghold_of_drakenvale.md →  id: stronghold-of-drakenvale
```

Validators enforce the `stem == id.replace("-", "_")` rule in both directions.

## Why this split

**Snake_case filesystem paths.** Python's ecosystem expects it. Directories and module files must be snake_case anyway (PEP 8). Splitting files off into kebab-case while directories stay snake_case creates visible inconsistency in every path.

**Kebab-case content IDs and tags.** These are web-facing strings that appear in URLs, anchors, and search. Hyphens are URL-safe and visually survive inside underlined links; underscores do not.

**The transformation rule.** Gives you the "one identity, two surface forms" invariant without forcing either domain to compromise. Tooling that needs to bridge them does one `.replace("-", "_")` call.

## Exceptions

- **Template files** use a leading underscore: `_template_ancestry.json`, `_template.yaml`. Loaders skip files starting with `_`.
- **Pytest discovery** requires `test_*.py` — follow pytest conventions.
- **Markdown docs at the repo root or in `/docs/`** (this file, `README.md`, `testing.md`, etc.) use kebab-case. They are not tied to an ID.
- **Historical legacy names** may persist where renaming would break live session state or external references. Document each exception below when it occurs.

### Documented exceptions

The following root-level files are exempt from the kebab-case rule because
external tooling depends on the exact uppercase filename. This exemption
applies whether or not the file currently exists in the repo.

- `README.md` — GitHub auto-render; universal package-ecosystem expectation.
- `LICENSE.md` (and variants `LICENSE`, `LICENSE.txt`) — GitHub license
  detection requires this exact filename.
- `CHANGELOG.md` — Keep a Changelog / Common Changelog convention.
- `CONTRIBUTING.md` — GitHub community health file (surfaces as the
  "Contributing" link in repo UI).
- `CODE_OF_CONDUCT.md` — GitHub community health file.
- `SECURITY.md` — GitHub security policy file.
- `SUPPORT.md` — GitHub community health file.

Any future addition to this list must include the specific tooling constraint
that justifies the exception. Convenience or habit is not sufficient.

## Enforcement

- `ruff` catches Python-side violations.
- `scripts/validate_data_files.py` asserts `Path(file).stem == data["id"].replace("-", "_")` for every world YAML.
- `scripts/validate_prompts.py` asserts the same for every vault Markdown mirror with an `id` field.
- Tag-level hygiene: no snake_case tags, no authoring meta tags (`placeholder`, `canonical`, `canonical-realm`, `TODO`, `draft`) in canonical world data.
- All validators run in CI on every PR (`.github/workflows/ci.yml`).

## When you find a violation

1. Confirm the identifier's category in the table above.
2. Check whether live session state in Postgres or external references depend on the current name before renaming.
3. If safe to rename: use `git mv` to preserve history.
4. If unsafe: add an entry to **Documented exceptions** above with the reason and a link to the blocking constraint.
5. Run the full validation suite before committing.

## Revision policy

This document is authoritative. If you want to change a convention, update this file first on its own commit, then land the content changes that follow. Never do both in the same commit — it destroys the audit trail of why things are named what they are.