# Canonical Issue Workflow (Project-Local)

> **Status:** Active standard until reviewed.
>
> This workflow is now the default project standard for creating, tracking, prioritizing, and closing issues **inside the repository**.

## Purpose

This project tracks issues in-repo to keep governance, implementation context, and evidence in one auditable place.

## Scope

- Applies to all engineering, documentation, testing, and process issues.
- Applies to all contributors opening or updating issues.
- Applies to work discovered during coding, review, testing, and operations.

## Issue locations

- **Workflow and policy:** `docs/issues.md`
- **Issue records:** `docs/issues/*.md`
- **Issue IDs:** `ISSUE-XXXX` (zero-padded, monotonically increasing)

## Canonical issue record format

Every issue file MUST include the following sections:

1. `ID`
2. `Title`
3. `Status` (`open`, `in_progress`, `blocked`, `resolved`, `closed`)
4. `Severity` (`red`, `amber`, `green`)
5. `Owner`
6. `Created`
7. `Target Sprint`
8. `Principle Alignment`
9. `Problem Statement`
10. `Evidence`
11. `Impact`
12. `Acceptance Criteria` (measurable)
13. `Work Plan`
14. `Verification`
15. `Closure Notes`

## Severity and Red-Tag area

A **Red-Tag** issue is any issue with severity `red` and one or more of:

- Contract/invariant violation risk
- Safety or correctness regression risk
- Inability to run mandatory quality gates
- Traceability/auditability breakage

Red-Tag handling requirements:

- Must be visible in `docs/issues/RED_TAG.md`
- Must have an owner and target sprint before merge of related changes
- Must include explicit rollback/mitigation in `Work Plan`

## Measurability standards

Each issue must define metrics where relevant, for example:

- Reproduction rate (`x/y` runs)
- Time-to-detect / time-to-fix
- Gate pass rate
- Count of affected contributors
- Documentation coverage completeness

Acceptance criteria must be binary/verifiable (pass/fail) and reference concrete commands or file updates.

## Workflow lifecycle

1. **Capture** issue in `docs/issues/` with canonical fields.
2. **Classify** severity + principle alignment.
3. **Prioritize** in sprint planning, including a **red-tag review checkpoint** with evidence captured in `docs/issues/evidence/sprint-<NN>-red-tag-review.md`.
4. **Execute** with linked commits.
5. **Verify** against acceptance criteria.
6. **Close** with evidence and residual risk note.

## Principle alignment taxonomy

Use one or more tags:

- `contract-first`
- `invariant-driven`
- `traceable`
- `deterministic`
- `ci-enforced`
- `ontology-aware`
- `user-centric`

## Pull request requirements

PRs that address an issue must include:

- `Issue:` reference (e.g., `Issue: ISSUE-0002`)
- Summary of acceptance criteria addressed
- Verification commands and outcomes
- Updated issue `Status`

## File naming convention

Use: `docs/issues/ISSUE-XXXX-short-kebab-title.md`

Example:

- `docs/issues/ISSUE-0002-behave-dev-deps-reminders.md`

