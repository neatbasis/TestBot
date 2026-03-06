# ISSUE-0007: Behave gate not enforced in PR validation

- **ID:** ISSUE-0007
- **Title:** Behave gate not enforced in PR validation
- **Status:** closed
- **Severity:** green
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
2. Canonical gate scripts fail fast if `behave` is unavailable and always include mandatory `python -m behave` execution in blocking checks.
3. Risk-assessment notes must explicitly state when `behave`/`behat` was not run and why, with remediation steps.

## Work Plan

- Add issue record and red-tag tracking for enforcement gap.
- Update affected tests and rerun `behave` after installing dev dependencies.
- Propose a CI check that fails when `behave` is unavailable or not executed.

## Verification

- Command: `python -m pip install -e .[dev]`
  - Expected: exits `0` and installs `behave`.
- Command: `python -m behave`
  - Expected: executes feature suite and reports pass/fail scenarios.
- Command: `behave --tags=@fast`
  - Expected: executes fast contract suite with non-zero exit on regressions.

## Closure Notes

- 2026-03-06: Closed after enforcing fail-fast BDD preflight in both `scripts/all_green_gate.py` and `scripts/release_gate.py`.
- Gate execution now blocks immediately when `behave` is missing with explicit remediation: `python -m pip install -e .[dev]`.
- Deterministic regression tests were added to prove missing `behave` causes a blocking failure before other checks execute.
- README and testing workflow continue to require `pip install -e .[dev]` before running canonical gate commands.
