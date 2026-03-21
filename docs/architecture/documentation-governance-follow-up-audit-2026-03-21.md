# Documentation Governance Follow-up Audit — Structural Honesty (2026-03-21)

## 1. Scope accounting
This continuation pass is anchored to `docs/architecture/documentation-governance-audit-2026-03-21.md`. Scope/backlog accounting starts from that anchor audit’s out-of-scope list, then subtracts files already audited in prior follow-up passes, then selects a bounded new subset from the remaining pool.

- Total Markdown files currently in repo: **107**.
- Markdown files already covered by previous documentation governance audits (before this pass): **48 current files**.
- Markdown files newly selected for this audit pass: **5**.
- Markdown files still not yet audited after selection: **54**.
- Non-Markdown enforcement artifacts reviewed for evidence: `scripts/all_green_gate.py`, `scripts/validate_issues.py`, `scripts/validate_issue_links.py`, `.github/workflows/issue-link-validation.yml`, `docs/qa/feature-status.yaml`.
- Scope reconstruction note: prior follow-up scope was reconstructed from this follow-up document’s earlier pass tables/findings; anchor out-of-scope backlog remained the canonical seed set.
- Repository-delta note from anchor snapshot: `.github/PULL_REQUEST_TEMPLATE.md` (Markdown) is no longer present; `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` is present and tracked as part of current Markdown surface accounting.

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
- `docs/issues/ISSUE-0006-operationalize-docs-issues-area.md`
- `docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md`
- `docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md`
- `docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md`
- `docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md`
- `docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md`

### 1.2 Candidate remaining Markdown files
- `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
- `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md`
- `docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md`
- `docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md`
- `docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md`
- `AGENTS.md`
- `CHANGELOG.md`
- `docs/architecture/commit-drift-audit-2026-03-19.md`
- `docs/architecture/documentation-governance-audit-2026-03-21.md`
- `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`
- `docs/architecture/system-structure-audit-2026-03-19.md`
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
- `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
- `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md`
- `docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md`
- `docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md`
- `docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md`

Selection rationale (why these before other remaining files): they are the remaining active issue records most likely to shape governance behavior directly through blocker/dependency language, acceptance-criteria gating, and cross-linking to readiness commands and status artifacts.

### 1.4 Remaining files not audited in this pass
- `AGENTS.md`
- `CHANGELOG.md`
- `docs/architecture/commit-drift-audit-2026-03-19.md`
- `docs/architecture/documentation-governance-audit-2026-03-21.md`
- `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`
- `docs/architecture/system-structure-audit-2026-03-19.md`
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
This pass prioritized the remaining active issue-control tranche (`ISSUE-0014`, `ISSUE-0015`, `ISSUE-0019`, `ISSUE-0020`, `ISSUE-0021`) because these files still contain live blocker/dependency semantics that can influence contributor and reviewer decisions now.

Why these files matter now:
1. They carry explicit lifecycle states (`open`, red/amber severity) and closure criteria with direct references to canonical commands and gates.
2. They sit between previously audited canonical governance surfaces (`docs/testing.md`, `docs/issues.md`, `docs/issues/RED_TAG.md`) and execution evidence artifacts, making them high-risk split-authority points.
3. They are more governance-relevant than remaining evidence snapshots and historical roadmap/session notes, which are lower leverage unless active issue authority is first stabilized.

Expected uncertainty reduction from this pass:
- determine whether these issues function as operational trackers versus de facto policy owners,
- surface any newly introduced split authority between issue prose and canonical enforcement artifacts,
- and tighten task sequencing for the remaining 54 unaudited Markdown files.

## 3. Executive summary
Coverage is now **53/107 current Markdown files (49.5%)**. This pass materially advanced governance clarity by auditing the remaining active issue-control documents (`ISSUE-0014`, `ISSUE-0015`, `ISSUE-0019`, `ISSUE-0020`, `ISSUE-0021`), confirming they are predominantly operational/transitional trackers rather than canonical policy owners, but still capable of creating split authority when they restate gate semantics or closure truth. Newly surfaced ambiguity centers on issue-local closure claims versus canonical feature-status/gate artifacts and on architecture-migration authority overlap between `ISSUE-0021` and previously audited boundary/testing documents. The most important next tasks are (a) auditing QA/runbook documents that translate issue state into contributor behavior and (b) de-authority framing of issue evidence snapshots so historical records are not mistaken as live governance.

## 4. Audit findings for newly selected documents

| Document | Claimed purpose | Actual role in practice | Evidence | Classification | Governance risk | Action |
| -------- | --------------- | ----------------------- | -------- | -------------- | --------------- | ------ |
| `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md` | Track the identity-continuity regression and required closure evidence. | Active red-tag operational blocker with extensive transitional governance language and dependency coupling to other issues. | Listed in `docs/issues/RED_TAG.md`; referenced by `docs/testing.md` readiness criteria; embeds command/evidence requirements but is not directly machine-enforced. | operational | high | Keep as execution tracker; keep canonical pass/fail truth in gate/status artifacts and link to them. |
| `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md` | Review and harden ISSUE-0014 quality/governance closure discipline. | Transitional governance hardening record that acts as dependency gate narrative for closure ordering. | Cross-linked from `RED_TAG`; contains lifecycle/dependency policy prose and validator command expectations; no direct CI consumer for issue-local wording. | transitional | high | Retain until dependency chain closes; avoid treating issue-local prose as canonical policy source. |
| `docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md` | Track channel-agnostic engine and shared-history migration. | Operational implementation-planning tracker with architecture/process implications, but not canonical architecture owner by itself. | Contains open work-plan and dependencies to ISSUE-0018/0020; acceptance criteria reference tests/docs sync but enforcement still flows through canonical docs/scripts. | operational | medium | Keep implementation tracking here; move durable architecture contract truth to canonical architecture/invariant docs when decisions land. |
| `docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md` | Govern deprecation of `SOURCE_INGEST_ENABLED` quickstart requirement. | Transitional change-control tracker spanning runtime behavior and quickstart documentation evolution. | Links runtime validation and quickstart docs; issue is open/blocked on upstream decisions; acceptance criteria include docs/tests updates but issue text itself is non-enforcing. | transitional | medium | Use as migration log; ensure final authoritative behavior lives in runtime code/tests + `docs/quickstart.md`. |
| `docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md` | Track deprecation/migration of legacy boundary patterns. | Operational migration debt register overlapping with previously audited boundary/testing authorities. | References `docs/architecture-boundaries.md`, pipeline tests, and all-green gate; issue states migration inventory/closure criteria but canonical boundary rules are elsewhere. | operational | medium | Keep as debt-tracking ledger; keep boundary rule authority in architecture-boundary docs + executable tests. |

## 5. Newly discovered split-authority or duplication findings

| Topic | Newly selected documents involved | Interaction with previously audited authorities | Why this creates ambiguity | Canonical owner | Required action |
| ----- | --------------------------------- | ----------------------------------------------- | -------------------------- | --------------- | --------------- |
| Red-tag closure truth can drift between issue prose and canonical status artifacts | `ISSUE-0014`, `ISSUE-0015` | Overlaps with previously audited `docs/testing.md`, `docs/issues/RED_TAG.md`, and gate/status artifacts. | Issue-local lifecycle narration can appear normative even when canonical gate/status outputs are the actual current truth surface. | `scripts/all_green_gate.py` outputs + `docs/qa/feature-status.yaml`/derived report + `docs/issues/RED_TAG.md` | Require issue entries to reference snapshot IDs/artifacts as truth anchors instead of restating mutable pass/fail claims. |
| Architecture migration ownership fan-out | `ISSUE-0019`, `ISSUE-0021` | Interacts with `docs/architecture-boundaries.md`, `docs/architecture.md`, and previously audited migration/governance docs. | Issue work plans include architecture-contract statements that can be mistaken as canonical architecture authority. | `docs/architecture/canonical-turn-pipeline.md`, `docs/architecture-boundaries.md`, executable tests | Add explicit “non-canonical tracker” note in issue templates or issue body convention for architecture-impact issues. |
| Quickstart behavior contract split during deprecation | `ISSUE-0020` | Interacts with previously audited `docs/quickstart.md` and test/gate artifacts. | During migration, issue text and quickstart examples can temporarily disagree on default/opt-out semantics. | Runtime code/tests + `docs/quickstart.md` | Time-box deprecation window with explicit cutover date and one canonical behavior statement in quickstart. |

## 6. Remaining-document task planning table

| Remaining document | Suspected role | Why it still needs audit | Priority | Audit tasks required | Dependencies / prerequisite evidence | Recommended future audit batch |
| ------------------ | -------------- | ------------------------ | -------- | -------------------- | ------------------------------------ | ------------------------------ |
| `AGENTS.md` | reference/meta governance | Entry-point or meta docs may subtly influence contributor behavior despite weak direct enforcement linkage. | medium | Trace entrypoint references; test for contradictions with canonical docs (`docs/testing.md`, `docs/issues.md`, `docs/architecture/plan-execution-checklist.md`); classify as active authority/reference/decorative. | Inbound-link scan and validator script behavior review. | Batch 7E: entrypoint/meta surfaces |
| `CHANGELOG.md` | reference/meta governance | Entry-point or meta docs may subtly influence contributor behavior despite weak direct enforcement linkage. | medium | Trace entrypoint references; test for contradictions with canonical docs (`docs/testing.md`, `docs/issues.md`, `docs/architecture/plan-execution-checklist.md`); classify as active authority/reference/decorative. | Inbound-link scan and validator script behavior review. | Batch 7E: entrypoint/meta surfaces |
| `docs/architecture/commit-drift-audit-2026-03-19.md` | historical/transitional planning | Time-scoped planning docs can be mistaken for current authority unless explicitly bounded. | low | Check inbound references from README/plan/checklist; determine if still decision-driving; if superseded, add explicit historical banner and pointer to canonical current owner. | `rg -n` reference scan across README/plan/checklist and issues. | Batch 7D: roadmap and retrospective framing |
| `docs/architecture/documentation-governance-audit-2026-03-21.md` | reference/meta governance | Entry-point or meta docs may subtly influence contributor behavior despite weak direct enforcement linkage. | medium | Trace entrypoint references; test for contradictions with canonical docs (`docs/testing.md`, `docs/issues.md`, `docs/architecture/plan-execution-checklist.md`); classify as active authority/reference/decorative. | Inbound-link scan and validator script behavior review. | Batch 7E: entrypoint/meta surfaces |
| `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` | reference/meta governance | Entry-point or meta docs may subtly influence contributor behavior despite weak direct enforcement linkage. | medium | Trace entrypoint references; test for contradictions with canonical docs (`docs/testing.md`, `docs/issues.md`, `docs/architecture/plan-execution-checklist.md`); classify as active authority/reference/decorative. | Inbound-link scan and validator script behavior review. | Batch 7E: entrypoint/meta surfaces |
| `docs/architecture/system-structure-audit-2026-03-19.md` | historical/transitional planning | Time-scoped planning docs can be mistaken for current authority unless explicitly bounded. | low | Check inbound references from README/plan/checklist; determine if still decision-driving; if superseded, add explicit historical banner and pointer to canonical current owner. | `rg -n` reference scan across README/plan/checklist and issues. | Batch 7D: roadmap and retrospective framing |
| `docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/coordination-failure-contract-drift-matrix.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-craap-analysis-main-alignment.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-open-questions-audit-2026-03-16.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-stabilization-checklist.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/issue-0022-pass-seven-verification-log.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/open-pr-assessment-2026-03-17.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/sprint-00-kpi-review.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/issues/evidence/work-history-assessment-2026-03-17.md` | historical evidence log | Can still be misread as live authority if linked from active issues without clear historical framing. | medium | Trace inbound links from `docs/issues.md`/`RED_TAG`; verify no CI or scripts consume it; add historical-only marker + superseded pointer if purely evidentiary. | `rg -n` inbound-link scan, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`. | Batch 7C: issue-evidence de-authority sweep |
| `docs/ops.md` | operational runbook | Contains imperative guidance that may steer release/readiness behavior. | high | Map each imperative statement to executable checks/workflows; identify duplicate policy claims vs `docs/testing.md` and gate scripts; separate advisory troubleshooting from normative policy. | `scripts/all_green_gate.py`, `.github/workflows/issue-link-validation.yml`, `docs/testing.md`. | Batch 7B: QA and runbook governance |
| `docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md` | operational runbook | Contains imperative guidance that may steer release/readiness behavior. | high | Map each imperative statement to executable checks/workflows; identify duplicate policy claims vs `docs/testing.md` and gate scripts; separate advisory troubleshooting from normative policy. | `scripts/all_green_gate.py`, `.github/workflows/issue-link-validation.yml`, `docs/testing.md`. | Batch 7B: QA and runbook governance |
| `docs/qa/feature-status-report.md` | operational runbook | Contains imperative guidance that may steer release/readiness behavior. | high | Map each imperative statement to executable checks/workflows; identify duplicate policy claims vs `docs/testing.md` and gate scripts; separate advisory troubleshooting from normative policy. | `scripts/all_green_gate.py`, `.github/workflows/issue-link-validation.yml`, `docs/testing.md`. | Batch 7B: QA and runbook governance |
| `docs/qa/live-smoke.md` | operational runbook | Contains imperative guidance that may steer release/readiness behavior. | high | Map each imperative statement to executable checks/workflows; identify duplicate policy claims vs `docs/testing.md` and gate scripts; separate advisory troubleshooting from normative policy. | `scripts/all_green_gate.py`, `.github/workflows/issue-link-validation.yml`, `docs/testing.md`. | Batch 7B: QA and runbook governance |
| `docs/qa/smoke-evidence-contract.md` | operational runbook | Contains imperative guidance that may steer release/readiness behavior. | high | Map each imperative statement to executable checks/workflows; identify duplicate policy claims vs `docs/testing.md` and gate scripts; separate advisory troubleshooting from normative policy. | `scripts/all_green_gate.py`, `.github/workflows/issue-link-validation.yml`, `docs/testing.md`. | Batch 7B: QA and runbook governance |
| `docs/regression-progression-audit-8f9317a-to-head.md` | historical/transitional planning | Time-scoped planning docs can be mistaken for current authority unless explicitly bounded. | low | Check inbound references from README/plan/checklist; determine if still decision-driving; if superseded, add explicit historical banner and pointer to canonical current owner. | `rg -n` reference scan across README/plan/checklist and issues. | Batch 7D: roadmap and retrospective framing |
| `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md` | historical/transitional planning | Time-scoped planning docs can be mistaken for current authority unless explicitly bounded. | low | Check inbound references from README/plan/checklist; determine if still decision-driving; if superseded, add explicit historical banner and pointer to canonical current owner. | `rg -n` reference scan across README/plan/checklist and issues. | Batch 7D: roadmap and retrospective framing |
| `docs/roadmap/current-status-and-next-5-priorities.md` | historical/transitional planning | Time-scoped planning docs can be mistaken for current authority unless explicitly bounded. | low | Check inbound references from README/plan/checklist; determine if still decision-driving; if superseded, add explicit historical banner and pointer to canonical current owner. | `rg -n` reference scan across README/plan/checklist and issues. | Batch 7D: roadmap and retrospective framing |
| `docs/roadmap/next-4-sprints-grounded-knowing.md` | historical/transitional planning | Time-scoped planning docs can be mistaken for current authority unless explicitly bounded. | low | Check inbound references from README/plan/checklist; determine if still decision-driving; if superseded, add explicit historical banner and pointer to canonical current owner. | `rg -n` reference scan across README/plan/checklist and issues. | Batch 7D: roadmap and retrospective framing |
| `docs/roadmap/reflective-milestone-10-sprints.md` | historical/transitional planning | Time-scoped planning docs can be mistaken for current authority unless explicitly bounded. | low | Check inbound references from README/plan/checklist; determine if still decision-driving; if superseded, add explicit historical banner and pointer to canonical current owner. | `rg -n` reference scan across README/plan/checklist and issues. | Batch 7D: roadmap and retrospective framing |
| `docs/sessions/ISSUE-0014-cross-functional-session-plan.md` | historical/transitional planning | Time-scoped planning docs can be mistaken for current authority unless explicitly bounded. | low | Check inbound references from README/plan/checklist; determine if still decision-driving; if superseded, add explicit historical banner and pointer to canonical current owner. | `rg -n` reference scan across README/plan/checklist and issues. | Batch 7D: roadmap and retrospective framing |
| `docs/style-guide.md` | reference/meta governance | Entry-point or meta docs may subtly influence contributor behavior despite weak direct enforcement linkage. | medium | Trace entrypoint references; test for contradictions with canonical docs (`docs/testing.md`, `docs/issues.md`, `docs/architecture/plan-execution-checklist.md`); classify as active authority/reference/decorative. | Inbound-link scan and validator script behavior review. | Batch 7E: entrypoint/meta surfaces |
| `docs/testing-triage.md` | operational runbook | Contains imperative guidance that may steer release/readiness behavior. | high | Map each imperative statement to executable checks/workflows; identify duplicate policy claims vs `docs/testing.md` and gate scripts; separate advisory troubleshooting from normative policy. | `scripts/all_green_gate.py`, `.github/workflows/issue-link-validation.yml`, `docs/testing.md`. | Batch 7B: QA and runbook governance |
| `examples/Experiments.md` | reference/meta governance | Entry-point or meta docs may subtly influence contributor behavior despite weak direct enforcement linkage. | medium | Trace entrypoint references; test for contradictions with canonical docs (`docs/testing.md`, `docs/issues.md`, `docs/architecture/plan-execution-checklist.md`); classify as active authority/reference/decorative. | Inbound-link scan and validator script behavior review. | Batch 7E: entrypoint/meta surfaces |
| `features/README.md` | reference/meta governance | Entry-point or meta docs may subtly influence contributor behavior despite weak direct enforcement linkage. | medium | Trace entrypoint references; test for contradictions with canonical docs (`docs/testing.md`, `docs/issues.md`, `docs/architecture/plan-execution-checklist.md`); classify as active authority/reference/decorative. | Inbound-link scan and validator script behavior review. | Batch 7E: entrypoint/meta surfaces |
| `src/seem_bot/README.md` | reference/meta governance | Entry-point or meta docs may subtly influence contributor behavior despite weak direct enforcement linkage. | medium | Trace entrypoint references; test for contradictions with canonical docs (`docs/testing.md`, `docs/issues.md`, `docs/architecture/plan-execution-checklist.md`); classify as active authority/reference/decorative. | Inbound-link scan and validator script behavior review. | Batch 7E: entrypoint/meta surfaces |

## 7. Coverage progression summary

| Audit pass | Date | Newly audited Markdown files | Total audited Markdown files after pass | Remaining Markdown files after pass | Notes |
| ---------- | ---- | ---------------------------- | --------------------------------------- | ----------------------------------- | ----- |
| Anchor audit | 2026-03-21 | 11 | 11 | 96 | Established methodology and initial out-of-scope backlog. |
| Follow-up pass 1 | 2026-03-21 | 9 | 20 | 87 | Audited entrypoint + directives + quickstart/invariants layer. |
| Follow-up pass 2 | 2026-03-21 | 5 | 25 | 82 | Audited canonical pipeline + boundary evidence/matrix surfaces. |
| Follow-up pass 3 | 2026-03-21 | 7 | 32 | 75 | Audited governance tracker layer (`docs/governance/*`). |
| Follow-up pass 4 | 2026-03-21 | 6 | 38 | 69 | Audited RED_TAG + active issue contract layer. |
| Follow-up pass 5 | 2026-03-21 | 5 | 43 | 64 | Audited foundational issue-governance origin set (`ISSUE-0001`..`0005`). |
| Follow-up pass 6 | 2026-03-21 | 6 | 49 historical audited / 48 current audited | 59 | Audited active issue-control tranche (`ISSUE-0006`..`0011`). |
| Follow-up pass 7 (this pass) | 2026-03-21 | 5 | 54 historical audited / 53 current audited | 54 | Audited remaining active issue-control tranche (`ISSUE-0014`, `0015`, `0019`, `0020`, `0021`). |

## 8. Minimal next-step sequence

1. **Next batch to audit:** `docs/ops.md`, `docs/testing-triage.md`, `docs/qa/feature-status-report.md`, `docs/qa/live-smoke.md`, `docs/qa/smoke-evidence-contract.md`, and `docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md`.
2. **Why that batch should come next:** these are the highest-risk remaining docs for practical governance fan-out because they translate policy/issues into day-to-day readiness and review behavior.
3. **Evidence to gather first:**
   - inbound-link traces from README/contributor docs/issues/RED_TAG,
   - mapping of imperative statements to executable checks/workflows,
   - gate-status and feature-status artifact usage in these runbooks,
   - any contradictions with `docs/testing.md` and `docs/issues.md`.
4. **Repository-level uncertainty reduced by doing so:** whether operational runbooks are currently canonical decision surfaces or merely reference/troubleshooting aids, and where to collapse duplicate readiness authority.
