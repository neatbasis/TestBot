# Documentation Governance Follow-up Audit — Structural Honesty (2026-03-21)

## 1. Scope accounting

This continuation pass uses `docs/architecture/documentation-governance-audit-2026-03-21.md` as the anchor backlog source. Scope was selected from the anchor out-of-scope list after subtracting files already audited in the earlier follow-up pass.

- Total Markdown files currently in repo: **108**.
- Anchor out-of-scope backlog size (from 2026-03-21 anchor audit): **96**.
- Files already audited before this pass: **20** (11 anchor in-scope + 9 prior follow-up selections).
- Newly selected files audited in this pass: **5**.
- Remaining anchor-backlog files not yet audited after this pass: **82**.

Repository-change accounting versus anchor backlog:
- Added Markdown not in anchor scope/backlog: `['docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md']` (excluded from anchor-backlog accounting).
- Removed/renamed files from anchor backlog: `[]`.

Non-Markdown enforcement artifacts reviewed for evidence in this pass:
- `scripts/all_green_gate.py`
- `scripts/validate_pipeline_stage_conformance.py`
- `scripts/validate_invariant_sync.py`
- `scripts/architecture_boundary_report.py`

Prior audit scope reconstruction was **not required** (the anchor audit explicitly listed in-scope and out-of-scope Markdown).

### 1.1 Previously audited Markdown files

- `plan.md`
- `docs/pivot.md`
- `docs/architecture/plan-execution-checklist.md`
- `docs/architecture/architecture-governance-audit-2026-03-20.md`
- `docs/testing.md`
- `docs/issues.md`
- `docs/issues/governance-control-surface-contract-freeze.md`
- `docs/architecture-boundaries.md`
- `CONTRIBUTING.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `docs/architecture.md`
- `README.md`
- `docs/invariants.md`
- `docs/directives/CHANGE_POLICY.md`
- `docs/directives/decision-policy.md`
- `docs/directives/invariants.md`
- `docs/directives/product-principles.md`
- `docs/directives/traceability-matrix.md`
- `docs/quickstart.md`
- `docs/terminology.md`

### 1.2 Candidate remaining Markdown files

- `AGENTS.md`
- `CHANGELOG.md`
- `artifacts/architecture-boundary-report.current.md`
- `docs/architecture/behavior-governance.md`
- `docs/architecture/canonical-turn-pipeline.md`
- `docs/architecture/commit-drift-audit-2026-03-19.md`
- `docs/architecture/documentation-governance-audit-2026-03-21.md`
- `docs/architecture/system-structure-audit-2026-03-19.md`
- `docs/governance/architecture-drift-register.md`
- `docs/governance/code-review-governance-automation-dependency-boundaries.md`
- `docs/governance/drift-remediation-backlog.md`
- `docs/governance/drift-traceability-matrix.md`
- `docs/governance/issue-implementation-audit.md`
- `docs/governance/mission-vision-alignment.md`
- `docs/governance/python-code-review-checklist-dependency-boundaries.md`
- `docs/invariants/answer-policy.md`
- `docs/invariants/pipeline.md`
- `docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md`
- `docs/issues/ISSUE-0002-behave-dev-deps-reminders.md`
- `docs/issues/ISSUE-0003-readme-layout-drift.md`
- `docs/issues/ISSUE-0004-bdd-policy-not-yet-executable.md`
- `docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md`
- `docs/issues/ISSUE-0006-operationalize-docs-issues-area.md`
- `docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md`
- `docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md`
- `docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md`
- `docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md`
- `docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md`
- `docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`
- `docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`
- `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
- `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md`
- `docs/issues/ISSUE-0016-startup-degraded-mode-bdd-coverage-gap.md`
- `docs/issues/ISSUE-0017-invariant-boundary-ambiguity-answer-commit-regression.md`
- `docs/issues/ISSUE-0018-dual-trigger-event-loop-for-proactive-ingestion-lifecycle.md`
- `docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md`
- `docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md`
- `docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md`
- `docs/issues/RED_TAG.md`
- `docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md`
- `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md`
- `docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md`
- `docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md`
- `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md`
- `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md`
- `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md`
- `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md`
- `docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md`
- `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md`
- `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md`
- `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md`
- `docs/issues/evidence/coordination-failure-contract-drift-matrix.md`
- `docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md`
- `docs/issues/evidence/governance-craap-analysis-main-alignment.md`
- `docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md`
- `docs/issues/evidence/governance-open-questions-audit-2026-03-16.md`
- `docs/issues/evidence/governance-stabilization-checklist.md`
- `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md`
- `docs/issues/evidence/issue-0022-pass-seven-verification-log.md`
- `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md`
- `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md`
- `docs/issues/evidence/open-pr-assessment-2026-03-17.md`
- `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md`
- `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md`
- `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md`
- `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md`
- `docs/issues/evidence/sprint-00-kpi-review.md`
- `docs/issues/evidence/work-history-assessment-2026-03-17.md`
- `docs/ops.md`
- `docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md`
- `docs/qa/feature-status-report.md`
- `docs/qa/live-smoke.md`
- `docs/qa/smoke-evidence-contract.md`
- `docs/regression-progression-audit-8f9317a-to-head.md`
- `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md`
- `docs/roadmap/current-status-and-next-5-priorities.md`
- `docs/roadmap/next-4-sprints-grounded-knowing.md`
- `docs/roadmap/reflective-milestone-10-sprints.md`
- `docs/sessions/ISSUE-0014-cross-functional-session-plan.md`
- `docs/style-guide.md`
- `docs/testing-triage.md`
- `examples/Experiments.md`
- `features/README.md`
- `src/seem_bot/README.md`

### 1.3 Newly selected files for this audit pass

- `artifacts/architecture-boundary-report.current.md`
- `docs/architecture/behavior-governance.md`
- `docs/architecture/canonical-turn-pipeline.md`
- `docs/invariants/answer-policy.md`
- `docs/invariants/pipeline.md`

Selection rationale: this batch is the highest-governance-impact subset in the remaining pool because it covers (a) runtime contract authority (`canonical-turn-pipeline`), (b) invariant canon (`docs/invariants/*`), and (c) an architecture evidence artifact and supporting non-authoritative matrix that can create hidden split authority if they drift.

### 1.4 Remaining files not audited in this pass

- `AGENTS.md`
- `CHANGELOG.md`
- `docs/architecture/commit-drift-audit-2026-03-19.md`
- `docs/architecture/documentation-governance-audit-2026-03-21.md`
- `docs/architecture/system-structure-audit-2026-03-19.md`
- `docs/governance/architecture-drift-register.md`
- `docs/governance/code-review-governance-automation-dependency-boundaries.md`
- `docs/governance/drift-remediation-backlog.md`
- `docs/governance/drift-traceability-matrix.md`
- `docs/governance/issue-implementation-audit.md`
- `docs/governance/mission-vision-alignment.md`
- `docs/governance/python-code-review-checklist-dependency-boundaries.md`
- `docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md`
- `docs/issues/ISSUE-0002-behave-dev-deps-reminders.md`
- `docs/issues/ISSUE-0003-readme-layout-drift.md`
- `docs/issues/ISSUE-0004-bdd-policy-not-yet-executable.md`
- `docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md`
- `docs/issues/ISSUE-0006-operationalize-docs-issues-area.md`
- `docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md`
- `docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md`
- `docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md`
- `docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md`
- `docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md`
- `docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`
- `docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`
- `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
- `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md`
- `docs/issues/ISSUE-0016-startup-degraded-mode-bdd-coverage-gap.md`
- `docs/issues/ISSUE-0017-invariant-boundary-ambiguity-answer-commit-regression.md`
- `docs/issues/ISSUE-0018-dual-trigger-event-loop-for-proactive-ingestion-lifecycle.md`
- `docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md`
- `docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md`
- `docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md`
- `docs/issues/RED_TAG.md`
- `docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md`
- `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md`
- `docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md`
- `docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md`
- `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md`
- `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md`
- `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md`
- `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md`
- `docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md`
- `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md`
- `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md`
- `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md`
- `docs/issues/evidence/coordination-failure-contract-drift-matrix.md`
- `docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md`
- `docs/issues/evidence/governance-craap-analysis-main-alignment.md`
- `docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md`
- `docs/issues/evidence/governance-open-questions-audit-2026-03-16.md`
- `docs/issues/evidence/governance-stabilization-checklist.md`
- `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md`
- `docs/issues/evidence/issue-0022-pass-seven-verification-log.md`
- `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md`
- `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md`
- `docs/issues/evidence/open-pr-assessment-2026-03-17.md`
- `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md`
- `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md`
- `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md`
- `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md`
- `docs/issues/evidence/sprint-00-kpi-review.md`
- `docs/issues/evidence/work-history-assessment-2026-03-17.md`
- `docs/ops.md`
- `docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md`
- `docs/qa/feature-status-report.md`
- `docs/qa/live-smoke.md`
- `docs/qa/smoke-evidence-contract.md`
- `docs/regression-progression-audit-8f9317a-to-head.md`
- `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md`
- `docs/roadmap/current-status-and-next-5-priorities.md`
- `docs/roadmap/next-4-sprints-grounded-knowing.md`
- `docs/roadmap/reflective-milestone-10-sprints.md`
- `docs/sessions/ISSUE-0014-cross-functional-session-plan.md`
- `docs/style-guide.md`
- `docs/testing-triage.md`
- `examples/Experiments.md`
- `features/README.md`
- `src/seem_bot/README.md`

## 2. Scope selection rationale

These five files were chosen ahead of the other remaining files because they reduce the highest-value unknowns about architectural truth and executable governance binding:

1. `docs/architecture/canonical-turn-pipeline.md` is repeatedly linked from README/architecture/testing as runtime contract authority; auditing it resolves whether declared authority matches enforcement.
2. `docs/invariants/answer-policy.md` and `docs/invariants/pipeline.md` define canonical invariant IDs that are supposed to map to runtime checks/tests; auditing them reduces uncertainty around ID-to-enforcement integrity.
3. `artifacts/architecture-boundary-report.current.md` is produced evidence that influences remediation decisions; auditing clarifies whether it is operational evidence, transitional report, or stale decorative output.
4. `docs/architecture/behavior-governance.md` explicitly labels itself non-authoritative but is linked from README; auditing verifies whether practice follows that label or if it behaves as shadow authority.

This selection reduces uncertainty about: (a) contract source-of-truth, (b) invariant enforcement realism, and (c) evidence-artifact authority boundaries.

## 3. Executive summary

After this continuation pass, **25 of 96 anchor-backlog Markdown files (26.0%)** are audited for documentation-governance role. The newly selected documents that materially affect governance clarity are `docs/architecture/canonical-turn-pipeline.md` and `docs/invariants/{answer-policy,pipeline}.md` because they define runtime and invariant contract surfaces that other docs claim as canonical. New findings show (1) these canonical docs are meaningfully connected to scripts/tests, but (2) `artifacts/architecture-boundary-report.current.md` and `docs/architecture/behavior-governance.md` are high-visibility supporting surfaces that can still create interpretation fan-out if not clearly bounded. The most important next tasks are to audit governance tracker docs and issue contract docs that likely duplicate or shadow this newly confirmed canonical layer.

Coverage progressed by auditing previously unaudited files from the anchor backlog only; this pass did not re-audit prior scope.

## 4. Audit findings for newly selected documents

| Document | Claimed purpose | Actual role in practice | Evidence | Classification | Governance risk | Action |
| -------- | --------------- | ----------------------- | -------- | -------------- | --------------- | ------ |
| `artifacts/architecture-boundary-report.current.md` | Current architecture-boundary remediation report. | Transitional operational evidence artifact consumed in readiness discussion, but not itself canonical policy. | `docs/testing.md` points to machine-readable boundary report output while `scripts/all_green_gate.py` marks boundary report check as warning-mode/non-blocking. | `transitional` | Medium: report can be mistaken as binding policy or current truth if stale. | Keep as generated evidence only; add explicit freshness/producer metadata and pointer to canonical boundary policy owner. |
| `docs/architecture/behavior-governance.md` | Non-authoritative test/spec traceability support matrix. | Reference/support matrix that routes verification discussions but defers authority to architecture + directives + ISSUE-0013. | File header explicitly marks non-authoritative; README links it in authority neighborhood, creating discoverability despite non-authoritative claim. | `reference` | Medium: discoverability near canonical docs can still cause shadow-authority usage. | Keep non-authoritative banner; add short “if conflict, follow X/Y/Z” precedence block at top. |
| `docs/architecture/canonical-turn-pipeline.md` | Canonical runtime stage contract and sequencing doctrine. | De facto canonical runtime behavior contract for stage order and typed stage semantics. | Linked from README, docs/architecture.md, docs/testing.md, and directives traceability matrix; stage sequence aligns to pipeline conformance validator scope. | `canonical` | High if drifted: many downstream docs/tests route to it. | Retain as canonical contract; add explicit “enforced-by” mapping table to validators/tests to reduce interpretation gaps. |
| `docs/invariants/answer-policy.md` | Canonical response-policy invariants (`INV-*`) and scenario map. | Canonical invariant registry with operational mirror-sync linkage into `docs/directives/invariants.md`. | File defines sync block and points to `scripts/sync_invariants_mirror.py`; invariant sync validator exists in readiness checks (`qa_validate_invariant_sync`). | `canonical` | Medium: drift risk if sync/validator not always run in CI contexts. | Keep canonical role; publish validator status in readiness evidence output so mirror integrity is visible. |
| `docs/invariants/pipeline.md` | Canonical pipeline semantics invariants (`PINV-*`). | Canonical semantics reference linked to executable conformance validation. | File states conformance via `scripts/validate_pipeline_stage_conformance.py`; all_green gate includes `safety_validate_pipeline_stage_conformance`. | `canonical` | Medium-high: semantics become documentary if validator scope lags document updates. | Add explicit row-level mapping from each `PINV-*` to validator assertion identifiers/tests. |

## 5. Newly discovered split-authority or duplication findings

| Topic | Newly selected documents involved | Interaction with previously audited authorities | Why this creates ambiguity | Canonical owner | Required action |
| ----- | --------------------------------- | ----------------------------------------------- | -------------------------- | --------------- | --------------- |
| Canonical contract vs support-matrix discoverability | `docs/architecture/canonical-turn-pipeline.md`, `docs/architecture/behavior-governance.md` | Prior pass already found README fan-out across multiple “authoritative” docs. | A non-authoritative matrix is linked near canonical docs; reviewers may treat matrix text as policy when conflicts arise. | `docs/architecture/canonical-turn-pipeline.md` (+ directives matrix for traceability) | Add explicit conflict-resolution pointer in behavior-governance doc header and README authority map. |
| Boundary report evidence vs enforceable policy | `artifacts/architecture-boundary-report.current.md` | Prior audit found boundary report is warning-mode while import-boundary tests are blocking when run. | Remediation report narrative can be misread as enforcement truth although blocking semantics live in gate/workflows. | `scripts/all_green_gate.py` + workflow checks | Mark artifact as generated evidence only and surface blocking/non-blocking matrix beside artifact links. |
| Invariant canonical docs vs derivative mirror surface | `docs/invariants/answer-policy.md`, `docs/invariants/pipeline.md` | Prior pass audited directive mirror and traceability matrix canonical claims. | Multiple high-authority docs hold overlapping invariant references; without explicit enforcement mapping, drift detection responsibility is unclear. | `docs/invariants/*` for canonical invariant text; validators for enforcement | Add a single invariant enforcement index (doc or generated artifact) mapping INV/PINV IDs to validator/tests and gate status. |

## 6. Remaining-document task planning table

| Remaining document | Suspected role | Why it still needs audit | Priority | Audit tasks required | Dependencies / prerequisite evidence | Recommended future audit batch |
| ------------------ | -------------- | ------------------------ | -------- | -------------------- | ------------------------------------ | ------------------------------ |
| `AGENTS.md` | operational agent policy | Agent instructions shape contributor behavior and can supersede repo docs during automation. | high | Compare AGENTS requirements to CONTRIBUTING/testing/issues contracts; identify conflicts and whether any AGENTS rule is machine-enforced vs prompt-only. | AGENTS.md text, CONTRIBUTING.md, docs/testing.md, CI workflows. | Batch A: entrypoint governance |
| `CHANGELOG.md` | historical release log | Could contain normative release policy used by reviewers. | low | Check for references from README/CONTRIBUTING/release scripts; if no enforcement links exist, classify historical and remove normative language if present. | README.md, CONTRIBUTING.md, scripts/*release*. | Batch F: roadmap/historical planning |
| `docs/architecture/commit-drift-audit-2026-03-19.md` | historical audit | Historical audit may be mistaken for current authority. | low | Trace inbound links; verify header clearly marks date-bounded historical scope; add superseded pointer task if missing. | README/docs indexes; architecture folder cross-links. | Batch F: roadmap/historical planning |
| `docs/architecture/documentation-governance-audit-2026-03-21.md` | historical anchor audit | Anchor file is historical but still used for backlog authority. | medium | Verify this file is treated as anchor only; ensure follow-up file links are explicit and no stale active directives are embedded. | docs/architecture/*governance*audit*.md cross-links. | Batch A2: audit trail hygiene |
| `docs/architecture/system-structure-audit-2026-03-19.md` | historical architecture audit | Could duplicate current architecture claims if consumed as live guidance. | medium | Compare findings against current architecture.md and canonical-turn-pipeline references; mark historical deltas and remove live-authority wording. | docs/architecture.md, docs/architecture/canonical-turn-pipeline.md. | Batch F: roadmap/historical planning |
| `docs/governance/architecture-drift-register.md` | governance tracker/reference | Governance trackers can duplicate directive authority or become shadow roadmaps. | high | Trace references from README/testing/issues; compare each rule/status field against canonical directives and gate checks; identify duplicate authorities and downgrade or merge non-canonical trackers. | docs/directives/*.md, scripts/all_green_gate.py, workflow files. | Batch C: governance tracker consolidation |
| `docs/governance/code-review-governance-automation-dependency-boundaries.md` | governance tracker/reference | Governance trackers can duplicate directive authority or become shadow roadmaps. | high | Trace references from README/testing/issues; compare each rule/status field against canonical directives and gate checks; identify duplicate authorities and downgrade or merge non-canonical trackers. | docs/directives/*.md, scripts/all_green_gate.py, workflow files. | Batch C: governance tracker consolidation |
| `docs/governance/drift-remediation-backlog.md` | governance tracker/reference | Governance trackers can duplicate directive authority or become shadow roadmaps. | high | Trace references from README/testing/issues; compare each rule/status field against canonical directives and gate checks; identify duplicate authorities and downgrade or merge non-canonical trackers. | docs/directives/*.md, scripts/all_green_gate.py, workflow files. | Batch C: governance tracker consolidation |
| `docs/governance/drift-traceability-matrix.md` | governance tracker/reference | Governance trackers can duplicate directive authority or become shadow roadmaps. | high | Trace references from README/testing/issues; compare each rule/status field against canonical directives and gate checks; identify duplicate authorities and downgrade or merge non-canonical trackers. | docs/directives/*.md, scripts/all_green_gate.py, workflow files. | Batch C: governance tracker consolidation |
| `docs/governance/issue-implementation-audit.md` | governance tracker/reference | Governance trackers can duplicate directive authority or become shadow roadmaps. | high | Trace references from README/testing/issues; compare each rule/status field against canonical directives and gate checks; identify duplicate authorities and downgrade or merge non-canonical trackers. | docs/directives/*.md, scripts/all_green_gate.py, workflow files. | Batch C: governance tracker consolidation |
| `docs/governance/mission-vision-alignment.md` | governance tracker/reference | Governance trackers can duplicate directive authority or become shadow roadmaps. | high | Trace references from README/testing/issues; compare each rule/status field against canonical directives and gate checks; identify duplicate authorities and downgrade or merge non-canonical trackers. | docs/directives/*.md, scripts/all_green_gate.py, workflow files. | Batch C: governance tracker consolidation |
| `docs/governance/python-code-review-checklist-dependency-boundaries.md` | governance tracker/reference | Governance trackers can duplicate directive authority or become shadow roadmaps. | high | Trace references from README/testing/issues; compare each rule/status field against canonical directives and gate checks; identify duplicate authorities and downgrade or merge non-canonical trackers. | docs/directives/*.md, scripts/all_green_gate.py, workflow files. | Batch C: governance tracker consolidation |
| `docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0002-behave-dev-deps-reminders.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0003-readme-layout-drift.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0004-bdd-policy-not-yet-executable.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0006-operationalize-docs-issues-area.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0016-startup-degraded-mode-bdd-coverage-gap.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0017-invariant-boundary-ambiguity-answer-commit-regression.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0018-dual-trigger-event-loop-for-proactive-ingestion-lifecycle.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md` | transitional issue contract | Issue acceptance criteria may still be acting as policy outside canonical docs. | medium | Map each issue's acceptance criteria to current tests/gates; verify whether docs/issues.md or directives already supersede it; mark active-vs-historical role and record required backlinks. | docs/issues.md, scripts/validate_issue_links.py, referenced tests/features. | Batch D: issue contract normalization |
| `docs/issues/RED_TAG.md` | operational escalation index | Escalation index may impose de facto priority/merge policy. | high | Trace RED_TAG references in issue workflow/checklists; verify whether escalation criteria are enforced in validators or only manual. | docs/issues.md, scripts/validate_issues.py, CI workflow usage. | Batch D: issue contract normalization |
| `docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/coordination-failure-contract-drift-matrix.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/governance-craap-analysis-main-alignment.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/governance-open-questions-audit-2026-03-16.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/governance-stabilization-checklist.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/issue-0022-pass-seven-verification-log.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/open-pr-assessment-2026-03-17.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/sprint-00-kpi-review.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/issues/evidence/work-history-assessment-2026-03-17.md` | historical evidence | Need classification to confirm it is evidence-only and not live authority. | low | Trace inbound links from docs/issues/RED_TAG.md, docs/issues.md, and README; check if any script/CI command parses this file; if unused in decision flow, mark historical and link to owning issue record. | Inbound-link scan (rg), validator scripts under scripts/, issue index documents. | Batch E: issue evidence sweep |
| `docs/ops.md` | operational runbook | May define operational behavior expectations outside testing/quickstart. | medium | Trace command and policy statements to executable scripts and workflows; detect overlap with quickstart/testing and assign canonical owner by concern. | docs/testing.md, docs/quickstart.md, scripts/all_green_gate.py. | Batch B2: QA enforcement alignment |
| `docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md` | operational QA reference | QA docs may assert gates or evidence expectations that are not executable. | medium | Map every mandatory statement to an actual command/job in scripts/all_green_gate.py or workflows; flag documentary-only blockers and split advisory content. | scripts/all_green_gate.py, .github/workflows/*.yml, pytest/behave commands. | Batch B2: QA enforcement alignment |
| `docs/qa/feature-status-report.md` | operational QA reference | QA docs may assert gates or evidence expectations that are not executable. | medium | Map every mandatory statement to an actual command/job in scripts/all_green_gate.py or workflows; flag documentary-only blockers and split advisory content. | scripts/all_green_gate.py, .github/workflows/*.yml, pytest/behave commands. | Batch B2: QA enforcement alignment |
| `docs/qa/live-smoke.md` | operational QA reference | QA docs may assert gates or evidence expectations that are not executable. | medium | Map every mandatory statement to an actual command/job in scripts/all_green_gate.py or workflows; flag documentary-only blockers and split advisory content. | scripts/all_green_gate.py, .github/workflows/*.yml, pytest/behave commands. | Batch B2: QA enforcement alignment |
| `docs/qa/smoke-evidence-contract.md` | operational QA reference | QA docs may assert gates or evidence expectations that are not executable. | medium | Map every mandatory statement to an actual command/job in scripts/all_green_gate.py or workflows; flag documentary-only blockers and split advisory content. | scripts/all_green_gate.py, .github/workflows/*.yml, pytest/behave commands. | Batch B2: QA enforcement alignment |
| `docs/regression-progression-audit-8f9317a-to-head.md` | historical audit | May contain stale governance assertions. | low | Check references in current docs/issues; classify historical evidence and add superseded note if still linked as active guidance. | docs/issues/* links; README links. | Batch F: roadmap/historical planning |
| `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md` | transitional planning | Roadmap docs may contain live policy claims that should be in canonical checklist/issues. | medium | Check whether roadmap milestones are cited as merge/review criteria; compare with plan-execution checklist and issue backlog; classify strictly as planning vs policy authority. | docs/architecture/plan-execution-checklist.md, plan.md, docs/issues/*.md. | Batch F: roadmap/historical planning |
| `docs/roadmap/current-status-and-next-5-priorities.md` | transitional planning | Roadmap docs may contain live policy claims that should be in canonical checklist/issues. | medium | Check whether roadmap milestones are cited as merge/review criteria; compare with plan-execution checklist and issue backlog; classify strictly as planning vs policy authority. | docs/architecture/plan-execution-checklist.md, plan.md, docs/issues/*.md. | Batch F: roadmap/historical planning |
| `docs/roadmap/next-4-sprints-grounded-knowing.md` | transitional planning | Roadmap docs may contain live policy claims that should be in canonical checklist/issues. | medium | Check whether roadmap milestones are cited as merge/review criteria; compare with plan-execution checklist and issue backlog; classify strictly as planning vs policy authority. | docs/architecture/plan-execution-checklist.md, plan.md, docs/issues/*.md. | Batch F: roadmap/historical planning |
| `docs/roadmap/reflective-milestone-10-sprints.md` | transitional planning | Roadmap docs may contain live policy claims that should be in canonical checklist/issues. | medium | Check whether roadmap milestones are cited as merge/review criteria; compare with plan-execution checklist and issue backlog; classify strictly as planning vs policy authority. | docs/architecture/plan-execution-checklist.md, plan.md, docs/issues/*.md. | Batch F: roadmap/historical planning |
| `docs/sessions/ISSUE-0014-cross-functional-session-plan.md` | transitional session plan | Session plans can leak temporary decisions into perceived policy. | low | Identify whether any current document cites this plan as authority; if not, classify historical meeting artifact and link to resulting issue updates. | docs/issues/ISSUE-0014*.md, docs/issues/evidence/*.md. | Batch E: issue evidence sweep |
| `docs/style-guide.md` | reference writing/style policy | Style guidance may conflict with canonical governance terminology rules. | medium | Compare normative rules with docs/terminology.md and CONTRIBUTING.md; isolate style-only guidance from governance directives. | docs/terminology.md, CONTRIBUTING.md. | Batch A: entrypoint governance |
| `docs/testing-triage.md` | operational triage runbook | Could define de facto severity/decision rules outside canonical testing doc. | high | Map triage decisions to all_green gate outputs and issue workflow; verify whether escalation thresholds are enforced or advisory only. | docs/testing.md, scripts/all_green_gate.py, docs/issues.md. | Batch B2: QA enforcement alignment |
| `examples/Experiments.md` | informational example | Likely non-governance, but could be mistaken as recommended workflow. | low | Check inbound links and command snippets for normative language; if unused operationally, classify decorative/reference. | README links and docs index searches. | Batch G: low-risk informational docs |
| `features/README.md` | test surface reference | May define BDD governance expectations not synchronized with testing/doc directives. | medium | Compare scenario/tagging guidance with directives traceability matrix and testing.md; identify duplicate/competing rules. | docs/directives/traceability-matrix.md, docs/testing.md, feature files. | Batch D2: behavior spec governance |
| `src/seem_bot/README.md` | component reference | Could describe architecture boundaries that conflict with canonical docs. | medium | Check if referenced by architecture/testing docs; compare claims with architecture-boundary rules and runtime package ownership. | docs/architecture*.md, docs/qa/architecture-boundaries.json. | Batch G: low-risk informational docs |

## 7. Coverage progression summary

| Audit pass | Date | Newly audited Markdown files | Total audited Markdown files after pass | Remaining Markdown files after pass | Notes |
| ---------- | ---- | ---------------------------- | --------------------------------------- | ----------------------------------- | ----- |
| Anchor audit | 2026-03-21 | 11 | 11 | 96 | Initial structural-honesty baseline with explicit out-of-scope backlog. |
| Follow-up pass 1 | 2026-03-21 | 9 | 20 | 87 | Audited README + directives + quickstart/terminology authority layer. |
| Follow-up pass 2 (this revision) | 2026-03-21 | 5 | 25 | 82 | Advanced into canonical pipeline + invariant canon + boundary evidence/matrix surfaces. |

## 8. Minimal next-step sequence

1. **Next batch:** `Batch C: governance tracker consolidation` (`docs/governance/*`).
2. **Why next:** these files are likely to duplicate or shadow the now-audited canonical pipeline/invariant layer and directly influence review prioritization.
3. **Evidence to gather first:** inbound-link graph from README/testing/issues; mapping of each tracker rule/status field to gate/workflow checks; update-history scan to see which files are maintained when behavior changes.
4. **Uncertainty reduced:** whether governance tracker docs are operationally authoritative, merely reporting surfaces, or split-authority sources requiring consolidation.

Then execute `Batch D: issue contract normalization` to determine which ISSUE files remain active policy carriers versus historical tracking records.
