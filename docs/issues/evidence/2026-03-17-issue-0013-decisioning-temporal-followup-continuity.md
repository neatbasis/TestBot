# 2026-03-17 ISSUE-0013 decisioning evidence: temporal follow-up continuity hardening

- **Issue linkage:** ISSUE-0013
- **Capability slice:** canonical_turn_pipeline_decisioning
- **Acceptance criteria focus:** AC-0013-10 (deterministic behavior continuity for memory/temporal follow-ups)

## Stakeholder-visible gap addressed

Temporal follow-up utterances such as `when was that again?` were being classified as
`knowledge_question` and remained unresolved, which allowed direct-answer routing drift instead
of preserving memory-continuity-aware time query handling.

## Deterministic evidence

### Focused BDD

Command:

```bash
python -m behave features/testbot/intent_grounding.feature -n "temporal follow-up after memory recall preserves time-query continuity"
```

Result: **pass**.

### Focused pytest (decisioning/runtime wrappers/routing)

Command:

```bash
python -m pytest tests/test_decisioning_stages.py tests/test_runtime_modes.py tests/test_retrieval_routing.py -k "temporal_followup or time_query_queries_require_retrieval or resolve_turn_intent_temporal_followup_after_memory_recall or resolve_turn_intent_affirmation_preserves_clarification_intent or resolve_turn_intent_non_affirmation_does_not_preserve_prior_intent"
```

Result: **pass** (5 selected tests).

## Behavioral closure statement

Decisioning now promotes temporal follow-ups to `time_query` when committed memory continuity
anchors are present, and retrieval routing treats `time_query` as retrieval-required to avoid
knowledge-question/direct-answer fallback drift.
