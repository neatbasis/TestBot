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
- Markdown files already covered by previous documentation governance audits (before this pass): **54 current files**.
- Markdown files newly selected for this audit pass: **6**.
- Markdown files still not yet audited after selection: **48**.
- Non-Markdown enforcement artifacts reviewed for evidence in this pass: `scripts/all_green_gate.py`, `scripts/report_feature_status.py`, `scripts/smoke/run_live_smoke.sh`, `scripts/smoke/run_live_smoke.py`, `scripts/triage_router.py`, `scripts/validate_roadmap_consistency.py`, `.github/workflows/issue-link-validation.yml`, `docs/qa/feature-status.yaml`.

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
- `docs/ops.md`
- `docs/testing-triage.md`
- `docs/qa/feature-status-report.md`
- `docs/qa/live-smoke.md`
- `docs/qa/smoke-evidence-contract.md`
- `docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md`

Selection rationale: these six files were the highest-priority remaining tranche because they directly shape day-to-day operator/reviewer decisions (triage routing, gate interpretation, live smoke evidence handling, and status interpretation) and therefore have high risk of governance fan-out if they drift from canonical gate outputs.

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
These six files were selected now because they are the highest remaining governance-leverage documents in the unaudited pool:

1. They are operationally referenced by issue workflow and status-generation paths (`docs/issues.md` points to feature-status generation/review; scripts consume feature-status contracts and emit guidance that reviewers treat as release evidence).
2. They shape contributor behavior in failure conditions (`docs/testing-triage.md`, `docs/ops.md`, and smoke docs prescribe owner routing, escalation flow, and verification commands).
3. They can create split authority against already-audited canonical surfaces (`docs/testing.md`, `docs/issues.md`, `scripts/all_green_gate.py`) if they restate policy rather than linking to canonical policy owners.

Why they were chosen ahead of other remaining files:
- They have immediate reviewer/operator effect and can alter merge-readiness interpretation.
- Most remaining files are historical evidence snapshots or roadmap/session records; those are important, but lower immediate blast radius than current runbooks and status reports.

Uncertainty reduced in this pass:
- whether these runbooks are canonical or merely operational/reference,
- where status truth actually lives when generated report text and gate artifacts differ,
- whether live-smoke contracts are enforceable governance or execution guidance.

## 3. Executive summary
Repository Markdown coverage is now **60/108 (55.6%)** after auditing six previously unaudited QA/operations documents in this pass. The newly selected documents that materially affect governance clarity are `docs/qa/feature-status-report.md`, `docs/testing-triage.md`, and the live-smoke contract pair (`docs/qa/live-smoke.md`, `docs/qa/smoke-evidence-contract.md`), because they influence how contributors interpret readiness, route failures, and record evidence. New split-authority findings surfaced around (a) generated feature-status report text being treated as policy rather than derived output, and (b) live-smoke sequencing language potentially competing with canonical issue/governance owners. The most important next tasks are to de-authority and classify the remaining architecture-audit/history docs and then sweep issue evidence files so historical snapshots cannot be mistaken for current governance truth.

## 4. Audit findings for newly selected documents

| Document | Claimed purpose | Actual role in practice | Evidence | Classification | Governance risk | Action |
| -------- | --------------- | ----------------------- | -------- | -------------- | --------------- | ------ |
| `docs/ops.md` | Central operations troubleshooting and runtime guidance. | Operational runbook with mixed concerns (log schema, KPI policy, troubleshooting, and source-ingestion examples) that can influence release interpretation even though checks are enforced elsewhere. | Contains gate-mode guidance and threshold language while enforcement is implemented in scripts; includes direct command paths but no direct CI binding. | operational | medium | Keep runbook role; convert policy-like threshold/phase text to links to canonical script/config owners. |
| `docs/testing-triage.md` | Default owner/action map for readiness failures. | Operational routing guide that standardizes human response, while authoritative lifecycle/severity remains in `docs/issues.md` and validators. | Explicitly defers to `docs/issues.md`; introduces triage-router workflow that is optional and not sole source of severity truth. | operational | low | Keep as operational mapping; add explicit “non-canonical severity owner” note near routing tables. |
| `docs/qa/feature-status-report.md` | Generated capability status report for readiness interpretation. | Derived evidence artifact (reference snapshot) that is consumed by humans and cross-linked by issue/governance docs; not primary policy owner. | Generated by `scripts/report_feature_status.py`; report itself says gate snapshot artifact is authoritative for gate-state fields; linked from issue workflow. | reference | high | Treat as generated reference only; avoid embedding durable policy statements in the generated report body. |
| `docs/qa/live-smoke.md` | Configure/run live smoke checks and environment requirements. | Operational execution guide with some transitional sequencing authority tied to specific issue IDs. | Defines required env vars and commands; includes explicit routing to ISSUE-0013 for defect sequencing, creating issue-level governance coupling. | operational | medium | Keep execution instructions; move sequencing/precedence policy language into canonical issue/governance owners and keep this as procedure-only. |
| `docs/qa/smoke-evidence-contract.md` | Define deterministic smoke artifact schema/contract. | Reference contract for smoke evidence shape; functionally tied to smoke scripts and capability map rather than standalone authority. | Specifies artifact fields and deterministic guarantees; binds to `scripts/smoke/run_live_smoke.sh` and capability map file. | reference | medium | Maintain as schema reference; add explicit owner mapping to script/tests for field-level truth. |
| `docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md` | Alignment review across architecture→evidence chain. | Historical analysis snapshot with recommendations; not active canonical authority but could be misread as current because it references active issue IDs and commands. | Date-stamped review; recommendations depend on specific historical gate state. | historical | low | Add/retain clear historical framing and avoid using as current policy source in active docs. |

## 5. Newly discovered split-authority or duplication findings

| Topic | Newly selected documents involved | Interaction with previously audited authorities | Why this creates ambiguity | Canonical owner | Required action |
| ----- | --------------------------------- | ----------------------------------------------- | -------------------------- | --------------- | --------------- |
| Generated status report interpreted as normative policy | `docs/qa/feature-status-report.md` | Interacts with `docs/issues.md`, `docs/testing.md`, and gate artifacts. | Contributors may treat generated prose as policy even though it is derived from contracts/artifacts and can lag regeneration. | `scripts/report_feature_status.py` inputs + `artifacts/all-green-gate-summary.json` for gate state | Preserve generated-only framing and require references to source artifacts for any enforcement claim. |
| Live-smoke sequencing language vs canonical issue/governance lifecycle | `docs/qa/live-smoke.md`, `docs/qa/smoke-evidence-contract.md` | Interacts with `docs/issues.md`, `docs/issues/RED_TAG.md`, and ISSUE-0013 tracker. | Procedure docs include issue-precedence wording that can look like governance policy ownership. | `docs/issues.md` + active issue records (`ISSUE-0013`/`RED_TAG`) | Keep smoke docs procedural; centralize lifecycle precedence in issue governance docs and link out. |
| Triage owner mapping duplicated across runbooks and issue policy | `docs/testing-triage.md`, `docs/ops.md` | Interacts with canonical lifecycle and severity semantics in `docs/issues.md`. | Owner/action maps can be misread as severity authority if not clearly scoped as recommendation. | `docs/issues.md` and issue validators | Add explicit scope note: triage map suggests routing only; severity/status truth is issue workflow authority. |

## 6. Remaining-document task planning table

| Remaining document | Suspected role | Why it still needs audit | Priority | Audit tasks required | Dependencies / prerequisite evidence | Recommended future audit batch |
| ------------------ | -------------- | ------------------------ | -------- | -------------------- | ------------------------------------ | ------------------------------ |
| `AGENTS.md` | entrypoint/reference | These files influence contributor behavior even when not directly enforced. | medium | Map contributor-facing instructions to enforced checks; flag any normative statements without executable backing; classify canonical/reference/decorative. | CONTRIBUTING.md; docs/issues.md; docs/testing.md; workflows | Batch 9D: entrypoint and contributor-surface review |
| `CHANGELOG.md` | entrypoint/reference | These files influence contributor behavior even when not directly enforced. | medium | Map contributor-facing instructions to enforced checks; flag any normative statements without executable backing; classify canonical/reference/decorative. | CONTRIBUTING.md; docs/issues.md; docs/testing.md; workflows | Batch 9D: entrypoint and contributor-surface review |
| `docs/architecture/commit-drift-audit-2026-03-19.md` | historical audit/control narrative | Architecture audit docs can be mistaken for current canonical control statements. | high | Map each normative claim to current canonical owners (checklist, testing, gate scripts); mark superseded vs still-operational guidance; identify duplicated authority text. | docs/architecture/plan-execution-checklist.md; docs/testing.md; scripts/all_green_gate.py | Batch 9A: architecture audit-history reconciliation |
| `docs/architecture/documentation-governance-audit-2026-03-21.md` | historical audit/control narrative | Architecture audit docs can be mistaken for current canonical control statements. | high | Map each normative claim to current canonical owners (checklist, testing, gate scripts); mark superseded vs still-operational guidance; identify duplicated authority text. | docs/architecture/plan-execution-checklist.md; docs/testing.md; scripts/all_green_gate.py | Batch 9A: architecture audit-history reconciliation |
| `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` | historical audit/control narrative | Architecture audit docs can be mistaken for current canonical control statements. | high | Map each normative claim to current canonical owners (checklist, testing, gate scripts); mark superseded vs still-operational guidance; identify duplicated authority text. | docs/architecture/plan-execution-checklist.md; docs/testing.md; scripts/all_green_gate.py | Batch 9A: architecture audit-history reconciliation |
| `docs/architecture/system-structure-audit-2026-03-19.md` | historical audit/control narrative | Architecture audit docs can be mistaken for current canonical control statements. | high | Map each normative claim to current canonical owners (checklist, testing, gate scripts); mark superseded vs still-operational guidance; identify duplicated authority text. | docs/architecture/plan-execution-checklist.md; docs/testing.md; scripts/all_green_gate.py | Batch 9A: architecture audit-history reconciliation |
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
| Follow-up pass 8 (this pass) | 2026-03-21 | 6 | 61 historical / 60 current | 48 | Audited QA+operations runbook/status tranche (`docs/ops.md`, `docs/testing-triage.md`, `docs/qa/*` selected set). |

## 8. Minimal next-step sequence

1. **Next batch to audit:** `docs/architecture/commit-drift-audit-2026-03-19.md`, `docs/architecture/system-structure-audit-2026-03-19.md`, `docs/architecture/documentation-governance-audit-2026-03-21.md`, and `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`.
2. **Why this batch should come next:** these documents can silently retain stale normative statements and create self-referential authority loops if not explicitly classed as historical/transitional.
3. **Evidence to gather first:**
   - reference trace showing where these audits are linked from current contributor/governance entrypoints,
   - comparison of each claim against current canonical owners (`docs/architecture/plan-execution-checklist.md`, `docs/testing.md`, `scripts/all_green_gate.py`),
   - validation of whether any enforcement script/workflow still depends on these audit documents.
4. **Repository-level uncertainty reduced:** whether architecture/governance audit-history documents are purely historical artifacts or still acting as implicit policy owners that fragment authority.

Practical completeness check for this pass:
- Prior/current/remaining scope are explicitly separated.
- Coverage progressed into previously unaudited files (6 files).
- Every remaining unaudited Markdown file has one concrete task-plan row.
