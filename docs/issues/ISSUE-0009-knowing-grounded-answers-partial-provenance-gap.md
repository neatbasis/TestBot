# ISSUE-0009: Knowing grounded answers remain partial due to provenance/recall gate debt

- **ID:** ISSUE-0009
- **Title:** Knowing grounded answers remain partial due to provenance/recall gate debt
- **Status:** open
- **Severity:** amber
- **Owner:** platform-qa
- **Created:** 2026-03-06
- **Target Sprint:** Sprint 2
- **Principle Alignment:** contract-first, traceable, deterministic, user-centric

## Problem Statement

The `knowing_grounded_answers` capability remains `partial`. There is no active issue explicitly tying this partial state to measurable gate evidence for `product_behave`, `safety_behave_answer_contract_and_memory`, and `qa_eval_fixtures_and_runtime_parity`.

## Evidence

- `docs/qa/feature-status.yaml` marks `knowing_grounded_answers` as `partial`.
- Existing issue set does not currently provide a dedicated open issue scoped to this capability.
- Capability acceptance tests span contract behavior, memory recall, runtime logging, and eval/runtime parity; closure requires cross-check consistency.

## Impact

- Knowing-mode outputs may regress in provenance transparency or memory-grounding quality without immediate governance visibility.
- Stakeholder confidence in grounded answers can drift from actual runtime behavior.
- QA report consumers cannot quickly map partial status to an accountable issue owner/work plan.

## Acceptance Criteria

1. `python -m behave features/answer_contract.feature features/memory_recall.feature` passes.
2. `python -m pytest tests/test_runtime_logging_events.py tests/test_eval_runtime_parity.py` passes.
3. `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json` reports `product_behave`, `safety_behave_answer_contract_and_memory`, and `qa_eval_fixtures_and_runtime_parity` as `passed`.
4. `docs/qa/feature-status.yaml` is updated to `implemented` for `knowing_grounded_answers` only after criteria 1-3 are met.

## Work Plan

- Add targeted deterministic fixtures where provenance/basis output remains weak.
- Align memory recall BDD and parity assertions to prevent drift between runtime and eval contracts.
- Keep report artifacts regenerated after linkage updates.

## Verification

- Command: `python -m behave features/answer_contract.feature features/memory_recall.feature`
  - Expected: exits `0`.
- Command: `python -m pytest tests/test_runtime_logging_events.py tests/test_eval_runtime_parity.py`
  - Expected: exits `0`.
- Command: `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json`
  - Expected: required gate checks pass.

## Closure Notes

- 2026-03-06: Opened to provide capability-specific governance traceability for partial knowing-mode grounded answers.
