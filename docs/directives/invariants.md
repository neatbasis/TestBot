# Invariant Registry (Directive View)

`docs/invariants.md` is the canonical invariant registry with stable IDs and traceability. This directive view mirrors the same invariants for readers navigating the `docs/directives/` tree.

## Assumptions and invariants

| Invariant ID | Invariant | Definition | Enforcement location(s) | Test/BDD coverage location(s) | Failure mode |
|---|---|---|---|---|---|
| INV-001 | Citation requirement for factual answers | **Citation-required factual responses**: Any response containing factual claims must include at least one memory citation with both `doc_id` and `ts`; otherwise the response is contract-invalid. | `response_contains_claims()`, `has_required_memory_citation()`, and `validate_answer_contract()` plus `ANSWER_PROMPT` in `src/testbot/sat_chatbot_memory_v2.py`. | `Scenario: rejection of uncited factual response from eval pattern` in `features/answer_contract.feature` with assertions in `features/steps/answer_contract_steps.py`; `Scenario: cited memory-grounded answer path` in `features/memory_recall.feature` with assertions in `features/steps/memory_steps.py`. | Answer is replaced by exact fallback (`I don't know from memory.`) when citation checks fail. |
| INV-002 | Exact memory-grounded fallback behavior | **Exact fallback on insufficient confidence or invalid citation**: If memory confidence is insufficient, response is empty, or citation validation fails, output must be exactly `I don't know from memory.` | Confidence gate (`has_sufficient_context_confidence`) and explicit fallback branches in `main` plus `ANSWER_PROMPT` in `src/testbot/sat_chatbot_memory_v2.py`. | `Scenario: exact fallback path` in `features/memory_recall.feature` with exact assertion in `features/steps/memory_steps.py`; contract-invalid path enforced by scenario in `features/answer_contract.feature`. | Any deviation from the exact fallback string is a contract violation and should fail acceptance checks. |
| INV-003 | General-knowledge labeling and certainty gate | **General-knowledge responses must be explicitly marked and confidence-gated**: When provenance is `GENERAL_KNOWLEDGE`, the answer must begin with `General definition (not from your memory): ...` and factual certainty is blocked unless the general-knowledge confidence gate meets threshold (`general_knowledge_confidence >= 0.85` and `general_knowledge_support >= 2`). | `build_provenance_metadata()`, `has_general_knowledge_marker()`, `passes_general_knowledge_confidence_gate()`, and `validate_general_knowledge_contract()` in `src/testbot/sat_chatbot_memory_v2.py`; enforced in `stage_answer()` fallback branching. | `Scenario: disallowed unlabeled general-knowledge factual output` and `Scenario: allowed labeled general-knowledge output when confidence gate passes` in `features/answer_contract.feature` with checks in `features/steps/answer_contract_steps.py`. | Non-compliant output is replaced by exact fallback (`I don't know from memory.`); unsupported factual certainty is not surfaced to users. |

## Scenario ID mapping

- `BDD-AC-01` → `features/answer_contract.feature` → `Scenario: rejection of uncited factual response from eval pattern`
- `BDD-MR-01` → `features/memory_recall.feature` → `Scenario: cited memory-grounded answer path`
- `BDD-MR-02` → `features/memory_recall.feature` → `Scenario: exact fallback path`
- `BDD-AC-02` → `features/answer_contract.feature` → `Scenario: disallowed unlabeled general-knowledge factual output`
- `BDD-AC-03` → `features/answer_contract.feature` → `Scenario: allowed labeled general-knowledge output when confidence gate passes`


## Stage transition contracts

| Stage | Preconditions | Postconditions | Invariant linkage |
|---|---|---|---|
| `observe` | `user_input` is present and non-empty before processing begins. | Canonical state remains initialized with the same non-empty `user_input`. | `INV-002` (fallback flow is only meaningful for non-empty user turns). |
| `encode` | `user_input` is present. | `rewritten_query` is present and non-empty. | `INV-002` (downstream confidence/fallback logic relies on a query entering retrieval). |
| `retrieve` | `rewritten_query` is present. | `retrieval_candidates` is a scored candidate list (`doc_id`, `score`, `ts`, `card_type`) shape. | `INV-002` (insufficient context is measured from retrieval outputs). |
| `rerank` | `retrieval_candidates` already matches scored candidate shape. | `reranked_hits` keeps scored candidate shape and `confidence_decision.context_confident` is explicitly boolean. | `INV-002` (exact fallback path is keyed by confidence decision). |
| `answer` | `confidence_decision.context_confident` is explicitly boolean. | `invariant_decisions` is recorded, `INV-001` citation contract is enforced, `INV-003` general-knowledge marker and certainty gating are enforced for `GENERAL_KNOWLEDGE` provenance, and `INV-002` exact fallback behavior is enforced whenever confidence is insufficient, draft is empty, citation checks fail, or general-knowledge contract checks fail. | `INV-001`, `INV-002`, `INV-003`. |
