# Main-head first authoritative failure boundaries

| Cluster | First authoritative stage/function where behavior becomes wrong | Evidence | Notes |
|---|---|---|---|
| A. Missing compatibility export | `answer.commit`-adjacent runtime compatibility surface in `sat_chatbot_memory_v2` module export layer | `AttributeError` for `CanonicalTurnOrchestrator` in runtime logging tests | Break occurs before business-stage evaluation; compatibility API boundary is missing. |
| B. Seeded store self-retrieval + policy drift | `retrieve.evidence` (wrapper path through `_SeededMemoryStore.similarity_search_with_score`) | Time-query probe showed `intent=time_query` but retrieval returns same-turn docs and downstream sets `fallback_action=ANSWER_FROM_MEMORY` | First wrongness is retrieval contamination; policy/assembly/validate/commit effects are downstream. |
| C. Fact merge regression | `answer.commit` (`_merge_confirmed_user_facts`) | `confirmed_user_facts` loses prior fact `timezone=UTC` in stage-contract test | Commit stage merges only assembly facts and discards prior continuity facts. |
| D. Continuity anchor drift | `context.resolve` (`_commit_continuity_anchors`) | deterministic anchor test receives extra `commit.assistant_offer_anchor:...` anchor | Behavior changed at context boundary; later retrieval continuity assertions downstream fail. |
| E. DTO adapter drift | `answer.validate`-adjacent DTO adapter (`ValidationResult.to_validated_answer`) | roundtrip mismatch on `None` vs empty dict fields | Compatibility contract drift in canonical DTO translation layer. |
| F. Live smoke degraded-mode drift | `policy.decide` (downstream of contaminated retrieval/evidence + fallback mapping) | degraded-mode matrix mismatch in capability status output | Likely secondary from B, but authoritative wrong branch is policy decision result. |

## Stage coverage against requested canonical sequence
- `context.resolve`: Cluster D.
- `intent.resolve`: No primary break isolated as first failure in this baseline.
- `retrieve.evidence`: Cluster B.
- `policy.decide`: Cluster F (and downstream in B).
- `answer.assemble`: downstream-only in B.
- `answer.validate`: Cluster E (adapter boundary).
- `answer.commit`: Clusters A/C and post-invariant manifestations in B.
