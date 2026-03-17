# ISSUE-0022: Test issue for hook bypass

- **ID:** ISSUE-0022
- **Title:** Test issue for hook bypass
- **Status:** open
- **Issue State:** governed_execution
- **Severity:** green
- **Owner:** governance
- **Created:** 2026-03-17
- **Target Sprint:** Sprint 6
- **Principle Alignment:** traceable, deterministic

## Problem Statement

A disposable test issue is needed to verify that local commits are no longer blocked by issue-validation pre-commit hooks while governance tooling changes are under development.

## Evidence

- Local pre-commit configuration currently includes issue governance hooks tied to `docs/issues/` path changes.
- Contributors need a safe fixture issue file to exercise docs/issues workflows after hook disablement.

## Impact

- Confirms development flow for issue drafting is unblocked.
- Provides a concrete sample issue for validating non-blocking local governance iteration.

## Acceptance Criteria

- [ ] `.pre-commit-config.yaml` no longer runs `validate_issue_links` and `validate_issues` hooks.
- [ ] A new issue file exists under `docs/issues/` and follows canonical governed-execution schema.

## Work Plan

1. Remove issue-governance hook entries from local pre-commit configuration.
2. Add this test issue record as a fixture for follow-up verification.
3. Keep status open until the temporary workflow objective is complete.

## Verification

```bash
pre-commit run --all-files
python scripts/validate_issues.py --all-issue-files --base-ref HEAD~1
```

## Closure Notes

Pending.
