# Drakenvale Design Notes

> **For author reference only. Do not upload to GPT builder.**
> This document tracks open questions, resolved decisions, authoring gaps, and narrative design thinking for the Drakenvale world. Updated as decisions are made.

---

## Tags

`#design` `#drakenvale` `#internal`

---

## Resolved Decisions

These were open questions that have now been answered and committed to the world files.

**Heartstone (legacy: "Radiant Crystal")** — Discovered during early Heartmass excavation and later infused with the founding dragons' gathered magic. Housed in the Draconic Hall. Serves as an exceptional deadlock-guidance artifact. Canon. In `world.md`.

**Mortal/kobold political standing** — Advisory standing, petition rights, no vote. Mortals can hold enforcement roles (Acolytes of Justice). Kobolds are a protected class with welfare access. Neither group holds formal political representation. Canon. In `world.md`.

**Wardens vs. Dragon Guard** — Two distinct organizations. The Wardens report to Eryndor in peacetime (sacred sites, internal security, investigation). They temporarily fall under Zarkeros when militarized (precision strikes, crisis response). The Dragon Guard is Zarkeros's exclusively for external defense. Canon. In both world and organizations files.

**Trial of Wings** — Non-lethal ritualized duel, overseen by the Council, for disputes of honor or grievance. Rarely invoked, highly respected. Open to dragons and dragonborn; mortals typically use mediation instead. Canon. In `world.md`.

**SSTC relationship** — Independent guild, not a state organ. All three Council members hold advisory or operational roles within it. Varethyn runs the Amethyst Veil through its trade routes. Canon. In both world and organizations files.

**Draconic Conclave timing** — Approximately century-frequency, but convened by Council decree when needed. Not on a fixed schedule. Left malleable as a story hook. Canon.

**Per-dragon elite guards** — Not a separate named unit per dragon. Maps to: Wardens (Eryndor/Zarkeros shared, split by context), Dragon Guard (Zarkeros exclusively), Amethyst Veil/Sapphire Sentinels (Varethyn covertly). Canon.

---

## Open Stub Organizations

These organizations are named in source material but have no authored content. Reserved for future development. Do not invent content for them in GPT responses — treat them as existing but unknown.

Also partially stubbed:

- **Sapphire Sentinels** — Intelligence org tied to Varethyn/Amethyst Veil. Structure not yet authored.
- **Silver Wing Envoys** — External diplomacy. Structure not yet authored.
- **Circle of Artisans** — Infrastructure and arts. Structure not yet authored.
- **Sapphire Choir** — Oral traditions and culture. Structure not yet authored.
- **Order of the Platinum Flame** — External Bahamut knightly order. Authored at summary level but no full detail on headquarters, operations, or campaign integration.

---

## Unresolved Design Threads

### 2. Crisis Management Protocol

**Status: Partially resolved.** The Warden/Dragon Guard dual structure is now clear. The organizations file establishes that Sapphire Sentinels and Dragon Guard coordinate on multi-front threats.

Still missing: A unified Crisis Management Protocol. No explicit chain of command when all three Council members are needed simultaneously in a crisis. No named backup communication systems.

**Design note:** This can remain underdeveloped until a story demands it. If a Council crisis scene arises, the GPT should default to: Zarkeros commands military response, Eryndor oversees civilian protection and Warden deployment, Varethyn manages intelligence and magical countermeasures. That's enough for narrative coherence.

### 5. Threat Management and Countermeasures

**Status: Partially resolved.** Wardens handle internal magical threats. Sapphire Sentinels handle external intelligence. Dragon Guard handles external military threats.

Still missing: Countermeasures against forbidden magic specifically. No authored response to magical corruption seeping from the Temple to Tiamat. The Wardens' "Vigilance Rituals" are referenced but not detailed.

**Design note:** The Shadowed Hollows biome entry captures what corruption looks like when it's already spreading. The gap is the *response* — what does a Warden actually do when they detect Tiamat's influence in someone or something? This is a good thing to author before Phase 4 since it's almost certainly a story arc.

### 8. Post-Crisis Recovery

**Status: Not authored.** No formal post-crisis recovery framework exists.

**Design note:** The Renewal Rites concept (referenced in Apple Notes) could fill this gap. A short entry in the organizations file under Platinum Acolytes would cover it adequately. Not needed for Phase 4 unless a story arc involves recovering from a crisis.

---

## Narrative Design Notes

### The Temple to Tiamat

The single highest-stakes location in Drakenvale. Its seal is the Platinum Warden's sacrifice made permanent. Three escalating states are possible:

1. **Sealed (current)** — Vigilance Rituals ongoing. Shadowed Hollows slowly expanding. No active threat but ambient unease.
2. **Partially unsealed** — A major story event. Corruption spreads faster. Alignment tensions spike. The Council fractures under pressure.
3. **Unsealed** — Campaign-level event. Tiamat's influence is active. Existential threat to Drakenvale.

The GPT should not move between these states without player-driven cause. State 1 is default. State 2 requires a significant story beat.

### The Rift of Discord

Not a dungeon — a wound. Its relationship to the Temple is proximity-based: the Rift and the Shadowed Hollows are in the same geographic corner, which is not coincidental. The chaos energy in the Rift and the necrotic energy in the Hollows interact and reinforce each other.

If the Temple moves toward State 2, the Rift destabilizes first — use it as an early warning system narratively.

### Varethyn and the Amethyst Veil

The most asymmetric character on the Council. He knows things the other two don't and acts on that information without sharing it. He is not malevolent — he genuinely believes long-term stability is served by his approach. But his definition of "stable" and Eryndor's are not the same thing.

Players who discover the Amethyst Veil face a genuine dilemma: it's illegal under the spirit of the Ptarian Code (unauthorized intelligence gathering, deception of Council peers), but it may also be the only thing that has prevented several catastrophes. Varethyn knows this. He's betting you'll reach the same conclusion.

### Zarkeros and the Code

Zarkeros upholds the Ptarian Code not from belief but because it is the framework within which his power operates most effectively. This means he is scrupulously compliant in observable behavior and genuinely dangerous in edge cases. He would subvert the Code if the gain were sufficient and the cost manageable. The key design constraint: what would make it worth it to him? Power isn't sufficient — he already has it. Loss of Drakenvale as a functioning power base would threaten him. An external threat that the Code's restrictions prevent him from addressing would be his breaking point.

### The Draconic Conclave as Story Anchor

The Conclave is called by Council decree when needed, not on a fixed schedule. Its last convening is unspecified. Possible story uses:

- **Approaching Conclave** — Political maneuvering, factions lobbying for Code amendments, outsiders trying to influence the outcome
- **Conclave in session** — Player characters caught in a politically charged moment; every dragon in Drakenvale is present and engaged
- **Post-Conclave** — A controversial amendment was passed; factions are adjusting; something destabilizing was put into law

---

## Source Material Notes

### Apple Notes — What to Keep vs. Discard

Files to keep in Obsidian as reference but not GPT-upload:

- `Continuity` (Apple Notes) — Full gap analysis; superseded by this design notes file
- All Dec 9 policy notes (Apple Notes) — Superseded by this design notes file
- Individual biome Apple Notes — Superseded by `drakenvale_biomes.md`; keep as species reference if needed

### Ptarian Codex Note

The `NEW_NEW_DRAKENVALE.docx` contains the most complete version of the Ptarian Codex as a formal charter document. If a full in-world legal text is ever needed (for roleplay, as a found document, etc.), that file is the source. It was intentionally not included in the GPT files because its length and legal prose format are not useful for the GPT's narrative function. The principles are captured in `world.md`.

---

## Companion Schema Design (2026-04)

### Status

Schema design locked. Implementation deferred to a future arc.

Supersedes the open TODO item "Decide on companion `species` asymmetry"
from the post-naming-cleanup open items list.

### Three-tier model

Companions split into three distinct Pydantic models, not a single
model with a tier field. Separate types give free compile-time
guarantees about which fields are present for each tier and keep the
schema clean for consumers.

**SapientCompanion** — humanoid party members (halfling scout, elven
healer, dragonborn duelist). Mirrors the PC schema.

Fields:
- `ancestry`, `culture`, `background`, `focus`
- `domains`, `knowledge`, `application`
- `identity`: motivations, alignment, quirks, bonds, flaws
- `equipment`, `reputation`, `hp`
- `known_languages` (placeholder; see Language System Deferral below)
- `bond_links`: primary + optional secondary

**CreatureCompanion** — non-sapient animals acting on instinct and
training (wolf, hawk, horse, war hound).

Fields:
- `species`, `subtype` (subtype is narrative flavor, not mechanical)
- `age_category`, `size`
- `tactical_role` (enum: `mount | pack | scout | guard | hunter | companion`)
- `training_level` (enum: `untrained | basic | trained | expert`)
- `bond_level` (enum: `wary | accepting | bonded | devoted`)
- `natural_abilities` (enum list — intrinsic traits)
- `learned_commands` (controlled enum list — vocabulary TBD)
- `command_notes` (free text — stress-behavior and edge cases)
- `movement_modes` (enum list: walk, fly, swim, climb, burrow)
- `natural_weapons` (enum list: bite, claw, hoof, tail-slam, breath, none)
- `carrying_capacity` (small | medium | large | none)
- `domains` (simplified: `physical`, `instinct`, `composure` on 25–60 scale)
- `hp`, `temperament`
- `bond_links`

**ExceptionalCompanion** — sub-sapient or magically significant entities
(pseudodragon familiar, bound sprite, partially-awakened wolf). Extends
creature base with sapience and supernatural capacity.

Fields (creature base):
- all CreatureCompanion fields above

Fields (exceptional extensions):
- `exceptional_profile`:
  - `sapience`: `partial | full`
  - `communication`: `instinctive | symbolic | speech`
  - `autonomy`: `limited | moderate | high`
- `motivations` (required if any sapience)
- `domains` (simplified if `sapience=partial`, full 7-domain if
  `sapience=full`)
- `knowledge`, `application` (required if `sapience=full`)
- `alignment` (required if `sapience=full`)
- `supernatural_traits` (enum list)
- `known_languages` (populated only if `communication=speech`)

### Enum definitions

**bond_level**
- `wary` — minimal trust, may resist or flee
- `accepting` — tolerates handler, follows routine cues
- `bonded` — recognizes handler as primary social anchor
- `devoted` — prioritizes handler even under danger or conflict

**training_level**
- `untrained` — no conditioned responses
- `basic` — sit, stay, come, reliable in calm conditions
- `trained` — tactical commands, reliable under moderate pressure
- `expert` — complex multi-step tasks, reliable under extreme pressure

**autonomy**
- `limited` — acts only on direct command or reflex
- `moderate` — exercises judgment within handler's stated intent
- `high` — may act independently when circumstances warrant

`autonomy` and `bond_level` are orthogonal. A well-trained war horse is
obedient (low autonomy) and may or may not be bonded. A sphinx
companion is bonded and highly autonomous.

### Reliability model

No dedicated `reliability_under_stress` field. Reliability is adjudicated
narratively from `composure` domain (25–60 scale) + `training_level` +
`bond_level` + situational context. One source of truth per axis.

### Tier transitions

Tiers are immutable in place. A creature that transitions to exceptional
(e.g. awakens through magical exposure) is handled by:

1. Archiving the existing `CreatureCompanion` record
2. Constructing a new `ExceptionalCompanion` record
3. Carrying forward name, bond, and history via explicit field copies
4. Recording the trigger in a `tier_history` field on the new entity

This preserves the narrative weight of transformation (it's a real
event, not a silent field flip) and keeps type guarantees intact
(code reading an `ExceptionalCompanion` knows exceptional-only fields
are populated).

No schema mutation on live records. No in-place promotion.

### Language system deferral

`known_languages` is a placeholder field (`list[str]`, free-form strings)
on SapientCompanion and on ExceptionalCompanion when
`communication=speech`.

A full language system — taxonomy, competency levels, comprehension
rules, literacy, linguistic magic — is deferred to its own design arc.
Known-languages as free strings is sufficient scaffolding until that
arc happens. The placeholder is noted here to prevent it from being
formalized casually inside the companion arc.

### bond_links structure

Replaces the earlier `handler_id` proposal. Companions belong to parties,
not individuals.

```
bond_links:
  primary: <character_id>
  secondary: <character_id>    # optional
```

### Implementation deferral

Not yet built. When the companion arc is prioritized, implementation
touches:

- `api/models.py` — three new Pydantic classes
- `api/routes/options.py` — new `/options` entries for enums
- `data/beasts/creatures.json` — seed catalog (starter set)
- `data/beasts/exceptional.json` — seed catalog (probably empty at
  start)
- Seeding helpers for `CompanionModel` equivalents
- `scripts/validate_naming.py` and `scripts/validate_data_files.py`
  extensions
- `schemas/openapi.yaml` regeneration + prose audit
- `prompts/engine.md` companion handling (watch the 8000-char ceiling)
- `prompts/character-creation.md` updates if companion selection is
  part of creation flow
- GPT builder re-upload of updated knowledge files

Estimated 4–6 Cline packages.

### Decisions explicitly not made in this capture

- Exact catalog of `natural_abilities` enum values
- Exact catalog of `learned_commands` enum values
- Starter creature seed list (species, subtypes)
- API surface for adding/removing companions from a session
  (POST endpoint, state delta shape, etc.)
- Whether sapient companions can also have their own companions
  (nested companion graph; currently noted as "optional" — needs
  explicit resolution)

These are worth addressing when the implementation arc starts, not now.
