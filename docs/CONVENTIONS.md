# Naming Conventions

Authoritative reference for naming identifiers in this repository.

When a naming question arises, match the identifier's **category**, not the file it appears in.

This file covers naming only. Structural, schema, validation, and content-integrity rules belong in a separate policy document.

---

## Core policy

1. Prefer **ecosystem-native conventions** over invented project-local ones.
2. Use **one rule per identifier category**.
3. Use **tool-required filenames exactly as required**.
4. If a framework or external API requires a different convention, follow that at the boundary and document the exception.
5. Avoid unnecessary abbreviations.
6. When in doubt, choose the most boring, widely expected name.

---

## Quick reference table

| Category | Convention | Example |
|---|---|---|
| Repository meta files recognized by tooling | exact conventional name | `README.md`, `LICENSE`, `CONTRIBUTING.md` |
| General directories | `snake_case` | `api_clients/`, `test_fixtures/` |
| Python modules / packages / files | `snake_case` | `auth_service.py` |
| Python functions / methods / variables | `snake_case` | `build_user_profile()`, `session_id` |
| Python classes / exceptions | `PascalCase` | `UserProfile`, `AuthenticationError` |
| Python constants | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT_SECONDS` |
| Shell / Bash scripts | `snake_case` | `deploy_service.sh` |
| Shell functions / local variables | `snake_case` | `load_config()`, `target_dir` |
| Shell exported env vars / constants | `UPPER_SNAKE_CASE` | `DATABASE_URL` |
| JSON / YAML keys (internal schemas) | `snake_case` | `user_id`, `created_at` |
| Database tables / columns / views / indexes | `snake_case` | `user_accounts`, `created_at`, `idx_users_email` |
| SQL constraints | `snake_case` with type prefix | `fk_orders_user_id`, `uq_users_email` |
| Java packages | lowercase dot notation | `com.example.billing` |
| Java classes / interfaces / enums / records | `PascalCase` | `PaymentService` |
| Java methods / fields / local vars | `camelCase` | `findActiveSubscription()` |
| Java constants | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT_MILLIS` |
| JavaScript functions / variables | `camelCase` | `buildSessionPayload()` |
| JavaScript classes | `PascalCase` | `SessionManager` |
| JavaScript constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| JS/TS React component files | `PascalCase` | `UserCard.jsx` |
| Non-component JS/TS files | `kebab-case` | `session-manager.js` |
| HTML / CSS class names / web-facing asset names | `kebab-case` | `account-settings.html`, `user-card` |
| URL path segments / public slugs | `kebab-case` | `/user-profiles`, `billing-events` |
| Query params / internal API fields | `snake_case` | `?session_id=123` |
| Environment variables | `UPPER_SNAKE_CASE` | `RAILWAY_ENVIRONMENT`, `JWT_SECRET` |
| Git branches | `kebab-case` with prefix | `feat/add-auth-middleware` |
| Markdown docs (general) | `kebab-case` | `deployment-runbook.md` |
| Mirrored artifacts | preserve canonical filename stem | `customer_profile.yaml` ↔ `customer_profile.md` |
| Generated files | suffix or prefix marker | `openapi.generated.json`, `generated_schema.sql` |
| Template files | leading underscore or `.template` marker | `_template.env`, `config.template.yaml` |
| Test files (Python) | `test_*.py` | `test_auth_service.py` |
| Test functions (Python) | `test_<behavior>` | `test_rejects_expired_token()` |

---

## The default rule

**Use `snake_case` unless the language or platform has a strong, well-established alternative.**

That means:

- Python internals: `snake_case`
- SQL objects: `snake_case`
- JSON/YAML internal schema keys: `snake_case`
- shell internals: `snake_case`

Use other conventions only where they are the clear industry norm:

- Java / JavaScript methods and variables: `camelCase`
- classes and types: `PascalCase`
- public slugs, branch names, CSS classes, URL segments: `kebab-case`
- constants and environment variables: `UPPER_SNAKE_CASE`

---

## Repository root files

### Use exact conventional names for tooling-sensitive files

These filenames are exceptions to the lowercase rule and should be preserved exactly:

- `README.md`
- `LICENSE` or `LICENSE.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `SUPPORT.md`
- `Makefile`

Do not rename these for style consistency. Tooling and ecosystem expectations matter more than aesthetics.

### All other root files

Use the name required by the ecosystem or tool:

- `pyproject.toml`
- `package.json`
- `railway.json`
- `docker-compose.yml`
- `.editorconfig`
- `.env.example`

Do not invent alternate casing.

---

## Python

Follow Python ecosystem conventions:

- files/modules/packages: `snake_case`
- functions/methods/variables: `snake_case`
- classes/exceptions: `PascalCase`
- constants: `UPPER_SNAKE_CASE`
- non-public functions/methods/helpers: leading underscore (`_build_payload`)
- dunder names only for actual Python protocol methods (`__init__`, `__repr__`)

Examples:

- `auth_service.py`
- `build_scene_context()`
- `user_profile`
- `AuthenticationError`
- `DEFAULT_PAGE_SIZE`

Do not use `camelCase` in Python except when mirroring an external API exactly.

---

## SQL

Use `snake_case` for all database objects:

- tables
- columns
- views
- indexes
- constraints
- functions/procedures where practical

Examples:

- `user_accounts`
- `created_at`
- `vw_active_subscriptions`
- `idx_users_email`
- `fk_orders_user_id`

### Table rule

Use **plural table names** by default.

Examples:

- `users`
- `orders`
- `audit_logs`

### Constraint prefixes

Use type-prefixed names:

- `pk_<table>`
- `fk_<from>_<to>`
- `uq_<table>_<column>`
- `ck_<table>_<rule>`
- `idx_<table>_<column>`

Examples:

- `pk_users`
- `fk_orders_user_id`
- `uq_users_email`

Avoid quoted mixed-case SQL identifiers.

---

## JSON and YAML

### Internal schemas

Use `snake_case` keys.

Examples:

- `user_id`
- `display_name`
- `created_at`
- `is_active`

### External schemas

If an external API or framework is canonically `camelCase`, preserve that convention at the boundary instead of force-converting everything.

Examples:

- external JS API payload: `createdAt`
- internal Python schema: `created_at`

Document the boundary if both forms exist.

---

## Shell / Bash

Use:

- filenames: `snake_case.sh`
- functions: `snake_case`
- local variables: `snake_case`
- exported variables/constants: `UPPER_SNAKE_CASE`

Examples:

- `sync_backups.sh`
- `load_config()`
- `target_dir`
- `DATABASE_URL`

Do not use hyphens in variable names.

---

## Java

Use standard Java naming:

- packages: lowercase dot notation
- classes/interfaces/enums/records: `PascalCase`
- methods: `camelCase`
- fields/local vars: `camelCase`
- constants: `UPPER_SNAKE_CASE`

Examples:

- `com.example.billing`
- `PaymentService`
- `findActiveSubscription()`
- `retryCount`
- `DEFAULT_TIMEOUT_MILLIS`

Public class name should match the filename.

---

## JavaScript

Use:

- functions/variables: `camelCase`
- classes: `PascalCase`
- constants: `UPPER_SNAKE_CASE`

### File naming

Use:

- `PascalCase` for React component files
- `kebab-case` for non-component JS files

Examples:

- `UserCard.jsx`
- `session-manager.js`
- `buildSessionPayload()`
- `SessionManager`
- `MAX_RETRY_COUNT`

If a framework imposes a different file naming convention, follow the framework.

---

## HTML / CSS / web-facing assets

Use `kebab-case` for:

- HTML files
- CSS class names
- public-facing asset names
- `data-*` attributes
- URL path segments

Examples:

- `account-settings.html`
- `user-card`
- `data-user-id`
- `/api/v1/user-profiles`

---

## Environment variables

Always use `UPPER_SNAKE_CASE`.

Examples:

- `DATABASE_URL`
- `JWT_SECRET`
- `RAILWAY_ENVIRONMENT`
- `LOG_LEVEL`

Environment variables are never `camelCase`, never `kebab-case`.

---

## Git branches

Use:

`<type>/<kebab-case-description>`

Allowed prefixes:

- `feat/`
- `fix/`
- `refactor/`
- `docs/`
- `test/`
- `chore/`
- `perf/`
- `ci/`

Examples:

- `feat/add-auth-middleware`
- `fix/handle-null-session-id`
- `docs/update-naming-conventions`

---

## Documentation

### Tooling-sensitive docs

Use exact conventional names:

- `README.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `SECURITY.md`

### General docs

Use `kebab-case.md`.

Examples:

- `architecture-overview.md`
- `deployment-runbook.md`
- `database-migration-policy.md`

### Mirrored markdown artifacts

If a markdown file is a maintained mirror of a canonical non-markdown artifact, follow the mirrored-artifact rule instead of the general docs rule.

---

## Mirrored artifacts

When one artifact is a maintained mirror, derivative, or parallel representation of another canonical artifact, preserve a predictable filename-stem relationship between them unless tooling explicitly requires otherwise.

Default rule:

- the mirrored artifact should use the same filename stem as the canonical artifact
- only the extension or required platform-specific wrapper should differ

Examples:

- `customer_profile.yaml` ↔ `customer_profile.md`
- `magic_system.json` ↔ `magic_system.md`

If the mirrored artifact also carries an internal ID or slug, any stem-to-ID transformation rule should be defined in a separate data or schema policy, not in this naming file.

Mirrored artifacts are not treated as ad hoc exceptions when they follow the mirrored-artifact rule; they are a separate identifier category.

---

## Tests

### Python

- files: `test_<subject>.py`
- functions: `test_<behavior>()`

Examples:

- `test_auth_service.py`
- `test_rejects_expired_token()`

### Other languages

Use the dominant framework convention, but keep the stem descriptive and lowercase.

Examples:

- `session-manager.test.js`
- `payment-service.spec.js`

---

## Generated files and templates

### Generated files

Mark generated artifacts clearly:

- `*.generated.*`
- `generated_*`

Examples:

- `openapi.generated.json`
- `generated_schema.sql`

### Templates

Mark templates clearly:

- leading underscore, or
- `.template.` in name

Examples:

- `_template.env`
- `config.template.yaml`

---

## Abbreviations

Allowed when widely standard:

- `id`
- `url`
- `html`
- `sql`
- `api`
- `ui`
- `db`

Do not invent compressed names that reduce readability.

Bad examples:

- `usr_cfg_mgr`
- `dt_proc_fn`

Prefer full words unless the abbreviation is universal.

---

## Forbidden patterns

Do not use:

- spaces in filenames
- mixed casing for SQL identifiers
- `camelCase` in Python internals
- `snake_case` for Java methods or fields
- inconsistent singular/plural table naming
- decorative underscores or prefixes with no semantic meaning
- all-caps filenames except where tooling or ecosystem convention explicitly expects them

---

## Exception policy

An exception is allowed only if one of these is true:

1. A language or framework convention requires it.
2. A tool requires an exact filename.
3. An external API or schema must be mirrored exactly.
4. A legacy or public interface would break if renamed.

Every exception must be documented with:

- the current name
- why it is exempt
- what tool, framework, API, or interface requires it

Convenience is not a valid reason.

Mirrored artifacts that follow the mirroring rule are not ad hoc exceptions.

---

## Enforcement guidance

Recommended enforcement:

- Python: `ruff`, `flake8`, `pylint`
- Shell: `shellcheck`
- JavaScript: `eslint`
- YAML/JSON: schema validation + formatter
- SQL: SQL linter/formatter where available
- Repo-wide: custom naming checks in CI

Recommended CI checks:

- disallow spaces in filenames
- disallow mixed-case SQL migration filenames
- require `snake_case` for Python module names
- require `UPPER_SNAKE_CASE` for env vars in examples/templates
- require exact names for root meta files
- require approved branch prefixes
- enforce mirrored-artifact stem consistency where a project defines mirrored artifacts

---

## Decision rule

When naming something:

1. Identify the category.
2. Apply the category rule.
3. If a tool, framework, or external API requires something else, use that instead.
4. If the artifact is a maintained mirror of another artifact, apply the mirrored-artifact rule.
5. If still unclear, choose the most common convention in that language ecosystem.
6. Document exceptions instead of improvising.