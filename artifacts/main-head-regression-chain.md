# Main-head regression chain (root cause vs downstream)

## Chain 1 (dominant): wrapper seeded-store contamination
1. `run_canonical_answer_stage_flow` creates `_SeededMemoryStore` and runs full canonical pipeline.
2. `_SeededMemoryStore.similarity_search_with_score` ignores exclusion arguments (`exclude_doc_ids`, `exclude_turn_scoped_ids`, etc.) and appends same-turn docs via `add_documents`.
3. `retrieve.evidence` therefore returns turn-local synthetic artifacts as if they were memory hits.
4. `policy.decide` sees scored non-empty evidence and selects memory-grounded branch (`ANSWER_FROM_MEMORY`) in scenarios that should be unknown/capability/time/GK-safe.
5. `answer.assemble`/`answer.validate` inherit wrong routing and produce wrong fallback semantics, wrong provenance/doc_ids, and wrong GK contract outcomes.
6. `answer.commit.post` invariants then fail in multiple tests (`inv_003_general_knowledge_contract_enforced`, `alignment_decision_consistent`).

**Root cause:** stage-input contamination at retrieval boundary in compatibility wrapper path.
**Downstream symptoms:** wrong fallback action/mode, GK contract drift, time-query degradation, provenance/doc_id drift, many runtime logging failures.

## Chain 2: commit merge behavior change
1. `answer.commit` calls `_merge_confirmed_user_facts`.
2. Function currently only de-dupes `assembly.confirmed_user_facts`; prior committed facts are discarded.
3. Commit receipt continuity contract regresses.

**Root cause:** commit-stage merge function semantics.
**Downstream symptoms:** continuity regressions; related context/retrieval tests brittle/failing.

## Chain 3: legacy compatibility surface removal
1. Consumers/tests expect `CanonicalTurnOrchestrator` via `testbot.sat_chatbot_memory_v2` compatibility module.
2. Symbol is absent in module exports.
3. Logging/chat-loop compatibility tests crash with `AttributeError`.

**Root cause:** compatibility export regression.
**Downstream symptoms:** multiple runtime logging event tests fail early.

## Chain 4: continuity anchor schema drift
1. `context.resolve._commit_continuity_anchors` now emits `commit.assistant_offer_anchor:*` anchors.
2. Deterministic ordering/content no longer matches tests/contracts expecting prior anchor set.

**Root cause:** changed continuity anchor schema without synchronized contract updates.
**Downstream symptoms:** commit-receipt continuity assertion failures.

## Chain 5: DTO nullability drift
1. Canonical DTO conversion normalizes absent `invariant_decisions`/`alignment_decision` to `{}`.
2. Legacy contract expects `None` roundtrip identity in specific adapter test.

**Root cause:** adapter default normalization mismatch.
**Downstream symptom:** canonical DTO compatibility test failure.
