# Terminology Policy

## Purpose

This page defines how to write about TestBot internals using both:

- **canonical internal terms** (the contract names used by code, pipeline docs, and tests), and
- **preferred standard AI terms** (community-facing wording for broader readability).

Use this policy whenever you update `README.md`, `docs/architecture.md`, directives, issues, or stakeholder-facing design notes.

## Canonical internal terms

Canonical terms are the normative identifiers used by runtime and architecture artifacts. Keep these names exact when discussing implementation contracts.

| Canonical internal term | Meaning in TestBot |
| --- | --- |
| `observe.turn` | Capture turn input and metadata before interpretation. |
| `encode.candidates` | Generate candidate interpretations/facts/repair signals. |
| `stabilize.pre_route` | Persist stable pre-routing artifacts for deterministic processing. |
| `context.resolve` | Resolve pending repair/obligation/focus context from prior state. |
| `intent.resolve` | Determine semantic intent class from stabilized state. |
| `retrieve.evidence` | Retrieve memory/source evidence aligned to intent. |
| `policy.decide` | Select response policy class (answer, clarify, repair, fallback). |
| `answer.assemble` | Build answer candidate from chosen policy and evidence. |
| `answer.validate` | Enforce grounding/citation and policy-alignment checks. |
| `answer.render` | Produce user-facing phrasing without semantic drift. |
| `answer.commit` | Persist continuity artifacts for the next turn. |
| `commit_receipt` | Durable continuity receipt emitted by commit stage. |

## Preferred standard AI terms

Use these where audience familiarity benefits from standard wording.

| Standard AI term | Typical TestBot mapping |
| --- | --- |
| retrieval-augmented generation (RAG) | `retrieve.evidence` + evidence-backed answer assembly |
| context management | `context.resolve` |
| policy routing | `policy.decide` |
| response validation / guardrails | `answer.validate` |
| memory consolidation | `answer.commit` |
| provenance / attribution | `used_memory_refs`, `used_source_evidence_refs`, `source_evidence_attribution` |

## Canonical glossary terms

Use these repository-wide terms exactly as written in directives, code comments, tests, and contributor docs.

| Canonical term | Definition | Preferred term | Avoid aliases |
| --- | --- | --- | --- |
| contract | A required behavior or output shape that must be satisfied for the system to be considered correct. | contract | requirement, promise, rule set |
| invariant | A condition that must remain true across states, steps, or executions. | invariant | always-true assumption, constant rule |
| guardrail | A deterministic check or constraint that blocks unsafe or non-compliant behavior. | guardrail | safety check, protective rule |
| fallback | The deterministic backup behavior used when the contract cannot be satisfied with confidence. | fallback | backup answer, default response |
| confidence | A measurable signal that indicates whether retrieved context is strong enough to answer. | confidence | certainty score, trust level |
| citation | A structured reference to source memory evidence (for example `doc_id` and `ts`). | citation | source note, reference snippet |
| provenance | Structured attribution metadata describing where answer content came from. | provenance | source flavor, origin tags |
| basis statement | Brief natural-language justification of evidence classes used to produce an answer. | basis statement | rationale blurb, source note |
| memory reference | Stable pointer to memory evidence used for an answer (for example `<doc_id>@<ts>`). | memory reference | memory id, memory pointer |
| memory-grounded | Constrained to evidence from provided memory context and recent chat, without unsupported claims. | memory-grounded | grounded, memory-based |
| deterministic | Producing the same result for the same inputs and conditions. | deterministic | reproducible-by-chance, stable-ish |

## Provenance enum values

When recording `provenance_types`, use these exact uppercase values:

- `MEMORY`
- `CHAT_HISTORY`
- `SYSTEM_STATE`
- `GENERAL_KNOWLEDGE`
- `INFERENCE`
- `UNKNOWN`

## When to use canonical terms, standard terms, or both

- Use **canonical-only** wording for implementation specs, invariants, tests, traceability, and bug diagnosis.
- Use **standard-only** wording in high-level introductions aimed at non-maintainers, but only when no contract precision is required.
- Use **both together** for bridge docs (README, architecture overviews, stakeholder updates): canonical name first, standard term second.

Recommended pattern:

> `<canonical identifier>` (standard AI term)

Example:

> `context.resolve` (context management)

## Do not rename real system identifiers

When a term is a real identifier used in code, logs, tests, or policy artifacts, **do not rename it** in documentation.

- Keep `context.resolve` exactly as written (not "context resolution stage" as a replacement name).
- Keep `answer.commit` exactly as written (not "commit stage" as a replacement name).
- Keep `commit_receipt` exactly as written (not "memory receipt" as a replacement name).

You may add a parenthetical explanation, but the identifier itself must remain unchanged.

## Acceptable phrasing examples

- "`context.resolve` (context management) restores pending obligations and repair anchors before intent resolution."
- "`answer.commit` (memory consolidation) persists continuity state and emits a `commit_receipt`."
- "TestBot uses retrieval-augmented generation (RAG) through `retrieve.evidence` plus provenance-bound answer assembly."

## Non-acceptable phrasing examples

- "Context resolution runs after stabilize" (missing canonical `context.resolve` identifier).
- "Commit stage writes the final memory receipt" (renames both `answer.commit` and `commit_receipt`).
- "The renderer decides fallback policy" (semantic drift: policy selection belongs to `policy.decide`).

## Contributor word-choice rules

- Prefer the **canonical term** from the glossary table when a concept has a defined repository meaning.
- Keep **real identifiers exact** (for example `context.resolve`, `answer.commit`, `commit_receipt`) and add explanatory wording only as a parenthetical.
- Use **standard AI wording** only as a bridge for broader audiences, and pair it with the canonical term when precision matters.
- Do not substitute aliases listed in **Avoid aliases** in normative docs, tests, directives, issue records, or release notes.
