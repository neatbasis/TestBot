# ISSUE-0020: Deprecate `SOURCE_INGEST_ENABLED` toggle requirement in quickstart source-ingestion flow

- **ID:** ISSUE-0020
- **Title:** Deprecate `SOURCE_INGEST_ENABLED` toggle requirement in quickstart source-ingestion flow
- **Status:** open
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

- [Blocked] Align runtime contract decision with ISSUE-0018/ISSUE-0019 orchestration expectations (blocked by unresolved scheduler/engine ownership boundaries in ISSUE-0018 and ISSUE-0019).
- [Not Started] Implement ingestion-enable semantics with backward-compatible warning window.
- [Not Started] Update quickstart source-ingestion section to remove mandatory `SOURCE_INGEST_ENABLED=1` from canonical examples.
- [Not Started] Add deterministic tests covering implicit enablement and explicit disable override.
- [In Progress] Run governance validators now; run canonical gate in implementation PR once dependency decisions are merged.

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

## Closure Notes

- 2026-03-10: Opened after adding live-smoke + deterministic source-ingestion runtime coverage demonstrating current behavior and identifying quickstart env-toggle deprecation opportunity.
