# ISSUE-0007: Governance readiness gate traceability is partial for capability-linked issue enforcement

- **ID:** ISSUE-0007
- **Title:** Governance readiness gate traceability is partial for capability-linked issue enforcement
- **Status:** resolved
- **Issue State:** governed_execution
- **Severity:** red
- **Owner:** platform-qa
- **Created:** 2026-03-04
- **Target Sprint:** Sprint 2
- **Principle Alignment:** ci-enforced, deterministic, traceable, contract-first

## Problem Statement

`governance_readiness_gate` remains `partial`. Although behave preflight is enforced, capability status reporting does not reliably surface open issue linkage for partial capabilities unless explicit keywords are maintained. This creates a governance traceability gap where partial risk can appear untracked in generated QA artifacts.

## Evidence

- `docs/qa/feature-status.yaml` currently marks `governance_readiness_gate` as `partial`.
- Generated summaries can show `open_issue_count: 0` while multiple capabilities are partial if issue linkage metadata is missing/weak.
- The capability relies on governance checks (`qa_validate_issue_links`, `qa_validate_issues`, `qa_validate_invariant_sync`, `qa_validate_markdown_paths`) and should include explicit issue traceability.

## Impact

- Audit consumers may incorrectly infer no active governance debt.
- Merge readiness confidence is overstated when partial capabilities are not tied to active issue records.
- Red-tag triage can miss active governance risk without explicit index updates.

## Acceptance Criteria

1. `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json` shows at least one linked open issue for `governance_readiness_gate` while the capability remains partial.
2. `python scripts/validate_issue_links.py --all-issue-files --base-ref HEAD~1` passes with no missing issue-link validation failures.
3. `python scripts/validate_issues.py --all-issue-files --base-ref HEAD~1` passes with no canonical schema failures.
4. `docs/issues/RED_TAG.md` is synchronized with canonical issue state, and ISSUE-0007 is listed under Resolved red-tag issues with closure evidence.

## Work Plan

- Maintain explicit capability-to-issue linkage metadata in `docs/qa/feature-status.yaml`.
- Keep issue index and red-tag state synchronized with issue severity and status updates.
- Add deterministic regression coverage for feature-status report linkage resolution if not already present.
- **Rollback/Escalation Trigger:** If generated artifacts (for example, `artifacts/feature-status-summary.json` or `docs/qa/feature-status-report.md`) show `governance_readiness_gate` as `partial` while linked open issue reporting is missing or `open_issue_count` is inconsistent with active partial capability risk (“partial capability linkage not surfaced in generated artifacts”), treat as an active Red-Tag escalation condition.
- **Immediate Mitigation Action:** Immediately halt merge/readiness progression for affected changes, update `docs/issues/RED_TAG.md` to keep ISSUE-0007 visible as active, and rerun `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json` plus governance validators to restore auditable linkage before resuming.
- **Owner / Response Window:** `platform-qa` is the accountable owner and must acknowledge and start mitigation within **1 business day** of trigger detection, with status/evidence updates recorded in issue artifacts for reviewer verification.

## Verification

- Command: `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json`
  - Expected: capability-level open issue linkage appears for governance readiness capability.
- Command: `python scripts/validate_issue_links.py --all-issue-files --base-ref HEAD~1`
  - Expected: exits `0`.
- Command: `python scripts/validate_issues.py --all-issue-files --base-ref HEAD~1`
  - Expected: exits `0`.

## Closure Notes

- 2026-03-06: Original behave-enforcement scope closed.
- 2026-03-06: Reopened/rescoped as active red-tag governance traceability gap for capability-linked issue surfacing.
- 2026-03-06: Closed after regenerating feature-status artifacts, validating deterministic linkage coverage, and passing issue validators under base-ref fallback behavior.
