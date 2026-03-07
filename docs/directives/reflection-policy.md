# Reflection Fallback Policy

This policy is deterministic and keyed by four runtime fields: `intent`, `memory_hit`, `ambiguity`, and `capability_status` (plus optional non-memory source-confidence gating).

## Policy table

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

## Notes

- `intent=memory_recall`, `intent=non_memory`, and `intent=time_query` are produced by the deterministic intent router.
- `memory_hit` maps to answer-stage confidence (`context_confident`).
- `ambiguity` maps to near-tie ambiguity from reranking.
- `capability_status` reports whether Ask follow-up capability is available in the active channel.
- For `non_memory`, low source-confidence can force `ANSWER_UNKNOWN`, which is rendered as explicit uncertainty language rather than direct memory fallback phrasing.


## Reflection promotion normalization

When reflection cards are evaluated for promotion into durable context, the evaluator must parse a structured payload and normalize every claim into `{text, category, reliability, source}`.

- Promotion routing MUST use normalized `category` values (for example `clarified_intent`, `accepted_context`) rather than hard-coded substring checks.
- Rejection reasons remain stable for observability and tests (`confidence_below_threshold`, `has_uncertainties`, `claim_uncertain_or_conflicting`, `contains_internal_debug`).
- If parsing fails or fields are malformed, evaluation defaults to deterministic rejection via low-confidence behavior instead of attempting permissive guessing.
