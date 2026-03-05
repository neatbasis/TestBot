# Invariant Registry

This registry defines contract-level invariants for answer behavior. Each invariant has a stable ID and traceability links to implementation and verification coverage.

## Invariants

| Invariant ID | Invariant statement | Runtime enforcement (code location) | Test/BDD coverage |
|---|---|---|---|
| INV-001 | **Citation-required factual responses**: Any response containing factual claims must include at least one memory citation with both `doc_id` and `ts`; otherwise the response is contract-invalid. | `response_contains_claims`, `has_required_memory_citation`, and `validate_answer_contract` in [`src/testbot/sat_chatbot_memory_v2.py`](../src/testbot/sat_chatbot_memory_v2.py); answer contract language in `ANSWER_PROMPT` in the same module. | BDD: `Scenario: rejection of uncited factual response from eval pattern` in [`features/answer_contract.feature`](../features/answer_contract.feature) via step validator mirror in [`features/steps/answer_contract_steps.py`](../features/steps/answer_contract_steps.py). BDD: cited-answer path `Scenario: cited memory-grounded answer path` in [`features/memory_recall.feature`](../features/memory_recall.feature) via citation assertions in [`features/steps/memory_steps.py`](../features/steps/memory_steps.py). |
| INV-002 | **Progressive fallback for insufficient memory**: If memory is empty/low-confidence, assistant must ask one targeted clarifier or offer at least two capability-based alternatives; if memory is partial/ambiguous, assistant must provide a brief user-facing summary plus one bridging clarifier; exact `I don't know from memory.` is reserved for explicit deny/safety cases. | Fallback policy routing in `decide_fallback_action(...)` in [`src/testbot/reflection_policy.py`](../src/testbot/reflection_policy.py); progressive clarify/assist branches (`build_partial_memory_clarifier`, `ASSIST_ALTERNATIVES_ANSWER`) and deny-only exact fallback guidance in `ANSWER_PROMPT` in [`src/testbot/sat_chatbot_memory_v2.py`](../src/testbot/sat_chatbot_memory_v2.py). | BDD: `Scenario: progressive assist fallback path` and `Scenario: equivalent candidates remain ambiguous after tie-break` in [`features/memory_recall.feature`](../features/memory_recall.feature), validated via mode/shape assertions in [`features/steps/memory_steps.py`](../features/steps/memory_steps.py). BDD: contract rejection scenario in [`features/answer_contract.feature`](../features/answer_contract.feature) still validates uncited factual responses are rejected from memory-grounded mode. |

## Scenario ID map

- `BDD-AC-01`: `features/answer_contract.feature` → `Scenario: rejection of uncited factual response from eval pattern`
- `BDD-MR-01`: `features/memory_recall.feature` → `Scenario: cited memory-grounded answer path`
- `BDD-MR-02`: `features/memory_recall.feature` → `Scenario: progressive assist fallback path`


## Stage transition contracts

| Stage | Preconditions | Postconditions | Invariant linkage |
|---|---|---|---|
| `observe` | `user_input` is present and non-empty before processing begins. | Canonical state remains initialized with the same non-empty `user_input`. | `INV-002` (fallback flow is only meaningful for non-empty user turns). |
| `encode` | `user_input` is present. | `rewritten_query` is present and non-empty. | `INV-002` (downstream confidence/fallback logic relies on a query entering retrieval). |
| `retrieve` | `rewritten_query` is present. | `retrieval_candidates` is a scored candidate list (`doc_id`, `score`, `ts`, `card_type`) shape. | `INV-002` (insufficient context is measured from retrieval outputs). |
| `rerank` | `retrieval_candidates` already matches scored candidate shape. | `reranked_hits` keeps scored candidate shape and `confidence_decision.context_confident` is explicitly boolean. | `INV-002` (progressive fallback branch selection is keyed by confidence + ambiguity decisions). |
| `answer` | `confidence_decision.context_confident` is explicitly boolean. | `invariant_decisions` is recorded, `INV-001` citation contract is enforced, and `INV-002` progressive clarify/assist behavior is enforced for memory insufficiency while exact fallback is reserved for deny/safety-only cases. | `INV-001`, `INV-002`. |
