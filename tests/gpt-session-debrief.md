# Mystic Weave — Session Debrief

End-of-session postmortem prompt. Paste this verbatim into the narrator GPT
to step it out of narrator role and produce an analytical session report.
The output is technical and design-facing, not in-fiction.

---

Session debrief. Step out of narrator role and report analytically. No performative humility, no in-character framing, no apologies. State facts. The goal is to find what actually happened so the system and the play around it can improve.

Audience is engineering and design. Treat this as a technical and design postmortem.

Cover these six sections in order. Each section has required questions plus room for whatever else materially mattered. If a section had nothing notable this session, say so in one line and move on — do not pad.

1. ARC SYSTEM DISCIPLINE
   - Were arcs created at the right time, with the right scope, formality, and closure shape declared up front?
   - Did spawn / replace / merge get used correctly, or did any arc get extended past natural closure?
   - Were /progress, /transition, and /settle calls made when warranted, or skipped?
   - Where did arc structure work well? Where did it fail?

2. PROGRESSION ADJUDICATION
   - For each scene that resolved with progression, did you do a proper candidate scan (broad set → parent-cap check → strongest fit → player choice only when genuinely competitive)?
   - Where did the obvious-tag-first failure mode show up?
   - Did parent-cap, AP rollover, or counter behavior cause friction? Was that backend-correct but ergonomically rough, or actually wrong?
   - Was advancement narrated transparently to the player, or compressed and then backfilled under challenge?

3. STATE MUTATION & BACKEND BEHAVIOR
   - Did any save fail, partially fail, or behave unexpectedly?
   - Did you hit the reputation overwrite problem, log bloat, response-size issues, or any other state-mutation hazard?
   - Were there cases where the latest authoritative state mismatched what the player was reading?
   - What backend ergonomics would have helped (clearer error messages, structured suggestions, safer merge semantics, etc.)?

4. CANON & FICTION DISCIPLINE
   - Did you invent structure that contradicted established canon? If so, where, and why didn't the contradiction surface earlier?
   - Did narration outrun evidence at any point — claims made that the rolls or state did not actually support?
   - Where did gap-fill go right? Where did it slip into invention?
   - Were calendar, location, weather, and other deterministic fields handled cleanly?

5. PLAY DYNAMICS — BOTH SIDES
   - Where did your narration drift, stall, or collapse player tactics? Be specific about turning points.
   - Where did the player make the work harder — ambiguous direction, overridden useful constraints, pushed past natural closure, etc.? State these as facts. The point is understanding interaction patterns, not blame.
   - On rolls that failed or partially succeeded, did the world actually move (consequences advanced, new obstacles emerged, NPC reactions shifted), or did you soft-deny and ask "what do you do next?" Failure should advance the world, not stall it.
   - Were end-of-scene choices presented to the player meaningful, distinct, and grounded in actual location graph / character state / active arcs / current threat? Or were they generic, repetitive, or unmoored from current state?
   - Was companion role-separation honored when the player gave multi-vector commands?
   - Were closure moments missed by you, the player, or both? Name them.

6. STATE INTEGRITY (retrospective)
   For each of the following, does what you narrated this session match what /state/{session_id} actually shows now? Call /state if needed to verify.
   - Inventory (worn, carried, stashed)
   - Location and time
   - HP and status effects
   - Reputation values across factions touched this session
   - Companion presence and status
   - Active arcs and their states
   - Currency / coin

   For each mismatch: what the narration claimed happened, what /state actually shows, and (best guess) which turn introduced the divergence. If no mismatches, say so in one line.

After the six sections, give a short BOTTOM LINE:
- Three concrete things that, if changed in the system or in player-narrator interaction, would have most improved this session.
- One narration or flavor area where you want to improve specifically (this can be a craft note — pacing, sensory texture, NPC voice differentiation, whatever you noticed yourself doing flat work on).

Tone: clinical, specific, evidence-based. Cite scenes, locations, or session beats by name when relevant. If something can't be confirmed without checking state, say so rather than guessing. If you genuinely think a section went well, say that briefly — do not invent failures to seem properly self-critical.