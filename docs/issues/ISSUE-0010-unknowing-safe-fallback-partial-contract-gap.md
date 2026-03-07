# ISSUE-0010: Unknowing safe fallback remains partial for explicit uncertainty contract completeness

- **ID:** ISSUE-0010
- **Title:** Unknowing safe fallback remains partial for explicit uncertainty contract completeness
- **Status:** open
- **Severity:** amber
- **Owner:** platform-qa
- **Created:** 2026-03-06
- **Target Sprint:** Sprint 2
- **Principle Alignment:** contract-first, user-centric, deterministic, traceable

## Problem Statement

The `unknowing_safe_fallback` capability is still marked `partial`. ISSUE-0010 is the primary traceability record for this capability and tracks the remaining measurable deltas tied to its gate checks (`product_behave`, `safety_reflection_and_runtime_logging_pytests`), while preserving explicit cross-capability linkage with ISSUE-0009 in generated status reporting.

## Evidence

- `docs/qa/feature-status.yaml` marks `unknowing_safe_fallback` as `partial`.
- `docs/qa/feature-status-report.md` and `artifacts/feature-status-summary.json` list ISSUE-0009 and ISSUE-0010 as relevant open issues for this partial capability while `product_behave` remains failed for the capability's evidence profile.
- Contract behavior spans both BDD intent scenarios and deterministic reflection-policy/runtime-logging tests.

## Impact

- Incorrectly confident responses may leak into turns that should be explicit-uncertainty fallbacks.
- Safety posture can degrade if fallback messaging/action routing drifts from tested expectations.
- Stakeholders use ISSUE-0010 as the accountable primary mitigation tracker while ISSUE-0009 linkage remains visible for shared closure dependencies.

## Acceptance Criteria

1. `python -m behave features/answer_contract.feature features/intent_grounding.feature` passes for uncertainty/fallback scenarios.
2. `python -m pytest tests/test_reflection_policy.py tests/test_runtime_logging_events.py` passes.
3. `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json` reports `product_behave` and `safety_reflection_and_runtime_logging_pytests` as `passed`.
4. `docs/qa/feature-status.yaml` is updated to `implemented` for `unknowing_safe_fallback` only after criteria 1-3 are met.

## Work Plan

- [x] Capture production-debug evidence trace and map symptoms to ISSUE-0009/ISSUE-0010 acceptance criteria (`docs/issues/evidence/production-debug-cli-trace-2026-03-07.md`).
- [ ] **Remaining delta: confident memory-recall recovery** — complete memory confidence recovery updates so upstream product behave no longer fails from memory ambiguity edge cases that cascade into fallback posture.
- [ ] **Remaining delta: citation-context format** — ensure uncertainty/fallback outputs keep explicit provenance and basis formatting aligned with contract text across intent-grounding and runtime logging checks.
- [ ] **Remaining delta: debug reason accuracy** — reconcile debug/trace reason strings so low-confidence and unknown branches report accurate reasons for fallback decisions.
- [ ] Regenerate report/status artifacts with existing scripts only after acceptance criteria 1-3 are fully implemented and validated as passing.

## Verification

- Command: `python -m behave features/answer_contract.feature features/intent_grounding.feature`
  - Expected: exits `0`.
- Command: `python -m pytest tests/test_reflection_policy.py tests/test_runtime_logging_events.py`
  - Expected: exits `0`.
- Command: `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json`
  - Expected: required gate checks pass.

## Closure Notes

- 2026-03-06: Opened to establish explicit, measurable governance linkage for partial unknowing safe fallback capability.
