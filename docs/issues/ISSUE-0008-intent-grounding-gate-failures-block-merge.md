# ISSUE-0008: Intent-grounding router remains partial for deterministic route confidence

- **ID:** ISSUE-0008
- **Title:** Intent-grounding router remains partial for deterministic route confidence
- **Status:** in_progress
- **Severity:** amber
- **Owner:** platform-qa
- **Created:** 2026-03-05
- **Target Sprint:** Sprint 2
- **Principle Alignment:** contract-first, deterministic, ci-enforced, traceable

## Problem Statement

The initial merge-blocking failures were remediated, but `intent_grounding_router` is still declared `partial`. This issue is reopened/rescoped to track remaining deterministic confidence and route-selection quality needed to move the capability to `implemented`.

## Evidence

- Capability contract still marks `intent_grounding_router` as `partial`.
- Route selection quality depends on consistent `features/intent_grounding.feature` behavior and deterministic policy tests.
- Existing closure notes addressed acute gate failures but did not close all roadmap-aligned quality gaps for this capability.

## Impact

- Router misclassification at edge phrasing can trigger incorrect knowing/unknowing pathways.
- Behavior appears stable in core paths while remaining edge-case drift can still impact user trust.
- Downstream fallback/provenance decisions inherit routing uncertainty.

## Acceptance Criteria

1. `python -m behave features/intent_grounding.feature` passes with no flaky scenario outcomes across two consecutive local runs.
2. `python -m pytest tests/test_intent_router.py tests/test_promotion_policy.py` passes and includes deterministic coverage for all route branches currently marked partial.
3. `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json` reports `product_behave` and `qa_pytest_not_live_smoke` as `passed`.
4. `docs/qa/feature-status.yaml` is updated to `implemented` for `intent_grounding_router` only after criteria 1-3 are met.

## Work Plan

- Identify residual ambiguous-intent phrase classes and add deterministic fixture coverage.
- Tighten router threshold/rule handling where near-tie or fallback branch ambiguity remains.
- Regenerate feature-status artifacts after each iteration to keep governance traceability current.

- Align remaining route-confidence hardening tasks with the staged canonical pipeline plan tracked in ISSUE-0012 (Sprint 4 decisioning checkpoint).

## Verification

- Command: `python -m behave features/intent_grounding.feature`
  - Expected: all intent-grounding scenarios pass consistently.
- Command: `python -m pytest tests/test_intent_router.py tests/test_promotion_policy.py`
  - Expected: exits `0` with deterministic branch coverage.
- Command: `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json`
  - Expected: required gate checks pass.

## Closure Notes

- 2026-03-06: Original issue closed after fixing immediate gate-blocking failures.
- 2026-03-06: Reopened/rescoped to track residual capability-level partial status and deterministic route confidence work.
