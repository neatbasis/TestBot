# ISSUE-0004: BDD policy declared but not executable in repository

- **ID:** ISSUE-0004
- **Title:** BDD policy declared but not executable in repository
- **Status:** open
- **Severity:** red
- **Owner:** unassigned
- **Created:** 2026-03-04
- **Target Sprint:** Sprint 2
- **Principle Alignment:** contract-first, ci-enforced, traceable

## Problem Statement

The documentation declares BDD (`behave`) as required, but the repo lacks baseline `.feature` files and step definitions.

## Evidence

- README defines BDD as required and suggests `features/` structure.
- Current repository has no `features/` directory or step definition implementation.

## Impact

- Policy-to-practice gap.
- BDD compliance cannot be validated in CI.

## Acceptance Criteria

1. `features/` directory exists with baseline feature scenarios.
2. `features/steps/` contains deterministic step definitions for v0 contracts.
3. `behave` command runs and reports scenario results locally.
4. CI/local check docs specify BDD execution command.

## Work Plan

- Add baseline feature files for core contracts.
- Add step definitions and deterministic fixtures.
- Document command and expected result.

## Verification

- Run `behave` and capture pass/fail output.

## Closure Notes

- _Pending implementation._

