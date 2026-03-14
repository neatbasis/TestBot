# Decision Policy

This document is the canonical authority for answer-routing, fallback, and rejection policy.

Active program: ISSUE-0013. See `docs/roadmap/` for status and `docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md` for the full record.

## Scope and relationship to other authorities

Use this file for deterministic decisioning behavior:

- objective dimensions and allow/fallback/deny thresholds,
- fallback and clarification routing rules,
- canonical reject taxonomy,
- machine-readable decision fields expected in runtime/debug output.

Related authorities:

- Runtime stage contract: `docs/architecture/canonical-turn-pipeline.md`
- Traceability and enforcement mapping: `docs/directives/traceability-matrix.md`
- Invariant registries: `docs/invariants/answer-policy.md`, `docs/invariants/pipeline.md`
- Terminology policy: `docs/terminology.md`

## Alignment objective dimensions

Each turn decision emits all five dimensions and a final decision. Numeric scores remain in `[0.0, 1.0]` when applicable.

### 1) factual_grounding_reliability

Inputs:

- `raw_claim_like_text_detected` (`0|1`)
- `has_required_memory_citation` (`0|1`)
- `confidence_margin = top_final_score - second_final_score`
- `min_margin_to_second`

Normalization and score:

- Grounded answer classes:
  - `citation_validity = 1.0` if required citation exists, else `0.0`
  - `confidence_margin_normalized = clamp01(confidence_margin / min_margin_to_second)`
  - `factual_grounding_reliability = clamp01(0.65 * citation_validity + 0.35 * confidence_margin_normalized)`
- Contract-exempt uncertainty/fallback classes:
  - `citation_validity = "not_applicable"`
  - `confidence_margin_normalized = "not_applicable"`
  - `factual_grounding_reliability = "not_applicable"`

### 2) safety_compliance_strictness

- `1.0` when request is safe, or unsafe request is denied.
- `0.0` when unsafe request is not denied.

### 3) response_utility

Inputs:

- fallback mode class from `final_answer`
- `context_confident` as intent-fulfillment proxy

Normalization and score:

- `fallback_mode_score`: deny=`0.0`, fallback=`0.25`, clarify/assist=`0.7`, grounded answer=`1.0`
- `intent_fulfillment_proxy`: grounded confident answer=`1.0`, contract-exempt clarify/assist=`0.75`, otherwise=`0.45`
- `response_utility = clamp01(0.5 * fallback_mode_score + 0.5 * intent_fulfillment_proxy)`

### 4) cost_latency_budget

Inputs:

- `turn_latency_ms`, `latency_budget_ms` (default `3500`)
- `token_budget_ratio` (optional)

Normalization and score:

- `latency_score = 1.0` when latency signal missing, else `clamp01(1 - turn_latency_ms / latency_budget_ms)`
- `token_budget_score = 1.0` when token signal missing, else `clamp01(1 - token_budget_ratio)`
- `cost_latency_budget = min(latency_score, token_budget_score)`

### 5) provenance_transparency

For non-trivial answers, check completeness of:

- non-empty `claims`
- non-empty `provenance_types`
- non-empty `basis_statement`

Score:

- trivial outputs (`deny`, fallback, clarify/assist): `1.0`
- non-trivial outputs: `passed_checks / 3`

## Final alignment decision

- **deny** when `safety_compliance_strictness < 1.0`
- **fallback** when any of:
  - `factual_grounding_reliability < 0.6` (only when numeric/applicable)
  - `response_utility < 0.5`
  - `provenance_transparency < 0.75`
  - `cost_latency_budget < 0.35`
- **allow** otherwise

## Deterministic fallback and clarification routing

This table is deterministic and keyed by runtime fields `intent`, `memory_hit`, `ambiguity`, and `capability_status` (plus optional source-confidence gating for non-memory routes).

| intent | memory_hit | ambiguity | capability_status | action |
|---|---:|---:|---|---|
| memory_recall | true | true | ask_available | ROUTE_TO_ASK |
| memory_recall | true | true | ask_unavailable | ASK_CLARIFYING_QUESTION |
| memory_recall | true | false | ask_available | ANSWER_GENERAL_KNOWLEDGE |
| memory_recall | true | false | ask_unavailable | ANSWER_GENERAL_KNOWLEDGE |
| memory_recall | false | true | ask_available | ROUTE_TO_ASK |
| memory_recall | false | true | ask_unavailable | ASK_CLARIFYING_QUESTION |
| memory_recall | false | false | ask_available | OFFER_CAPABILITY_ALTERNATIVES |
| memory_recall | false | false | ask_unavailable | OFFER_CAPABILITY_ALTERNATIVES |
| non_memory | * | * | ask_available | ANSWER_GENERAL_KNOWLEDGE (or ANSWER_UNKNOWN when source-confidence gate fails) |
| non_memory | * | * | ask_unavailable | ANSWER_GENERAL_KNOWLEDGE (or ANSWER_UNKNOWN when source-confidence gate fails) |
| time_query | * | * | ask_available | ANSWER_TIME |
| time_query | * | * | ask_unavailable | ANSWER_TIME |

Notes:

- `intent` values come from deterministic intent routing.
- `memory_hit` maps to answer-stage confidence (`context_confident`).
- `ambiguity` maps to near-tie ambiguity from reranking.
- `capability_status` reflects Ask follow-up capability for the active channel.
- For `non_memory`, low source confidence forces `ANSWER_UNKNOWN` (explicit uncertainty output).

## Canonical reject taxonomy

Decision-stage reject outcomes use stable machine fields in `debug.policy`:

- `reject_code`
- `partition` (`intent`, `retrieval`, `rerank`, `contract`, `policy`, `temporal`, `none`)
- numeric context (`score`, `threshold`, `margin`)
- human-readable `reason`
- compatibility mirror `blocker_reason`

| reject_code | partition | Meaning | Example trigger |
| --- | --- | --- | --- |
| `CONTEXT_CONF_BELOW_THRESHOLD` | `rerank` | Context confidence gate did not clear threshold. | Top candidate score/margin does not support direct answer. |
| `TEMPORAL_REFERENCE_UNRESOLVED` | `temporal` | Temporal request could not be resolved reliably. | Time query falls back to clarify/unknown due to unresolved reference. |
| `NO_CITABLE_MEMORY_EVIDENCE` | `retrieval` | No reliable memory evidence for citation-backed answer. | Zero relevant memory hits or unknown fallback for missing evidence. |
| `AMBIGUOUS_MEMORY_CANDIDATES` | `rerank` | Retrieved memories conflict or remain ambiguous. | Clarify flow with ambiguity detected. |
| `ANSWER_CONTRACT_GROUNDING_FAIL` | `contract` | Memory-grounded answer contract failed grounding/citation checks. | Draft answer rejected by answer contract gate. |
| `GK_CONTRACT_MARKER_FAIL` | `contract` | General-knowledge contract marker/confidence support failed. | Missing marker or insufficient support for GK fallback answer. |
| `POLICY_SAFETY_DENY` | `policy` | Policy/safety denial path. | Deny mode selected by policy checks. |
| `NONE` | `none` | No reject condition active. | Memory-grounded or compliant direct answer path. |

## Runtime/debug field contract

`PipelineState.alignment_decision` must contain:

- `objective_version`
- `dimensions` object with the five required keys
- `dimension_inputs.raw`
- `dimension_inputs.normalized`
- `final_alignment_decision` in `{allow, fallback, deny}`

Session logs must include `alignment_decision_evaluated` with raw and normalized dimension data for auditability.

New machine integrations should use `reject_code` + `partition` + numeric fields rather than parsing free text.

## Reflection promotion normalization policy

When evaluating reflection cards for promotion into durable context:

- Parse structured payload and normalize each claim into `{text, category, reliability, source}`.
- Route promotion using normalized `category` values (for example `clarified_intent`, `accepted_context`), not substring heuristics.
- Keep stable rejection reasons for observability/tests: `confidence_below_threshold`, `has_uncertainties`, `claim_uncertain_or_conflicting`, `contains_internal_debug`.
- If parsing fails or fields are malformed, default to deterministic rejection via low-confidence behavior.
