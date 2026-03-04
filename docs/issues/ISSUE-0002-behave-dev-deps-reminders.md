# ISSUE-0002: Repeated reminders to install `behave` and dev dependencies

- **ID:** ISSUE-0002
- **Title:** Repeated reminders to install `behave` and dev dependencies
- **Status:** closed
- **Severity:** amber
- **Owner:** unassigned
- **Created:** 2026-03-04
- **Target Sprint:** Sprint 1
- **Principle Alignment:** deterministic, ci-enforced, user-centric

## Problem Statement

README now includes the `.[dev]` install command, but it is still framed as optional while `behave` is listed in the standard validation commands. The remaining gap is to make the BDD dependency requirement explicit at point-of-use so first-time contributors do not infer runtime-only setup is sufficient.

## Evidence

- README Setup includes `pip install -e .[dev]` and notes that `behave` is installed via the `dev` extra.
- README Validate now annotates the `behave` command with an inline prerequisite: requires `pip install -e .[dev]` first.
- `docs/testing.md` mirrors the same prerequisite callout in both the canonical commands table and the BDD command snippet.
- `pyproject.toml` keeps `behave` in `[project.optional-dependencies].dev`, and docs now align setup plus point-of-use guidance.

## Impact

- Onboarding friction and lost time.
- Inconsistent local test environments.
- Increased false-negative test setup failures.

## Acceptance Criteria

1. README explicitly states that running `behave` requires `pip install -e .[dev]` (or equivalent) before test execution.
2. README Validate section includes an inline prerequisite note adjacent to the `behave` command.
3. A new contributor following README alone can determine the exact install command needed to run BDD with no external reminder.

## Work Plan

- Update README wording so `behave` prerequisites are explicit where test commands are listed.
- Keep one canonical install command for developer test tooling.

## Verification

- Command: `python -m pip install -e .[dev]`
  - Expected: exits `0`; installs `behave` and other dev tools.
- Command: `behave --version`
  - Expected: exits `0`; prints Behave version.
- Command: `behave`
  - Expected: exits `0`; all scenarios pass with no undefined steps.

## Closure Notes

- 2026-03-04: Closed by adding explicit point-of-use prerequisites where `behave` appears as a canonical validation command.
- README Validate now annotates `behave` with the inline prerequisite text: requires `pip install -e .[dev]` first.
- `docs/testing.md` mirrors the same prerequisite near canonical `behave` command snippets, reducing split guidance between setup and execution docs.
- Residual risk reduced: contributors can now infer the required install command from both setup and command invocation contexts.
