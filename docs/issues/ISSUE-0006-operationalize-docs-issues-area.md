# ISSUE-0006: Operationalize `docs/issues/` and `docs/issues.md` as governed project infrastructure

- **ID:** ISSUE-0006
- **Title:** Operationalize `docs/issues/` and `docs/issues.md` as governed project infrastructure
- **Status:** resolved
- **Severity:** red
- **Owner:** Sebastian Mäki (@NeatBasis, Release Manager & Process Adoption Lead)
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

### Sprint milestones

- **Sprint 1 (Process adoption kickoff):** Sebastian Mäki (@NeatBasis, Release Manager & Process Adoption Lead) updates contributor-facing docs to reference `docs/issues.md` as the canonical workflow.
- **Sprint 1 (PR enforcement):** Sebastian Mäki (@NeatBasis, Engineering Manager & Docs Governance Lead) adds explicit issue-linking expectations in PR guidance and review checklists.
- **Sprint 2 (Operational cadence):** Sebastian Mäki (@NeatBasis, Quality Lead) runs recurring sprint triage for `severity: red` items and publishes evidence artifacts under `docs/issues/evidence/`.

### Execution tasks

- Add discoverability links from README.
- Integrate issue-link expectation into contribution guidance.
- Triage open issues by severity and sprint.

## Verification

- Confirm docs links and references are present.
- Confirm issue IDs appear in subsequent PR descriptions.

## Closure Notes

- Resolved by operationalizing validator-backed adoption checks in the merge gate and contributor/testing docs so governance evidence format matches enforced commands and failure modes.

