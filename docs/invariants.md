# Invariant Registry

This registry defines contract-level invariants for answer behavior. Each invariant has a stable ID and traceability links to implementation and verification coverage.

`docs/invariants.md` is the canonical source of truth; directive mirrors (for example `docs/directives/invariants.md`) must remain synchronized with this contract.

## Invariants

| Invariant ID | Invariant statement | Runtime enforcement (code location) | Test/BDD coverage |
|---|---|---|---|
| INV-001 | **Citation-required factual responses**: Any response containing factual claims must include at least one memory citation with both `doc_id` and `ts`; otherwise the response is contract-invalid. | `response_contains_claims`, `raw_claim_like_text_detected`, `has_required_memory_citation`, and `validate_answer_contract` in [`src/testbot/sat_chatbot_memory_v2.py`](../src/testbot/sat_chatbot_memory_v2.py); answer contract language in `ANSWER_PROMPT` in the same module. | BDD: `Scenario: rejection of uncited factual response from eval pattern` in [`features/answer_contract.feature`](../features/answer_contract.feature) via step validator mirror in [`features/steps/answer_contract_steps.py`](../features/steps/answer_contract_steps.py). BDD: cited-answer path `Scenario: cited memory-grounded answer path` in [`features/memory_recall.feature`](../features/memory_recall.feature) via citation assertions in [`features/steps/memory_steps.py`](../features/steps/memory_steps.py). |
| INV-002 | **Progressive fallback for insufficient memory**: If memory is empty/low-confidence, assistant must ask one targeted clarifier or offer at least two capability-based alternatives; if memory is partial/ambiguous, assistant must provide a brief user-facing summary plus one bridging clarifier; direct memory fallback phrase usage is not used for standard insufficiency paths. | Fallback policy routing in `decide_fallback_action(...)` in [`src/testbot/reflection_policy.py`](../src/testbot/reflection_policy.py); progressive clarify/assist branches (`build_partial_memory_clarifier`, `ASSIST_ALTERNATIVES_ANSWER`) and uncertainty fallback handling in `stage_answer(...)` in [`src/testbot/sat_chatbot_memory_v2.py`](../src/testbot/sat_chatbot_memory_v2.py). | BDD: `Scenario: progressive assist fallback path` and `Scenario: equivalent candidates remain ambiguous after tie-break` in [`features/memory_recall.feature`](../features/memory_recall.feature), validated via mode/shape assertions in [`features/steps/memory_steps.py`](../features/steps/memory_steps.py). |
| INV-003 | **General-knowledge responses require explicit marker + confidence gate**: non-memory factual answers must include `General definition (not from your memory):` and pass confidence/support thresholds; otherwise runtime must degrade to a knowledge-safe uncertainty response. | `has_general_knowledge_marker`, `passes_general_knowledge_confidence_gate`, `validate_general_knowledge_contract`, and enforcement/degrade logic in `stage_answer(...)` in [`src/testbot/sat_chatbot_memory_v2.py`](../src/testbot/sat_chatbot_memory_v2.py). | BDD: `Scenario: disallowed unlabeled general-knowledge factual output`, `Scenario: allowed labeled general-knowledge output when confidence gate passes`, and `Scenario: non-memory general-knowledge fallback stays knowledge-safe` in [`features/answer_contract.feature`](../features/answer_contract.feature) via [`features/steps/answer_contract_steps.py`](../features/steps/answer_contract_steps.py). |

## Scenario ID map

- `BDD-AC-01`: `features/answer_contract.feature` → `Scenario: rejection of uncited factual response from eval pattern`
- `BDD-MR-01`: `features/memory_recall.feature` → `Scenario: cited memory-grounded answer path`
- `BDD-MR-02`: `features/memory_recall.feature` → `Scenario: progressive assist fallback path`
- `BDD-AC-02`: `features/answer_contract.feature` → `Scenario: disallowed unlabeled general-knowledge factual output`
- `BDD-AC-03`: `features/answer_contract.feature` → `Scenario: allowed labeled general-knowledge output when confidence gate passes`
- `BDD-AC-04`: `features/answer_contract.feature` → `Scenario: non-memory general-knowledge fallback stays knowledge-safe`


## Stage transition contracts

| Stage | Preconditions | Postconditions | Invariant linkage |
|---|---|---|---|
| `observe` | `user_input` is present and non-empty before processing begins. | Canonical state remains initialized with the same non-empty `user_input`. | `INV-002` (fallback flow is only meaningful for non-empty user turns). |
| `encode` | `user_input` is present. | `rewritten_query` is present and non-empty. | `INV-002` (downstream confidence/fallback logic relies on a query entering retrieval). |
| `retrieve` | `rewritten_query` is present. | `retrieval_candidates` is a scored candidate list (`doc_id`, `score`, `ts`, `card_type`) shape. | `INV-002` (insufficient context is measured from retrieval outputs). |
| `rerank` | `retrieval_candidates` already matches scored candidate shape. | `reranked_hits` keeps scored candidate shape and `confidence_decision.context_confident` is explicitly boolean. | `INV-002` (progressive fallback branch selection is keyed by confidence + ambiguity decisions). |
| `answer` | `confidence_decision.context_confident` is explicitly boolean. | `invariant_decisions` is recorded, `INV-001` citation contract is enforced, `INV-002` progressive clarify/assist behavior is enforced for memory insufficiency, and `INV-003` general-knowledge marker/confidence gating is enforced with knowledge-safe degradation when needed. | `INV-001`, `INV-002`, `INV-003`. |
