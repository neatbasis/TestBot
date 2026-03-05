# ISSUE-0007: Behave gate not enforced in PR validation

- **ID:** ISSUE-0007
- **Title:** Behave gate not enforced in PR validation
- **Status:** open
- **Severity:** red
- **Owner:** platform-qa
- **Created:** 2026-03-04
- **Target Sprint:** Sprint 1
- **Principle Alignment:** ci-enforced, deterministic, traceable

## Problem Statement

The repository policy expects BDD coverage to be validated with `behave`, but prior PR validation skipped executable BDD because the environment did not have dev dependencies installed. This left policy compliance to contributor discretion and allowed a behavior regression to pass code review without the mandatory gate.

## Evidence

- Prior PR reported `python -m behave features/answer_contract.feature` could not run due to `No module named behave`.
- In this follow-up, installing dev dependencies (`python -m pip install -e .[dev]`) made `behave` available and running `behave` exposed a failing scenario (`provenance_present_for_non_trivial_answers` in `features/memory_recall.feature`).
- This demonstrates that missing gate execution can hide contract regressions and degrade groundedness assurance.

## Impact

- Invariant regressions can merge undetected when BDD is not executed.
- Groundedness/contract confidence is overstated if test reporting omits missing mandatory gates.
- Risk assessment is weakened because failures are discovered late instead of at PR time.

## Acceptance Criteria

1. PR validation docs explicitly require installation of dev dependencies before invoking `behave`.
2. CI or local gating guidance requires a non-skipped `behave` run as part of acceptance evidence.
3. Risk-assessment notes must explicitly state when `behave`/`behat` was not run and why, with remediation steps.

## Work Plan

- Add issue record and red-tag tracking for enforcement gap.
- Update affected tests and rerun `behave` after installing dev dependencies.
- Propose a CI check that fails when `behave` is unavailable or not executed.

## Verification

- Command: `python -m pip install -e .[dev]`
  - Expected: exits `0` and installs `behave`.
- Command: `behave`
  - Expected: executes feature suite and reports pass/fail scenarios.
- Command: `behave --tags=@fast`
  - Expected: executes fast contract suite with non-zero exit on regressions.

## Closure Notes

- Opened to track mandatory-gate enforcement risk after observing that `behave` was not used in prior PR testing and a regression was subsequently detected once dependencies were installed.
