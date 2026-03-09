# Answer Policy Invariants

This registry defines response-policy/UX contract invariants for answer behavior. Each invariant has a stable ID and explicit traceability to enforcement and verification coverage.

## Canonical mirror source (exact sync block)

The block between the markers below is the **single source section** for answer-policy invariants and the scenario map. `docs/directives/invariants.md` must mirror this block exactly via `python scripts/sync_invariants_mirror.py`.

<!-- BEGIN_SYNCED_INVARIANTS_TABLE_AND_SCENARIO_MAP -->

## Response-policy invariants

| Invariant ID | Invariant statement | Runtime enforcement (code location) | Test/BDD coverage |
|---|---|---|---|
| INV-001 | **Citation-required factual responses**: Any response containing factual claims must include at least one memory citation with both `doc_id` and `ts`; otherwise the response is contract-invalid. | `response_contains_claims`, `raw_claim_like_text_detected`, `has_required_memory_citation`, and `validate_answer_contract` in `src/testbot/sat_chatbot_memory_v2.py`; answer contract language in `ANSWER_PROMPT` in the same module. | BDD: `Scenario: rejection of uncited factual response from eval pattern` in `features/answer_contract.feature` via step validator mirror in `features/steps/answer_contract_steps.py`. BDD: cited-answer path `Scenario: cited memory-grounded answer path` in `features/memory_recall.feature` via citation assertions in `features/steps/memory_steps.py`. |
| INV-002 | **Progressive fallback and normalized pending-lookup semantics**: If memory is empty/low-confidence, assistant must ask one targeted clarifier or offer at least two capability-based alternatives; if memory is partial/ambiguous, assistant must provide a brief user-facing summary plus one bridging clarifier. When `background_ingestion_in_progress=true` (including canonical decision class `pending_lookup_background_ingestion`), fallback is normalized as a **non-clarify pending-lookup path**: answer mode resolves to `assist`, and final answer must remain pending-lookup-safe (`BACKGROUND_INGESTION_PROGRESS_ANSWER` or `NON_KNOWLEDGE_UNCERTAINTY_ANSWER`). | Fallback policy routing in `decide_fallback_action(...)` in `src/testbot/reflection_policy.py`; answer-mode normalization in `resolve_answer_mode(...)` in `src/testbot/answer_policy.py`; pending-lookup canonicalization and non-memory clarify degradation handling in `stage_answer(...)` in `src/testbot/sat_chatbot_memory_v2.py`; commit-post fallback classification checks in `_classify_canonical_fallback_path(...)` and `_fallback_invariant_outcomes(...)` in `src/testbot/stage_transitions.py`. | BDD: `Scenario: progressive assist fallback path` and `Scenario: equivalent candidates remain ambiguous after tie-break` in `features/memory_recall.feature`; `Scenario: async background ingestion uses pending non-clarify fallback` in `features/answer_contract.feature`, validated via mode/shape assertions in `features/steps/memory_steps.py` and `features/steps/answer_contract_steps.py`. |
| INV-003 | **General-knowledge responses require explicit marker + confidence gate**: non-memory factual answers must include `General definition (not from your memory):` and pass confidence/support thresholds; otherwise runtime must degrade to a knowledge-safe uncertainty response. | `has_general_knowledge_marker`, `passes_general_knowledge_confidence_gate`, `validate_general_knowledge_contract`, and enforcement/degrade logic in `stage_answer(...)` in `src/testbot/sat_chatbot_memory_v2.py`. | BDD: `Scenario: disallowed unlabeled general-knowledge factual output`, `Scenario: allowed labeled general-knowledge output when confidence gate passes`, and `Scenario: non-memory general-knowledge fallback stays knowledge-safe` in `features/answer_contract.feature` via `features/steps/answer_contract_steps.py`. |

## Scenario ID map

- `BDD-AC-01`: `features/answer_contract.feature` → `Scenario: rejection of uncited factual response from eval pattern`
- `BDD-MR-01`: `features/memory_recall.feature` → `Scenario: cited memory-grounded answer path`
- `BDD-MR-02`: `features/memory_recall.feature` → `Scenario: progressive assist fallback path`
- `BDD-AC-02`: `features/answer_contract.feature` → `Scenario: disallowed unlabeled general-knowledge factual output`
- `BDD-AC-03`: `features/answer_contract.feature` → `Scenario: allowed labeled general-knowledge output when confidence gate passes`
- `BDD-AC-04`: `features/answer_contract.feature` → `Scenario: non-memory general-knowledge fallback stays knowledge-safe`

<!-- END_SYNCED_INVARIANTS_TABLE_AND_SCENARIO_MAP -->
