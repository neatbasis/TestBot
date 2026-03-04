# ISSUE-0002: Repeated reminders to install `behave` and dev dependencies

- **ID:** ISSUE-0002
- **Title:** Repeated reminders to install `behave` and dev dependencies
- **Status:** open
- **Severity:** amber
- **Owner:** unassigned
- **Created:** 2026-03-04
- **Target Sprint:** Sprint 1
- **Principle Alignment:** deterministic, ci-enforced, user-centric

## Problem Statement

Developers repeatedly attempt to run BDD tests without installing dev dependencies and require manual reminders.

## Evidence

- `behave` is defined under optional `dev` dependencies in `pyproject.toml`.
- README quickstart install command only lists runtime dependencies and does not provide `.[dev]` install guidance.
- Project policy expects `behave` as mandatory for BDD workflow.

## Impact

- Onboarding friction and lost time.
- Inconsistent local test environments.
- Increased false-negative test setup failures.

## Acceptance Criteria

1. Quickstart includes explicit dev install path (e.g., `pip install -e ".[dev]"`).
2. Testing section references the dev install prerequisite before running `behave`.
3. New contributor can run `behave` after following docs with no manual reminders.
4. One reproducible setup command is documented and used in team guidance.

## Work Plan

- Update README quickstart with runtime and developer paths.
- Add explicit pre-test setup checklist.
- Validate by fresh environment install run.

## Verification

- Execute documented commands in clean venv.
- Confirm `behave --version` succeeds.

## Closure Notes

- _Pending documentation update and verification._

