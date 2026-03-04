# Canonical Terms

This glossary defines canonical language for directives, code comments, and contributor documentation.

| Canonical term | Definition | Preferred term | Avoid aliases |
|---|---|---|---|
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

## Usage rule

When writing or updating docs in this repository, use the **preferred term** exactly and avoid the listed aliases.

## Provenance enum values

Use these exact uppercase values when recording `provenance_types`:

- `MEMORY`
- `CHAT_HISTORY`
- `SYSTEM_STATE`
- `GENERAL_KNOWLEDGE`
- `INFERENCE`
- `UNKNOWN`
