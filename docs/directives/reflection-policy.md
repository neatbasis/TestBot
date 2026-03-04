# Reflection Fallback Policy

This policy is deterministic and keyed by four runtime fields: `intent`, `memory_hit`, `ambiguity`, and `capability_status`.

## Policy table

| intent | memory_hit | ambiguity | capability_status | action |
|---|---:|---:|---|---|
| memory_recall | true | true | ask_available | ROUTE_TO_ASK |
| memory_recall | true | true | ask_unavailable | ASK_CLARIFYING_QUESTION |
| memory_recall | true | false | ask_available | ANSWER_GENERAL_KNOWLEDGE |
| memory_recall | true | false | ask_unavailable | ANSWER_GENERAL_KNOWLEDGE |
| memory_recall | false | true | ask_available | ROUTE_TO_ASK |
| memory_recall | false | true | ask_unavailable | ASK_CLARIFYING_QUESTION |
| memory_recall | false | false | ask_available | EXACT_MEMORY_FALLBACK |
| memory_recall | false | false | ask_unavailable | EXACT_MEMORY_FALLBACK |
| non_memory | true | true | ask_available | ANSWER_GENERAL_KNOWLEDGE |
| non_memory | true | true | ask_unavailable | ANSWER_GENERAL_KNOWLEDGE |
| non_memory | true | false | ask_available | ANSWER_GENERAL_KNOWLEDGE |
| non_memory | true | false | ask_unavailable | ANSWER_GENERAL_KNOWLEDGE |
| non_memory | false | true | ask_available | ANSWER_GENERAL_KNOWLEDGE |
| non_memory | false | true | ask_unavailable | ANSWER_GENERAL_KNOWLEDGE |
| non_memory | false | false | ask_available | ANSWER_GENERAL_KNOWLEDGE |
| non_memory | false | false | ask_unavailable | ANSWER_GENERAL_KNOWLEDGE |

## Notes

- `intent=memory_recall` is produced by the deterministic intent router.
- `memory_hit` maps to answer-stage confidence (`context_confident`).
- `ambiguity` maps to near-tie ambiguity from reranking.
- `capability_status` reports whether Ask follow-up capability is available in the active channel.
