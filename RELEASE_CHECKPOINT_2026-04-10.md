# Release Checkpoint — 2026-04-10

Baseline checkpoint for the post-audit prompt/world topology state.

## Included in this checkpoint

- Prompt-system hardening and runtime guardrail follow-up from the 2026-04-10 audit
- API/OpenAPI follow-up alignment through v3.1.0
- New reference docs:
  - `prompts/magic_rules.md`
  - `prompts/difficulty_rules.md`
  - `prompts/items_rules.md`
- World topology reciprocity audit across `prompts/world/*.yaml`
- Corrected reciprocal route:
  - `stronghold-of-drakenvale` ↔ `volcanic-highlands`

## Intentional retained assumptions

- Hidden sanctum links remain one-way for discovery control:
  - `eryndors-lair` → `sacred-pools`
  - `eryndors-lair` → `platinum-heart`
- Off-map placeholder exits remain in place pending future authored destinations:
  - `dracelune` → `feywood-glade-border`
  - `volcanic-highlands` → `draconic-grasslands`

## Reference docs

- `WORLD_TOPOLOGY_BASELINE.md`
- `README.md`
- `TODO.md`

## Operator note

If a git tag is created for this baseline later, use a name aligned to this checkpoint, for example:

`topology-baseline-2026-04-10`

This file serves as the lightweight in-repo release note until a formal tag or GitHub release is created.