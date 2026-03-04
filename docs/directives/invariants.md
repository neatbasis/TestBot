# Invariant Registry (Directive View)

`docs/invariants.md` is the canonical invariant registry with stable IDs and traceability. This directive view mirrors the same invariants for readers navigating the `docs/directives/` tree.

## Assumptions and invariants

| Invariant ID | Invariant | Definition | Enforcement location(s) | Test/BDD coverage location(s) | Failure mode |
|---|---|---|---|---|---|
| INV-001 | Citation requirement for factual answers | Any answer containing factual claims must include memory citation fields `doc_id` and `ts`; otherwise it is not contract-compliant. | `response_contains_claims()`, `has_required_memory_citation()`, and `validate_answer_contract()` plus `ANSWER_PROMPT` in `src/testbot/sat_chatbot_memory_v2.py`. | `Scenario: rejection of uncited factual response from eval pattern` in `features/answer_contract.feature` with assertions in `features/steps/answer_contract_steps.py`; `Scenario: cited memory-grounded answer path` in `features/memory_recall.feature` with assertions in `features/steps/memory_steps.py`. | Answer is replaced by exact fallback (`I don't know from memory.`) when citation checks fail. |
| INV-002 | Exact memory-grounded fallback behavior | When context is insufficient, low-confidence, empty, or contract-invalid, output must be exactly `I don't know from memory.` | Confidence gate (`has_sufficient_context_confidence`) and explicit fallback branches in `main` plus `ANSWER_PROMPT` in `src/testbot/sat_chatbot_memory_v2.py`. | `Scenario: exact fallback path` in `features/memory_recall.feature` with exact assertion in `features/steps/memory_steps.py`; contract-invalid path enforced by scenario in `features/answer_contract.feature`. | Any deviation from the exact fallback string is a contract violation and should fail acceptance checks. |

## Scenario ID mapping

- `BDD-AC-01` → `features/answer_contract.feature` → `Scenario: rejection of uncited factual response from eval pattern`
- `BDD-MR-01` → `features/memory_recall.feature` → `Scenario: cited memory-grounded answer path`
- `BDD-MR-02` → `features/memory_recall.feature` → `Scenario: exact fallback path`
