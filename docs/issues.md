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

Issue files support two governance states:

### 1) `triage_intake` (minimal intake schema)

Use this only for rapid intake when the issue has not yet been accepted into active execution planning.

Required fields:

1. `ID`
2. `Title`
3. `Problem`
4. `Owner`
5. `Severity`
6. `Next Action`

SLA and transition rule:

- Any issue in `triage_intake` MUST be promoted to `governed_execution` **before** `Status` moves to `in_progress`.
- `triage_intake` is therefore valid only while `Status: open`.

### 2) `governed_execution` (full canonical schema)

Every issue file in `governed_execution` MUST include the following sections:

1. `ID`
2. `Title`
3. `Status` (`open`, `in_progress`, `blocked`, `resolved`, `closed`)
4. `Issue State` (`triage_intake`, `governed_execution`)
5. `Severity` (`red`, `amber`, `green`)
6. `Owner`
7. `Created`
8. `Target Sprint`
9. `Principle Alignment`
10. `Problem Statement`
11. `Evidence`
12. `Impact`
13. `Acceptance Criteria` (measurable)
14. `Work Plan`
15. `Verification`
16. `Closure Notes`

Recommended metadata extension for linked issue streams:

- `Canonical Cross-Reference` (optional but recommended when linked planning/implementation issues exist; use issue filename, e.g., `ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`).


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

Red-Tag index generation flow:

- Treat `docs/issues/ISSUE-*.md` files as the source of truth.
- Do not hand-edit `docs/issues/RED_TAG.md`.
- Regenerate the index after issue status/severity updates:

  ```bash
  python scripts/generate_red_tag_index.py
  ```

- Validation compares committed `docs/issues/RED_TAG.md` to generated output and fails only when they differ.

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

## Mandatory duplicate-prevention pre-check

Before creating any new issue record, contributors MUST review the current feature status report to avoid opening multiple tickets for the same underlying capability gap.

Required pre-check sequence:

1. Regenerate the report from current gate/issues/roadmap evidence:

   ```bash
   python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json
   ```

2. Review `docs/qa/feature-status-report.md` and verify whether an existing open issue already covers the underlying failure signal.
3. Create a new issue only when no existing open issue in the report captures that root cause; otherwise update the existing issue instead of filing a duplicate.

Rationale: `scripts/report_feature_status.py` computes capability status from the contract (`docs/qa/feature-status.yaml`), gate results (`artifacts/all-green-gate-summary.json`), open issue records (`docs/issues/*.md` with open-like statuses), and roadmap priority references. This provides the authoritative duplicate-check surface before issue creation.

Current canonical pipeline triage note: [`ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md) is the project's **primary bug-elimination program** in the current state; contributors should triage canonical pipeline defects and follow-on work against ISSUE-0013 first, with ISSUE-0012 treated as linked delivery planning context. ISSUE-0013 may be non-red while still serving as the canonical triage anchor; red-tag visibility remains governed solely by each issue file's current `Severity: red` declaration and `docs/issues/RED_TAG.md` indexing rules.

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

## Governance validator base-ref fallback workflow

When running governance validators from shallow or detached environments, use this supported flow:

1. Run validators with default base ref (`origin/main`).
2. If `origin/main` is unavailable, validators automatically fall back to `HEAD~1`, then `HEAD`.
3. In fallback mode, warnings are intentionally explicit (Codex/shallow-clone expected behavior, reduced diff baseline, and `git fetch origin main` guidance) to avoid false-alarm triage.
4. For explicit control, pass `--base-ref <ref>`.

Canonical commands:

```bash
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
python scripts/validate_issues.py --all-issue-files --base-ref origin/main
```

If needed, force an explicit detached-friendly base ref:

```bash
python scripts/validate_issue_links.py --all-issue-files --base-ref HEAD~1
python scripts/validate_issues.py --all-issue-files --base-ref HEAD~1
```

## Governance note: transition-log schema cutovers

When issue work changes `stage_transition_validation` schema (for example removing compatibility keys like `legacy_stage`), include in issue/PR metadata: the schema version bump, expected consumer migration target (`stage` canonical identifiers), and a compatibility window statement describing which older schema versions remain readable.
