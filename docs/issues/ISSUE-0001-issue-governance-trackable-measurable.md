# ISSUE-0001: Establish measurable and trackable in-repo issue governance

- **ID:** ISSUE-0001
- **Title:** Establish measurable and trackable in-repo issue governance
- **Status:** open
- **Severity:** red
- **Owner:** unassigned
- **Created:** 2026-03-04
- **Target Sprint:** Sprint 1
- **Principle Alignment:** contract-first, invariant-driven, traceable, ci-enforced

## Problem Statement

The project lacks a canonical, measurable, and auditable issue workflow inside the repository. This creates inconsistent problem tracking and weakens governance traceability.

## Evidence

- No existing `docs/issues.md` policy before this issue set.
- No canonical issue schema for measurable acceptance criteria.
- No red-tag escalation area to surface critical process risks.

## Impact

- Reduced visibility of critical risks and unresolved blockers.
- Inconsistent issue quality and closure criteria across contributors.
- Harder to audit whether project principles are being upheld.

## Acceptance Criteria

1. `docs/issues.md` exists with a canonical workflow and required issue fields.
2. `docs/issues/RED_TAG.md` exists and indexes active red-tag issues.
3. At least two exemplar issues exist in `docs/issues/` using canonical schema.
4. Issue lifecycle and severity policy are explicit and reviewable in-repo.

## Work Plan

- Create workflow policy file.
- Create red-tag index file.
- Seed issue backlog with priority issues and measurable criteria.

## Verification

- Confirm required files exist and contain required sections.
- Verify issue files are named and structured per policy.

## Closure Notes

- _Pending implementation and review._

