# Documentation Governance Follow-up Audit — Structural Honesty (2026-03-21)

## 1. Scope accounting
This continuation pass is anchored to `docs/architecture/documentation-governance-audit-2026-03-21.md`. I reused the anchor audit’s out-of-scope Markdown backlog, reconciled it against current repository Markdown files, then separated prior scope, this-pass scope, and remaining scope.

- Total Markdown files currently in repo: **107**.
- Markdown files already covered by previous documentation governance audits (before this pass): **42**.
- Markdown files newly selected for this audit pass: **6**.
- Markdown files still not yet audited after selection: **59**.
- Non-Markdown enforcement artifacts reviewed for evidence: `scripts/all_green_gate.py`, `scripts/validate_issues.py`, `scripts/validate_issue_links.py`, `.github/workflows/issue-link-validation.yml`, `docs/qa/feature-status.yaml`.
- Backlog reconciliation note: prior scope had to be partially reconstructed from the follow-up audit body/tables; repository delta since anchor audit includes one Markdown removal (`.github/PULL_REQUEST_TEMPLATE.md`) and one Markdown addition (`docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`).

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
- `docs/issues/RED_TAG.md`
- `docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`
- `docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`
- `docs/issues/ISSUE-0016-startup-degraded-mode-bdd-coverage-gap.md`
- `docs/issues/ISSUE-0017-invariant-boundary-ambiguity-answer-commit-regression.md`
- `docs/issues/ISSUE-0018-dual-trigger-event-loop-for-proactive-ingestion-lifecycle.md`
- `docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md`
- `docs/issues/ISSUE-0002-behave-dev-deps-reminders.md`
- `docs/issues/ISSUE-0003-readme-layout-drift.md`
- `docs/issues/ISSUE-0004-bdd-policy-not-yet-executable.md`
- `docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md`

### 1.2 Candidate remaining Markdown files
- `AGENTS.md`
- `CHANGELOG.md`
- `docs/architecture/commit-drift-audit-2026-03-19.md`
- `docs/architecture/documentation-governance-audit-2026-03-21.md`
- `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`
- `docs/architecture/system-structure-audit-2026-03-19.md`
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
- `docs/issues/ISSUE-0006-operationalize-docs-issues-area.md`
- `docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md`
- `docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md`
- `docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md`
- `docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md`
- `docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md`

Selection rationale: these six files were chosen first from the remaining pool because they are the highest-leverage unresolved governance records (live/open or recently active issue trackers) that can directly influence review/merge readiness interpretation.

### 1.4 Remaining files not audited in this pass
- `AGENTS.md`
- `CHANGELOG.md`
- `docs/architecture/commit-drift-audit-2026-03-19.md`
- `docs/architecture/documentation-governance-audit-2026-03-21.md`
- `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`
- `docs/architecture/system-structure-audit-2026-03-19.md`
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
This pass prioritized `ISSUE-0006` through `ISSUE-0011` because they are the first contiguous block of un-audited issue-governance records with the strongest operational coupling to current readiness behavior.

Why these files now:
1. They contain blocker chains, acceptance criteria, and closure language that reviewers can interpret as governance truth.
2. They are cross-linked with canonical execution surfaces (`docs/testing.md`, `scripts/all_green_gate.py`, validator scripts, and feature-status artifacts), so uncertainty here propagates into contributor behavior.
3. They are more governance-relevant than evidence snapshots and roadmap retrospectives that are likely historical unless these issue-control semantics are clarified first.

What uncertainty this pass reduces:
- whether these records are operational trackers, transitional contracts, or historical artifacts,
- where issue-local claims duplicate canonical gate/check authority,
- and which remaining documents should be sequenced next for maximum governance clarity.

## 3. Executive summary
Coverage is now **48/107 current Markdown files audited (44.9%)**. Newly selected documents that materially affect governance clarity are `ISSUE-0007`, `ISSUE-0008`, `ISSUE-0009`, `ISSUE-0010`, and `ISSUE-0011`, because they carry active capability-state and gate-linked acceptance semantics; `ISSUE-0006` is primarily a historical operationalization record. New split-authority findings center on issue-local gate-check naming and status narratives that can drift from canonical enforcement surfaces. The most important next tasks are auditing the remaining active issue-control set (`ISSUE-0014`, `ISSUE-0015`, `ISSUE-0019`, `ISSUE-0020`, `ISSUE-0021`) and then the QA/runbook surfaces that consume or restate those controls.

## 4. Audit findings for newly selected documents

| Document | Claimed purpose | Actual role in practice | Evidence | Classification | Governance risk | Action |
| -------- | --------------- | ----------------------- | -------- | -------------- | --------------- | ------ |
| `docs/issues/ISSUE-0006-operationalize-docs-issues-area.md` | Operationalize `docs/issues/` and `docs/issues.md` as governed infrastructure. | Historical origin record; current policy and enforcement authority now resides elsewhere. | Closure notes cite validator-backed adoption; active enforcement runs through issue validators and PR workflow checks, not this file. | historical | medium | Keep as provenance record and avoid citing as current policy owner. |
| `docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md` | Close governance traceability gaps for partial capability reporting. | Transitional operational tracker tied to feature-status linkage behavior. | Acceptance criteria and verification steps point to `report_feature_status.py`, `validate_issue_links.py`, and `validate_issues.py`; file itself is not consumed by CI. | transitional | high | Keep tracker role; collapse enduring gate semantics into canonical testing/gate docs. |
| `docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md` | Track residual deterministic intent-grounding quality needed for full implementation. | Operational issue tracker with active dependency sequencing and capability state implications. | File remains `in_progress`; cross-links execution chain via ISSUE-0013/0012; ACs restate canonical behave/pytest/gate commands. | operational | high | Keep as execution tracker; add explicit canonical-owner pointers for policy assertions. |
| `docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md` | Primary traceability record for partial knowing-mode capability. | Operational tracker with extensive transitional residual-blocker notes. | Evidence binds to `docs/qa/feature-status.yaml` and gate summary outputs; residual blockers document check-ID mismatch risk between issue AC text and gate artifacts. | operational | high | Align issue AC check references with a stable canonical check-ID publication surface. |
| `docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md` | Primary traceability record for partial unknowing fallback capability. | Operational tracker parallel to ISSUE-0009, with similar transitional blocker framing. | Evidence references feature-status artifacts and gate summary outputs; residual blockers again hinge on check-ID visibility. | operational | high | Same remediation pattern as ISSUE-0009: canonicalize check-ID source and reference it from issues. |
| `docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md` | Close analytics input-coverage diagnostics gaps with measurable implementation checks. | Operational issue record mixing open status with closure-style verification logs. | File remains open but includes detailed command outputs and artifact references; also linked by governance matrices and issue dependency chains. | operational | medium | Require explicit “remaining unmet criteria” section whenever open issues include successful verification evidence. |

## 5. Newly discovered split-authority or duplication findings

| Topic | Newly selected documents involved | Interaction with previously audited authorities | Why this creates ambiguity | Canonical owner | Required action |
| ----- | --------------------------------- | ----------------------------------------------- | -------------------------- | --------------- | --------------- |
| Gate-check naming and evidence drift in issue acceptance criteria | `ISSUE-0009`, `ISSUE-0010` | Overlaps with previously audited `docs/testing.md` and `scripts/all_green_gate.py`. | Issue text can declare ACs unsatisfied because named checks differ from current gate summary outputs, even when underlying behavior passes. | `scripts/all_green_gate.py` + generated gate summary artifacts | Publish and reference stable check aliases/matrix from canonical gate outputs. |
| Capability status split between issue narratives and QA status artifacts | `ISSUE-0007`, `ISSUE-0008`, `ISSUE-0009`, `ISSUE-0010` | Interacts with `docs/qa/feature-status.yaml` and `docs/qa/feature-status-report.md`. | Two parallel “current status” narratives can diverge (issue prose vs generated capability status). | `docs/qa/feature-status.yaml` (generated report as derivative) | Treat issues as rationale/work logs; reserve capability-state truth for feature-status artifacts. |
| Open-issue verification logs mimicking closure authority | `ISSUE-0011` | Interacts with previously audited testing/readiness documentation and governance matrices. | Rich pass evidence in an open issue can be interpreted as done-state unless unmet ACs are explicitly isolated. | Issue schema/status process in `docs/issues.md` | Add required unmet-criteria subsection pattern for open issues with verification logs. |

## 6. Remaining-document task planning table

| Remaining document | Suspected role | Why it still needs audit | Priority | Audit tasks required | Dependencies / prerequisite evidence | Recommended future audit batch |
| ------------------ | -------------- | ------------------------ | -------- | -------------------- | ------------------------------------ | ------------------------------ |
| `AGENTS.md` | reference/meta governance | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace contributor entrypoint references; verify whether instructions conflict with canonical governance docs; classify as active contributor authority, reference-only, or decorative. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6E: entrypoint/meta governance surfaces |
| `CHANGELOG.md` | reference/meta governance | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace contributor entrypoint references; verify whether instructions conflict with canonical governance docs; classify as active contributor authority, reference-only, or decorative. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6E: entrypoint/meta governance surfaces |
| `docs/architecture/commit-drift-audit-2026-03-19.md` | historical architecture audit | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Determine whether this audit artifact is still cited for live decisions; compare findings against latest canonical docs; ensure historical snapshots are not treated as current authority. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6F: architecture audit artifact positioning |
| `docs/architecture/documentation-governance-audit-2026-03-21.md` | historical architecture audit | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Determine whether this audit artifact is still cited for live decisions; compare findings against latest canonical docs; ensure historical snapshots are not treated as current authority. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6F: architecture audit artifact positioning |
| `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` | historical architecture audit | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Determine whether this audit artifact is still cited for live decisions; compare findings against latest canonical docs; ensure historical snapshots are not treated as current authority. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6F: architecture audit artifact positioning |
| `docs/architecture/system-structure-audit-2026-03-19.md` | historical architecture audit | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Determine whether this audit artifact is still cited for live decisions; compare findings against latest canonical docs; ensure historical snapshots are not treated as current authority. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6F: architecture audit artifact positioning |
| `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md` | operational/transitional issue record | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Map acceptance criteria and status semantics to `docs/issues.md` + validator-enforced fields; verify whether closure rules duplicate `docs/testing.md` or architecture/invariant canon; classify as operational tracker vs contract shadow. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6A |
| `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md` | operational/transitional issue record | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Map acceptance criteria and status semantics to `docs/issues.md` + validator-enforced fields; verify whether closure rules duplicate `docs/testing.md` or architecture/invariant canon; classify as operational tracker vs contract shadow. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6A |
| `docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md` | operational/transitional issue record | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Map acceptance criteria and status semantics to `docs/issues.md` + validator-enforced fields; verify whether closure rules duplicate `docs/testing.md` or architecture/invariant canon; classify as operational tracker vs contract shadow. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6A |
| `docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md` | operational/transitional issue record | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Map acceptance criteria and status semantics to `docs/issues.md` + validator-enforced fields; verify whether closure rules duplicate `docs/testing.md` or architecture/invariant canon; classify as operational tracker vs contract shadow. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6A |
| `docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md` | operational/transitional issue record | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Map acceptance criteria and status semantics to `docs/issues.md` + validator-enforced fields; verify whether closure rules duplicate `docs/testing.md` or architecture/invariant canon; classify as operational tracker vs contract shadow. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6A |
| `docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/coordination-failure-contract-drift-matrix.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/governance-craap-analysis-main-alignment.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/governance-open-questions-audit-2026-03-16.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/governance-stabilization-checklist.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/issue-0022-pass-seven-verification-log.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/open-pr-assessment-2026-03-17.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/sprint-00-kpi-review.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/issues/evidence/work-history-assessment-2026-03-17.md` | historical evidence log | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace inbound links from canonical entrypoints and issue records; verify no CI/scripts consume this file directly; determine whether it should carry a historical-only banner and superseded pointer. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6C: evidence de-authority sweep |
| `docs/ops.md` | operational runbook | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Enumerate imperative statements and map each to executable checks/workflows; separate advisory troubleshooting from normative policy; identify duplicated readiness authority against `docs/testing.md` and gate scripts. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6B: QA/runbook governance alignment |
| `docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md` | operational runbook | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Enumerate imperative statements and map each to executable checks/workflows; separate advisory troubleshooting from normative policy; identify duplicated readiness authority against `docs/testing.md` and gate scripts. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6B: QA/runbook governance alignment |
| `docs/qa/feature-status-report.md` | operational runbook | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Enumerate imperative statements and map each to executable checks/workflows; separate advisory troubleshooting from normative policy; identify duplicated readiness authority against `docs/testing.md` and gate scripts. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6B: QA/runbook governance alignment |
| `docs/qa/live-smoke.md` | operational runbook | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Enumerate imperative statements and map each to executable checks/workflows; separate advisory troubleshooting from normative policy; identify duplicated readiness authority against `docs/testing.md` and gate scripts. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6B: QA/runbook governance alignment |
| `docs/qa/smoke-evidence-contract.md` | operational runbook | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Enumerate imperative statements and map each to executable checks/workflows; separate advisory troubleshooting from normative policy; identify duplicated readiness authority against `docs/testing.md` and gate scripts. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6B: QA/runbook governance alignment |
| `docs/regression-progression-audit-8f9317a-to-head.md` | historical/transitional planning | Primarily time-scoped or retrospective, but could be mistaken as current authority without explicit framing. | low | Check inbound links from README/plan/checklist; determine if this still drives decisions; if superseded, add explicit historical framing and pointer to current canonical planning surface. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6D: roadmap/session historical framing |
| `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md` | historical/transitional planning | Primarily time-scoped or retrospective, but could be mistaken as current authority without explicit framing. | low | Check inbound links from README/plan/checklist; determine if this still drives decisions; if superseded, add explicit historical framing and pointer to current canonical planning surface. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6D: roadmap/session historical framing |
| `docs/roadmap/current-status-and-next-5-priorities.md` | historical/transitional planning | Primarily time-scoped or retrospective, but could be mistaken as current authority without explicit framing. | low | Check inbound links from README/plan/checklist; determine if this still drives decisions; if superseded, add explicit historical framing and pointer to current canonical planning surface. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6D: roadmap/session historical framing |
| `docs/roadmap/next-4-sprints-grounded-knowing.md` | historical/transitional planning | Primarily time-scoped or retrospective, but could be mistaken as current authority without explicit framing. | low | Check inbound links from README/plan/checklist; determine if this still drives decisions; if superseded, add explicit historical framing and pointer to current canonical planning surface. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6D: roadmap/session historical framing |
| `docs/roadmap/reflective-milestone-10-sprints.md` | historical/transitional planning | Primarily time-scoped or retrospective, but could be mistaken as current authority without explicit framing. | low | Check inbound links from README/plan/checklist; determine if this still drives decisions; if superseded, add explicit historical framing and pointer to current canonical planning surface. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6D: roadmap/session historical framing |
| `docs/sessions/ISSUE-0014-cross-functional-session-plan.md` | historical/transitional planning | Primarily time-scoped or retrospective, but could be mistaken as current authority without explicit framing. | low | Check inbound links from README/plan/checklist; determine if this still drives decisions; if superseded, add explicit historical framing and pointer to current canonical planning surface. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6D: roadmap/session historical framing |
| `docs/style-guide.md` | reference/meta governance | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace contributor entrypoint references; verify whether instructions conflict with canonical governance docs; classify as active contributor authority, reference-only, or decorative. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6E: entrypoint/meta governance surfaces |
| `docs/testing-triage.md` | operational runbook | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Enumerate imperative statements and map each to executable checks/workflows; separate advisory troubleshooting from normative policy; identify duplicated readiness authority against `docs/testing.md` and gate scripts. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6B: QA/runbook governance alignment |
| `examples/Experiments.md` | reference/meta governance | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace contributor entrypoint references; verify whether instructions conflict with canonical governance docs; classify as active contributor authority, reference-only, or decorative. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6E: entrypoint/meta governance surfaces |
| `features/README.md` | reference/meta governance | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace contributor entrypoint references; verify whether instructions conflict with canonical governance docs; classify as active contributor authority, reference-only, or decorative. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6E: entrypoint/meta governance surfaces |
| `src/seem_bot/README.md` | reference/meta governance | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace contributor entrypoint references; verify whether instructions conflict with canonical governance docs; classify as active contributor authority, reference-only, or decorative. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6E: entrypoint/meta governance surfaces |

## 7. Coverage progression summary

| Audit pass | Date | Newly audited Markdown files | Total audited Markdown files after pass | Remaining Markdown files after pass | Notes |
| ---------- | ---- | ---------------------------- | --------------------------------------- | ----------------------------------- | ----- |
| Anchor audit | 2026-03-21 | 11 | 11 | 96 | Established methodology and initial out-of-scope backlog. |
| Follow-up pass 1 | 2026-03-21 | 9 | 20 | 87 | Audited entrypoint + directives + quickstart/invariants layer. |
| Follow-up pass 2 | 2026-03-21 | 5 | 25 | 82 | Audited canonical pipeline + boundary evidence/matrix surfaces. |
| Follow-up pass 3 | 2026-03-21 | 7 | 32 | 75 | Audited governance tracker layer (`docs/governance/*`). |
| Follow-up pass 4 | 2026-03-21 | 6 | 38 | 69 | Audited RED_TAG + active issue contract layer. |
| Follow-up pass 5 | 2026-03-21 | 5 | 43 | 64 | Audited foundational issue-governance origin set (`ISSUE-0001`..`0005`). |
| Follow-up pass 6 (this pass) | 2026-03-21 | 6 | 49 historical audited / 48 current audited | 59 | Audited active issue-control tranche (`ISSUE-0006`..`0011`). |

## 8. Minimal next-step sequence

1. **Next batch to audit:** `ISSUE-0014`, `ISSUE-0015`, `ISSUE-0019`, `ISSUE-0020`, and `ISSUE-0021`.
2. **Why that batch should come next:** these remaining issue records still carry live blocker and acceptance semantics that can shadow canonical governance during planning/review.
3. **Evidence to gather first:**
   - inbound-link traces from `docs/issues.md`, `docs/issues/RED_TAG.md`, README/contributor entrypoints, and feature-status artifacts;
   - current gate/validator mapping for any acceptance-criteria check references;
   - CI/workflow touchpoints (if any) that consume issue metadata.
4. **Repository-level uncertainty reduced:** whether the remaining active issue records are purely execution tracking or still functioning as de facto governance authorities, unlocking cleaner classification for subsequent QA/evidence/runbook batches.
