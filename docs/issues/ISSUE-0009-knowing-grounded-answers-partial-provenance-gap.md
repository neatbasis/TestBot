# ISSUE-0009: Knowing grounded answers remain partial due to provenance/recall gate debt

- **ID:** ISSUE-0009
- **Title:** Knowing grounded answers remain partial due to provenance/recall gate debt
- **Status:** open
- **Severity:** amber
- **Owner:** platform-qa
- **Created:** 2026-03-06
- **Target Sprint:** Sprint 2
- **Principle Alignment:** contract-first, traceable, deterministic, user-centric

## Cross-Reference

- Primary implementation/bug-elimination program: ISSUE-0013
- This issue remains planning/history/context unless otherwise specified.

## Problem Statement

The `knowing_grounded_answers` capability remains `partial`. ISSUE-0009 is the primary traceability record for this capability and tracks the remaining measurable deltas against `product_behave`, `safety_behave_answer_contract_and_memory`, and `qa_eval_fixtures_and_runtime_parity`, while preserving explicit cross-capability linkage with ISSUE-0010 in generated status reporting.

## Evidence

- `docs/qa/feature-status.yaml` marks `knowing_grounded_answers` as `partial`.
- `docs/qa/feature-status-report.md` and `artifacts/feature-status-summary.json` list ISSUE-0009 and ISSUE-0010 as relevant open issues for this partial capability and still report failing checks (`product_behave`, `safety_behave_answer_contract_and_memory`).
- Capability acceptance tests span contract behavior, memory recall, runtime logging, and eval/runtime parity; closure requires cross-check consistency.

## Impact

- Knowing-mode outputs may regress in provenance transparency or memory-grounding quality without immediate governance visibility.
- Remaining failing gate checks keep this capability in partial state and continue to block readiness signals for knowing-mode quality.
- Stakeholder confidence in grounded answers can drift from actual runtime behavior.
- QA report consumers rely on ISSUE-0009 as the accountable primary tracker and on explicit ISSUE-0010 linkage for closure sequencing and delta burn-down.

## Acceptance Criteria

1. `python -m behave features/answer_contract.feature features/memory_recall.feature` passes.
2. `python -m pytest tests/test_runtime_logging_events.py tests/test_eval_runtime_parity.py` passes.
3. `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json` reports `product_behave`, `safety_behave_answer_contract_and_memory`, and `qa_eval_fixtures_and_runtime_parity` as `passed`.
4. `docs/qa/feature-status.yaml` is updated to `implemented` for `knowing_grounded_answers` only after criteria 1-3 are met.

## Work Plan

- [x] Capture production-debug evidence trace and map symptoms to ISSUE-0009/ISSUE-0010 acceptance criteria (`docs/issues/evidence/production-debug-cli-trace-2026-03-07.md`).
- [ ] **Remaining delta: confident memory-recall recovery** — fix equivalent-candidate ambiguity/tie-break flow so `features/memory_recall.feature:22` passes consistently.
- [ ] **Remaining delta: citation-context format** — align memory-hit citation/provenance formatting with deterministic contract expectations across BDD and pytest parity checks.
- [ ] **Remaining delta: debug reason accuracy** — ensure debug/trace reason values reflect true confidence/ambiguity branch decisions for memory-recall turns.
- [ ] Regenerate report/status artifacts with existing scripts only after acceptance criteria 1-3 are fully implemented and validated as passing.

- Sequence memory/provenance deltas against ISSUE-0012 Sprint 3 and Sprint 5 checkpoints so pre-route stabilization and answer validation changes are reviewed together.

## Verification

- Command: `python -m behave features/answer_contract.feature features/memory_recall.feature`
  - Expected: exits `0`.
- Command: `python -m pytest tests/test_runtime_logging_events.py tests/test_eval_runtime_parity.py`
  - Expected: exits `0`.
- Command: `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json`
  - Expected: required gate checks pass.

## Closure Notes

- 2026-03-06: Opened to provide capability-specific governance traceability for partial knowing-mode grounded answers.
