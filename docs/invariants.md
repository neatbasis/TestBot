# Invariant Registry

This registry defines contract-level invariants for answer behavior. Each invariant has a stable ID and traceability links to implementation and verification coverage.

## Invariants

| Invariant ID | Invariant statement | Runtime enforcement (code location) | Test/BDD coverage |
|---|---|---|---|
| INV-001 | **Citation-required factual responses**: Any response containing factual claims must include at least one memory citation with both `doc_id` and `ts`; otherwise the response is contract-invalid. | `response_contains_claims`, `has_required_memory_citation`, and `validate_answer_contract` in [`src/testbot/sat_chatbot_memory_v2.py`](../src/testbot/sat_chatbot_memory_v2.py); answer contract language in `ANSWER_PROMPT` in the same module. | BDD: `Scenario: rejection of uncited factual response from eval pattern` in [`features/answer_contract.feature`](../features/answer_contract.feature) via step validator mirror in [`features/steps/answer_contract_steps.py`](../features/steps/answer_contract_steps.py). BDD: cited-answer path `Scenario: cited memory-grounded answer path` in [`features/memory_recall.feature`](../features/memory_recall.feature) via citation assertions in [`features/steps/memory_steps.py`](../features/steps/memory_steps.py). |
| INV-002 | **Exact fallback on insufficient confidence or invalid citation**: If memory confidence is insufficient, response is empty, or citation validation fails, output must be exactly `I don't know from memory.` | Confidence gate `has_sufficient_context_confidence(...)` + fallback branches in `main` (`if not context_is_confident`, empty-draft branch, contract-invalid branch) in [`src/testbot/sat_chatbot_memory_v2.py`](../src/testbot/sat_chatbot_memory_v2.py); fallback requirement in `ANSWER_PROMPT` in the same module. | BDD: `Scenario: exact fallback path` in [`features/memory_recall.feature`](../features/memory_recall.feature) with exact string assertion in [`features/steps/memory_steps.py`](../features/steps/memory_steps.py). BDD: contract rejection scenario in [`features/answer_contract.feature`](../features/answer_contract.feature) verifies uncited factual responses are invalid, which routes to fallback in runtime flow. |

## Scenario ID map

- `BDD-AC-01`: `features/answer_contract.feature` → `Scenario: rejection of uncited factual response from eval pattern`
- `BDD-MR-01`: `features/memory_recall.feature` → `Scenario: cited memory-grounded answer path`
- `BDD-MR-02`: `features/memory_recall.feature` → `Scenario: exact fallback path`
