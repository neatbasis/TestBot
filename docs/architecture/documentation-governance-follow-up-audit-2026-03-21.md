# Documentation Governance Follow-up Audit — Structural Honesty (2026-03-21)

## 1. Scope accounting
This continuation pass is anchored to `docs/architecture/documentation-governance-audit-2026-03-21.md` and starts from that anchor audit’s out-of-scope Markdown list as the authoritative backlog seed.

Baseline method executed before scope selection:
1. Read the anchor audit and extract its out-of-scope Markdown backlog.
2. Compare that backlog against the current repository Markdown inventory.
3. Reconstruct prior follow-up audit scope from this file’s previous pass sections/tables.
4. Compute remaining unaudited files from the anchor backlog plus repository-delta Markdown additions.
5. Select a bounded subset only from remaining unaudited files.

Current accounting for this pass:
- Total Markdown files currently in repo: **108**.
- Markdown files already covered by previous documentation governance audits (before this pass): **63 current files**.
- Markdown files newly selected for this audit pass: **4**.
- Markdown files still not yet audited after selection: **41**.
- Non-Markdown enforcement artifacts reviewed for evidence in this pass: `scripts/all_green_gate.py`, `scripts/validate_issue_links.py`, `scripts/validate_issues.py`, `.github/workflows/issue-link-validation.yml`, plus repository-wide reference scans via `rg`.

Scope reconstruction note: prior follow-up scope was reconstructed from the existing follow-up audit content (coverage progression table, scope sections, and findings tables). No separate machine-generated prior-scope manifest exists.

Repository-delta note from anchor reconciliation:
- `.github/PULL_REQUEST_TEMPLATE.md` is present and treated as already audited via anchor scope.
- `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` is a post-anchor repository addition and is now audited in this pass.

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

### 1.2 Candidate remaining Markdown files
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

### 1.3 Newly selected files for this audit pass
- `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`
- `AGENTS.md`
- `docs/style-guide.md`
- `CHANGELOG.md`

Selection rationale: these four were selected from the remaining pool because they currently shape contributor behavior and governance interpretation more directly than issue evidence snapshots. The follow-up audit file is an active continuation ledger, `AGENTS.md` controls agent execution behavior, `docs/style-guide.md` defines cross-repo docs norms, and `CHANGELOG.md` prescribes required changelog entry structure that can be treated as process authority.

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
- `docs/regression-progression-audit-8f9317a-to-head.md`
- `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md`
- `docs/roadmap/current-status-and-next-5-priorities.md`
- `docs/roadmap/next-4-sprints-grounded-knowing.md`
- `docs/roadmap/reflective-milestone-10-sprints.md`
- `docs/sessions/ISSUE-0014-cross-functional-session-plan.md`
- `examples/Experiments.md`
- `features/README.md`
- `src/seem_bot/README.md`

## 2. Scope selection rationale
This pass prioritizes unresolved documents that can alter contributor behavior now:

1. **`docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`** is a live continuation artifact that controls scope accounting and backlog decisions across passes.
2. **`AGENTS.md`** is explicitly presented as canonical bootstrap contract for coding agents and is likely to influence implementation/testing flow in day-to-day change work.
3. **`docs/style-guide.md`** sets cross-repository writing/structure rules and can silently create process authority if not mapped to enforcement reality.
4. **`CHANGELOG.md`** contains prescriptive entry requirements (“use for every PR/refactor step”) and can impose quasi-governance expectations.

Why these before the remaining pool:
- They are more governance-relevant than issue evidence snapshots because they shape current authoring/review behavior rather than preserving historical traces.
- They can create split authority against already-audited canonical owners (`docs/testing.md`, `docs/issues.md`, `scripts/all_green_gate.py`) if their prescriptive language is not explicitly classified.

Uncertainty reduced in this pass:
- Whether agent bootstrap instructions are canonical, operationally enforced, or advisory.
- Whether docs style and changelog instructions are governance-bearing versus decorative/reference.
- Whether the follow-up audit file itself is drifting into de facto canonical policy ownership.

## 3. Executive summary
Repository Markdown coverage is now **67/108 (62.0%)** after auditing four previously unaudited files in this pass. The newly selected documents materially affecting governance clarity are `AGENTS.md` (agent behavior contract), `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` (scope/backlog control ledger), `docs/style-guide.md` (repo-wide docs rule framing), and `CHANGELOG.md` (process-prescriptive changelog rubric). New split-authority findings are: (a) `AGENTS.md` asserts canonical readiness behavior while enforcement remains in gate/workflow artifacts, and (b) the follow-up audit file mixes historical reporting with active process control, risking role confusion unless bounded. Most important next tasks are to audit the entire `docs/issues/evidence/*` remainder as one structured de-authority sweep and then audit roadmap/session planning docs for live-vs-historical drift.

## 4. Audit findings for newly selected documents

| Document | Claimed purpose | Actual role in practice | Evidence | Classification | Governance risk | Action |
| -------- | --------------- | ----------------------- | -------- | -------------- | --------------- | ------ |
| `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` | Continuation audit ledger and coverage progression tracker. | Transitional governance program ledger: actively drives what gets audited next, but is not executable enforcement. | Contains explicit pass sequencing, remaining backlog table, and next-step directives; no CI/script consumption found. | transitional | medium | Keep as active transition ledger until backlog closure; prohibit it from declaring runtime/testing policy outside references to canonical owners. |
| `AGENTS.md` | Canonical bootstrap contract for coding agents. | High-impact contributor operational reference with mixed authority: routes users to canonical docs/gates but itself is not machine-enforced. | Prescribes validation and issue workflow commands; points to `docs/testing.md`, `docs/issues.md`, and gate scripts; not directly consumed by workflow automation. | operational | medium | Keep as entrypoint operational guide; explicitly mark it as derivative of canonical owners to reduce “parallel canonical” interpretation. |
| `docs/style-guide.md` | Writing standards for repo docs. | Reference guidance document with advisory norms; no enforcement linkage detected. | Style rules/questions/review cadence are prose-only; no lint/check wiring in gate/workflow artifacts. | reference | low | Keep advisory; if mandatory, bind specific checks to tooling or relabel language to “recommended”. |
| `CHANGELOG.md` | Changelog policy + historical change ledger. | Hybrid reference/historical artifact: format guidance plus dated migration entries; not a gate owner. | “Entry template” is prescriptive prose; file mainly stores dated entries; no CI/script read path found. | historical | low | Preserve as historical log; keep template language explicitly non-blocking unless validated by an automated changelog checker. |

## 5. Newly discovered split-authority or duplication findings

| Topic | Newly selected documents involved | Interaction with previously audited authorities | Why this creates ambiguity | Canonical owner | Required action |
| ----- | --------------------------------- | ----------------------------------------------- | -------------------------- | --------------- | --------------- |
| Agent-facing canonical language vs executable canonical owners | `AGENTS.md` | Interacts with `docs/testing.md`, `docs/issues.md`, and `scripts/all_green_gate.py`. | “Canonical bootstrap contract” phrasing can be misread as policy source instead of an operational index that points to canonical owners. | `docs/testing.md`, `docs/issues.md`, and gate/workflow scripts | Add explicit statement that `AGENTS.md` is a derivative operational map and cannot override canonical/testing/enforcement artifacts. |
| Process-ledger authority creep | `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` | Interacts with anchor audit and current canonical docs. | Same file both records findings and sets forward program tasks, risking perception that it owns policy decisions rather than audit planning only. | Canonical policy docs/scripts; follow-up audit owns only audit program state | Add short boundary note: this file governs audit workflow only, not runtime/testing policy semantics. |

## 6. Remaining-document task planning table

| Remaining document | Suspected role | Why it still needs audit | Priority | Audit tasks required | Dependencies / prerequisite evidence | Recommended future audit batch |
| ------------------ | -------------- | ------------------------ | -------- | -------------------- | ------------------------------------ | ------------------------------ |
| `docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md` | historical evidence | May still be cited by active issues and misread as live governance truth. | medium | Trace inbound references from `docs/issues.md`, `docs/issues/RED_TAG.md`, and open issue files; verify zero CI/script consumers; determine if historical/superseded labeling is needed. | `rg -n` reference scan; `scripts/validate_issue_links.py`; `scripts/validate_issues.py` | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references; compare claims against current canonical owners; classify historical/transitional and define banner requirements. | same as above | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references; check whether any active issue relies on this as normative source; classify archival role. | same as above | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references; test for active-decision usage vs archival usage; assign role and required action. | same as above | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references; determine whether evidence is still cited as current truth; classify and prescribe pointer updates. | same as above | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references and compare with current gate behavior; classify as historical or transitional. | same as above + `scripts/all_green_gate.py` | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references and compare with current governance controls; classify archival status. | same as above | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace inbound references and compare with current runtime pipeline governance owners. | same as above | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Check if still linked from active issue plans; classify evidentiary value and required banners. | same as above | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Verify whether validator behavior described is current; compare with current scripts and classify. | same as above + validator scripts | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Determine if it is still used as decision input; classify historical/transitional role. | same as above | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md` | transitional evidence | Could still influence prioritization decisions without explicit canonical owner. | high | Compare matrix decisions to current `docs/issues/RED_TAG.md` and open issue status; classify active vs historical and define update/retirement rule. | `docs/issues/RED_TAG.md`; issue files; reference scan | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Trace links and check if RCA decisions were migrated into canonical docs/tests; classify role accordingly. | reference scan; canonical docs | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | medium | Verify whether continuity decisions now live in canonical plan/checklist; mark this artifact accordingly. | `plan.md`; checklist; reference scan | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md` | historical analysis evidence | Could be misread as current architecture decision authority. | medium | Check references from active planning docs; compare with latest architecture audits; classify historical/reference. | plan/checklist/architecture docs | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/coordination-failure-contract-drift-matrix.md` | historical/transitional evidence | Matrix language may resemble active control surface. | medium | Trace active inbound links and compare with current governance controls; determine if still operationally used. | issues docs + gate scripts | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md` | historical audit evidence | Audit framing can be mistaken for current authority. | medium | Compare conclusions with current canonical owners; classify and add superseded pointers if needed. | anchor + follow-up audits; canonical docs | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-craap-analysis-main-alignment.md` | historical evidence | Same ambiguity risk as other issue evidence artifacts. | low | Determine whether any active process references it for decisions; classify archival role. | reference scan | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md` | transitional evidence | Freeze/exit findings can collide with current issue workflow authority. | high | Compare to current freeze status in `docs/issues.md` and related issue files; determine if still transitional authority. | `docs/issues.md`; freeze doc; issues | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-open-questions-audit-2026-03-16.md` | transitional evidence | Open-questions list may still steer decisions without ownership clarity. | medium | Trace references from active issue docs; determine if questions have canonical resolution owners now. | issues docs and scans | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-stabilization-checklist.md` | transitional checklist | Checklist format can imply active gate authority. | high | Check whether checklist items map to executable checks; classify as transitional/historical and define retirement criteria. | gate scripts/workflows + issues docs | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md` | transitional status evidence | Status note may conflict with current state in canonical docs. | medium | Compare status claims against current repo state and canonical docs; classify and action superseded labels. | canonical docs + reference scan | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/issue-0022-pass-seven-verification-log.md` | historical verification log | Could be treated as active quality signal if still linked prominently. | medium | Trace inbound links and check if current readiness docs rely on it; classify archival role. | issues docs + testing docs | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md` | historical RCA evidence | Could be mistaken as active behavioral contract source. | medium | Check if RCA outcomes were integrated into invariants/tests; classify evidence-only vs residual authority. | invariants/tests + reference scan | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md` | historical RCA evidence | Same ambiguity risk as paired RCA document. | medium | Trace links and verify whether feedback items remain unresolved; classify archival status. | same as above | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/open-pr-assessment-2026-03-17.md` | historical PR assessment | PR-specific artifact can be confused with standing policy. | low | Verify no active policy doc points to this as normative; classify historical and recommend archival cues. | reference scan | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md` | historical debug evidence | Operational notes can be mistaken for policy if linked broadly. | low | Trace links and classify as debug log evidence only; verify no enforcement dependencies. | reference scan | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md` | historical debug evidence | Same ambiguity risk as paired debug notes. | low | Trace links and classify as debug evidence only. | reference scan | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md` | historical debug evidence | Same ambiguity risk as other debug traces. | low | Trace links and classify as historical/debug-only. | reference scan | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md` | historical debug evidence | Same ambiguity risk as other debug traces. | low | Trace links and classify as historical/debug-only. | reference scan | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/sprint-00-kpi-review.md` | historical KPI evidence | KPI review may be mistaken for current KPI gate status owner. | medium | Compare with current KPI guardrail mode in gate/docs; classify historical or transitional and define pointers. | `scripts/all_green_gate.py`; docs/testing.md | Batch 10A: issue-evidence de-authority sweep |
| `docs/issues/evidence/work-history-assessment-2026-03-17.md` | historical evidence | Work-history assessment could be reused as present policy narrative. | low | Trace links; classify historical/reference and determine if archive annotation needed. | reference scan | Batch 10A: issue-evidence de-authority sweep |
| `docs/regression-progression-audit-8f9317a-to-head.md` | transitional planning/history | Could still influence sequencing if referenced from active plans. | medium | Trace references from `README.md`, `plan.md`, `docs/testing.md`, and issue docs; compare claims to current status artifacts. | reference scan; `docs/qa/feature-status-report.md` | Batch 10B: roadmap/planning authority reconciliation |
| `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md` | roadmap/transitional planning | Planning doc may duplicate current canonical progress ledger. | medium | Determine inbound links; compare with checklist and issue plans; classify transitional vs historical. | `plan.md`; checklist; issue docs | Batch 10B: roadmap/planning authority reconciliation |
| `docs/roadmap/current-status-and-next-5-priorities.md` | roadmap/transitional planning | “Current status” framing can conflict with canonical owners. | high | Validate whether it still drives contributor action; compare status claims against current checklist/issues. | checklist + issue docs + reference scan | Batch 10B: roadmap/planning authority reconciliation |
| `docs/roadmap/next-4-sprints-grounded-knowing.md` | roadmap/transitional planning | Sprint plan may still be treated as active authority. | medium | Trace links and compare with active issue governance plans; classify with concrete retirement/update criteria. | issue docs + reference scan | Batch 10B: roadmap/planning authority reconciliation |
| `docs/roadmap/reflective-milestone-10-sprints.md` | roadmap/historical reflection | Reflection language may still include normative directives. | medium | Determine whether decisions migrated to canonical docs; classify historical/reference role. | plan/checklist/issues | Batch 10B: roadmap/planning authority reconciliation |
| `docs/sessions/ISSUE-0014-cross-functional-session-plan.md` | session planning artifact | Session plans can be mistaken for ongoing policy decisions. | medium | Trace active references from issue files and plan docs; classify historical/transitional and define action. | issue files + reference scan | Batch 10B: roadmap/planning authority reconciliation |
| `examples/Experiments.md` | reference/example notes | May contain tacit process recommendations without governance classification. | low | Scan for normative language; check if referenced by contributor entry docs; classify advisory vs decorative. | README/CONTRIBUTING reference scan | Batch 10C: contributor-surface cleanup |
| `features/README.md` | contributor reference for behavior specs | Can influence BDD workflow and test authoring expectations. | high | Map instructions to actual `behave`/pytest workflow; verify consistency with `docs/testing.md` and AGENTS guidance. | testing docs + AGENTS + feature tree | Batch 10C: contributor-surface cleanup |
| `src/seem_bot/README.md` | subsystem reference | Subsystem docs can create parallel authority for architecture behavior. | medium | Check inbound links and compare subsystem claims to canonical architecture docs/tests; classify role and drift risk. | architecture docs + reference scan | Batch 10C: contributor-surface cleanup |

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
| Follow-up pass 10 (this pass) | 2026-03-21 | 4 | 68 historical / 67 current | 41 | Audited remaining contributor/process authority tranche (`AGENTS.md`, `docs/style-guide.md`, `CHANGELOG.md`, and follow-up ledger itself). |

## 8. Minimal next-step sequence

1. **Next batch to audit:** all remaining `docs/issues/evidence/*` documents (31 files) as a single de-authority sweep batch.
2. **Why this batch should come next:** this is the largest unresolved cluster and the primary remaining source of historical-vs-active governance ambiguity.
3. **Evidence to gather first:**
   - inbound-link trace from `docs/issues.md`, `docs/issues/RED_TAG.md`, open `docs/issues/ISSUE-*.md`, `README.md`, and `plan.md`;
   - script/workflow scans to confirm none of these files are consumed directly by CI/gates;
   - comparison of evidence claims against current canonical owners (`docs/testing.md`, `docs/architecture/plan-execution-checklist.md`, `scripts/all_green_gate.py`).
4. **Repository-level uncertainty reduced:** whether issue evidence files are purely historical artifacts or still-shadow governance inputs that fragment authority and decision flow.

Practical completeness check for this pass:
- Prior/current/remaining scopes are explicitly separated.
- Coverage expanded into previously unaudited files (4 files).
- Every remaining unaudited Markdown file has one concrete task-plan row.
