# ISSUE-0020: Deprecate `SOURCE_INGEST_ENABLED` toggle requirement in quickstart source-ingestion flow

- **ID:** ISSUE-0020
- **Title:** Deprecate `SOURCE_INGEST_ENABLED` toggle requirement in quickstart source-ingestion flow
- **Status:** open
- **Issue State:** governed_execution
- **Severity:** amber
- **Owner:** runtime-pipeline
- **Created:** 2026-03-10
- **Target Sprint:** Sprint 8
- **Canonical Cross-Reference:** ISSUE-0018 (dual-trigger source ingestion lifecycle), ISSUE-0019 (channel-agnostic orchestration), ISSUE-0013 (canonical pipeline bug-elimination program)
- **Principle Alignment:** user-centric, contract-first, deterministic, traceable

## Problem Statement

Current source-ingestion quickstart examples require explicit command-time opt-in using `SOURCE_INGEST_ENABLED=1` for every connector invocation. This extra toggle increases operator friction and creates an avoidable mismatch between connector intent (`SOURCE_CONNECTOR_TYPE`, connector-specific parameters) and actual behavior (ingestion disabled unless another environment variable is set).

Live-smoke and deterministic runtime-pipeline validation now confirm that source ingestion can complete and that resulting turns produce non-empty answers with provenance contract fields in session logs for both live Wikipedia and fixture connector flows. The remaining product/documentation gap is the command ergonomics requirement itself.

## Evidence

- Live-smoke runtime e2e now includes an opt-in Wikipedia ingestion turn (`Hilbert space`) and asserts `source_ingest_completed` plus `final_answer_mode` provenance fields.
- Deterministic runtime test now validates the same startup-ingestion + one-turn answer flow using the fixture connector, avoiding internet dependency.
- `docs/quickstart.md` source-ingestion examples currently encode the repeated `SOURCE_INGEST_ENABLED=1` precondition, which is a candidate for deprecation once default/implicit enablement semantics are agreed.

## Impact

- Operators can misconfigure connector commands by forgetting the extra env toggle.
- Documentation complexity is higher than needed for first-run ingestion workflows.
- Runtime behavior appears less intuitive: connector selection does not imply ingestion intent.

## Acceptance Criteria

1. Decide and document deprecation strategy for `SOURCE_INGEST_ENABLED` in source-ingestion quickstart examples.
2. Implement one of the following runtime contracts:
   - connector-type presence implies ingestion enabled by default, or
   - startup flow auto-enables ingestion when connector-specific required fields are present.
3. Preserve deterministic opt-out path for operators who explicitly want ingestion disabled.
4. Update `docs/quickstart.md` source-ingestion examples to the new command flow.
5. Add/adjust tests that verify both enabling and explicit opt-out behavior.
6. Validate governance link integrity for the new issue and any related documentation changes.

## Work Plan

- [ ] **ISSUE-0020-WP1 (target 2026-03-20):** Ratify deprecation contract for `SOURCE_INGEST_ENABLED` after ISSUE-0018 lifecycle + ISSUE-0019 engine decisions are merged.
  **Depends on:** ISSUE-0018-WP4, ISSUE-0019-WP3.
- [ ] **ISSUE-0020-WP2 (target 2026-03-20):** Implement implicit-ingestion enablement when connector intent is present, with explicit disable override and warning window.
  **Depends on:** ISSUE-0020-WP1.
- [ ] **ISSUE-0020-WP3 (target 2026-03-21):** Update quickstart/source-ingestion docs to remove mandatory `SOURCE_INGEST_ENABLED=1` from canonical commands and add migration note.
  **Depends on:** ISSUE-0020-WP2.
- [ ] **ISSUE-0020-WP4 (target 2026-03-21):** Add deterministic tests for implicit enablement + explicit opt-out across fixture connector and runtime pipeline paths.
  **Depends on:** ISSUE-0020-WP2.
- [ ] **ISSUE-0020-WP5 (target 2026-03-21):** Run governance validators and canonical gate for implementation PR and publish closure evidence.
  **Depends on:** ISSUE-0020-WP3, ISSUE-0020-WP4.

## Current State (2026-03-14)

- **Scope:** convert ingestion quickstart from toggle-heavy ergonomics to connector-intent-driven defaults without losing explicit opt-out control.
- **Owner:** runtime-pipeline.
- **Blocker:** awaiting ISSUE-0018 and ISSUE-0019 contract decisions that define lifecycle timing and engine ownership assumptions.
- **Next Action:** draft deprecation contract text and warning strategy template so ISSUE-0020-WP1 can be finalized immediately after upstream decisions land.

## Cross-Issue Dependency Map

- **Depends on ISSUE-0018:** ISSUE-0018-WP4 defines proactive completion lifecycle semantics referenced by the quickstart behavior contract.
- **Depends on ISSUE-0019:** ISSUE-0019-WP3 defines shared engine/history behavior needed to ensure default-ingestion semantics are channel-neutral.
- **Feeds back to ISSUE-0018/0019:** ISSUE-0020 docs and runtime toggles provide operator-facing validation that lifecycle and engine contracts are usable in canonical startup flows.

## Triage Notes

- **2026-03-14:** **Phase:** blocked. **Immediate next owner action:** consume ISSUE-0018/ISSUE-0019 architecture decisions, then draft concrete deprecation contract and migration warning copy for review. **Target review date:** 2026-03-21.


## Verification

Planned verification bundle:

```bash
python -m pytest tests/test_source_ingestion_runtime_pipeline.py
python -m pytest tests/test_live_smoke_runtime_e2e.py -k wikipedia_source_ingest --maxfail=1
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
python scripts/validate_issues.py --all-issue-files --base-ref origin/main
python scripts/all_green_gate.py
```

Governance-validation artifacts (current branch triage run):
- `artifacts/issue-triage-2026-03-14/validate_issue_links.txt`
- `artifacts/issue-triage-2026-03-14/validate_issues.txt`

Next verification artifact expected for this issue:
- `artifacts/issue-0020/2026-03-21/source-ingestion-toggle-deprecation-validation.md`

## Closure Notes

- 2026-03-10: Opened after adding live-smoke + deterministic source-ingestion runtime coverage demonstrating current behavior and identifying quickstart env-toggle deprecation opportunity.
