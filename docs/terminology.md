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
