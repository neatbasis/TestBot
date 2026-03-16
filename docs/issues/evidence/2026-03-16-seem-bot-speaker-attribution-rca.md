# seem-bot speaker attribution root cause analysis (2026-03-16)

## Incident summary
A CLI session showed `seem-bot` incorrectly claiming ownership of a prior user statement ("I was making a joke earlier when I said the rope might be tired").

## Reproduction chain mapped to current pipeline
1. User message is stabilized as a passage with role only encoded inside `canonical_text` (e.g. `human: ...`).
2. Supporting context for generation is passed as raw strings (`supporting_passages`) with no structured speaker field.
3. `render_reply` prompts the model with those strings and no hard instruction to preserve strict speaker attribution.
4. The model hallucinates an assistant-authored antecedent because there is no first-class provenance guardrail in generation inputs.
5. Follow-up turns (`No`/`Yes`) are interpreted by user-act/focus mechanics as confirmations/rejections of the assistant's latest clarification question, further drifting the conversation away from user intent.

## Root causes
### RC1 — Speaker identity is not first-class in memory payloads
`PassageRecord` stores `kind` plus `canonical_text`, but not an explicit speaker/author field. Role attribution therefore depends on parsing prefixed prose rather than schema-level provenance.

### RC2 — Retrieval/rerender context drops structured provenance
`select_supporting_passages` returns a list of strings and strips the latest observation role prefix before rendering. This creates a "content without explicit author" prompt channel where attribution can be reconstructed incorrectly.

### RC3 — Prompt contract lacks attribution invariants
`render_reply` system/human prompts require directness and hiding internals, but do not enforce "never invert speaker ownership" or "when recalling conversation, cite user statements as user statements." This leaves attribution to model priors.

### RC4 — Short-utterance act heuristics over-index on local focus
`No`/`Yes` are deterministically mapped to rejection/confirmation and resolved against active assistant focus if present. After a clarification question is asked, terse user replies are bound to that focus even when the user may be objecting to prior misattribution.

## Why this is structurally reproducible
The current architecture forms a partial relational view of dialogue state: text survives, but authorship/provenance is weakly encoded. Under ambiguity, generation fills missing links with plausible narrative continuity. In practice that means false speaker arrows are likely whenever recall is requested or conversational repair is needed.

## Corrective actions (data layer first)
1. Add first-class `speaker` (and optional `turn_id`) to `PassageRecord`; keep `canonical_text` as a render artifact, not source-of-truth attribution.
2. Change render context to pass structured supporting passages (`[{speaker, kind, text, passage_id}]`) instead of plain strings.
3. Add prompt invariants: explicit prohibition on attributing user text to assistant and requirement to acknowledge uncertainty when provenance is missing.
4. Add a reply validator rule to flag first-person assistant claims about content only present in user-authored passages.
5. Refine user-act resolution so bare confirmations/rejections are gated by confidence + nearby quoted target (or ask disambiguation) when prior turn involved attribution dispute.

## Suggested verification additions
- BDD scenario: user asks "What did I tell you?" then challenges misattribution; bot must preserve user ownership and avoid self-attribution.
- Unit tests for render-context payload ensuring speaker field survives end-to-end.
- Unit tests for validator catching assistant self-attribution of user-only content.
