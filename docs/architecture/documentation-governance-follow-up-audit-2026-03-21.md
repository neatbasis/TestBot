# Documentation Governance Follow-up Audit — Structural Honesty (2026-03-21)

## 1. Scope accounting
This is a continuation audit anchored to `docs/architecture/documentation-governance-audit-2026-03-21.md`. I used the anchor audit out-of-scope Markdown list as the backlog baseline, compared it with the current tracked Markdown set, and then removed files already covered by prior passes before selecting this pass scope.

- Total Markdown files currently in repo: **108**.
- Markdown files already covered by previous documentation governance audits (before this pass): **38**.
- Markdown files newly selected for this audit pass: **5**.
- Markdown files still not yet audited after selection: **65** (**64** from the anchor backlog + 1 non-anchor file: this follow-up artifact).
- Non-Markdown enforcement artifacts reviewed for evidence: `scripts/validate_issues.py`, `scripts/validate_issue_links.py`, `scripts/generate_red_tag_index.py`, `scripts/all_green_gate.py`, `.github/workflows/issue-link-validation.yml`.

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

### 1.2 Candidate remaining Markdown files
(Reconstructed from the anchor out-of-scope list minus previously audited files, plus the additional non-anchor Markdown follow-up artifact now in-repo.)

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

### 1.3 Newly selected files for this audit pass
- `docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md`
- `docs/issues/ISSUE-0002-behave-dev-deps-reminders.md`
- `docs/issues/ISSUE-0003-readme-layout-drift.md`
- `docs/issues/ISSUE-0004-bdd-policy-not-yet-executable.md`
- `docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md`

Selection rationale: these are high-governance-impact issue records near the base of the issue program that define workflow establishment, executable-policy closure claims, and cross-links into README/testing/gate behavior. Auditing them now reduces ambiguity about whether early issue records are merely historical logs or still acting as de facto policy sources.

### 1.4 Remaining files not audited in this pass
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

## 2. Scope selection rationale
This pass prioritized `ISSUE-0001` through `ISSUE-0005` because they sit at the front of the issue-governance chain and shape interpretation of how issue policy became “real” in repository behavior.

Why these files now:
1. They include explicit acceptance criteria about governance controls (`docs/issues.md`, `RED_TAG`, validator-backed closure), so they can be mistaken as canonical policy if unaudited.
2. They bridge contributor-facing docs (`README.md`, `docs/testing.md`) and executable checks (`validate_issues`, `validate_issue_links`, `all_green_gate`), making them high leverage for governance clarity.
3. They precede later issue clusters and therefore determine whether downstream issue records should be read as operational trackers, historical evidence, or policy shadows.

Why these over other remaining files:
- Higher governance relevance than historical evidence notes and roadmap retrospectives because these issue files contain decision-shaping closure language and policy assertions.
- Higher uncertainty reduction than isolated reference docs because they directly interact with validator and readiness-gate narratives.

Uncertainty reduced by this pass:
- whether foundational issue records are still governance-active,
- where they duplicate canonical policy,
- and which unresolved issue-doc clusters should be audited next.

## 3. Executive summary
Documentation governance coverage is now **43/108 Markdown files (39.8%)** after this pass. The newly selected files that materially affect governance clarity are `ISSUE-0001` and `ISSUE-0005`: they make broad claims about validator/gate-backed governance and capability readiness, which can shadow canonical owners if not bounded. New split-authority findings show that issue-local closure language in `ISSUE-0002`/`0004`/`0005` can duplicate canonical testing and enforcement statements from `docs/testing.md` and `scripts/all_green_gate.py`. The most important next tasks are auditing the remaining active issue records (`ISSUE-0006` onward set in remaining pool), then de-authorizing evidence/roadmap artifacts that are not bound to executable controls.

## 4. Audit findings for newly selected documents

| Document | Claimed purpose | Actual role in practice | Evidence | Classification | Governance risk | Action |
| -------- | --------------- | ----------------------- | -------- | -------------- | --------------- | ------ |
| `docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md` | Establish canonical, measurable issue governance. | Transitional foundational record; historically launched the issue-governance program, but policy authority now lives in `docs/issues.md` + validators. | Closure notes reference validator-backed enforcement; `scripts/validate_issues.py` enforces issue fields/state semantics across `ISSUE-*.md`; `scripts/validate_issue_links.py` enforces issue linkage and RED_TAG sync paths. | historical | Medium: file can be misread as live policy instead of origin record. | Add explicit “historical origin record; canonical policy now in docs/issues.md” line in a future hygiene pass. |
| `docs/issues/ISSUE-0002-behave-dev-deps-reminders.md` | Ensure behave/dev dependency reminders are explicit at point-of-use. | Historical remediation ticket that documents a docs-onboarding fix; not an enforcement owner. | File closure cites README/testing wording changes; no issue-specific rule in validators; enforcement is indirect through broader gate/pytest/behave execution guidance. | historical | Medium: issue-local wording can be mistaken as normative testing policy. | Keep as historical trace; reduce duplicated policy by referencing `docs/testing.md` for live test command contract. |
| `docs/issues/ISSUE-0003-readme-layout-drift.md` | Fix README tree mismatch with tracked repo structure. | Historical documentation-integrity record with low ongoing governance authority. | Verification uses `validate_markdown_paths.py`; no direct validator/workflow reads this issue record for gating decisions. | historical | Low | Keep as resolved evidence; avoid using it as active policy source. |
| `docs/issues/ISSUE-0004-bdd-policy-not-yet-executable.md` | Close gap between declared BDD policy and executable BDD artifacts. | Historical policy-to-implementation closure record; describes completion state but does not own live BDD governance. | Evidence points to `features/` and step files; canonical test contract is maintained in `docs/testing.md`; issue validators do not enforce issue-local AC semantics beyond field structure. | historical | Medium: can shadow current BDD policy when behavior evolves. | Add or maintain explicit pointer to canonical behavior/test docs for current requirements. |
| `docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md` | Track capability-level readiness for time-aware ranking and gate parity. | Transitional historical-leaning issue record with strong operational closure claims tied to gate checks; potentially de facto authority if stale. | AC explicitly names gate commands and checks; `scripts/all_green_gate.py` is the actual blocking/warning semantics owner; issue-specific closure not automatically enforced after close. | transitional | High: issue-local readiness language can drift from current gate/test truth. | In future issue hygiene, replace repeated gate semantics with canonical references to current readiness/gate artifacts. |

## 5. Newly discovered split-authority or duplication findings

| Topic | Newly selected documents involved | Interaction with previously audited authorities | Why this creates ambiguity | Canonical owner | Required action |
| ----- | --------------------------------- | ----------------------------------------------- | -------------------------- | --------------- | --------------- |
| Foundational issue vs canonical issue policy | `ISSUE-0001` | Overlaps with previously audited `docs/issues.md` and validator scripts. | Historical origin issue still reads like active authority without explicit demotion. | `docs/issues.md` + `scripts/validate_issues.py` | Mark ISSUE-0001 as historical origin and point to canonical owners. |
| Issue-local testing/gate assertions | `ISSUE-0002`, `ISSUE-0004`, `ISSUE-0005` | Overlaps with `docs/testing.md` and `scripts/all_green_gate.py`. | Closed issues restate command expectations that can age independently of gate configuration. | `docs/testing.md` + `scripts/all_green_gate.py` | Replace future issue closure boilerplate with canonical reference blocks instead of restating policy semantics. |
| Capability readiness closure drift | `ISSUE-0005` | Interacts with QA feature-status docs and readiness gate outputs. | File can imply enduring readiness guarantees even as fixtures/check definitions evolve. | Gate outputs + current QA status artifacts | Require “as-of date + artifact pointer” framing for capability-closure statements in issues. |

## 6. Remaining-document task planning table

| Remaining document | Suspected role | Why it still needs audit | Priority | Audit tasks required | Dependencies / prerequisite evidence | Recommended future audit batch |
| ------------------ | -------------- | ------------------------ | -------- | -------------------- | ------------------------------------ | ------------------------------ |
| `AGENTS.md` | reference/meta governance | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace contributor entrypoint references; verify whether instructions conflict with canonical governance docs; classify as active contributor authority, reference-only, or decorative. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6E: entrypoint/meta governance surfaces |
| `CHANGELOG.md` | reference/meta governance | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Trace contributor entrypoint references; verify whether instructions conflict with canonical governance docs; classify as active contributor authority, reference-only, or decorative. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6E: entrypoint/meta governance surfaces |
| `docs/architecture/commit-drift-audit-2026-03-19.md` | historical architecture audit | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Determine whether this audit artifact is still cited for live decisions; compare findings against latest canonical docs; ensure historical snapshots are not treated as current authority. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6F: architecture audit artifact positioning |
| `docs/architecture/documentation-governance-audit-2026-03-21.md` | historical architecture audit | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Determine whether this audit artifact is still cited for live decisions; compare findings against latest canonical docs; ensure historical snapshots are not treated as current authority. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6F: architecture audit artifact positioning |
| `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` | historical architecture audit | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Determine whether this audit artifact is still cited for live decisions; compare findings against latest canonical docs; ensure historical snapshots are not treated as current authority. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6F: architecture audit artifact positioning |
| `docs/architecture/system-structure-audit-2026-03-19.md` | historical architecture audit | Can still shape behavior through references, but direct enforcement impact is less certain. | medium | Determine whether this audit artifact is still cited for live decisions; compare findings against latest canonical docs; ensure historical snapshots are not treated as current authority. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6F: architecture audit artifact positioning |
| `docs/issues/ISSUE-0006-operationalize-docs-issues-area.md` | operational/transitional issue record | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Map acceptance criteria and status semantics to `docs/issues.md` + validator-enforced fields; verify whether closure rules duplicate `docs/testing.md` or architecture/invariant canon; classify as operational tracker vs contract shadow. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6A |
| `docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md` | operational/transitional issue record | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Map acceptance criteria and status semantics to `docs/issues.md` + validator-enforced fields; verify whether closure rules duplicate `docs/testing.md` or architecture/invariant canon; classify as operational tracker vs contract shadow. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6A |
| `docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md` | operational/transitional issue record | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Map acceptance criteria and status semantics to `docs/issues.md` + validator-enforced fields; verify whether closure rules duplicate `docs/testing.md` or architecture/invariant canon; classify as operational tracker vs contract shadow. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6A |
| `docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md` | operational/transitional issue record | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Map acceptance criteria and status semantics to `docs/issues.md` + validator-enforced fields; verify whether closure rules duplicate `docs/testing.md` or architecture/invariant canon; classify as operational tracker vs contract shadow. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6A |
| `docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md` | operational/transitional issue record | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Map acceptance criteria and status semantics to `docs/issues.md` + validator-enforced fields; verify whether closure rules duplicate `docs/testing.md` or architecture/invariant canon; classify as operational tracker vs contract shadow. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6A |
| `docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md` | operational/transitional issue record | Likely to influence active contributor/reviewer behavior or closure decisions. | high | Map acceptance criteria and status semantics to `docs/issues.md` + validator-enforced fields; verify whether closure rules duplicate `docs/testing.md` or architecture/invariant canon; classify as operational tracker vs contract shadow. | Inbound-link scan (`rg`), `docs/issues.md`, `docs/testing.md`, `.github/workflows/*`, governance validators. | Batch 6A |
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
| Anchor audit | 2026-03-21 | 11 | 11 | 97 | Established methodology and initial out-of-scope backlog. |
| Follow-up pass 1 | 2026-03-21 | 9 | 20 | 88 | Audited entrypoint + directives + quickstart/invariants layer. |
| Follow-up pass 2 | 2026-03-21 | 5 | 25 | 83 | Audited canonical pipeline + boundary evidence/matrix surfaces. |
| Follow-up pass 3 | 2026-03-21 | 7 | 32 | 76 | Audited governance tracker layer (`docs/governance/*`). |
| Follow-up pass 4 | 2026-03-21 | 6 | 38 | 70 | Audited RED_TAG + active issue contract layer. |
| Follow-up pass 5 (this pass) | 2026-03-21 | 5 | 43 | 65 | Audited foundational issue-governance origin set (`ISSUE-0001`..`0005`). |

## 8. Minimal next-step sequence

1. **Next batch to audit:** Batch 6A focused on remaining active issue records (`ISSUE-0006`, `0007`, `0008`, `0009`, `0010`, `0011`, `0014`, `0015`, `0019`, `0020`, `0021`).
2. **Why this batch next:** these files still carry live status/blocker/acceptance language that likely affects triage and review decisions more than evidence and retrospective docs.
3. **Evidence to gather first:**
   - run issue validators over all issue files,
   - map inbound references from `docs/issues.md`, `README.md`, and `RED_TAG.md`,
   - map any workflow or gate references that consume issue metadata versus prose content.
4. **Repository-level uncertainty reduced by next batch:** determines whether remaining issue files are operational governance contracts, transitional trackers, or historical records, which is the largest unresolved authority surface in the remaining backlog.
