# Documentation Governance Follow-up Audit — Structural Honesty (2026-03-21)

## 1. Scope accounting
This continuation pass remains anchored to `docs/architecture/documentation-governance-audit-2026-03-21.md` and uses that anchor audit’s out-of-scope Markdown list as the authoritative backlog seed.

Baseline method executed before selecting scope for this pass:
1. Read the anchor audit and extract its out-of-scope Markdown backlog.
2. Compare that backlog with the current repository Markdown inventory.
3. Reconstruct previously audited follow-up scope from this file’s prior scope/finding tables.
4. Compute remaining unaudited files from the anchor backlog plus repository-delta Markdown additions.
5. Select a bounded subset only from the remaining unaudited files.

Current accounting for this pass:
- Total Markdown files currently in repo: **108**.
- Markdown files already covered by previous documentation governance audits (before this pass): **67 current files**.
- Markdown files newly selected for this audit pass: **5**.
- Markdown files still not yet audited after selection: **36**.
- Non-Markdown enforcement artifacts reviewed for evidence in this pass: `scripts/all_green_gate.py`, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`, `.github/workflows/issue-link-validation.yml`, plus repository-wide reference scans via `rg`.

Scope reconstruction note: prior follow-up scope was reconstructed from the existing follow-up audit content (scope sections, findings tables, remaining-task table, and coverage progression table). No separate prior-scope manifest exists.

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
- `docs/architecture/commit-drift-audit-2026-03-19.md`
- `docs/architecture/system-structure-audit-2026-03-19.md`
- `docs/architecture/documentation-governance-audit-2026-03-21.md`
- `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`
- `AGENTS.md`
- `docs/style-guide.md`
- `CHANGELOG.md`

### 1.2 Candidate remaining Markdown files
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
- `examples/Experiments.md`
- `features/README.md`
- `src/seem_bot/README.md`

### 1.3 Newly selected files for this audit pass
- `docs/roadmap/current-status-and-next-5-priorities.md`
- `docs/roadmap/next-4-sprints-grounded-knowing.md`
- `features/README.md`
- `docs/regression-progression-audit-8f9317a-to-head.md`
- `docs/sessions/ISSUE-0014-cross-functional-session-plan.md`

Selection rationale: these five were selected because they are directly linked from contributor-facing surfaces (`README.md` and active issue docs) and contain process-shaping language that can influence implementation and review behavior now, unlike most remaining evidence files that are primarily historical logs.

### 1.4 Remaining files not audited in this pass
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
- `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md`
- `docs/roadmap/reflective-milestone-10-sprints.md`
- `examples/Experiments.md`
- `src/seem_bot/README.md`

## 2. Scope selection rationale
This pass prioritized documents from the remaining pool that most affect governance clarity and contributor behavior in active flows:

1. `README.md` links `docs/roadmap/next-4-sprints-grounded-knowing.md` and `docs/roadmap/current-status-and-next-5-priorities.md` as live roadmap/status surfaces, so these can become de facto decision authority if not structurally classified.
2. `features/README.md` provides mandatory-looking BDD workflow/tagging language that can influence review and test authoring norms across contributor paths.
3. `docs/sessions/ISSUE-0014-cross-functional-session-plan.md` is linked from the active ISSUE-0014 record and could be mistaken for standing policy if not bounded as session-scoped/transitional.
4. `docs/regression-progression-audit-8f9317a-to-head.md` is an audit narrative with architecture claims; it needed classification to prevent historical findings from being interpreted as current canonical doctrine.

Why these before the other remaining files:
- They are directly connected to present contributor guidance and planning paths (README and open issue references).
- They have a higher probability of causing split authority with already-audited canonical owners (`docs/testing.md`, `docs/architecture/plan-execution-checklist.md`, `docs/issues.md`) than isolated evidence logs.

Uncertainty reduced by this pass:
- Whether roadmap/status docs are canonical policy vs transitional program references.
- Whether BDD README guidance is operationally enforced or advisory.
- Whether session/audit artifacts are historical/transitional only versus decision-authority sources.

## 3. Executive summary
Repository Markdown coverage is now **72/108 (66.7%)** after auditing five previously unaudited files in this pass. The newly selected documents that materially affect governance clarity are the two roadmap/status files linked from `README.md`, `features/README.md` (which carries mandatory-style behavior-spec guidance), and the session/audit artifacts that could otherwise be misread as standing policy authority. Newly surfaced split-authority risk is concentrated in roadmap/status language that references gate/readiness and “required” process semantics while canonical enforcement still lives in scripts/workflows. The most important next tasks are a full `docs/issues/evidence/*` de-authority sweep and then finishing the remaining roadmap/history contributor surfaces (`docs/roadmap/alignment-drift-technical-debt-2026-03-05.md`, `docs/roadmap/reflective-milestone-10-sprints.md`, `examples/Experiments.md`, `src/seem_bot/README.md`).

## 4. Audit findings for newly selected documents

| Document | Claimed purpose | Actual role in practice | Evidence | Classification | Governance risk | Action |
| -------- | --------------- | ----------------------- | -------- | -------------- | --------------- | ------ |
| `docs/roadmap/current-status-and-next-5-priorities.md` | Current capability/gate status and next priorities. | Transitional operational status ledger referenced from README; influences prioritization but not executable authority. | README links it as “Current status”; file contains snapshot timestamps and gate command interpretation language, but no CI/script consumes it directly. | transitional | medium | Keep as status projection only; explicitly defer gate truth to generated artifacts and canonical testing docs. |
| `docs/roadmap/next-4-sprints-grounded-knowing.md` | Four-sprint execution roadmap with exits/checkpoints. | Transitional planning authority that can steer implementation sequencing; not canonical runtime policy owner. | README links it as roadmap; includes mandatory-style checkpoint/DoD language referencing canonical docs and commands, with no direct enforcement consumer. | transitional | medium | Keep as planning decomposition; avoid normative wording that conflicts with canonical owners (`docs/testing.md`, issue program docs). |
| `features/README.md` | BDD/Gherkin usage guide for TestBot feature work. | High-impact contributor reference for test authoring conventions; partially operational through human workflow but not machine-enforced itself. | Contains mandatory phrasing for tags/ownership/grain; behavior is executable only when corresponding features/tests run, and no dedicated linter/CI step was found for this README itself. | operational | medium | Retain as contributor playbook; mark mandatory claims as “validated by X checks” or downgrade to advisory where unvalidated. |
| `docs/regression-progression-audit-8f9317a-to-head.md` | Point-in-time regression/progression audit narrative. | Historical audit evidence with architectural interpretation context; not active decision authority. | File self-labels as point-in-time and non-normative; no inbound references from README/testing entrypoints discovered. | historical | low | Keep as historical evidence; add/retain explicit supersession pointer to current canonical architecture/testing owners. |
| `docs/sessions/ISSUE-0014-cross-functional-session-plan.md` | Timeboxed working-session execution plan for ISSUE-0014. | Transitional issue-execution artifact; useful for coordination but not standing governance policy. | Linked from ISSUE-0014 issue file; contains session agenda/output checklists and one-issue scope language, with no global policy linkage. | transitional | low | Keep issue-scoped; add “session artifact only” cue to prevent policy overreach interpretation. |

## 5. Newly discovered split-authority or duplication findings

| Topic | Newly selected documents involved | Interaction with previously audited authorities | Why this creates ambiguity | Canonical owner | Required action |
| ----- | --------------------------------- | ----------------------------------------------- | -------------------------- | --------------- | --------------- |
| Roadmap/status “required” language vs canonical enforcement | `docs/roadmap/current-status-and-next-5-priorities.md`, `docs/roadmap/next-4-sprints-grounded-knowing.md` | Interacts with `docs/testing.md`, `scripts/all_green_gate.py`, and issue program docs. | Roadmap text can read as normative gate policy even though enforcement/definitions live elsewhere. | `docs/testing.md` + gate/workflow scripts + canonical issue program docs | Add explicit boundary line in roadmap docs: they track planning/status; enforcement semantics are owned by testing/gate artifacts. |
| BDD guidance authority fan-out | `features/README.md` | Interacts with `docs/testing.md`, `AGENTS.md`, and feature/test execution rules. | “Mandatory” prose without direct validation mapping can create policy-by-doc drift. | Executable checks (`behave`, pytest, gate) and canonical testing guidance | Add traceability note in `features/README.md` linking each mandatory rule to enforcing test/lint mechanism or mark as convention only. |

## 6. Remaining-document task planning table

| Remaining document | Suspected role | Why it still needs audit | Priority | Audit tasks required | Dependencies / prerequisite evidence | Recommended future audit batch |
| ------------------ | -------------- | ------------------------ | -------- | -------------------- | ------------------------------------ | ------------------------------ |
| `docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound references from `docs/issues.md`, `docs/issues/RED_TAG.md`, and open issue files; verify zero CI/script consumers; determine if historical/superseded labeling is needed. | `rg -n` reference scan; `scripts/validate_issue_links.py`; `scripts/validate_issues.py` | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references; compare claims against current canonical owners; classify historical/transitional and define banner requirements. | same as above | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references; check whether any active issue relies on this as normative source; classify archival role. | same as above | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references; test for active-decision usage vs archival usage; assign role and required action. | same as above | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references; determine whether evidence is still cited as current truth; classify and prescribe pointer updates. | same as above | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references and compare with current gate behavior; classify as historical or transitional. | same as above + `scripts/all_green_gate.py` | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references and compare with current governance controls; classify archival status. | same as above | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references and compare with current runtime pipeline governance owners. | same as above | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Check if still linked from active issue plans; classify evidentiary value and required banners. | same as above | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Verify whether validator behavior described is current; compare with current scripts and classify. | same as above + validator scripts | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Determine if it is still used as decision input; classify historical/transitional role. | same as above | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md` | transitional evidence | Could still influence prioritization decisions without explicit canonical owner. | high | Compare matrix decisions to current `docs/issues/RED_TAG.md` and open issue status; classify active vs historical and define update/retirement rule. | `docs/issues/RED_TAG.md`; issue files; reference scan | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace links and check if RCA decisions were migrated into canonical docs/tests; classify role accordingly. | reference scan; canonical docs | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Verify whether continuity decisions now live in canonical plan/checklist; mark this artifact accordingly. | `plan.md`; checklist; reference scan | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md` | historical analysis evidence | Could be misread as current architecture decision authority. | medium | Check references from active planning docs; compare with latest architecture audits; classify historical/reference. | plan/checklist/architecture docs | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/coordination-failure-contract-drift-matrix.md` | historical/transitional evidence | Matrix language may resemble active control surface. | medium | Trace active inbound links and compare with current governance controls; determine if still operationally used. | issues docs + gate scripts | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md` | historical audit evidence | Audit framing can be mistaken for current authority. | medium | Compare conclusions with current canonical owners; classify and add superseded pointers if needed. | anchor + follow-up audits; canonical docs | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-craap-analysis-main-alignment.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | low | Determine whether any active process references it for decisions; classify archival role. | reference scan | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md` | transitional evidence | Freeze/exit findings can collide with current issue workflow authority. | high | Compare to current freeze status in `docs/issues.md` and related issue files; determine if still transitional authority. | `docs/issues.md`; freeze doc; issues | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-open-questions-audit-2026-03-16.md` | transitional evidence | Open-questions list may still steer decisions without ownership clarity. | medium | Trace references from active issue docs; determine if questions have canonical resolution owners now. | issues docs and scans | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-stabilization-checklist.md` | transitional checklist | Checklist format can imply active gate authority. | high | Check whether checklist items map to executable checks; classify as transitional/historical and define retirement criteria. | gate scripts/workflows + issues docs | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md` | transitional status evidence | Status note may conflict with current state in canonical docs. | medium | Compare status claims against current repo state and canonical docs; classify and action superseded labels. | canonical docs + reference scan | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/issue-0022-pass-seven-verification-log.md` | historical verification log | Could be treated as active quality signal if still linked prominently. | medium | Trace inbound links and check if current readiness docs rely on it; classify archival role. | issues docs + testing docs | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md` | historical RCA evidence | Could be mistaken as active behavioral contract source. | medium | Check if RCA outcomes were integrated into invariants/tests; classify evidence-only vs residual authority. | invariants/tests + reference scan | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md` | historical RCA evidence | Same ambiguity risk as paired RCA document. | medium | Trace links and verify whether feedback items remain unresolved; classify archival status. | same as above | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/open-pr-assessment-2026-03-17.md` | historical PR assessment | PR-specific artifact can be confused with standing policy. | low | Verify no active policy doc points to this as normative; classify historical and recommend archival cues. | reference scan | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md` | historical debug evidence | Operational notes can be mistaken for policy if linked broadly. | low | Trace links and classify as debug log evidence only; verify no enforcement dependencies. | reference scan | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md` | historical debug evidence | Same ambiguity risk as paired debug notes. | low | Trace links and classify as debug evidence only. | reference scan | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md` | historical debug evidence | Same ambiguity risk as other debug traces. | low | Trace links and classify as historical/debug-only. | reference scan | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md` | historical debug evidence | Same ambiguity risk as other debug traces. | low | Trace links and classify as historical/debug-only. | reference scan | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/sprint-00-kpi-review.md` | historical KPI evidence | KPI review may be mistaken for current KPI gate status owner. | medium | Compare with current KPI guardrail mode in gate/docs; classify historical or transitional and define pointers. | `scripts/all_green_gate.py`; `docs/testing.md` | Batch 11A: issue-evidence de-authority sweep |
| `docs/issues/evidence/work-history-assessment-2026-03-17.md` | historical evidence | Work-history assessment could be reused as present policy narrative. | low | Trace links; classify historical/reference and determine if archive annotation needed. | reference scan | Batch 11A: issue-evidence de-authority sweep |
| `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md` | roadmap/transitional planning | May still duplicate canonical progress authorities and unresolved migration status language. | medium | Trace inbound references from README/plan/issues; compare current claims against checklist and issue-program state; classify transitional vs historical. | `README.md`; `plan.md`; checklist; issue docs | Batch 11B: roadmap remainder reconciliation |
| `docs/roadmap/reflective-milestone-10-sprints.md` | roadmap/historical reflection | Reflection may contain latent prescriptive guidance that conflicts with current canon. | medium | Identify any normative directives; compare against current canonical docs; classify historical/reference and define retirement/supersession pointers. | roadmap files + canonical docs | Batch 11B: roadmap remainder reconciliation |
| `examples/Experiments.md` | example/reference notes | Could contain tacit process recommendations without governance classification. | low | Scan for normative language and inbound links from contributor entrypoints; classify reference vs decorative and capture action. | `README.md`; `CONTRIBUTING.md`; reference scan | Batch 11C: contributor-surface closure |
| `src/seem_bot/README.md` | subsystem reference | Could create parallel architecture/behavior authority for subsystem contributors. | medium | Trace inbound links; compare subsystem claims with canonical architecture/testing docs; classify role and identify drift/duplication. | architecture/testing docs + reference scan | Batch 11C: contributor-surface closure |

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
| Follow-up pass 8 | 2026-03-21 | 6 | 61 historical / 60 current | 48 | Audited QA+operations runbook/status tranche. |
| Follow-up pass 9 | 2026-03-21 | 3 | 64 historical / 63 current | 45 | Audited architecture/governance audit-history tranche. |
| Follow-up pass 10 | 2026-03-21 | 4 | 68 historical / 67 current | 41 | Audited contributor/process authority tranche (`AGENTS.md`, `docs/style-guide.md`, `CHANGELOG.md`, and follow-up ledger itself). |
| Follow-up pass 11 (this pass) | 2026-03-21 | 5 | 73 historical / 72 current | 36 | Audited roadmap/status + BDD/session/audit narrative tranche tied to active contributor paths. |

## 8. Minimal next-step sequence

1. **Next batch to audit:** all remaining `docs/issues/evidence/*` documents (32 files) as one explicit de-authority sweep (`Batch 11A`).
2. **Why that batch next:** this is still the largest unresolved cluster and primary source of potential historical-vs-live governance confusion.
3. **Evidence to gather first:**
   - inbound-link traces from `docs/issues.md`, `docs/issues/RED_TAG.md`, open `docs/issues/ISSUE-*.md`, `README.md`, and `plan.md`;
   - CI/script scans confirming whether any evidence files are directly consumed;
   - delta checks against current canonical owners (`docs/testing.md`, `docs/architecture/plan-execution-checklist.md`, `scripts/all_green_gate.py`).
4. **Repository-level uncertainty reduced:** whether the evidence corpus is purely archival or still acting as shadow decision authority.

Practical completeness check for this pass:
- Prior/current/remaining scopes are explicitly separated.
- Coverage expanded into previously unaudited files (5 files).
- Every remaining unaudited Markdown file has one concrete task-plan row.
