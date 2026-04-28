# Mystic Weave — TODO

## CI / Process Debt

- [ ] Configure branch protection on main: require Lint+Unit+Contract,
      Integration+Loop Test, and catalog-validation status checks before merge.
- [ ] Set up failure notification on main CI (GitHub email-on-failure or
      Slack webhook). Main CI was red for 30+ runs without anyone noticing.
- [x] Audit recent direct-to-main pushes: commit 0c4b579b ("Renames Feywood
      Glade to Feywood in all content") corrupted tests/unit/test_companion_models.py
      via sloppy find-replace and merged anyway. Investigate whether mass-rename
      commits go through PR review.
- [ ] Update GitHub Actions to Node.js 24 before Sept 16 2026 deprecation.

## Item Schema Follow-ups

- [ ] Tighten Effect.params validation against effect registry param contracts
      in mechanics/effects.json.
- [ ] Author next batch of items: 10-20 mundane (basic weapons, armor, common gear).
- [ ] JSON Schema export: emit data/catalog/schemas/*.schema.json from Pydantic
      models for non-Python consumers (GPT builder).
- [ ] Pricing rules engine: design and implement economy/price_rules.json so
      future items can use pricing.model: "computed".
- [ ] API integration: add endpoints reading from data/catalog/, plan cutover
      from data/items/.

---

## 🚫 Restricted Future Builds

These items are not buildable within the current architecture without significant rebuild. Documented here for future planning.

### Full Multi-Agent Orchestration

**Barrier:** Mystic Weave uses a single custom GPT instance via the GPT builder. Running separate specialized model instances for Narrator, Referee, Planner, and Extractor roles requires an orchestration layer — either a custom backend that manages multiple API calls and coordinates outputs, or migrating away from the GPT builder entirely to a direct API implementation. Neither is a small change.
**When to revisit:** When the GPT builder becomes the bottleneck and direct API control is needed for reliability or cost.

### Combat Subsystem

**Barrier:** Explicitly deferred. A real combat system requires its own turn structure, initiative, action economy, and resolution model distinct from the current narrative roll system. Building it on top of the existing d100 roll-under framework is possible but requires new endpoints, new state schema (combat status, turn order, active effects), and significant GPT instruction changes. The current system handles combat narratively.
**When to revisit:** When narrative combat resolution feels insufficient and players need tactical depth.

### NPC Simulation — Independent Goals and Schedules

**Barrier:** Treating NPCs as autonomous agents with their own goals, schedules, and world-modifying actions requires a simulation layer that runs independently of player turns. This is architecturally separate from the current request-response game loop. NPCs currently have static attitude scores and narrative flavor — they react, they do not act.
**When to revisit:** When the world needs to feel like it moves without the player.

### Procedural Content Generation

**Barrier:** Encounter generation, dynamic loot tables, and procedural world events require a generation layer with its own rules and randomness model separate from the dice roller. The current world is entirely authored. Procedural content would need to integrate with the location graph, the faction system, and the economy without contradicting canon.
**When to revisit:** When authored content cannot keep pace with player exploration.

### Vector Search Lore Retrieval

**Barrier:** Currently all lore is in static knowledge files uploaded to the GPT builder. A semantic retrieval layer would allow the GPT to query specific lore on demand rather than having everything in context. Requires embedding infrastructure, a vector database, and a retrieval API — meaningful infrastructure that doesn't exist in the current stack.
**When to revisit:** When the GPT knowledge file upload limit or context ceiling becomes a real constraint on world depth.

### Multi-Player Support

**Barrier:** The entire architecture assumes one player per session. Session state, character state, and the turn loop are single-player constructs. Multi-player would require concurrent session management, shared world state with conflict resolution, and a turn coordination layer. Not a small addition.
**When to revisit:** If the game ever needs to support shared campaigns.
