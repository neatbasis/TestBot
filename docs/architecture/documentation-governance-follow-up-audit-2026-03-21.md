# Documentation Governance Follow-up Audit — Structural Honesty (2026-03-21)

## 1. Scope accounting
This continuation pass is explicitly anchored to `docs/architecture/documentation-governance-audit-2026-03-21.md` and starts from that anchor audit’s out-of-scope Markdown list as the authoritative backlog seed.

Baseline method used before scope selection in this pass:
1. Read anchor audit and extract its out-of-scope Markdown backlog.
2. Compare backlog to current repository Markdown inventory.
3. Reconstruct previously audited scope from prior follow-up sections/tables in this file.
4. Compute remaining unaudited files from that seed set plus repository-delta files.
5. Select a bounded subset only from remaining unaudited files.

Current accounting for this pass:
- Total Markdown files currently in repo: **108**.
- Markdown files already covered by previous documentation governance audits (before this pass): **60 current files**.
- Markdown files newly selected for this audit pass: **3**.
- Markdown files still not yet audited after selection: **45**.
- Non-Markdown enforcement artifacts reviewed for evidence in this pass: `scripts/all_green_gate.py`, `.github/workflows/issue-link-validation.yml` (absence check for audit-doc linkage), and repository-wide reference scans via `rg`.

Scope reconstruction note: prior follow-up scope was reconstructed from the existing follow-up document’s earlier pass content (coverage table, scope lists, and findings tables). No explicit separate machine manifest of prior follow-up scope exists.

Repository-delta note from anchor snapshot reconciliation:
- `.github/PULL_REQUEST_TEMPLATE.md` is present in the current repo and treated as already audited via the anchor audit scope.
- `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` is a repository-addition relative to the anchor’s listed out-of-scope set and is tracked as remaining until explicitly audited as a governance artifact.

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
- `docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
- `docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md`
- `docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md`
- `docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md`
- `docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md`
- `docs/ops.md`
- `docs/testing-triage.md`
- `docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md`
- `docs/qa/feature-status-report.md`
- `docs/qa/live-smoke.md`
- `docs/qa/smoke-evidence-contract.md`

### 1.2 Candidate remaining Markdown files
- `.github/PULL_REQUEST_TEMPLATE.md` was removed from this candidate set because it is already in prior audited scope.
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
- `docs/regression-progression-audit-8f9317a-to-head.md`
- `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md`
- `docs/roadmap/current-status-and-next-5-priorities.md`
- `docs/roadmap/next-4-sprints-grounded-knowing.md`
- `docs/roadmap/reflective-milestone-10-sprints.md`
- `docs/sessions/ISSUE-0014-cross-functional-session-plan.md`
- `docs/style-guide.md`
- `examples/Experiments.md`
- `features/README.md`
- `src/seem_bot/README.md`

### 1.3 Newly selected files for this audit pass
- `docs/architecture/commit-drift-audit-2026-03-19.md`
- `docs/architecture/system-structure-audit-2026-03-19.md`
- `docs/architecture/documentation-governance-audit-2026-03-21.md`

Selection rationale: these three files were selected from the remaining pool because they are architecture/governance audit artifacts that are actively linked from `plan.md` and can therefore still influence contributor decisions despite being date-stamped. Auditing them now reduces the risk that historical snapshots are misread as current policy owners.

### 1.4 Remaining files not audited in this pass
- `AGENTS.md`
- `CHANGELOG.md`
- `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`
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
- `docs/regression-progression-audit-8f9317a-to-head.md`
- `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md`
- `docs/roadmap/current-status-and-next-5-priorities.md`
- `docs/roadmap/next-4-sprints-grounded-knowing.md`
- `docs/roadmap/reflective-milestone-10-sprints.md`
- `docs/sessions/ISSUE-0014-cross-functional-session-plan.md`
- `docs/style-guide.md`
- `examples/Experiments.md`
- `features/README.md`
- `src/seem_bot/README.md`

## 2. Scope selection rationale
These three documents were selected now because they are the highest-priority remaining files for governance clarity among the unaudited architecture subset:

1. `docs/architecture/system-structure-audit-2026-03-19.md` is repeatedly linked from `plan.md` as an architecture-risk explainer, so stale normative language there can directly affect implementation sequencing.
2. `docs/architecture/commit-drift-audit-2026-03-19.md` contains explicit “recommended corrective actions” and therefore can be misread as live control direction unless classified.
3. `docs/architecture/documentation-governance-audit-2026-03-21.md` is the anchor audit itself; auditing its present operational role clarifies that methodology authority remains useful while date-specific findings remain historical.

Why these before other remaining files:
- They have more direct governance impact than evidence snapshots because they discuss architecture/control posture and are linked from active planning surfaces.
- They are more decision-shaping than roadmap/session notes because they include corrective-action and enforcement framing.

Uncertainty reduced in this pass:
- whether these dated audits still act as live policy owners,
- whether architecture extraction advice in dated audits conflicts with current canonical owners,
- and whether governance-audit documents are historical records versus active authority.

## 3. Executive summary
Repository Markdown coverage is now **63/108 (58.3%)** after auditing three previously unaudited architecture/governance audit documents in this pass. The newly selected documents that materially affect governance clarity are `docs/architecture/system-structure-audit-2026-03-19.md` (linked in `plan.md` for extraction sequencing) and `docs/architecture/commit-drift-audit-2026-03-19.md` (contains remediation recommendations), while `docs/architecture/documentation-governance-audit-2026-03-21.md` remains the methodological anchor but should be treated as a dated findings snapshot. Newly surfaced split-authority risk is limited but real: dated audit recommendations can be mistaken for current canonical policy unless each audit is explicitly framed as historical/reference and routed to current canonical owners. The most important next tasks are (a) auditing `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` as an active transition ledger, and then (b) sweeping issue-evidence files to prevent historical artifacts from masquerading as present governance truth.

## 4. Audit findings for newly selected documents

| Document | Claimed purpose | Actual role in practice | Evidence | Classification | Governance risk | Action |
| -------- | --------------- | ----------------------- | -------- | -------------- | --------------- | ------ |
| `docs/architecture/system-structure-audit-2026-03-19.md` | Diagnose architecture collapse points and extraction protocol. | Hybrid historical/reference artifact: still used as an explainer for extraction risk, but many claims are date-scoped snapshots rather than current authority. | Linked multiple times from `plan.md`; not consumed by scripts/workflows; contains dated “historical snapshot/current state” framing. | historical | medium | Keep as historical risk context; add explicit pointer to current canonical owners for live decisions (`docs/architecture/plan-execution-checklist.md`, `docs/testing.md`, gate artifacts). |
| `docs/architecture/commit-drift-audit-2026-03-19.md` | Commit-by-commit progression/regression audit and corrective actions. | Historical audit log with transitional guidance; useful for provenance but not governance control. | Date-window method and commit ledger; includes “recommended corrective actions”; no script/workflow references detected. | historical | medium | Mark recommendations as superseded-by-current-authorities and prevent this file from being cited as active policy. |
| `docs/architecture/documentation-governance-audit-2026-03-21.md` | Structural-honesty audit establishing method and initial authority map. | Dual role: methodological anchor for follow-up process plus historical findings snapshot tied to the 2026-03-21 repo state. | Follow-up audit explicitly uses this file as backlog/method anchor; out-of-scope list seeds continuation accounting; no executable enforcement binding. | reference | medium | Preserve method sections as stable reference, but clearly label findings tables as date-bounded and non-canonical for current enforcement state. |

## 5. Newly discovered split-authority or duplication findings

| Topic | Newly selected documents involved | Interaction with previously audited authorities | Why this creates ambiguity | Canonical owner | Required action |
| ----- | --------------------------------- | ----------------------------------------------- | -------------------------- | --------------- | --------------- |
| Dated audit recommendations read as live architecture policy | `docs/architecture/system-structure-audit-2026-03-19.md`, `docs/architecture/commit-drift-audit-2026-03-19.md` | Interacts with `plan.md`, `docs/architecture/plan-execution-checklist.md`, and `docs/testing.md`. | Contributor may follow legacy corrective steps instead of current checklist/gate truth. | `docs/architecture/plan-execution-checklist.md` + executable checks in `scripts/all_green_gate.py`/tests | Add explicit “for historical context only” banner where recommendations are no longer operative; add direct canonical-owner links near recommendation sections. |
| Methodology authority vs findings authority conflation | `docs/architecture/documentation-governance-audit-2026-03-21.md` | Interacts with this follow-up audit file as process anchor. | Readers can misinterpret dated findings as still-canonical because method and findings coexist in one document. | Follow-up series process in `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`; live policy owners remain canonical docs/scripts | Separate “method contract” and “dated findings” framing within anchor audit via clear labels in future cleanup pass. |
## 6. Remaining-document task planning table

| Remaining document | Suspected role | Why it still needs audit | Priority | Audit tasks required | Dependencies / prerequisite evidence | Recommended future audit batch |
| ------------------ | -------------- | ------------------------ | -------- | -------------------- | ------------------------------------ | ------------------------------ |
| `AGENTS.md` | entrypoint/reference | These files influence contributor behavior even when not directly enforced. | medium | Map contributor-facing instructions to enforced checks; flag any normative statements without executable backing; classify canonical/reference/decorative. | CONTRIBUTING.md; docs/issues.md; docs/testing.md; workflows | Batch 9D: entrypoint and contributor-surface review |
| `CHANGELOG.md` | entrypoint/reference | These files influence contributor behavior even when not directly enforced. | medium | Map contributor-facing instructions to enforced checks; flag any normative statements without executable backing; classify canonical/reference/decorative. | CONTRIBUTING.md; docs/issues.md; docs/testing.md; workflows | Batch 9D: entrypoint and contributor-surface review |
| `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` | historical audit/control narrative | Architecture audit docs can be mistaken for current canonical control statements. | high | Map each normative claim to current canonical owners (checklist, testing, gate scripts); mark superseded vs still-operational guidance; identify duplicated authority text. | docs/architecture/plan-execution-checklist.md; docs/testing.md; scripts/all_green_gate.py | Batch 9A: architecture audit-history reconciliation |
| `docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/coordination-failure-contract-drift-matrix.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-craap-analysis-main-alignment.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-open-questions-audit-2026-03-16.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-stabilization-checklist.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/issue-0022-pass-seven-verification-log.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/open-pr-assessment-2026-03-17.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/sprint-00-kpi-review.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/issues/evidence/work-history-assessment-2026-03-17.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound links from docs/issues.md, RED_TAG, and open issues; verify no CI/script consumer; determine if historical banner + superseded pointer is required. | rg -n link scan; scripts/validate_issue_links.py; scripts/validate_issues.py | Batch 9B: issue-evidence de-authority sweep |
| `docs/regression-progression-audit-8f9317a-to-head.md` | transitional planning/history | Planning snapshots may still drive contributor decisions if referenced from active docs. | medium | Trace references from README/issues/testing docs; test whether status claims conflict with feature-status artifacts; classify as transitional vs historical. | docs/qa/feature-status-report.md; artifacts/all-green-gate-summary.json; rg -n reference scan | Batch 9C: roadmap and session authority cleanup |
| `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md` | transitional planning/history | Planning snapshots may still drive contributor decisions if referenced from active docs. | medium | Trace references from README/issues/testing docs; test whether status claims conflict with feature-status artifacts; classify as transitional vs historical. | docs/qa/feature-status-report.md; artifacts/all-green-gate-summary.json; rg -n reference scan | Batch 9C: roadmap and session authority cleanup |
| `docs/roadmap/current-status-and-next-5-priorities.md` | transitional planning/history | Planning snapshots may still drive contributor decisions if referenced from active docs. | medium | Trace references from README/issues/testing docs; test whether status claims conflict with feature-status artifacts; classify as transitional vs historical. | docs/qa/feature-status-report.md; artifacts/all-green-gate-summary.json; rg -n reference scan | Batch 9C: roadmap and session authority cleanup |
| `docs/roadmap/next-4-sprints-grounded-knowing.md` | transitional planning/history | Planning snapshots may still drive contributor decisions if referenced from active docs. | medium | Trace references from README/issues/testing docs; test whether status claims conflict with feature-status artifacts; classify as transitional vs historical. | docs/qa/feature-status-report.md; artifacts/all-green-gate-summary.json; rg -n reference scan | Batch 9C: roadmap and session authority cleanup |
| `docs/roadmap/reflective-milestone-10-sprints.md` | transitional planning/history | Planning snapshots may still drive contributor decisions if referenced from active docs. | medium | Trace references from README/issues/testing docs; test whether status claims conflict with feature-status artifacts; classify as transitional vs historical. | docs/qa/feature-status-report.md; artifacts/all-green-gate-summary.json; rg -n reference scan | Batch 9C: roadmap and session authority cleanup |
| `docs/sessions/ISSUE-0014-cross-functional-session-plan.md` | transitional planning/history | Planning snapshots may still drive contributor decisions if referenced from active docs. | medium | Trace references from README/issues/testing docs; test whether status claims conflict with feature-status artifacts; classify as transitional vs historical. | docs/qa/feature-status-report.md; artifacts/all-green-gate-summary.json; rg -n reference scan | Batch 9C: roadmap and session authority cleanup |
| `docs/style-guide.md` | entrypoint/reference | These files influence contributor behavior even when not directly enforced. | medium | Map contributor-facing instructions to enforced checks; flag any normative statements without executable backing; classify canonical/reference/decorative. | CONTRIBUTING.md; docs/issues.md; docs/testing.md; workflows | Batch 9D: entrypoint and contributor-surface review |
| `examples/Experiments.md` | entrypoint/reference | These files influence contributor behavior even when not directly enforced. | medium | Map contributor-facing instructions to enforced checks; flag any normative statements without executable backing; classify canonical/reference/decorative. | CONTRIBUTING.md; docs/issues.md; docs/testing.md; workflows | Batch 9D: entrypoint and contributor-surface review |
| `features/README.md` | entrypoint/reference | These files influence contributor behavior even when not directly enforced. | medium | Map contributor-facing instructions to enforced checks; flag any normative statements without executable backing; classify canonical/reference/decorative. | CONTRIBUTING.md; docs/issues.md; docs/testing.md; workflows | Batch 9D: entrypoint and contributor-surface review |
| `src/seem_bot/README.md` | entrypoint/reference | These files influence contributor behavior even when not directly enforced. | medium | Map contributor-facing instructions to enforced checks; flag any normative statements without executable backing; classify canonical/reference/decorative. | CONTRIBUTING.md; docs/issues.md; docs/testing.md; workflows | Batch 9D: entrypoint and contributor-surface review |

## 7. Coverage progression summary

| Audit pass | Date | Newly audited Markdown files | Total audited Markdown files after pass | Remaining Markdown files after pass | Notes |
| ---------- | ---- | ---------------------------- | --------------------------------------- | ----------------------------------- | ----- |
| Anchor audit | 2026-03-21 | 11 | 11 | 96 | Established structural-honesty method and initial out-of-scope backlog seed. |
| Follow-up pass 1 | 2026-03-21 | 9 | 20 | 87 | Audited entrypoint/directives/quickstart/invariants tranche. |
| Follow-up pass 2 | 2026-03-21 | 5 | 25 | 82 | Audited canonical pipeline + boundary contract surfaces. |
| Follow-up pass 3 | 2026-03-21 | 7 | 32 | 75 | Audited governance tracker layer (`docs/governance/*`). |
| Follow-up pass 4 | 2026-03-21 | 6 | 38 | 69 | Audited `RED_TAG` and active issue contract layer (part 1). |
| Follow-up pass 5 | 2026-03-21 | 5 | 43 | 64 | Audited foundational issue-governance origin set (`ISSUE-0001`..`0005`). |
| Follow-up pass 6 | 2026-03-21 | 6 | 49 historical / 48 current | 59 | Audited active issue-control tranche (`ISSUE-0006`..`0011`). |
| Follow-up pass 7 | 2026-03-21 | 5 | 54 historical / 53 current | 54 | Audited remaining active issue-control tranche (`ISSUE-0014`, `0015`, `0019`, `0020`, `0021`). |
| Follow-up pass 8 | 2026-03-21 | 6 | 61 historical / 60 current | 48 | Audited QA+operations runbook/status tranche (`docs/ops.md`, `docs/testing-triage.md`, `docs/qa/*` selected set). |
| Follow-up pass 9 (this pass) | 2026-03-21 | 3 | 64 historical / 63 current | 45 | Audited architecture/governance audit-history tranche (`commit-drift`, `system-structure`, and anchor documentation-governance audit). |

## 8. Minimal next-step sequence

1. **Next batch to audit:** `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`, `AGENTS.md`, `CHANGELOG.md`, `docs/style-guide.md`, `features/README.md`, and `src/seem_bot/README.md`.
2. **Why this batch should come next:** this set controls contributor entry behavior and process interpretation; unresolved classification here can still redirect implementation/review choices even without executable binding.
3. **Evidence to gather first:**
   - inbound-link trace from `README.md`, `CONTRIBUTING.md`, `plan.md`, and issue workflow docs,
   - script/workflow scans confirming whether any of these docs are consumed by automation,
   - conflict checks between stated contributor rules and canonical enforcement owners (`docs/issues.md`, `docs/testing.md`, `scripts/all_green_gate.py`).
4. **Repository-level uncertainty reduced:** whether remaining entrypoint/process docs are operational references, decorative guidance, or hidden authority surfaces that still fragment governance.

Practical completeness check for this pass:
- Prior/current/remaining scope are explicitly separated.
- Coverage progressed into previously unaudited files (3 files).
- Every remaining unaudited Markdown file has one concrete task-plan row.
