# Mystic Weave — Bug Report

Mid-session bug-report prompt. Paste this verbatim into the narrator GPT to
step it out of narrator role and produce a technical incident report. The
output is for engineering, not design or play retrospective.

Use when something failed: an API call 500'd, a response was wrong-shaped,
state drifted from expectation, an endpoint the GPT thought existed didn't,
or the GPT noticed itself fabricating around a missing capability.

---

Bug report. Step out of narrator role. No fiction, no in-character framing, no apologies, no performative humility. The audience is the engineer reading Railway logs alongside this. Clinical and specific.

Cover these sections in order. Brevity over completeness — only include what you actually observed. If a section doesn't apply, say "n/a" and move on.

1. INCIDENT SUMMARY
   - One paragraph: what were you trying to do, what broke.
   - Session id (fetch from /state if you don't have it cached).
   - Approximate timestamp(s) of failure(s) in UTC, for log correlation.

2. API CALL TRACE
   For each call relevant to the failure, in order:
   - Endpoint, HTTP method, OpenAPI operationId.
   - Request payload — verbatim, full, not summarized.
   - Response status code and body — verbatim, full, not summarized.
   - Whether the failure came from the OpenAI Actions layer (operation rejected before reaching the API) or from the API itself (response body returned). The error shapes differ; this distinction matters.
   - If the call succeeded but returned something you didn't expect, say so and quote the response.

   Do not paraphrase error messages. Quote response bodies exactly. If you no longer have the response in context, say so explicitly — "reconstructed from memory" is worse than "I don't have that anymore."

3. YOUR RESPONSE TO THE FAILURE
   - Did you retry? How many times, with what changes to the payload between attempts?
   - Did you fabricate state forward — claim something happened that the backend did not confirm? If yes, exactly where, and what state the player now believes is canon that isn't actually persisted.
   - Did you stop and report the failure to the player?
   - Did you continue narrating around the failure (treating it as not having happened)? If yes, where.

   State this plainly. The point is to know what the player saw versus what state actually contains. Confessing fabrication is what the engineer needs; do not soften it.

4. EXPECTED VS ACTUAL
   - What did you expect the failing call to do?
   - On what basis — your knowledge files, OpenAPI spec, prior session behavior, narrator-facing rules document? Name the source.
   - If your expectation came from a knowledge file, cite the file and the relevant section. If it came from the OpenAPI spec, cite the operationId and the schema field.
   - If actual response shape did not match the schema you were operating from, that is a contract drift signal — flag it.

5. HYPOTHESIS
   - Your best guess at cause. Mark it explicitly as hypothesis, not finding.
   - Category: backend bug, contract drift between API and knowledge files, missing endpoint you assumed existed, malformed payload from your side, stale knowledge file, OpenAI Actions issue, or something else.
   - If you can't form a hypothesis, say so. Don't manufacture one.

6. WHAT WOULD HAVE HELPED
   - Clearer error message? Different endpoint shape? Missing endpoint that should exist? Knowledge file update? Be specific.
   - Ergonomics issues that aren't bugs but made the failure hard to handle gracefully belong here.

After the six sections, give a short BOTTOM LINE:
- One sentence: most likely category of cause.
- One sentence: what the engineer most needs from logs or DB to confirm.

Tone: clinical, specific, evidence-based. No retroactive justification of decisions made under uncertainty. No padding. If you genuinely don't have data for a section, say so — guessing is worse than absence.