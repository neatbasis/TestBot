# Main-head failure clusters (baseline)

Baseline run on commit `b7f9cb1ba23aec0368e59f6962375d93b51eb424` produced **46 failing tests** (`751 passed`).

## Cluster A — Canonical wrapper compatibility/export regression (high blast radius)
**Shared symptom**
- `AttributeError: module 'testbot.sat_chatbot_memory_v2' has no attribute 'CanonicalTurnOrchestrator'`
- Secondary chat-loop/logging failures in `tests/test_runtime_logging_events.py`.

**Representative failures**
- `tests/test_runtime_logging_events.py::test_chat_loop_routes_issue_0013_regression_utterances_through_canonical_pipeline[...]`
- `tests/test_runtime_logging_events.py::test_chat_loop_does_not_use_pre_pipeline_intent_classifier_route_authority`

**Why clustered**
- All fail via legacy-compat accesses to symbols expected from `sat_chatbot_memory_v2`.

## Cluster B — run_canonical_answer_stage_flow seeded-store behavior drift causing self-retrieval + wrong routing/invariants
**Shared symptom**
- Non-memory/time/capability flows collapse into memory-grounded or assist fallbacks.
- Wrong `fallback_action` / `answer_mode` / GK semantics.
- Wrong cited `doc_id`s (ephemeral same-turn artifacts).
- `answer.commit.post` invariant failures (`inv_003_general_knowledge_contract_enforced`, `alignment_decision_consistent`).

**Representative failures**
- `tests/test_alignment_transitions.py` (3 failures)
- `tests/test_answer_contract.py` (4 failures)
- `tests/test_capabilities_help.py` (6 failures)
- `tests/test_capabilities_runtime_status.py` (2 failures)
- `tests/test_runtime_logging_events.py` (majority of 24 failures)
- `tests/test_time_reasoning.py::...time_query_uses_fake_clock_and_helsinki`

**Why clustered**
- Wrapper path (`run_canonical_answer_stage_flow`) uses `_SeededMemoryStore` that ignores exclusion filters and allows same-turn synthetic artifacts into retrieval, which skews downstream decisioning.

## Cluster C — answer.commit confirmed-user-facts continuity regression
**Shared symptom**
- Commit loses prior facts instead of merging continuity facts.

**Representative failure**
- `tests/pipeline/test_stage_contracts.py::test_answer_commit_merges_stabilized_facts_once_per_fact_without_duplicate_commit_effects`

## Cluster D — context continuity anchor drift (commit receipt/continuity semantics)
**Shared symptom**
- Extra continuity anchor (`commit.assistant_offer_anchor:followup_route=...`) appears where deterministic anchor sequence expected.

**Representative failure**
- `tests/test_runtime_logging_events.py::test_resolve_context_consumes_commit_receipt_continuity_deterministically`

## Cluster E — DTO backward-compat default-normalization drift
**Shared symptom**
- Legacy-to-canonical-to-legacy roundtrip differs (`None` vs `{}` for invariant/alignment payloads).

**Representative failure**
- `tests/test_canonical_stage_dtos.py::test_validation_result_has_explicit_constructor_and_legacy_adapter`

## Cluster F — live smoke degraded-mode contract drift
**Shared symptom**
- `tests/test_live_smoke_degraded_modes.py` matrix fails (3 cases) with capability/degraded-mode contract mismatch.

**Why clustered**
- Same degraded-mode behavior contract surface, likely downstream of cluster B (routing/state semantics).
