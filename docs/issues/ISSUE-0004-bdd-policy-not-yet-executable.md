# ISSUE-0004: BDD policy declared but not executable in repository

- **ID:** ISSUE-0004
- **Title:** BDD policy declared but not executable in repository
- **Status:** resolved
- **Severity:** red
- **Owner:** testbot-maintainers
- **Created:** 2026-03-04
- **Target Sprint:** Sprint 2
- **Principle Alignment:** contract-first, ci-enforced, traceable

## Problem Statement

Resolved. The repository now contains executable baseline BDD features and step definitions for the current v0 behavior contracts.

## Evidence

- `features/` exists with baseline scenarios in `memory_recall.feature` and `answer_contract.feature`.
- `features/steps/` contains deterministic step definitions in `memory_steps.py` and `answer_contract_steps.py`.
- README Validate section and docs/testing include `behave` command guidance.
- Local `behave` run passes all scenarios.

## Impact

- Policy-to-practice gap closed.
- BDD compliance is now locally verifiable and CI-ready.

## Acceptance Criteria

1. ✅ `features/` directory exists with baseline feature scenarios.
2. ✅ `features/steps/` contains deterministic step definitions for v0 contracts.
3. ✅ `behave` command runs and reports scenario results locally.
4. ✅ CI/local check docs specify BDD execution command.

## Work Plan

- Maintain feature/step coverage as acceptance contract source-of-truth.
- Extend scenarios as new stakeholder-visible behavior is introduced.

## Verification

- Command: `behave`
  - Expected: exits `0`; all scenarios and steps pass; no undefined steps.
- Command: `rg --files features`
  - Expected: lists baseline feature files and step definition modules.

## Closure Notes

- 2026-03-04: Closed as resolved; BDD artifacts are present and executable with passing local run.
- Residual risk: medium-low; contract drift can recur if runtime behavior changes without companion feature updates.
