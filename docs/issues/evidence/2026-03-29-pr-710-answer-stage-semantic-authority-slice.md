# 2026-03-29 PR-710 answer-stage semantic authority slice

## Scope
Bounded seam reduction for answer-stage alignment semantics.

## Findings (pre-change)
- `answer_validate_for_turn_service(...)` accepted legacy-shaped injections for alignment evaluator and special-answer constants, and runtime loop wiring supplied those via `sat_chatbot_memory_v2`.
- `validate_answer_commit_post(...).alignment_decision_consistent` carried local category logic instead of consuming one canonical answer-semantic owner.

## Canonical vs transitional authority after this slice
- **Canonical now**:
  - `testbot.answer_stage_semantics` defines special-answer classes and expected alignment decisions.
  - `answer_validate_for_turn_service(...)` defaults to canonical provenance/alignment functions and canonical answer semantic contract.
  - `stage_transitions` consumes canonical answer-semantic expectations from `testbot.answer_stage_semantics`.
- **Still transitional/deferred**:
  - `answer_assemble_for_turn_service(...)` still receives some legacy-shaped collaborators from `sat_chatbot_memory_v2` (prompt/render helpers and selected constants) pending a separate seam-reduction slice.

## Semantic authority moved/clarified in this PR
- Moved answer/alignment category semantics from per-call legacy injection + validator-local heuristics to a shared canonical owner (`testbot.answer_stage_semantics`).
