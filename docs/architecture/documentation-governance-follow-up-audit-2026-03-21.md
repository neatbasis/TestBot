# Documentation Governance Follow-up Audit — Structural Honesty (2026-03-21)
## 1. Scope accounting
This continuation pass used `docs/architecture/documentation-governance-audit-2026-03-21.md` as the anchor backlog and advanced scope into previously unaudited files only. Prior scope did not require reconstruction because the anchor and earlier follow-up explicitly listed audited files.
- Total Markdown files currently in repo: **108**.
- Markdown files already covered by previous documentation governance audits: **25**.
- Markdown files newly selected for this audit pass: **7**.
- Markdown files still not yet audited after selection (anchor backlog remainder): **75**.
- Non-Markdown enforcement artifacts reviewed for evidence: `scripts/all_green_gate.py`, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`, `tests/test_validate_issue_links.py`, `tests/test_validate_issues.py`.
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

### 1.2 Candidate remaining Markdown files
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

### 1.3 Newly selected files for this audit pass
- `docs/governance/architecture-drift-register.md`
- `docs/governance/code-review-governance-automation-dependency-boundaries.md`
- `docs/governance/drift-remediation-backlog.md`
- `docs/governance/drift-traceability-matrix.md`
- `docs/governance/issue-implementation-audit.md`
- `docs/governance/mission-vision-alignment.md`
- `docs/governance/python-code-review-checklist-dependency-boundaries.md`

Selection rationale: this batch was chosen because these governance tracker documents most directly shape triage priority, closure language, and perceived architecture truth, yet were not referenced as executable enforcement surfaces in scripts/workflows. Auditing them now reduces high-impact uncertainty about tracker-vs-canonical authority boundaries before lower-risk historical and evidence notes.

### 1.4 Remaining files not audited in this pass
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
The selected `docs/governance/*` files were prioritized because they are decision-shaping surfaces (drift register, remediation backlog, traceability matrices, and checklist/audit documents) that can override contributor behavior even when not executable. They were chosen ahead of issue-evidence and historical notes because they: (a) contain normative-style language (acceptance criteria, severity, sprint targeting), (b) cross-link active issue files, and (c) are likely to create split authority with already-audited canonical docs (`docs/architecture/canonical-turn-pipeline.md`, `docs/directives/*`, `docs/testing.md`). This pass specifically reduces uncertainty about whether governance trackers are canonical, operational planning artifacts, or decorative/historical material.

## 3. Executive summary
After this pass, documentation governance audits cover **32 of 108 Markdown files (29.6%)** repository-wide, with **32 audited files total** (11 anchor in-scope + 21 follow-up selections across passes). Newly selected governance tracker documents materially affect governance clarity because they are used for drift framing and remediation prioritization, but not bound directly to merge-blocking automation. This pass found new split-authority risk where governance tracker files restate or reinterpret canonical directives and issue policy without executable binding. The most important next tasks are to audit `docs/issues/ISSUE-*` and `docs/issues/RED_TAG.md` as the next highest-risk remaining policy-carrying surface, then clear the issue-evidence backlog as explicitly historical/non-authoritative where appropriate.

## 4. Audit findings for newly selected documents

| Document | Claimed purpose | Actual role in practice | Evidence | Classification | Governance risk | Action |
| -------- | --------------- | ----------------------- | -------- | -------------- | --------------- | ------ |
| docs/governance/architecture-drift-register.md | Architecture-contract drift ledger against canonical pipeline. | Transitional drift register used for remediation framing; not directly enforced by CI. | References canonical contract and issue IDs but no script/workflow consumes this file directly. | transitional | Medium-high: can be mistaken for current canonical policy if not synchronized. | Keep as remediation ledger; add explicit freshness stamp and link to canonical owner sections. |
| docs/governance/code-review-governance-automation-dependency-boundaries.md | Code-review findings for governance automation scripts. | Historical audit snapshot of one change set; informative for context, not live policy. | Contains dated 'action taken in this change set' language and no inbound canonical references. | historical | Medium: checklist-style findings can be applied as standing policy unintentionally. | Mark as historical snapshot and move normative checklist references to maintained owner doc only. |
| docs/governance/drift-remediation-backlog.md | Sprintable remediation backlog for documented drift. | Operational planning backlog that routes implementation work via issue IDs and commands. | Defines target sprints, acceptance criteria, and validation commands tied to active ISSUE files. | operational | High: can shadow issue files/checklist if priority or closure criteria diverge. | Declare precedence: issue records + canonical checklist own closure; backlog is prioritization only. |
| docs/governance/drift-traceability-matrix.md | Drift audit matrix companion to directive traceability matrix. | Reference/transitional companion matrix that mirrors canonical directives for drift tracking. | File explicitly labels itself non-canonical and points to docs/directives/traceability-matrix.md as authority. | reference | Medium: dense matrix can still be misread as normative source. | Keep non-canonical banner; add required update trigger tied to directive changes. |
| docs/governance/issue-implementation-audit.md | Audit mapping issue acceptance criteria to implementation/tests. | Historical point-in-time evidence artifact; useful for provenance, not current governance authority. | Dated scope (2026-03-09) and fixed issue range (ISSUE-0008..0015) indicate snapshot role. | historical | Low-medium: stale verdicts may be cited as current status. | Label as dated snapshot and add pointer to current issue status surfaces. |
| docs/governance/mission-vision-alignment.md | Map product principles to behavior/spec/tests/implementation. | Reference bridge from principles to executable surfaces; partially operational because issues reference it. | Links to directives/product-principles and is referenced by ISSUE-0016 acceptance criteria. | reference | Medium: may become shadow requirement source if principle language drifts from directives. | Retain as mapping doc; enforce one-way derivation from directives and issue updates. |
| docs/governance/python-code-review-checklist-dependency-boundaries.md | Reusable boundary-focused Python review checklist. | Decorative/reference checklist (generic guidance, not repo-bound enforcement). | Contains broad generic items (mypy/ruff/pydeps) without demonstrated repository gate binding. | decorative | Medium: reviewers may treat non-enforced items as mandatory governance policy. | Either bind selected items to actual gates or relabel explicitly as optional guidance. |

## 5. Newly discovered split-authority or duplication findings

| Topic | Newly selected documents involved | Interaction with previously audited authorities | Why this creates ambiguity | Canonical owner | Required action |
| ----- | --------------------------------- | ----------------------------------------------- | -------------------------- | --------------- | --------------- |
| Remediation criteria duplication | `docs/governance/drift-remediation-backlog.md`, `docs/governance/architecture-drift-register.md` | Overlaps with `docs/issues/*.md` acceptance criteria and `docs/architecture/plan-execution-checklist.md` closure signaling. | Same issue IDs can carry different readiness framing across backlog vs issue records, creating closure ambiguity. | `docs/issues/*.md` for issue closure; `docs/architecture/plan-execution-checklist.md` for readiness status. | Add explicit precedence note and restrict backlog to prioritization metadata. |
| Traceability matrix duality | `docs/governance/drift-traceability-matrix.md`, `docs/governance/mission-vision-alignment.md` | Potentially overlaps directive canon in `docs/directives/traceability-matrix.md` and `docs/directives/product-principles.md`. | Readers can treat governance matrices as normative requirements instead of derivative mappings. | `docs/directives/*` | Add “derived-from” and conflict-resolution blocks at top of both governance files. |
| Checklist authority inflation | `docs/governance/python-code-review-checklist-dependency-boundaries.md`, `docs/governance/code-review-governance-automation-dependency-boundaries.md` | Can be conflated with enforceable review policy in `CONTRIBUTING.md` and `docs/testing.md`. | Generic review checklists look mandatory but are not linked to CI/gates, causing discretionary enforcement drift. | `docs/testing.md` + executable CI/workflow gates | Mark checklist docs as advisory unless specific checks are wired to automated gates. |

## 6. Remaining-document task planning table

| Remaining document | Suspected role | Why it still needs audit | Priority | Audit tasks required | Dependencies / prerequisite evidence | Recommended future audit batch |
| ------------------ | -------------- | ------------------------ | -------- | -------------------- | ------------------------------------ | ------------------------------ |
| `AGENTS.md` | operational contributor policy | Agent-only instructions may impose stronger rules than contributor docs and affect merged behavior. | high | Compare rules against docs/testing.md, docs/issues.md, and CONTRIBUTING.md; identify precedence conflicts and classify as operational or transitional agent policy. | AGENTS.md; docs/testing.md; docs/issues.md; CONTRIBUTING.md. | Batch A2: contributor-entrypoint alignment |
| `CHANGELOG.md` | historical release log | Could include normative promises still referenced during review. | low | Check whether release entries are referenced by current docs/issues as active requirements; classify as historical record unless actively referenced. | README/docs links; issue references. | Batch G: low-risk informational docs |
| `docs/architecture/commit-drift-audit-2026-03-19.md` | historical/transitional planning | May be cited as current authority despite being date-scoped or milestone-scoped. | low | Trace inbound references from current canonical docs; determine whether file drives current decisions; if historical, label superseded and point to canonical owner. | README/docs indexes; plan.md; docs/architecture/plan-execution-checklist.md. | Batch F: planning-and-historical cleanup |
| `docs/architecture/documentation-governance-audit-2026-03-21.md` | historical/transitional planning | May be cited as current authority despite being date-scoped or milestone-scoped. | low | Trace inbound references from current canonical docs; determine whether file drives current decisions; if historical, label superseded and point to canonical owner. | README/docs indexes; plan.md; docs/architecture/plan-execution-checklist.md. | Batch F: planning-and-historical cleanup |
| `docs/architecture/system-structure-audit-2026-03-19.md` | historical/transitional planning | May be cited as current authority despite being date-scoped or milestone-scoped. | low | Trace inbound references from current canonical docs; determine whether file drives current decisions; if historical, label superseded and point to canonical owner. | README/docs indexes; plan.md; docs/architecture/plan-execution-checklist.md. | Batch F: planning-and-historical cleanup |
| `docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0002-behave-dev-deps-reminders.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0003-readme-layout-drift.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0004-bdd-policy-not-yet-executable.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0006-operationalize-docs-issues-area.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0016-startup-degraded-mode-bdd-coverage-gap.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0017-invariant-boundary-ambiguity-answer-commit-regression.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0018-dual-trigger-event-loop-for-proactive-ingestion-lifecycle.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | medium | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/RED_TAG.md` | transitional issue contract | Could still carry de facto policy/closure criteria outside canonical docs. | high | Map normative statements to executable tests/gates; verify status fields and dependency semantics against validators; classify active policy carrier vs historical tracker. | docs/issues.md schema/validators; tests for issue validators; all_green_gate readiness profile. | Batch D: issue-contract normalization |
| `docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/coordination-failure-contract-drift-matrix.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/governance-craap-analysis-main-alignment.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/governance-open-questions-audit-2026-03-16.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/governance-stabilization-checklist.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/issue-0022-pass-seven-verification-log.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/open-pr-assessment-2026-03-17.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/sprint-00-kpi-review.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/issues/evidence/work-history-assessment-2026-03-17.md` | historical evidence | Verify it is evidence-only and not used as live policy in review/merge decisions. | low | Trace inbound links from README, docs/issues.md, RED_TAG, and active issue files; search scripts/workflows for direct parsing; if unused, classify historical and add superseded/owner pointer. | rg inbound-link scan; scripts/validate_issue_links.py; scripts/validate_issues.py; workflow references. | Batch E: issue-evidence sweep |
| `docs/ops.md` | operational QA/runbook | May contain decision rules that are advisory in prose but treated as required during review. | medium | Map every mandatory claim to concrete script/workflow enforcement; separate advisory runbook text from blocking criteria and identify canonical owner. | scripts/all_green_gate.py; .github/workflows/*.yml; docs/testing.md. | Batch B2: QA enforcement alignment |
| `docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md` | operational QA/runbook | May contain decision rules that are advisory in prose but treated as required during review. | medium | Map every mandatory claim to concrete script/workflow enforcement; separate advisory runbook text from blocking criteria and identify canonical owner. | scripts/all_green_gate.py; .github/workflows/*.yml; docs/testing.md. | Batch B2: QA enforcement alignment |
| `docs/qa/feature-status-report.md` | operational QA/runbook | May contain decision rules that are advisory in prose but treated as required during review. | medium | Map every mandatory claim to concrete script/workflow enforcement; separate advisory runbook text from blocking criteria and identify canonical owner. | scripts/all_green_gate.py; .github/workflows/*.yml; docs/testing.md. | Batch B2: QA enforcement alignment |
| `docs/qa/live-smoke.md` | operational QA/runbook | May contain decision rules that are advisory in prose but treated as required during review. | medium | Map every mandatory claim to concrete script/workflow enforcement; separate advisory runbook text from blocking criteria and identify canonical owner. | scripts/all_green_gate.py; .github/workflows/*.yml; docs/testing.md. | Batch B2: QA enforcement alignment |
| `docs/qa/smoke-evidence-contract.md` | operational QA/runbook | May contain decision rules that are advisory in prose but treated as required during review. | medium | Map every mandatory claim to concrete script/workflow enforcement; separate advisory runbook text from blocking criteria and identify canonical owner. | scripts/all_green_gate.py; .github/workflows/*.yml; docs/testing.md. | Batch B2: QA enforcement alignment |
| `docs/regression-progression-audit-8f9317a-to-head.md` | historical/transitional planning | May be cited as current authority despite being date-scoped or milestone-scoped. | low | Trace inbound references from current canonical docs; determine whether file drives current decisions; if historical, label superseded and point to canonical owner. | README/docs indexes; plan.md; docs/architecture/plan-execution-checklist.md. | Batch F: planning-and-historical cleanup |
| `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md` | historical/transitional planning | May be cited as current authority despite being date-scoped or milestone-scoped. | medium | Trace inbound references from current canonical docs; determine whether file drives current decisions; if historical, label superseded and point to canonical owner. | README/docs indexes; plan.md; docs/architecture/plan-execution-checklist.md. | Batch F: planning-and-historical cleanup |
| `docs/roadmap/current-status-and-next-5-priorities.md` | historical/transitional planning | May be cited as current authority despite being date-scoped or milestone-scoped. | medium | Trace inbound references from current canonical docs; determine whether file drives current decisions; if historical, label superseded and point to canonical owner. | README/docs indexes; plan.md; docs/architecture/plan-execution-checklist.md. | Batch F: planning-and-historical cleanup |
| `docs/roadmap/next-4-sprints-grounded-knowing.md` | historical/transitional planning | May be cited as current authority despite being date-scoped or milestone-scoped. | medium | Trace inbound references from current canonical docs; determine whether file drives current decisions; if historical, label superseded and point to canonical owner. | README/docs indexes; plan.md; docs/architecture/plan-execution-checklist.md. | Batch F: planning-and-historical cleanup |
| `docs/roadmap/reflective-milestone-10-sprints.md` | historical/transitional planning | May be cited as current authority despite being date-scoped or milestone-scoped. | medium | Trace inbound references from current canonical docs; determine whether file drives current decisions; if historical, label superseded and point to canonical owner. | README/docs indexes; plan.md; docs/architecture/plan-execution-checklist.md. | Batch F: planning-and-historical cleanup |
| `docs/sessions/ISSUE-0014-cross-functional-session-plan.md` | historical/transitional planning | May be cited as current authority despite being date-scoped or milestone-scoped. | low | Trace inbound references from current canonical docs; determine whether file drives current decisions; if historical, label superseded and point to canonical owner. | README/docs indexes; plan.md; docs/architecture/plan-execution-checklist.md. | Batch F: planning-and-historical cleanup |
| `docs/style-guide.md` | reference style policy | May conflict with contributor/governance docs if treated as normative for review outcomes. | medium | Compare normative language with CONTRIBUTING.md and terminology docs; separate writing conventions from governance requirements. | CONTRIBUTING.md; docs/terminology.md. | Batch A2: contributor-entrypoint alignment |
| `docs/testing-triage.md` | operational QA/runbook | May contain decision rules that are advisory in prose but treated as required during review. | high | Map every mandatory claim to concrete script/workflow enforcement; separate advisory runbook text from blocking criteria and identify canonical owner. | scripts/all_green_gate.py; .github/workflows/*.yml; docs/testing.md. | Batch B2: QA enforcement alignment |
| `examples/Experiments.md` | informational example | Could be misread as recommended production workflow. | low | Check inbound links and imperative language; if not used in decision paths, classify decorative/reference and add non-authoritative note. | README/docs link scan. | Batch G: low-risk informational docs |
| `features/README.md` | behavior-spec governance reference | Could define BDD process requirements that diverge from testing/directive canon. | medium | Crosswalk BDD rules and tags with docs/testing.md and directives traceability matrix; identify duplicate authority and recommend canonical owner. | docs/testing.md; docs/directives/traceability-matrix.md; feature tags. | Batch D2: behavior-spec governance |
| `src/seem_bot/README.md` | component reference | May document architecture boundaries that differ from current canonical architecture docs. | medium | Compare component claims with docs/architecture.md and canonical-turn-pipeline contract; classify as reference vs stale architecture authority. | docs/architecture.md; docs/architecture/canonical-turn-pipeline.md. | Batch G: low-risk informational docs |

## 7. Coverage progression summary

| Audit pass | Date | Newly audited Markdown files | Total audited Markdown files after pass | Remaining Markdown files after pass | Notes |
| ---------- | ---- | ---------------------------- | --------------------------------------- | ----------------------------------- | ----- |
| Anchor audit | 2026-03-21 | 11 | 11 | 96 | Initial baseline and out-of-scope backlog declared. |
| Follow-up pass 1 | 2026-03-21 | 9 | 20 | 87 | Audited entrypoint/directive layer (`README`, directives, quickstart, terminology). |
| Follow-up pass 2 | 2026-03-21 | 5 | 25 | 82 | Audited canonical pipeline + invariant canon + boundary evidence/matrix surfaces. |
| Follow-up pass 3 (this revision) | 2026-03-21 | 7 | 32 | 75 | Audited governance tracker surfaces to separate operational planning from canonical authority. |

## 8. Minimal next-step sequence

1. **Next batch to audit:** `Batch D: issue-contract normalization` — `docs/issues/ISSUE-0001` through `ISSUE-0021` plus `docs/issues/RED_TAG.md`.
2. **Why this batch next:** remaining highest governance-risk docs likely to carry closure and escalation authority that affects review decisions directly.
3. **Evidence to gather first:** (a) validator schema and enforcement behavior (`scripts/validate_issue_links.py`, `scripts/validate_issues.py`, tests), (b) cross-file dependency semantics among ISSUE records and RED_TAG, (c) inbound references from canonical entrypoints.
4. **Repository-level uncertainty reduced:** whether issue files are canonical policy carriers, transitional trackers, or historical logs; and whether any split authority remains between issue governance and already-audited canonical docs.
