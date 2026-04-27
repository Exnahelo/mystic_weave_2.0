# NPC Persistence Infrastructure Design

## 1. Scope and non-scope

This infrastructure covers **dynamic NPC persistence for play-created continuity**. Its purpose is to persist named NPCs that the GPT creates or concretizes during play when they become relevant, recurring, or continuity-bearing. In practice, this means NPCs who deliver actionable information, accept or offer work, become a stable point of contact, or otherwise create future-scene obligations that the system should remember outside the current turn.

This design does **not** attempt to replace the authored canonical NPC corpus in `prompts/npcs.md` for v1. It also does not include combat systems, simulation features, route-planning AI, schedules, independent goals, off-turn behavior, or autonomous world actions. Those are explicitly deferred, consistent with `todo.md`'s restricted future builds note on NPC simulation. Faction-system redesign is also out of scope; this design only permits lightweight faction linkage via affiliation IDs.

## 2. Relationship to existing canonical NPCs

The repo already has a strong authored-canon layer for NPCs:
- `prompts/npcs.md` defines major named figures, anchor NPCs, and generative roles.
- `prompts/world_vault/**` and corresponding runtime world content use `known_npcs` as location-facing authored anchor metadata.

The central design question is whether canonical NPCs and dynamic NPCs should live in one store or two.

### Option A: two-store model

- **Canonical NPCs** remain authored in markdown/world files.
- **Dynamic NPCs** live in the database.

**Advantages**
- Fastest path to shipping persistence for emergent play-created NPCs.
- Preserves the current human-readable canon authoring workflow.
- Avoids an immediate canon backfill/mirroring project for all major NPCs and generative-role incumbents.
- Fits the current architecture, where authored canon and runtime state already coexist in separate layers.

**Disadvantages**
- NPC truth is split across authored files and DB records.
- Scene assembly must merge authored anchor metadata with runtime NPC rows.
- Long-term convergence to a single queryable NPC source becomes a future migration task.

### Option B: one-store model

- Canonical NPCs are backfilled or seeded into the DB.
- Dynamic NPCs and canonical NPCs use the same table and API surface.

**Advantages**
- Cleaner long-term query model.
- A single persistence surface for retrieval, filtering, and future tooling.
- Easier future evolution into richer NPC systems.

**Disadvantages**
- Much higher initial churn.
- Requires immediate canonical backfill/seeding and governance rules for file-vs-DB authority.
- Risks disrupting the current lore authoring process before the persistence surface is proven.

### Recommendation

Recommend **Option A: two-store for v1**.

This is the best match for current repo structure and the stated rationale for the task: persist dynamic, continuity-bearing NPCs without expanding into a larger canon migration arc. The authored markdown corpus remains the human-readable source of canonical major NPC identity. The DB becomes the runtime persistence layer for dynamic NPCs and targeted backfills of recent session-important NPCs.

This recommendation should be treated as a **deliberate v1 compromise**, not an ideological endpoint. If NPC persistence proves valuable and the project later wants a unified query surface, the DB can become the long-term single store with a separate canonical backfill project.

## 3. Data model

### Recommendation: global NPCs, not per-session NPCs

NPC state should be **global**, not per-session.

**Rationale**
- The world model already treats locations and authored canon as persistent world entities rather than session-private constructs.
- The need being solved is continuity across scenes and later play, not isolated one-session memory.
- The recent-session backfill list reads like world-facing people who should survive beyond one session.
- Global persistence keeps route design and lookup simpler and avoids multiplying endpoints by session scope.

Per-session NPC storage would only become preferable if the game later supports alternate timelines, parallel campaign realities, or multiple incompatible world states. That is not the current architecture.

### Proposed NPC record shape

Minimum v1 record:

- `id`: kebab-case slug; stable primary identifier
- `name`: display name or title used in play
- `location`: current `locations.id` reference; nullable when offstage or unknown
- `role`: short narrative role, free text
- `disposition`: integer from `-100` to `100`
- `notes`: free text continuity notes for GPT/runtime recall
- `last_seen_turn`: integer, nullable
- `first_seen_turn`: integer, nullable
- `status`: one of `active | inactive | deceased | departed`
- `tags`: list of string tags
- `faction_affiliations`: optional list of faction IDs
- `discovered`: boolean indicating whether the player has actually met or learned of this NPC in play

### Naming recommendation

Use **`disposition`** rather than `disposition_to_pc` for consistency with existing companion vocabulary and to avoid overly narrow naming. The stored meaning in v1 is still effectively “disposition toward the player/party,” but the shorter field is more repo-consistent and leaves room for future expansion without an awkward rename.

### Validation expectations

- `id` should be kebab-case and stable after creation.
- `disposition` should be clamped or validated to `-100..100`.
- `status` should be enum-constrained.
- `tags` and `faction_affiliations` should default to empty lists.
- `discovered` defaults to `true` for persisted play-created NPCs, unless the implementation later needs hidden/preloaded NPC support.
- `first_seen_turn` and `last_seen_turn` remain nullable to support manual backfill and off-turn imports.

### Location handling

V1 should support a **single current location reference** via `location`. This aligns with the existing location graph model and keeps retrieval simple for `GET /location/{location_id}/npcs`.

If an NPC is traveling, offstage, missing, or globally known but not presently placeable, `location` may be `null`. Multi-location presence, route patrols, or schedules are explicitly deferred.

### Relationship to `LocationData.known_npcs`

For v1, `LocationData.known_npcs` should remain **authored-anchor metadata**, not the runtime source of truth for persisted NPCs.

Recommendation:
- `LocationData.known_npcs` continues to express authored canonical anchors, expected roles, or location-associated named figures from world content.
- The new NPC table becomes the **runtime source of truth** for dynamic NPC persistence.

This keeps authored canon readable and stable while preventing location blobs from becoming an accidental mutable NPC database. Scene-building can merge authored anchors with runtime NPC rows, but the DB should own runtime continuity.

## 4. Storage

### Table design

Recommend a new **`npcs`** table that mirrors the repo’s `locations` pattern.

Suggested shape:

- top-level columns
  - `id` (text primary key)
  - `name` (text, not null)
  - `location_id` (text, nullable, foreign key to `locations.id`)
  - `data` (jsonb, not null)
  - `updated_at` (timestamp, default `now()`)

### Why this pattern

- It matches the repo’s established JSONB-first persistence style.
- It minimizes schema churn for future NPC field additions.
- It supports a thin top-level query layer (`id`, `name`, `location_id`) while preserving narrative flexibility in JSONB.
- It mirrors route and migration patterns the codebase already uses for `locations`.

### JSONB payload recommendation

The `data` payload should contain the full NPC record, including repeated canonical fields such as `id`, `name`, and `location`, so the stored object is self-describing when loaded independently of top-level columns. This matches how `LocationResponse` and game-state JSON are currently handled.

### Querying and filtering

For v1, the principal DB query pattern should be by:
- `id`
- `location_id`

Additional JSONB indexing can be deferred unless performance demands it.

### Migration plan

Add a new Alembic revision that:
- creates `npcs`
- adds `location_id` foreign key to `locations.id`
- sets `updated_at` default to `now()`

No migration should alter existing location rows or game-state tables in v1. The point is to add an adjacent persistence surface, not rewrite existing world storage.

## 5. API surface

Minimum viable routes:

- `GET /npc/{npc_id}`
- `POST /npc`
- `GET /location/{location_id}/npcs`

These should follow the same route style as `api/routes/location.py`: async route handlers, `asyncpg` pool dependency, UPSERT-style creation/update behavior, and narrow response models.

### `GET /npc/{npc_id}`

Returns one persisted NPC record by ID.

**Behavior**
- `404` if not found
- response contains ID, name, full structured NPC payload, and `updated_at`

### `POST /npc`

Creates or updates an NPC by ID via UPSERT.

**Behavior**
- `201` on create
- `200` on update
- request body is the full NPC payload for v1; sparse-patch semantics can be deferred
- `location_id` top-level and `data.location` should remain consistent

### `GET /location/{location_id}/npcs`

This route should be the default runtime list endpoint for scene-facing retrieval.

### Explicit recommendation: Option 1

Commit to **Option 1: return only discovered and active NPCs by default**.

Proposed filter rule for v1:
- include rows where `location_id = {location_id}`
- include only NPCs with `discovered = true`
- include only NPCs whose `status = active`

This keeps the route tightly aligned to scene utility and avoids surfacing hidden, departed, deceased, or merely archived continuity records as if they are presently available in the scene.

If a future need arises for GM/admin views, a separate endpoint or optional query mode can be added later. V1 should optimize for safe narrator behavior, not exhaustive diagnostics.

### Request/response shape in prose

All three endpoints should use the same conceptual NPC payload shape described in Section 3. `GET /location/{location_id}/npcs` should return a list wrapper rather than a bare list if the implementation wants room for metadata, but either approach is acceptable. The important v1 requirement is that the route returns current-scene-eligible runtime NPCs only, using the discovered/active filter above.

## 6. Prompt integration

### When the GPT should persist NPCs

Recommend this v1 rule:

The GPT should call `POST /npc` **the first turn an NPC is named and either**:
- delivers information likely to matter later,
- accepts or offers a job, task, duty, or obligation,
- becomes a stable contact, witness, gatekeeper, patron, clerk, or counterpart,
- or takes a position the player may return to later.

This is a concrete runtime interpretation of the current `prompts/engine.md` instruction to persist named NPCs that become relevant, recurring, or continuity-bearing.

### How NPC context should enter scene context

Recommend that scene context use **both** sources:
- authored anchors from `LocationData.known_npcs`
- runtime dynamic NPCs from the NPC table for the current location

However, the runtime lookup path should be treated as the authoritative source for **persisted dynamic presence**. In other words:
- `known_npcs` says who is canonically associated with a place
- the NPC table says which dynamic NPCs actually exist in runtime continuity and are currently present

For v1, the simplest design is for `GET /scene/{session_id}` / scene-context assembly to load active/discovered NPCs for the current location using the same logic as `GET /location/{location_id}/npcs`, then merge those names with authored anchors when building visible scene entities.

### Prompt intent for `prompts/engine.md`

The prompt update should be minimal and operational, not verbose. Intent only:

- when a newly named NPC becomes continuity-bearing, persist them immediately
- use location NPC retrieval as part of scene grounding
- do not rely on memory alone for recurring local NPC continuity

The final wording should stay short because `prompts/engine.md` is already near builder budget.

## 7. Migration and backfill

### Schema migration

First step is the Alembic migration adding the `npcs` table. Until that lands, there is no safe persistent substrate for dynamic NPCs.

### Backfill recommendation

Backfill should happen **after** infrastructure lands, using a **one-off scripted or manual upsert process** rather than a new permanent seed-file format.

Recommendation:
- use manual or script-assisted `POST /npc` upserts once the route exists
- keep the backfill list human-reviewed because some entries are emergent, session-specific, or title-based placeholders

Backfill targets:
- Rellan Sive
- Mira Seln
- Ressa Thorn
- Hollis Reed
- Mara Fen
- Tamsin Vale
- SSTC Western Supervisor (placeholder title until a personal name exists)

### Why not a permanent seed file

The backfill list is small and clearly derived from recent play rather than canon-authoring policy. A permanent seed format would introduce extra system surface for a one-time operational need.

## 8. Risks and open questions

### Canon split risk

The biggest architectural compromise is the two-store split between authored canonical NPC data and runtime DB NPC data. This is acceptable for v1, but it does create a long-term question about whether canonical anchors should eventually be mirrored into the DB.

### Location ambiguity

A single `location` field is correct for v1, but it cannot express patrol routes, travel states, multi-site influence, or offstage-but-nearby characters cleanly. That complexity is intentionally deferred.

### Disposition granularity

`disposition` works well as a single scalar in v1, but it may later prove too coarse for faction-linked, party-split, or event-history-rich NPC relationships.

### Placeholder and title-only identities

The design should allow stable title-based NPCs such as `SSTC Western Supervisor` or canon figures like `The Warden of Greymantle`, but Daniel may want an explicit rule on when a title counts as a stable persisted identity versus a temporary generic role.

### Scene-context budget

Adding too much NPC detail to scene context risks prompt bloat. V1 should bias toward compact summaries and names rather than large per-NPC context blocks.

### Authored anchors vs runtime truth

This design recommends that `LocationData.known_npcs` remain authored-anchor metadata while the NPC table is the runtime source of truth. That division is clean, but it must be documented explicitly during implementation so the GPT and future contributors do not accidentally keep mutating location blobs for NPC continuity.

### GPT behavior when NPC persistence fails mid-session

If `POST /npc` fails during play, the GPT should treat the write failure as a continuity-risk event rather than silently continuing as if persistence succeeded. It may continue the current scene only if doing so does not depend on the NPC already being safely committed as canonical runtime continuity. The preferred behavior is: acknowledge the failure briefly, avoid presenting the NPC as safely persistent fact for later turns, retry within the existing runtime safety policy if allowed, and avoid building subsequent choices around persistence-dependent assumptions until the write succeeds. In short: NPC invention may occur in prose, but recurring continuity should not be trusted unless the persistence write lands.

## 9. Implementation phasing

### Phase A: schema migration + model + basic routes

- add `npcs` migration
- add Pydantic models for NPC request/response payloads
- add `GET /npc/{npc_id}`
- add `POST /npc`
- add `GET /location/{location_id}/npcs`

This phase should ship a usable persistence substrate with no scene-context changes yet.

### Phase B: scene context integration

- extend scene assembly to load runtime NPCs for current location
- merge authored anchors (`known_npcs`) with persisted runtime NPCs
- keep output compact and scene-safe

This phase makes NPC persistence matter during normal narration.

### Phase C: prompt integration

- tighten `prompts/engine.md` intent around when to persist NPCs
- direct the GPT to rely on route-backed retrieval rather than memory for recurring continuity
- keep wording minimal to respect prompt budget

This phase reduces behavioral drift between infrastructure and narrator practice.

### Phase D: backfill

- manually or script-assist upsert the recent-session NPC list
- verify IDs, names, locations, notes, and placeholder-title handling

### Explicit dependency note

Backfill **cannot precede migration**. That creates an unavoidable interim window in which dynamic NPCs remain operationally unpersistable until Phase A lands. The implementation task should acknowledge that window explicitly rather than pretending the continuity gap does not exist.

## Review gate note

This document is intended to lock the design only. No production code, migration SQL, route stubs, tests, or implementation scaffolding should be created as part of this task. A later Cline task can implement Phase A after Daniel approves this design.