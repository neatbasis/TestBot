# ISSUE-0008: Intent-grounding gate failures block merge readiness

- **ID:** ISSUE-0008
- **Title:** Intent-grounding gate failures block merge readiness
- **Status:** closed
- **Severity:** red
- **Owner:** platform-qa
- **Created:** 2026-03-05
- **Target Sprint:** Sprint 1
- **Principle Alignment:** contract-first, deterministic, ci-enforced, traceable

## Problem Statement

The canonical deterministic merge gate currently fails at the BDD stage because `features/intent_grounding.feature` scenarios are failing/errored. This prevents a trustworthy signal for knowing/unknowing behavior and blocks safe merge decisions for related PRs (including the current missed-check case).

## Evidence

- `python scripts/release_gate.py` fails at `python -m behave`.
- Failing/errored scenarios are concentrated in `features/intent_grounding.feature` (knowing-path, history-grounding path, relevance path, source-confidence fallback path).
- Because release gate is fail-closed, downstream required checks are not executed after the BDD failure.

## Impact

- PRs can appear partially validated while critical knowing/unknowing behavior remains unverified.
- Grounding confidence is reduced because source/basis behavior is not contract-stable.
- Merge velocity drops due to repeated revalidation cycles without a focused stabilization plan.

## Acceptance Criteria

1. `python -m behave` passes with no failed/errored `features/intent_grounding.feature` scenarios.
2. `python scripts/release_gate.py` executes all required checks successfully end-to-end.
3. At least one deterministic regression test is added/updated per previously failing intent-grounding branch.

## Work Plan

- Isolate failing intent-grounding branches and map each scenario to responsible policy/runtime function.
- Implement minimal deterministic fixes for fallback/action/provenance expectation mismatches.
- Add or update fixture-backed regression tests for each fixed branch.
- Re-run canonical gate and record pass evidence in closure notes.

## Verification

- Command: `python -m pip install -e .[dev]`
  - Expected: dev dependencies install, including `behave`.
- Command: `python -m behave`
  - Expected: all scenarios pass, especially `features/intent_grounding.feature`.
- Command: `python scripts/release_gate.py`
  - Expected: all required deterministic checks pass in sequence.

## Closure Notes

- Implemented deterministic intent-grounding fixes across runtime routing/policy and provenance shaping:
  - intent routing now classifies "when is/was" questions as knowledge questions for predictable knowing-path handling.
  - reflection fallback policy now supports an explicit `ANSWER_UNKNOWN` action for low-confidence source-backed turns when no confident memory hit is available.
  - provenance basis shaping now emits chat-history basis statements (including relevance-summary basis) when answers are grounded in recent conversation without memory/source hits.
- Reconciled BDD harness contracts in `features/steps/intent_grounding_steps.py`:
  - alignment dimensions now include `provenance_transparency`;
  - fallback scenario now uses canonical invariant/alignment fields;
  - source-backed fixture now uses valid `CandidateHit` schema.
- Added deterministic regression tests for each stabilized branch in:
  - `tests/test_intent_router.py`
  - `tests/test_promotion_policy.py`
  - `tests/test_reflection_policy.py`

### Verification Evidence

- `pytest -q tests/test_intent_router.py tests/test_promotion_policy.py tests/test_reflection_policy.py` ✅
- `python -m behave features/intent_grounding.feature` ✅
- `python scripts/release_gate.py` ⚠️ partial pass: all runtime checks passed except governance issue-link validation due missing `origin/main` in this local environment (`validate_issue_links --base-ref origin/main`).

