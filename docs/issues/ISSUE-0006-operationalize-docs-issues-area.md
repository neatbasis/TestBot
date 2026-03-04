# ISSUE-0006: Operationalize `docs/issues/` and `docs/issues.md` as governed project infrastructure

- **ID:** ISSUE-0006
- **Title:** Operationalize `docs/issues/` and `docs/issues.md` as governed project infrastructure
- **Status:** open
- **Severity:** red
- **Owner:** unassigned
- **Created:** 2026-03-04
- **Target Sprint:** Sprint 1
- **Principle Alignment:** contract-first, traceable, ci-enforced

## Problem Statement

A new in-repo issue system was introduced and must be formalized to avoid becoming informal documentation without consistent usage.

## Evidence

- New files `docs/issues.md` and `docs/issues/RED_TAG.md` now define process and escalation.
- No existing enforcement mechanism ensures contributors use this system yet.

## Impact

- Without explicit adoption rules, issues may fragment across ad-hoc channels.
- Governance intent may not produce measurable project behavior.

## Acceptance Criteria

1. README references `docs/issues.md` as canonical issue workflow.
2. PR guidance requires linking issue IDs for non-trivial changes.
3. Red-tag process (`docs/issues/RED_TAG.md`) is acknowledged in sprint planning notes.
4. First sprint includes explicit triage of seeded issues.

## Work Plan

- Add discoverability links from README.
- Integrate issue-link expectation into contribution guidance.
- Triage open issues by severity and sprint.

## Verification

- Confirm docs links and references are present.
- Confirm issue IDs appear in subsequent PR descriptions.

## Closure Notes

- _Pending adoption._

