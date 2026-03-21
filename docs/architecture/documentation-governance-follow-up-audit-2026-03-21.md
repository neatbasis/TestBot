# Documentation Governance Follow-up Audit — Structural Honesty (2026-03-21)

## 1. Scope accounting
This is a continuation audit anchored to `docs/architecture/documentation-governance-audit-2026-03-21.md`. I used the anchor audit out-of-scope list as the authoritative backlog, then removed files already covered by prior follow-up passes before selecting this pass scope.

- Total Markdown files currently in repo: **108**.
- Markdown files already covered by previous documentation governance audits (before this pass): **32**.
- Markdown files newly selected for this audit pass: **6**.
- Markdown files still not yet audited after selection: **70** (**69** from the anchor backlog + 1 new non-anchor file: this follow-up artifact itself).
- Non-Markdown enforcement artifacts reviewed for evidence: `scripts/generate_red_tag_index.py`, `scripts/validate_issues.py`, `scripts/validate_issue_links.py`, `scripts/all_green_gate.py`.

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
- `artifacts/architecture-boundary-report.current.md`
- `docs/architecture/behavior-governance.md`
- `docs/architecture/canonical-turn-pipeline.md`
- `docs/invariants/answer-policy.md`
- `docs/invariants/pipeline.md`
- `docs/governance/architecture-drift-register.md`
- `docs/governance/code-review-governance-automation-dependency-boundaries.md`
- `docs/governance/drift-remediation-backlog.md`
- `docs/governance/drift-traceability-matrix.md`
- `docs/governance/issue-implementation-audit.md`
- `docs/governance/mission-vision-alignment.md`
- `docs/governance/python-code-review-checklist-dependency-boundaries.md`

### 1.2 Candidate remaining Markdown files
(From anchor out-of-scope backlog minus previously audited files. The repository also now contains one additional non-anchor Markdown file: `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`.)

- `AGENTS.md`
- `CHANGELOG.md`
- `docs/architecture/commit-drift-audit-2026-03-19.md`
- `docs/architecture/documentation-governance-audit-2026-03-21.md`
- `docs/architecture/system-structure-audit-2026-03-19.md`
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
- `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
- `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md`
- `docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md`
- `docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md`
- `docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md`
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
- `docs/issues/RED_TAG.md`
- `docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`
- `docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`
- `docs/issues/ISSUE-0016-startup-degraded-mode-bdd-coverage-gap.md`
- `docs/issues/ISSUE-0017-invariant-boundary-ambiguity-answer-commit-regression.md`
- `docs/issues/ISSUE-0018-dual-trigger-event-loop-for-proactive-ingestion-lifecycle.md`

Selection rationale: these were prioritized because they are active issue-governance control surfaces (dependency order, closure gating language, severity routing, and generated red escalation index) that directly shape reviewer and maintainer decisions, and they are referenced/validated by issue governance tooling.

### 1.4 Remaining files not audited in this pass
- `AGENTS.md`
- `CHANGELOG.md`
- `docs/architecture/commit-drift-audit-2026-03-19.md`
- `docs/architecture/documentation-governance-audit-2026-03-21.md`
- `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`
- `docs/architecture/system-structure-audit-2026-03-19.md`
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
- `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
- `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md`
- `docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md`
- `docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md`
- `docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md`
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
This pass focused on the issue-governance core (RED_TAG + ISSUE-0012/0013/0016/0017/0018) because these files currently carry decision-bearing closure language, dependency labels, and explicit verification commands that influence real triage and review flow. They outrank remaining evidence/historical notes because:

1. they are parsed or indirectly enforced by scripts (`generate_red_tag_index.py`, `validate_issues.py`),
2. they encode open/blocked/resolved state transitions used by contributors,
3. they can fragment authority from already-audited canonical documents (`docs/issues.md`, `docs/testing.md`, directives, checklist) if left unaudited.

Uncertainty reduced in this pass: whether these issue records are merely planning notes versus active governance operators in repository decision paths.

## 3. Executive summary
Documentation governance audits now cover **38/108 Markdown files (35.2%)**. Newly audited files that materially affect governance clarity are `docs/issues/RED_TAG.md` and ISSUE records 0012/0013/0016/0017/0018: they carry active dependency/closure semantics and are tied to validator and index-generation workflows. New split-authority findings center on issue-local acceptance criteria and lifecycle notes potentially overriding canonical policy surfaces (`docs/issues.md`, `docs/testing.md`, directives) without explicit precedence text. The most important next tasks are auditing the remaining active ISSUE files (0001–0011, 0014, 0015, 0019–0021), then de-authorizing issue evidence notes that are not bound to executable governance.

## 4. Audit findings for newly selected documents

| Document | Claimed purpose | Actual role in practice | Evidence | Classification | Governance risk | Action |
| -------- | --------------- | ----------------------- | -------- | -------------- | --------------- | ------ |
| `docs/issues/RED_TAG.md` | Live index of red open issues. | Operational generated escalation surface consumed by humans during triage; content derived from issue metadata, not standalone policy. | File states generated-only contract; `scripts/generate_red_tag_index.py` reads `ISSUE-*.md` `Severity` + `Status` and writes this file. | operational | Medium: if manually edited or stale, escalation view diverges from issue canon. | Keep generated-only; require `--check` in readiness flow and maintain clear “do not edit” banner. |
| `docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md` | Staged delivery and checkpoint governance for canonical pipeline. | Operational/transitional program-management issue used to sequence implementation and validation commands. | Contains sprint checkpoints, explicit dependencies, and validator commands; linked from ISSUE-0013 as canonical cross-reference. | transitional | High: may become de facto canonical architecture authority if not constrained to execution planning. | Add explicit precedence line: architecture contract remains in canonical pipeline doc; ISSUE-0012 owns schedule/dependency tracking only. |
| `docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md` | Primary bug-elimination governance stream. | Operational dependency hub and closure gate for multiple issues; heavily decision-shaping in practice. | Defines ordered dependency labels, acceptance criteria with required tests, and closure conditions tied to ISSUE-0014/0015 + gate artifacts. | operational | High: closure semantics and KPI notes can conflict with `docs/testing.md` gate policy if unsynchronized. | Normalize shared gate language by referencing one canonical readiness status source instead of issue-local restatement. |
| `docs/issues/ISSUE-0016-startup-degraded-mode-bdd-coverage-gap.md` | Close a policy-to-BDD coverage gap. | Mostly historical closed issue with provenance and evidence trail; still useful traceability record. | Status closed, dated closure notes, verification outcomes recorded; no direct script consumes issue-specific ACs for runtime gating. | historical | Low-medium: closed issue narrative could be mistaken for current policy source. | Add “historical implementation record” note and point to ongoing canonical behavior specs/docs for live policy. |
| `docs/issues/ISSUE-0017-invariant-boundary-ambiguity-answer-commit-regression.md` | Track invariant-boundary regression and remediation. | Active operational issue carrying detailed acceptance/verification and cross-issue blockers. | Open status + explicit work plan phases, dependency map (to ISSUE-0018/0019/0020), mandatory validation command set. | operational | High: issue-local invariant wording can drift from directive/invariant canon. | Add explicit linkage field to canonical invariant owner sections and require sync check at close. |
| `docs/issues/ISSUE-0018-dual-trigger-event-loop-for-proactive-ingestion-lifecycle.md` | Define dual-trigger lifecycle scheduler contract and closure evidence. | Active transitional/operational design-governance issue that currently shapes implementation sequencing. | Open status, AC list, dependency chain, and mandatory evidence commands; referenced as blocker/unblocker in ISSUE-0017 and ISSUE-0020. | transitional | High: design-contract language may shadow architecture canon while still in issue form. | Promote stabilized contract clauses to canonical architecture/invariant docs, then leave issue as execution tracker only. |

## 5. Newly discovered split-authority or duplication findings

| Topic | Newly selected documents involved | Interaction with previously audited authorities | Why this creates ambiguity | Canonical owner | Required action |
| ----- | --------------------------------- | ----------------------------------------------- | -------------------------- | --------------- | --------------- |
| Issue-local readiness language vs gate canon | `ISSUE-0012`, `ISSUE-0013`, `ISSUE-0017`, `ISSUE-0018` | Overlaps with `docs/testing.md` and `scripts/all_green_gate.py` blocking semantics. | Each issue restates expected pass/fail interpretation, risking inconsistent closure decisions. | `docs/testing.md` + `scripts/all_green_gate.py` | Replace repeated gate interpretation text with canonical-reference blocks. |
| Contract-in-issue drift | `ISSUE-0013`, `ISSUE-0018` | Overlaps architecture and invariant canon (`docs/architecture/canonical-turn-pipeline.md`, `docs/invariants/*`, directives). | Active issues contain detailed contract clauses that can outpace canonical docs and become de facto authority. | Canonical architecture + invariant docs | Add “contract owner” pointers and migrate stable clauses into canonical docs during closure. |
| Escalation index freshness risk | `RED_TAG.md` with red issues | Depends on issue metadata and generator script, not manual doc maintenance. | If generation/check cadence is unclear, triage can use stale severity status. | `docs/issues/*.md` fields + `scripts/generate_red_tag_index.py` | Add explicit CI/readiness check step for `generate_red_tag_index.py --check`. |

## 6. Remaining-document task planning table

| Remaining document | Suspected role | Why it still needs audit | Priority | Audit tasks required | Dependencies / prerequisite evidence | Recommended future audit batch |
| ------------------ | -------------- | ------------------------ | -------- | -------------------- | ------------------------------------ | ------------------------------ |
| `AGENTS.md` | reference/meta governance | Entrypoint/meta docs can influence contributor behavior and audit routing. | medium | Verify real decision-path usage, inbound links, and conflict with canonical governance docs; classify as operational reference vs archival/meta-only. | `README.md`, `CONTRIBUTING.md`, `docs/testing.md`, `docs/issues.md`. | Batch 5E: entrypoint + meta governance surfaces |
| `CHANGELOG.md` | reference/meta governance | Entrypoint/meta docs can influence contributor behavior and audit routing. | medium | Verify real decision-path usage, inbound links, and conflict with canonical governance docs; classify as operational reference vs archival/meta-only. | `README.md`, `CONTRIBUTING.md`, `docs/testing.md`, `docs/issues.md`. | Batch 5E: entrypoint + meta governance surfaces |
| `docs/architecture/commit-drift-audit-2026-03-19.md` | historical/transitional planning | Time-scoped planning notes may still be treated as current direction. | low | Check inbound links from entrypoint docs; classify as historical vs active plan; add superseded-date and canonical owner pointer where needed. | `README.md`, `plan.md`, `docs/architecture/plan-execution-checklist.md`. | Batch 5D: historical planning cleanup |
| `docs/architecture/documentation-governance-audit-2026-03-21.md` | reference/meta governance | Entrypoint/meta docs can influence contributor behavior and audit routing. | medium | Verify real decision-path usage, inbound links, and conflict with canonical governance docs; classify as operational reference vs archival/meta-only. | `README.md`, `CONTRIBUTING.md`, `docs/testing.md`, `docs/issues.md`. | Batch 5E: entrypoint + meta governance surfaces |
| `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` | reference/meta governance | Entrypoint/meta docs can influence contributor behavior and audit routing. | medium | Verify real decision-path usage, inbound links, and conflict with canonical governance docs; classify as operational reference vs archival/meta-only. | `README.md`, `CONTRIBUTING.md`, `docs/testing.md`, `docs/issues.md`. | Batch 5E: entrypoint + meta governance surfaces |
| `docs/architecture/system-structure-audit-2026-03-19.md` | historical/transitional planning | Time-scoped planning notes may still be treated as current direction. | low | Check inbound links from entrypoint docs; classify as historical vs active plan; add superseded-date and canonical owner pointer where needed. | `README.md`, `plan.md`, `docs/architecture/plan-execution-checklist.md`. | Batch 5D: historical planning cleanup |
| `docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0002-behave-dev-deps-reminders.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0003-readme-layout-drift.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0004-bdd-policy-not-yet-executable.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0006-operationalize-docs-issues-area.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md` | transitional issue contract | Active issue files can hold de facto closure policy outside canon. | high | Map acceptance criteria and dependency claims to executable gates/tests; determine whether closure authority is issue-local or delegated to checklist/directives. | `docs/issues.md`, `scripts/validate_issues.py`, `scripts/all_green_gate.py`, related tests/features. | Batch 5A: remaining active issue contracts |
| `docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/coordination-failure-contract-drift-matrix.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-craap-analysis-main-alignment.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-open-questions-audit-2026-03-16.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-stabilization-checklist.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/issue-0022-pass-seven-verification-log.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/open-pr-assessment-2026-03-17.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/sprint-00-kpi-review.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/issues/evidence/work-history-assessment-2026-03-17.md` | historical evidence | Evidence notes may be cited as live policy without provenance boundaries. | medium | Trace inbound links from README/issues/RED_TAG and scripts/workflows; verify no enforcement consumes it; mark as historical with superseded pointer if unused. | `rg` inbound-link scan; `.github/workflows/*`; validator scripts. | Batch 5B: issue-evidence de-authority sweep |
| `docs/ops.md` | operational runbook | QA/runbook docs can silently become normative without CI binding. | high | Enumerate every MUST/required statement; map each to a check/script or downgrade to advisory; identify canonical owner for each enforced rule. | `docs/testing.md`, `scripts/all_green_gate.py`, `.github/workflows/*`. | Batch 5C: QA/runbook enforcement alignment |
| `docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md` | operational runbook | QA/runbook docs can silently become normative without CI binding. | high | Enumerate every MUST/required statement; map each to a check/script or downgrade to advisory; identify canonical owner for each enforced rule. | `docs/testing.md`, `scripts/all_green_gate.py`, `.github/workflows/*`. | Batch 5C: QA/runbook enforcement alignment |
| `docs/qa/feature-status-report.md` | operational runbook | QA/runbook docs can silently become normative without CI binding. | high | Enumerate every MUST/required statement; map each to a check/script or downgrade to advisory; identify canonical owner for each enforced rule. | `docs/testing.md`, `scripts/all_green_gate.py`, `.github/workflows/*`. | Batch 5C: QA/runbook enforcement alignment |
| `docs/qa/live-smoke.md` | operational runbook | QA/runbook docs can silently become normative without CI binding. | high | Enumerate every MUST/required statement; map each to a check/script or downgrade to advisory; identify canonical owner for each enforced rule. | `docs/testing.md`, `scripts/all_green_gate.py`, `.github/workflows/*`. | Batch 5C: QA/runbook enforcement alignment |
| `docs/qa/smoke-evidence-contract.md` | operational runbook | QA/runbook docs can silently become normative without CI binding. | high | Enumerate every MUST/required statement; map each to a check/script or downgrade to advisory; identify canonical owner for each enforced rule. | `docs/testing.md`, `scripts/all_green_gate.py`, `.github/workflows/*`. | Batch 5C: QA/runbook enforcement alignment |
| `docs/regression-progression-audit-8f9317a-to-head.md` | historical/transitional planning | Time-scoped planning notes may still be treated as current direction. | low | Check inbound links from entrypoint docs; classify as historical vs active plan; add superseded-date and canonical owner pointer where needed. | `README.md`, `plan.md`, `docs/architecture/plan-execution-checklist.md`. | Batch 5D: historical planning cleanup |
| `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md` | historical/transitional planning | Time-scoped planning notes may still be treated as current direction. | low | Check inbound links from entrypoint docs; classify as historical vs active plan; add superseded-date and canonical owner pointer where needed. | `README.md`, `plan.md`, `docs/architecture/plan-execution-checklist.md`. | Batch 5D: historical planning cleanup |
| `docs/roadmap/current-status-and-next-5-priorities.md` | historical/transitional planning | Time-scoped planning notes may still be treated as current direction. | low | Check inbound links from entrypoint docs; classify as historical vs active plan; add superseded-date and canonical owner pointer where needed. | `README.md`, `plan.md`, `docs/architecture/plan-execution-checklist.md`. | Batch 5D: historical planning cleanup |
| `docs/roadmap/next-4-sprints-grounded-knowing.md` | historical/transitional planning | Time-scoped planning notes may still be treated as current direction. | low | Check inbound links from entrypoint docs; classify as historical vs active plan; add superseded-date and canonical owner pointer where needed. | `README.md`, `plan.md`, `docs/architecture/plan-execution-checklist.md`. | Batch 5D: historical planning cleanup |
| `docs/roadmap/reflective-milestone-10-sprints.md` | historical/transitional planning | Time-scoped planning notes may still be treated as current direction. | low | Check inbound links from entrypoint docs; classify as historical vs active plan; add superseded-date and canonical owner pointer where needed. | `README.md`, `plan.md`, `docs/architecture/plan-execution-checklist.md`. | Batch 5D: historical planning cleanup |
| `docs/sessions/ISSUE-0014-cross-functional-session-plan.md` | historical/transitional planning | Time-scoped planning notes may still be treated as current direction. | low | Check inbound links from entrypoint docs; classify as historical vs active plan; add superseded-date and canonical owner pointer where needed. | `README.md`, `plan.md`, `docs/architecture/plan-execution-checklist.md`. | Batch 5D: historical planning cleanup |
| `docs/style-guide.md` | reference/meta governance | Entrypoint/meta docs can influence contributor behavior and audit routing. | medium | Verify real decision-path usage, inbound links, and conflict with canonical governance docs; classify as operational reference vs archival/meta-only. | `README.md`, `CONTRIBUTING.md`, `docs/testing.md`, `docs/issues.md`. | Batch 5E: entrypoint + meta governance surfaces |
| `docs/testing-triage.md` | operational runbook | QA/runbook docs can silently become normative without CI binding. | high | Enumerate every MUST/required statement; map each to a check/script or downgrade to advisory; identify canonical owner for each enforced rule. | `docs/testing.md`, `scripts/all_green_gate.py`, `.github/workflows/*`. | Batch 5C: QA/runbook enforcement alignment |
| `examples/Experiments.md` | reference/meta governance | Entrypoint/meta docs can influence contributor behavior and audit routing. | medium | Verify real decision-path usage, inbound links, and conflict with canonical governance docs; classify as operational reference vs archival/meta-only. | `README.md`, `CONTRIBUTING.md`, `docs/testing.md`, `docs/issues.md`. | Batch 5E: entrypoint + meta governance surfaces |
| `features/README.md` | reference/meta governance | Entrypoint/meta docs can influence contributor behavior and audit routing. | medium | Verify real decision-path usage, inbound links, and conflict with canonical governance docs; classify as operational reference vs archival/meta-only. | `README.md`, `CONTRIBUTING.md`, `docs/testing.md`, `docs/issues.md`. | Batch 5E: entrypoint + meta governance surfaces |
| `src/seem_bot/README.md` | reference/meta governance | Entrypoint/meta docs can influence contributor behavior and audit routing. | medium | Verify real decision-path usage, inbound links, and conflict with canonical governance docs; classify as operational reference vs archival/meta-only. | `README.md`, `CONTRIBUTING.md`, `docs/testing.md`, `docs/issues.md`. | Batch 5E: entrypoint + meta governance surfaces |

## 7. Coverage progression summary

| Audit pass | Date | Newly audited Markdown files | Total audited Markdown files after pass | Remaining Markdown files after pass | Notes |
| ---------- | ---- | ---------------------------- | --------------------------------------- | ----------------------------------- | ----- |
| Anchor audit | 2026-03-21 | 11 | 11 | 97 | Established methodology and initial out-of-scope backlog. |
| Follow-up pass 1 | 2026-03-21 | 9 | 20 | 88 | Audited entrypoint + directives + quickstart/invariants layer. |
| Follow-up pass 2 | 2026-03-21 | 5 | 25 | 83 | Audited canonical pipeline + boundary evidence/matrix surfaces. |
| Follow-up pass 3 | 2026-03-21 | 7 | 32 | 76 | Audited governance tracker layer (`docs/governance/*`). |
| Follow-up pass 4 (this pass) | 2026-03-21 | 6 | 38 | 70 | Audited RED_TAG + high-impact active issue contracts. |

## 8. Minimal next-step sequence

1. **Next batch:** Batch 5A (`docs/issues/ISSUE-0001`..`0011`, `0014`, `0015`, `0019`..`0021`).
2. **Why next:** These are the highest remaining governance-impact files still carrying active status, blockers, and acceptance criteria that may steer merge/review behavior.
3. **Evidence to gather first:** run issue-validator scripts against all issue files, map inbound links from `README.md`/`docs/issues.md`/`RED_TAG.md`, and capture where workflows/scripts consume issue metadata versus prose.
4. **Uncertainty reduced:** clarifies whether issue files are operational governance contracts or transitional trackers, and collapses closure-authority ambiguity before low-risk evidence/historical sweeps.
