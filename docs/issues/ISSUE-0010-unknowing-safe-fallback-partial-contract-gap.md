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

The `unknowing_safe_fallback` capability is still marked `partial`, but there is no dedicated open issue that maps this partial state to measurable acceptance criteria tied to its gate checks (`product_behave`, `safety_reflection_and_runtime_logging_pytests`).

## Evidence

- `docs/qa/feature-status.yaml` marks `unknowing_safe_fallback` as `partial`.
- Existing closed issues only partially overlap with fallback behavior and do not provide active accountability for current residual gaps.
- Contract behavior spans both BDD intent scenarios and deterministic reflection-policy/runtime-logging tests.

## Impact

- Incorrectly confident responses may leak into turns that should be explicit-uncertainty fallbacks.
- Safety posture can degrade if fallback messaging/action routing drifts from tested expectations.
- Stakeholders cannot easily trace partial status to accountable mitigation work.

## Acceptance Criteria

1. `python -m behave features/answer_contract.feature features/intent_grounding.feature` passes for uncertainty/fallback scenarios.
2. `python -m pytest tests/test_reflection_policy.py tests/test_runtime_logging_events.py` passes.
3. `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json` reports `product_behave` and `safety_reflection_and_runtime_logging_pytests` as `passed`.
4. `docs/qa/feature-status.yaml` is updated to `implemented` for `unknowing_safe_fallback` only after criteria 1-3 are met.

## Work Plan

- Tighten fallback action/messaging contracts for low-confidence and no-evidence branches.
- Extend deterministic tests for uncertainty wording and provenance transparency in unknowing mode.
- Keep capability linkage metadata current so reports show open issue traceability until closure.

## Verification

- Command: `python -m behave features/answer_contract.feature features/intent_grounding.feature`
  - Expected: exits `0`.
- Command: `python -m pytest tests/test_reflection_policy.py tests/test_runtime_logging_events.py`
  - Expected: exits `0`.
- Command: `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json`
  - Expected: required gate checks pass.

## Closure Notes

- 2026-03-06: Opened to establish explicit, measurable governance linkage for partial unknowing safe fallback capability.
