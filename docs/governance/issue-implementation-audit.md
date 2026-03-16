# Issue Implementation Audit

Date: 2026-03-09  
Scope: Active issue files in `docs/issues/` with status `open` or `in_progress` (`ISSUE-0008` through `ISSUE-0015`).

Verdict taxonomy:
- `implemented_tested`: criterion has concrete implementation path(s) in `src/testbot/` plus behavior spec and deterministic test coverage.
- `partial`: some coverage exists, but at least one required axis (implementation/spec/test or closure evidence) is incomplete.
- `missing`: no concrete implementation/spec/test evidence found.
- `governance_only`: criterion is documentation/governance-only and not expected to map to runtime modules.

## Summary of mismatches

| Issue | Status | Criteria audited | implemented_tested | partial | missing | governance_only | Mismatch summary |
|---|---|---:|---:|---:|---:|---:|---|
| ISSUE-0008 | in_progress | 4 | 3 | 1 | 0 | 0 | Capability remains declared `partial`; AC-4 not complete. |
| ISSUE-0009 | open | 4 | 2 | 2 | 0 | 0 | Gate + feature-status closure criteria still open. |
| ISSUE-0010 | open | 4 | 1 | 3 | 0 | 0 | Explicit uncertainty/fallback coverage incomplete and status still `partial`. |
| ISSUE-0011 | open | 5 | 4 | 1 | 0 | 0 | Deterministic threshold warning behavior needs clearer verification linkage. |
| ISSUE-0012 | open | 4 | 1 | 3 | 0 | 3 | Delivery-plan/governance criteria are documented but not yet closure-complete. |
| ISSUE-0013 | open | 12 | 0 | 12 | 0 | 0 | Every AC is tracked as `[~]` (in progress), none closure-complete. |
| ISSUE-0014 | open | 8 | 1 | 7 | 0 | 0 | Structural fixes exist; behavioral proof criteria remain open. |
| ISSUE-0015 | open | 8 | 8 | 0 | 0 | 0 | Governance hardening updates are present in ISSUE-0014 + RED_TAG linkage. |

## Closed/done inconsistency flags

No issue file in this repository currently uses a `done` status label. For `closed`/`resolved` issues (`ISSUE-0001` to `ISSUE-0007`), this audit did not find an active criterion mapped to a non-implemented verdict from the reviewed evidence paths; **no closed/done mismatch flag is raised in this pass**.

---

## ISSUE-0008 (`in_progress`)

Acceptance criteria extracted from `docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md`.

| Criterion | `src/testbot/` implementation mapping | `features/` mapping | `tests/` mapping | Verdict | Evidence note |
|---|---|---|---|---|---|
| 1. Behave intent grounding passes deterministically | `intent_router.py` (`classify_intent`, `extract_intent_facets`), `sat_chatbot_memory_v2.py` (`resolve_turn_intent`) | `features/testbot/intent_grounding.feature` | `tests/test_intent_router.py` | implemented_tested | Issue AC command aligns with existing feature + deterministic router tests. |
| 2. Pytest router + promotion policy coverage | `intent_router.py`, `promotion_policy.py` (`evaluate_promotion_policy`) | `features/testbot/intent_grounding.feature` | `tests/test_intent_router.py`, `tests/test_promotion_policy.py` | implemented_tested | Criterion names exact deterministic test files with concrete policy/router modules. |
| 3. All-green gate reports behave + pytest pass | Gate consumes whole runtime including routing path | `features/testbot/intent_grounding.feature` (indirect) | `tests/test_intent_router.py`, `tests/test_promotion_policy.py` (indirect) | implemented_tested | Command is explicit and deterministic; maps to active suite artifacts. |
| 4. `feature-status.yaml` moved to implemented only after 1-3 | Runtime capability emitted via `sat_chatbot_memory_v2.py` (`build_capability_snapshot`) | N/A | `tests/test_report_feature_status.py` | partial | `docs/qa/feature-status-report.md` still reports intent grounding as partial/open. |

## ISSUE-0009 (`open`)

| Criterion | `src/testbot/` implementation mapping | `features/` mapping | `tests/` mapping | Verdict | Evidence note |
|---|---|---|---|---|---|
| 1. Behave answer-contract + memory-recall pass | `answer_validation.py`, `answer_rendering.py`, `sat_chatbot_memory_v2.py` (`validate_answer_contract`, `build_provenance_metadata`) | `features/testbot/answer_contract.feature`, `features/testbot/memory_recall.feature` | `tests/test_answer_contract.py`, `tests/test_memory_segments_and_strata.py` | implemented_tested | Behavior specs exist for provenance + recall pathways with deterministic tests present. |
| 2. Runtime logging + eval/runtime parity tests pass | `sat_chatbot_memory_v2.py` logging/build pipeline paths, `eval_fixtures.py` | N/A | `tests/test_runtime_logging_events.py`, `tests/test_eval_runtime_parity.py` | implemented_tested | Criterion names concrete tests that map to runtime/eval parity modules. |
| 3. All-green gate includes behave + parity checks passing | End-to-end runtime and feature status gate | `features/testbot/answer_contract.feature`, `features/testbot/memory_recall.feature` (indirect) | parity/logging tests (indirect) | partial | Issue remains open and feature status still partial, indicating closure gate not yet satisfied. |
| 4. `knowing_grounded_answers` moved to implemented only after 1-3 | `sat_chatbot_memory_v2.py` capability snapshot and status reporting consumers | N/A | `tests/test_report_feature_status.py` | partial | `docs/qa/feature-status-report.md` lists knowing capability as partial with open ISSUE-0009. |

## ISSUE-0010 (`open`)

| Criterion | `src/testbot/` implementation mapping | `features/` mapping | `tests/` mapping | Verdict | Evidence note |
|---|---|---|---|---|---|
| 1. Behave uncertainty/fallback scenarios pass | `reflection_policy.py` (`decide_fallback_action`), `answer_policy.py`, `sat_chatbot_memory_v2.py` response policy gating | `features/testbot/answer_contract.feature`, `features/testbot/intent_grounding.feature` | `tests/test_reflection_policy.py` | partial | Unknowing capability is still tracked as partial in feature status artifacts. |
| 2. Pytest reflection-policy + runtime-logging pass | `reflection_policy.py`, runtime logging in `sat_chatbot_memory_v2.py` | N/A | `tests/test_reflection_policy.py`, `tests/test_runtime_logging_events.py` | implemented_tested | Deterministic tests and concrete modules exist. |
| 3. All-green gate contains required pass set | End-to-end paths | behavior features (indirect) | deterministic suites (indirect) | partial | Criterion is a closure gate still blocked by issue open state. |
| 4. `unknowing_safe_fallback` set to implemented only after 1-3 | capability snapshot/status surfaces in runtime/reporting | N/A | `tests/test_report_feature_status.py` | partial | `docs/qa/feature-status-report.md` still shows unknowing capability as partial/open ISSUE-0010. |

## ISSUE-0011 (`open`)

| Criterion | `src/testbot/` implementation mapping | `features/` mapping | `tests/` mapping | Verdict | Evidence note |
|---|---|---|---|---|---|
| 1. Analytics summary includes input/recognized/ignored/turn_start counters | `sat_chatbot_memory_v2.py` runtime event generation feeding analytics | N/A | `tests/test_turn_analytics_aggregator.py` | implemented_tested | Deterministic aggregator tests cover normalized rows and counters. |
| 2. Summary includes event/ignored-event counts | same as above | N/A | `tests/test_turn_analytics_aggregator.py` | implemented_tested | Event-class observability checks are present in aggregator tests. |
| 3. Warning emitted for threshold anomalies | upstream runtime event quality in `sat_chatbot_memory_v2.py` | N/A | `tests/test_turn_analytics_aggregator.py` | partial | Evidence of warning-threshold contract exists but explicit threshold command evidence remains open in issue state. |
| 4. Testing docs define analytics input semantics | governance/document criterion | N/A | `tests/test_turn_analytics_aggregator.py` (contract-adjacent) | implemented_tested | Criterion is documented and aligned with deterministic aggregator tests. |
| 5. Deterministic analytics tests added/updated | runtime turn logging feeds analytics input | N/A | `tests/test_turn_analytics_aggregator.py` | implemented_tested | Dedicated deterministic suite exists for analytics normalization/coverage. |

## ISSUE-0012 (`open`)

| Criterion | `src/testbot/` implementation mapping | `features/` mapping | `tests/` mapping | Verdict | Evidence note |
|---|---|---|---|---|---|
| 1. feature-status has planned canonical pipeline slices | capability runtime status originates from `sat_chatbot_memory_v2.py` (`build_capability_snapshot`) | N/A | `tests/test_report_feature_status.py` | implemented_tested | Planned slices and ISSUE-0013 linkage are represented in feature-status artifacts. |
| 2. Open issues impacting canonical turn semantics reference ISSUE-0012 | governance-only linkage criterion | N/A | `tests/test_validate_issue_links.py` | governance_only | Cross-reference language exists, but this is not runtime behavior. |
| 3. Work Plan defines sprint slices + checkpoints | governance-only delivery-plan criterion | N/A | `tests/test_validate_issues.py` | governance_only | Work-plan text exists; still open because stream is planning context. |
| 4. Verification section names deterministic validation commands | governance-only process criterion | N/A | `tests/test_validate_issues.py` | governance_only | Deterministic commands are listed; issue remains open for ongoing governance sequencing. |

## ISSUE-0013 (`open`)

Issue ACs are tracked as checklist items `[~]` (`AC-0013-01` through `AC-0013-12`) in `docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`; all are explicitly in-progress. Verdict per criterion is therefore `partial` pending closure evidence.

Primary implementation coverage mapped by AC cluster:
- Stage ordering/typed boundaries: `src/testbot/canonical_turn_orchestrator.py`, `src/testbot/stage_transitions.py`, `src/testbot/stabilization.py`, `src/testbot/pipeline_state.py`.
- Retrieval/memory strata: `src/testbot/evidence_retrieval.py`, `src/testbot/memory_strata.py`, `src/testbot/vector_store.py`.
- Policy/commit continuity: `src/testbot/intent_router.py`, `src/testbot/policy_decision.py`, `src/testbot/answer_commit.py`, `src/testbot/context_resolution.py`, `src/testbot/sat_chatbot_memory_v2.py`.

Behavior/spec and deterministic coverage mapped:
- `features/testbot/intent_grounding.feature`, `features/testbot/memory_recall.feature`, `features/testbot/source_ingestion.feature`, `features/testbot/capabilities.feature`.
- `tests/test_runtime_logging_events.py`, `tests/test_canonical_turn_pipeline_contract_ac_0013_02.py`, `tests/test_memory_segments_and_strata.py`, `tests/test_evidence_retrieval_mapping.py`, `tests/test_validate_pipeline_stage_conformance.py`, `tests/test_turn_analytics_aggregator.py`.

Verdict roll-up:
- AC-0013-01 … AC-0013-12: `partial` (explicitly marked `[~]` in issue file despite concrete implementation/test scaffolding).

## ISSUE-0014 (`open`)

| Criterion | `src/testbot/` implementation mapping | `features/` mapping | `tests/` mapping | Verdict | Evidence note |
|---|---|---|---|---|---|
| 1. Add deterministic BDD + pytest for reproduction pair | `sat_chatbot_memory_v2.py` identity routing helpers (`_is_self_identity_declaration`, `_is_self_referential_identity_recall_query`) | `features/testbot/memory_recall.feature`, `features/testbot/intent_grounding.feature` | `tests/test_runtime_logging_events.py` | partial | Coverage exists broadly, but issue remains open for exact end-to-end closure proof. |
| 2. Rewrite preserves discourse type for self-identification | `sat_chatbot_memory_v2.py` (`stage_rewrite_query`), `stabilization.py` (`stabilize_pre_route`) | `features/testbot/memory_recall.feature` | `tests/test_runtime_logging_events.py` | partial | Structural stage functions exist; behavioral acceptance still open. |
| 3. Intent/context favors stabilized identity facts | `intent_resolution.py`, `context_resolution.py`, `sat_chatbot_memory_v2.py` (`resolve_turn_intent`) | `features/testbot/memory_recall.feature` | `tests/test_runtime_logging_events.py` | partial | Continuity-aware modules present but not yet closure-complete by issue status. |
| 4. Retrieval avoids default direct answer on self-referential recall | `evidence_retrieval.py` (`retrieval_result`), `sat_chatbot_memory_v2.py` (`stage_retrieve`) | `features/testbot/intent_grounding.feature` | `tests/test_intent_router.py` | partial | Routing hardening exists; criterion tied to unresolved red-tag issue. |
| 5. Commit receipts include confirmed identity facts | `answer_commit.py` (`commit_answer_stage`, `_extract_stabilized_identity_fact`) | `features/testbot/memory_recall.feature` | `tests/test_runtime_logging_events.py` | partial | Commit-path implementation exists; issue indicates remaining semantic correctness work. |
| 6. Canonical gate + feature-status reflect closure state | runtime capability/status path in `sat_chatbot_memory_v2.py` | N/A | `tests/test_report_feature_status.py` | partial | ISSUE-0014 status remains open; closure reflection not satisfied. |
| 7. Closure requires behavioral proof, not structural telemetry only | runtime + deterministic evidence contract | feature scenarios above | tests above | partial | Explicit governance rule present; unmet per open state. |
| 8. ISSUE-0013 linkage blocks 0013 closure until 0014 proof complete | cross-issue dependency implemented in issue metadata/process | N/A | `tests/test_validate_issue_links.py` | implemented_tested | Dependency language is explicit in issue governance and link-validation tests. |

## ISSUE-0015 (`open`)

| Criterion | `src/testbot/` implementation mapping | `features/` mapping | `tests/` mapping | Verdict | Evidence note |
|---|---|---|---|---|---|
| 1. ISSUE-0014 has defect taxonomy section | N/A (governance in issue docs) | N/A | `tests/test_validate_issues.py` | implemented_tested | Present in ISSUE-0014 document structure. |
| 2. ISSUE-0014 has earliest-invalid-state declaration | N/A | N/A | `tests/test_validate_issues.py` | implemented_tested | Present in ISSUE-0014. |
| 3. ISSUE-0014 has explicit stage contracts | N/A | N/A | `tests/test_validate_issues.py` | implemented_tested | Present in ISSUE-0014 with rewrite/intent/routing/commit clauses. |
| 4. ISSUE-0014 includes quality-system gap section | N/A | N/A | `tests/test_validate_issues.py` | implemented_tested | Present in ISSUE-0014. |
| 5. ISSUE-0014 mandates observability fields | Runtime fields implemented through logging paths in `sat_chatbot_memory_v2.py` | N/A | `tests/test_runtime_logging_events.py` | implemented_tested | Observability requirements are now explicit and map to runtime logging tests. |
| 6. ISSUE-0014 links governance to ISSUE-0013 closure discipline | N/A | N/A | `tests/test_validate_issue_links.py` | implemented_tested | Dependency language is explicit in issue docs and validator scope. |
| 7. Deterministic regression coverage requirement is specified | runtime identity/continuity modules: `stabilization.py`, `context_resolution.py`, `answer_commit.py` | `features/testbot/memory_recall.feature` | `tests/test_runtime_logging_events.py` | implemented_tested | Requirement is explicitly specified and mapped to deterministic suites. |
| 8. RED_TAG and issue metadata consistency maintained | N/A | N/A | `tests/test_validate_issue_links.py`, `tests/test_validate_issues.py` | implemented_tested | RED_TAG entries remain synchronized with open dependency chain language. |
