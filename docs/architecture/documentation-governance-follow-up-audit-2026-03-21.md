# Documentation Governance Follow-up Audit — Structural Honesty (2026-03-21)

## 1. Scope accounting

This follow-up pass extends the prior documentation governance audit (`docs/architecture/documentation-governance-audit-2026-03-21.md`) and advances into previously unaudited Markdown.

- Total Markdown files currently in repository: **107**
- Previously audited Markdown files (prior pass): **11**
- Candidate remaining Markdown files before this pass: **96**
- Newly selected files audited in this pass: **9**
- Remaining Markdown files not yet audited after this pass: **87**

Non-Markdown enforcement artifacts reviewed for evidence in this pass:
- `scripts/all_green_gate.py`
- `scripts/sync_invariants_mirror.py`
- `scripts/validate_pipeline_stage_conformance.py`
- `scripts/validate_invariant_sync.py`
- `scripts/validate_issue_links.py`
- `.github/workflows/issue-link-validation.yml`

Prior audit scope reconstruction was **not** required; the prior audit explicitly listed in-scope Markdown files.

### 1.1 Previously audited Markdown files

- `./plan.md`
- `./docs/pivot.md`
- `./docs/architecture/plan-execution-checklist.md`
- `./docs/architecture/architecture-governance-audit-2026-03-20.md`
- `./docs/testing.md`
- `./docs/issues.md`
- `./docs/issues/governance-control-surface-contract-freeze.md`
- `./docs/architecture-boundaries.md`
- `./CONTRIBUTING.md`
- `./.github/PULL_REQUEST_TEMPLATE.md`
- `./docs/architecture.md`

### 1.2 Candidate remaining Markdown files

All Markdown files not listed in 1.1:

- `./AGENTS.md`
- `./CHANGELOG.md`
- `./README.md`
- `./artifacts/architecture-boundary-report.current.md`
- `./docs/architecture/behavior-governance.md`
- `./docs/architecture/canonical-turn-pipeline.md`
- `./docs/architecture/commit-drift-audit-2026-03-19.md`
- `./docs/architecture/documentation-governance-audit-2026-03-21.md`
- `./docs/architecture/system-structure-audit-2026-03-19.md`
- `./docs/directives/CHANGE_POLICY.md`
- `./docs/directives/decision-policy.md`
- `./docs/directives/invariants.md`
- `./docs/directives/product-principles.md`
- `./docs/directives/traceability-matrix.md`
- `./docs/governance/architecture-drift-register.md`
- `./docs/governance/code-review-governance-automation-dependency-boundaries.md`
- `./docs/governance/drift-remediation-backlog.md`
- `./docs/governance/drift-traceability-matrix.md`
- `./docs/governance/issue-implementation-audit.md`
- `./docs/governance/mission-vision-alignment.md`
- `./docs/governance/python-code-review-checklist-dependency-boundaries.md`
- `./docs/invariants.md`
- `./docs/invariants/answer-policy.md`
- `./docs/invariants/pipeline.md`
- `./docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md`
- `./docs/issues/ISSUE-0002-behave-dev-deps-reminders.md`
- `./docs/issues/ISSUE-0003-readme-layout-drift.md`
- `./docs/issues/ISSUE-0004-bdd-policy-not-yet-executable.md`
- `./docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md`
- `./docs/issues/ISSUE-0006-operationalize-docs-issues-area.md`
- `./docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md`
- `./docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md`
- `./docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md`
- `./docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md`
- `./docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md`
- `./docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`
- `./docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`
- `./docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
- `./docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md`
- `./docs/issues/ISSUE-0016-startup-degraded-mode-bdd-coverage-gap.md`
- `./docs/issues/ISSUE-0017-invariant-boundary-ambiguity-answer-commit-regression.md`
- `./docs/issues/ISSUE-0018-dual-trigger-event-loop-for-proactive-ingestion-lifecycle.md`
- `./docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md`
- `./docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md`
- `./docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md`
- `./docs/issues/RED_TAG.md`
- `./docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md`
- `./docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md`
- `./docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md`
- `./docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md`
- `./docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md`
- `./docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md`
- `./docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md`
- `./docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md`
- `./docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md`
- `./docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md`
- `./docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md`
- `./docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md`
- `./docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md`
- `./docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md`
- `./docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md`
- `./docs/issues/evidence/coordination-failure-contract-drift-matrix.md`
- `./docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md`
- `./docs/issues/evidence/governance-craap-analysis-main-alignment.md`
- `./docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md`
- `./docs/issues/evidence/governance-open-questions-audit-2026-03-16.md`
- `./docs/issues/evidence/governance-stabilization-checklist.md`
- `./docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md`
- `./docs/issues/evidence/issue-0022-pass-seven-verification-log.md`
- `./docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md`
- `./docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md`
- `./docs/issues/evidence/open-pr-assessment-2026-03-17.md`
- `./docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md`
- `./docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md`
- `./docs/issues/evidence/production-debug-cli-trace-2026-03-07.md`
- `./docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md`
- `./docs/issues/evidence/sprint-00-kpi-review.md`
- `./docs/issues/evidence/work-history-assessment-2026-03-17.md`
- `./docs/ops.md`
- `./docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md`
- `./docs/qa/feature-status-report.md`
- `./docs/qa/live-smoke.md`
- `./docs/qa/smoke-evidence-contract.md`
- `./docs/quickstart.md`
- `./docs/regression-progression-audit-8f9317a-to-head.md`
- `./docs/roadmap/alignment-drift-technical-debt-2026-03-05.md`
- `./docs/roadmap/current-status-and-next-5-priorities.md`
- `./docs/roadmap/next-4-sprints-grounded-knowing.md`
- `./docs/roadmap/reflective-milestone-10-sprints.md`
- `./docs/sessions/ISSUE-0014-cross-functional-session-plan.md`
- `./docs/style-guide.md`
- `./docs/terminology.md`
- `./docs/testing-triage.md`
- `./examples/Experiments.md`
- `./features/README.md`
- `./src/seem_bot/README.md`

### 1.3 Newly selected files for this audit pass

- `./README.md`
- `./docs/invariants.md`
- `./docs/directives/CHANGE_POLICY.md`
- `./docs/directives/decision-policy.md`
- `./docs/directives/invariants.md`
- `./docs/directives/product-principles.md`
- `./docs/directives/traceability-matrix.md`
- `./docs/quickstart.md`
- `./docs/terminology.md`

Selection rationale: this batch is the highest-impact previously unaudited governance surface because README routes contributor behavior, directives claim canonical policy authority, and quickstart/terminology change operator and reviewer decisions. These files most directly shape implementation/review choices and have the highest risk of split authority if decorative claims are not enforced.

### 1.4 Remaining files not audited in this pass

All candidate remaining files except 1.3 (87 files):

- `./AGENTS.md`
- `./CHANGELOG.md`
- `./artifacts/architecture-boundary-report.current.md`
- `./docs/architecture/behavior-governance.md`
- `./docs/architecture/canonical-turn-pipeline.md`
- `./docs/architecture/commit-drift-audit-2026-03-19.md`
- `./docs/architecture/documentation-governance-audit-2026-03-21.md`
- `./docs/architecture/system-structure-audit-2026-03-19.md`
- `./docs/governance/architecture-drift-register.md`
- `./docs/governance/code-review-governance-automation-dependency-boundaries.md`
- `./docs/governance/drift-remediation-backlog.md`
- `./docs/governance/drift-traceability-matrix.md`
- `./docs/governance/issue-implementation-audit.md`
- `./docs/governance/mission-vision-alignment.md`
- `./docs/governance/python-code-review-checklist-dependency-boundaries.md`
- `./docs/invariants/answer-policy.md`
- `./docs/invariants/pipeline.md`
- `./docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md`
- `./docs/issues/ISSUE-0002-behave-dev-deps-reminders.md`
- `./docs/issues/ISSUE-0003-readme-layout-drift.md`
- `./docs/issues/ISSUE-0004-bdd-policy-not-yet-executable.md`
- `./docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md`
- `./docs/issues/ISSUE-0006-operationalize-docs-issues-area.md`
- `./docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md`
- `./docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md`
- `./docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md`
- `./docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md`
- `./docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md`
- `./docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`
- `./docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`
- `./docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`
- `./docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md`
- `./docs/issues/ISSUE-0016-startup-degraded-mode-bdd-coverage-gap.md`
- `./docs/issues/ISSUE-0017-invariant-boundary-ambiguity-answer-commit-regression.md`
- `./docs/issues/ISSUE-0018-dual-trigger-event-loop-for-proactive-ingestion-lifecycle.md`
- `./docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md`
- `./docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md`
- `./docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md`
- `./docs/issues/RED_TAG.md`
- `./docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md`
- `./docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md`
- `./docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md`
- `./docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md`
- `./docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md`
- `./docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md`
- `./docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md`
- `./docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md`
- `./docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md`
- `./docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md`
- `./docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md`
- `./docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md`
- `./docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md`
- `./docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md`
- `./docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md`
- `./docs/issues/evidence/coordination-failure-contract-drift-matrix.md`
- `./docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md`
- `./docs/issues/evidence/governance-craap-analysis-main-alignment.md`
- `./docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md`
- `./docs/issues/evidence/governance-open-questions-audit-2026-03-16.md`
- `./docs/issues/evidence/governance-stabilization-checklist.md`
- `./docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md`
- `./docs/issues/evidence/issue-0022-pass-seven-verification-log.md`
- `./docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md`
- `./docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md`
- `./docs/issues/evidence/open-pr-assessment-2026-03-17.md`
- `./docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md`
- `./docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md`
- `./docs/issues/evidence/production-debug-cli-trace-2026-03-07.md`
- `./docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md`
- `./docs/issues/evidence/sprint-00-kpi-review.md`
- `./docs/issues/evidence/work-history-assessment-2026-03-17.md`
- `./docs/ops.md`
- `./docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md`
- `./docs/qa/feature-status-report.md`
- `./docs/qa/live-smoke.md`
- `./docs/qa/smoke-evidence-contract.md`
- `./docs/regression-progression-audit-8f9317a-to-head.md`
- `./docs/roadmap/alignment-drift-technical-debt-2026-03-05.md`
- `./docs/roadmap/current-status-and-next-5-priorities.md`
- `./docs/roadmap/next-4-sprints-grounded-knowing.md`
- `./docs/roadmap/reflective-milestone-10-sprints.md`
- `./docs/sessions/ISSUE-0014-cross-functional-session-plan.md`
- `./docs/style-guide.md`
- `./docs/testing-triage.md`
- `./examples/Experiments.md`
- `./features/README.md`
- `./src/seem_bot/README.md`

## 2. Scope selection rationale

This pass prioritized **governance-control documents that route contributor behavior or claim canonical authority**:

1. `README.md` is the top contributor entrypoint and explicitly routes readers to directives and workflow docs.
2. The `docs/directives/*.md` set contains explicit canonical/sole-authority claims (decision policy, traceability, change policy, invariant mirror) that can create or reduce split authority.
3. `docs/invariants.md` defines ontology boundaries (`PINV-*` vs `INV-*`) and ownership split that materially affects review and implementation expectations.
4. `docs/quickstart.md` and `docs/terminology.md` are linked from README and influence operator/contributor behavior; both can become de facto governance if they include normative constraints.

This batch is more governance-relevant than remaining issue evidence logs, historical audits, roadmap notes, and session artifacts because it directly shapes ongoing implementation, review criteria, and architecture truth claims.

Uncertainty reduced by this pass:
- whether directive docs are genuinely operational or only declared-authoritative,
- where canonical policy is still fragmented across README/directives/testing,
- whether invariant ownership split is executable or documentary only.

## 3. Executive summary

After this pass, **20 of 107 Markdown files (18.7%)** are now covered by documentation-governance audits (11 prior + 9 new). The newly audited files that materially affect governance clarity are `README.md`, `docs/directives/traceability-matrix.md`, `docs/directives/decision-policy.md`, `docs/directives/CHANGE_POLICY.md`, and `docs/invariants.md` because they route contributor behavior and claim canonical ownership of policy mappings. New findings include a split between directive policy claims and actual CI enforcement (notably PR-field merge blockers declared in `docs/directives/CHANGE_POLICY.md` without observed blocking automation), plus fan-out risk where `README.md` simultaneously elevates multiple directive authorities. Highest-priority next tasks are auditing `docs/architecture/canonical-turn-pipeline.md`, `docs/invariants/{answer-policy,pipeline}.md`, and governance register/checklist docs to close authoritative-contract uncertainty and verify executable binding.

Coverage progressed by advancing into previously unaudited canonical-entrypoint and directive files; this was not a re-audit of prior scope.

## 4. Audit findings for newly selected documents

| Document | Claimed purpose | Actual role in practice | Evidence | Classification | Governance risk | Action |
| -------- | --------------- | ----------------------- | -------- | -------------- | --------------- | ------ |
| `./README.md` | Top-level orientation and canonical routing | De facto governance router to testing/issues/directives/quickstart | Explicit role-based routing and canonical references; issue workflow and directive links used across issue docs/scripts | `operational` | Routing fan-out can amplify split authority if linked targets conflict | Keep as routing index only; avoid embedding normative status details not machine-bound |
| `./docs/invariants.md` | Canonical invariant registry index and ontology split | Active index defining ownership boundaries (`PINV-*` vs `INV-*`) | Referenced by `scripts/all_green_gate.py`; links canonical sub-registries; cited by directive change policy | `canonical` | Medium: if index drifts from sub-registries, ontology ambiguity returns | Keep as ownership index; add explicit pointer to validating script outputs in future |
| `./docs/directives/CHANGE_POLICY.md` | Mandatory process for directive changes and merge blockers | Mixed: partially operational (sync checks) plus documentary-only merge blocker claims | Sync tooling exists (`sync_invariants_mirror.py`, `validate_invariant_sync.py`); no observed CI enforcement for required PR fields/SemVer footer claims | `transitional` | High: false “merge blocker” claims without observable enforcement create trust gaps | Separate executable requirements from advisory review checklist; bind blocker claims to CI or downgrade language |
| `./docs/directives/decision-policy.md` | Canonical authority for routing/fallback/reject policy | Substantive policy reference used by README/traceability; enforcement appears indirect through runtime/tests | README links it as authoritative; traceability matrix maps policy to code/tests; no single validator proving document-to-runtime parity | `reference` | Medium: can drift from runtime if parity checks stay indirect | Add explicit parity check IDs or script linkage for critical thresholds/taxonomy |
| `./docs/directives/invariants.md` | Mirror view of response-policy invariants | True derivative mirror for directive readers | File declares mirror-only; canonical source in `docs/invariants/answer-policy.md`; sync script and validator exist | `operational` | Low if sync checks run; medium if CI does not enforce validator on PR | Preserve mirror-only scope; ensure validator is part of blocking readiness workflow |
| `./docs/directives/product-principles.md` | Mission/vision principles mapped to deterministic signals | Reference bridge from vision claims to tests/gates | README elevates file; rows point to BDD/tests/gate artifacts | `reference` | Medium: advisory unless principle-to-check mapping is validated systematically | Add lightweight validator for principle row targets existing and runnable |
| `./docs/directives/traceability-matrix.md` | Sole canonical behavior→stage→test traceability mapping | High-impact operational reference with partial enforcement linkage | `scripts/validate_pipeline_stage_conformance.py` consumes this doc; README/architecture docs route here; contains mandatory update rules | `canonical` | High: broad scope and embedded appendices risk over-concentration and hidden drift | Keep canonical matrix but trim non-core appendices or mark them non-canonical sections |
| `./docs/quickstart.md` | Operator setup/run guidance | Operational runbook; includes some normative behavior statements | README routes operators here; issue docs discuss quickstart command semantics | `operational` | Medium: runtime policy language in setup doc can conflict with policy docs | Keep startup/run procedures; move behavior-contract claims to directives/testing |
| `./docs/terminology.md` | Canonical naming policy for identifiers and AI terms | Reference control preventing identifier drift across docs | README and directive docs link to it; CHANGE_POLICY requires terminology updates on term changes | `reference` | Low-medium: could become shadow policy if it starts defining behavior | Keep lexical scope only; avoid adding runtime policy rules |

## 5. Newly discovered split-authority or duplication findings

| Topic | Newly selected documents involved | Interaction with previously audited authorities | Why this creates ambiguity | Canonical owner | Required action |
| ----- | --------------------------------- | ----------------------------------------------- | -------------------------- | --------------- | --------------- |
| Directive merge-blocker claims vs actual blocking checks | `./docs/directives/CHANGE_POLICY.md` | Prior audit found blocking evidence concentrated in workflow + `all_green_gate`; CHANGE_POLICY declares additional merge blockers | “Missing fields are a merge blocker” is documentary unless CI validates PR metadata fields | CI workflow + executable validators | Either implement PR-metadata validator in CI or relabel these fields as reviewer-required/advisory |
| Policy authority fan-out from entrypoint | `./README.md`, `./docs/directives/decision-policy.md`, `./docs/directives/traceability-matrix.md`, `./docs/invariants.md` | Prior audit already found split around testing/checklist/pivot status authority | README simultaneously elevates several “canonical” docs without explicit precedence for conflicts | `docs/architecture/canonical-turn-pipeline.md` + `docs/directives/traceability-matrix.md` + executable validators (mapped by concern) | Add concise precedence map in README (“for X truth use Y artifact”) |
| Traceability matrix scope expansion | `./docs/directives/traceability-matrix.md` | Prior audit flagged policy fan-out in testing/plan/pivot; matrix now also embeds appendices with broader governance notes | One file claims sole canonical mapping while also carrying quick-reference/process appendix material that may age at different rates | `docs/directives/traceability-matrix.md` (core matrix only) | Split appendices into clearly non-canonical companion docs or mark section-level authority boundaries |
| Invariant ownership clarity vs derivative mirror | `./docs/invariants.md`, `./docs/directives/invariants.md` | Prior audit did not cover invariant ownership layer | Canonical index and mirror are mostly clear, but if sync checks are non-blocking in CI, mirror may quietly drift | `docs/invariants/{answer-policy,pipeline}.md` as canonical + sync validator as enforcement | Confirm blocking CI path for invariant sync check; publish status in gate matrix |

## 6. Remaining-document task planning table

| Remaining document | Suspected role | Why it still needs audit | Priority | Audit tasks required | Dependencies / prerequisite evidence | Recommended future audit batch |
| ------------------ | -------------- | ------------------------ | -------- | -------------------- | ------------------------------------ | ------------------------------ |
| `./AGENTS.md` | operational | Agent bootstrap policy may supersede contributor docs in practice | high | Trace references from task prompts to AGENTS contract sections; verify whether rules duplicate/conflict with CONTRIBUTING/testing docs; confirm enforcement is social vs scripted | AGENTS file text; prior audited `CONTRIBUTING.md`; CI workflow scope | Batch A: governance entrypoints |
| `./CHANGELOG.md` | historical | Could contain normative release-policy claims still treated as active | low | Check whether release rules here are referenced by README/CONTRIBUTING/workflows; classify as historical log vs active governance | README/CONTRIBUTING links; release scripts/workflows | Batch D: historical/admin docs |
| `./artifacts/architecture-boundary-report.current.md` | operational | Artifact may be de facto enforcement evidence for boundary drift | high | Map producer script and CI consumption path; determine whether reviewers treat it as blocking or advisory; verify update cadence against code changes | `scripts/architecture_boundary_report.py`; `scripts/all_green_gate.py`; workflow usage | Batch B: architecture enforcement artifacts |
| `./docs/architecture/behavior-governance.md` | reference | Linked from README as non-authoritative, but may still influence decisions | medium | Trace inbound links; compare claims against canonical pipeline and directives; classify sections as explanatory vs normative | README links; `docs/architecture/canonical-turn-pipeline.md`; directives matrix | Batch B: architecture governance docs |
| `./docs/architecture/canonical-turn-pipeline.md` | canonical | Core runtime contract was not audited in this pass; high governance impact | high | Validate claims against runtime stage functions and tests; map which sections are executable-enforced vs descriptive; detect overlaps with traceability matrix | `src/testbot/*stage*`; tests; traceability matrix; gate scripts | Batch B: architecture governance docs |
| `./docs/architecture/commit-drift-audit-2026-03-19.md` | historical | Might be misused as live authority due to concrete remediation directions | medium | Identify whether any active docs/issues cite this as current policy; determine if header needs explicit historical superseded marker | Cross-links in docs/issues/roadmap | Batch D: historical/admin docs |
| `./docs/architecture/documentation-governance-audit-2026-03-21.md` | historical | Prior pass artifact may still be treated as active without pass-trail context | medium | Verify whether this file is referenced as current canonical audit; ensure progression links to follow-up audits are explicit | README/docs/architecture index links | Batch D: historical/admin docs |
| `./docs/architecture/system-structure-audit-2026-03-19.md` | historical | Could overlap with canonical architecture claims | medium | Compare claims to current architecture docs/tests; classify stale findings vs active governance rules | architecture docs; test suite references | Batch D: historical/admin docs |
| `./docs/governance/architecture-drift-register.md` | transitional | Likely tracks open governance debt with owner/severity semantics | high | Determine whether register drives prioritization/review decisions; trace links from roadmap/issues; verify if statuses are maintained and bound to checks | issue records; roadmap docs; all_green outputs | Batch C: governance trackers |
| `./docs/governance/code-review-governance-automation-dependency-boundaries.md` | reference | Review policy may shadow CONTRIBUTING/testing and enforce unofficial rules | high | Compare checklist items to actual CI blockers; identify documentary-only blockers; map overlaps with python checklist doc | CONTRIBUTING/testing; workflow checks; python checklist doc | Batch C: governance trackers |
| `./docs/governance/drift-remediation-backlog.md` | transitional | Backlog might be de facto roadmap for governance closure | high | Trace owner/due-date linkage to issues; verify whether backlog state updates follow merged PRs; detect duplicate ownership with roadmap/issues | issues, roadmap, governance register | Batch C: governance trackers |
| `./docs/governance/drift-traceability-matrix.md` | transitional | Could duplicate canonical directives traceability matrix | high | Compare row semantics to canonical traceability matrix; identify fields unique to drift triage; determine whether duplication is controlled or split authority | `docs/directives/traceability-matrix.md`; governance scripts | Batch C: governance trackers |
| `./docs/governance/issue-implementation-audit.md` | historical | May contain implementation assertions that still drive review behavior | medium | Check inbound references from issue docs/review checklists; classify as snapshot vs living authority | docs/issues/*; governance docs | Batch C: governance trackers |
| `./docs/governance/mission-vision-alignment.md` | reference | Potential overlap with product principles and README vision claims | medium | Compare principle mappings with directives product-principles; check whether it introduces competing normative requirements | README; product-principles; testing obligations | Batch C: governance trackers |
| `./docs/governance/python-code-review-checklist-dependency-boundaries.md` | reference | Language-specific checklist may define de facto blockers without automation | high | Map checklist items to existing linters/tests; mark non-enforced controls; compare with broader code-review governance doc | CI configs; ruff/mypy/pytest invocations; governance checklist doc | Batch C: governance trackers |
| `./docs/invariants/answer-policy.md` | canonical | Canonical response-policy invariant source; high authority | high | Validate invariant IDs/statements against runtime guards and BDD scenarios; verify mirror sync boundaries and update behavior | runtime enforcement functions; BDD feature files; sync scripts | Batch B: architecture enforcement artifacts |
| `./docs/invariants/pipeline.md` | canonical | Canonical stage-semantics invariants not yet audited | high | Validate PINV linkage against stage transitions and `validate_pipeline_stage_conformance.py`; detect any undocumented semantics | stage transition validators; traceability matrix | Batch B: architecture enforcement artifacts |
| `./docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md` | transitional | Issue may still define policy details outside canonical workflow | medium | Determine whether AC text is still used as governance source; compare with `docs/issues.md` and validators | docs/issues.md; validate_issue_links rules | Batch E: issue canon set |
| `./docs/issues/ISSUE-0002-behave-dev-deps-reminders.md` | historical | Could carry setup policy now moved elsewhere | low | Check whether README/testing/quickstart already supersede; mark as historical evidence if no active references | README/testing/quickstart links | Batch E: issue canon set |
| `./docs/issues/ISSUE-0003-readme-layout-drift.md` | historical | Might encode documentation structure rules not captured elsewhere | low | Compare issue ACs with current README structure and contributor workflow docs; classify if closed-history only | README current content; issue status markers | Batch E: issue canon set |
| `./docs/issues/ISSUE-0004-bdd-policy-not-yet-executable.md` | transitional | BDD enforcement claims may still anchor current governance debt | medium | Verify which ACs became automated checks; map unresolved ACs to current gaps in CI | behave usage in gate/workflows; testing policy | Batch E: issue canon set |
| `./docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md` | transitional | Could define parity authority between eval and runtime | medium | Trace whether tests/scripts reference this issue as active requirement; classify as program artifact vs historical | tests/test_eval_runtime_parity.py; roadmap links | Batch E: issue canon set |
| `./docs/issues/ISSUE-0006-operationalize-docs-issues-area.md` | historical | Foundational issue may still be cited as policy source | medium | Check if current issue workflow derives from this issue text or only from `docs/issues.md`; mark as historical if superseded | docs/issues.md; validator behavior | Batch E: issue canon set |
| `./docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md` | transitional | Might still track unresolved CI governance gap | high | Verify open/closed state vs actual workflows; map acceptance criteria to existing CI jobs | workflows; all_green profiles; issue status | Batch E: issue canon set |
| `./docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md` | transitional | Red-tag issue may define de facto merge policy | high | Check if referenced by RED_TAG or checklist docs; determine if obligations are now encoded in tests/gates | RED_TAG; testing doc; issue-link validator | Batch E: issue canon set |
| `./docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md` | transitional | Could carry active behavior contract details | medium | Compare acceptance criteria against directives decision-policy and invariant docs; identify duplicate authority | directives/invariants; tests/features references | Batch E: issue canon set |
| `./docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md` | transitional | Potential overlap with decision policy and invariants | medium | Map ACs to runtime fallback code/tests; determine whether issue still authoritative or purely tracking | decision-policy, invariants, BDD/tests | Batch E: issue canon set |
| `./docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md` | transitional | Analytics contract may be specified here before docs/testing update | high | Trace if analytics semantics live primarily in this issue; verify downstream docs/scripts alignment | scripts/aggregate_turn_analytics.py; docs/testing.md | Batch E: issue canon set |
| `./docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md` | historical | Superseded program context still referenced in some docs | medium | Audit references to determine whether it remains active authority vs historical feed into ISSUE-0013 | README/traceability references | Batch E: issue canon set |
| `./docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md` | transitional | Program anchor for multiple canonical docs; high authority pressure | high | Determine whether this issue is de facto project control plane; map which requirements are duplicated in directives/checklist | README links; checklist; traceability matrix; gate evidence | Batch E: issue canon set |
| `./docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md` | transitional | Large issue may include governance policy beyond bug tracking | medium | Identify embedded policy statements used elsewhere; separate bug evidence from normative rules | linked evidence docs; testing policy references | Batch E: issue canon set |
| `./docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md` | transitional | May define open-issue quality criteria used operationally | high | Compare criteria to `docs/issues.md`; verify whether this issue effectively overrides canonical workflow | docs/issues.md; validator requirements; RED_TAG | Batch E: issue canon set |
| `./docs/issues/ISSUE-0016-startup-degraded-mode-bdd-coverage-gap.md` | transitional | Could define obligations for degraded-mode policy/testing | medium | Map ACs to runtime mode tests and quickstart/testing docs; classify active vs closed | runtime mode tests; quickstart/testing docs | Batch E: issue canon set |
| `./docs/issues/ISSUE-0017-invariant-boundary-ambiguity-answer-commit-regression.md` | transitional | Potentially authoritative on invariant boundary split | high | Compare issue requirements with current invariants split and sync tooling; verify unresolved items | invariants docs; sync scripts; transition validators | Batch E: issue canon set |
| `./docs/issues/ISSUE-0018-dual-trigger-event-loop-for-proactive-ingestion-lifecycle.md` | transitional | May set runtime lifecycle policy outside architecture docs | medium | Check whether lifecycle constraints in this issue are reflected in canonical pipeline/quickstart | architecture pipeline doc; runtime code/tests | Batch E: issue canon set |
| `./docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md` | transitional | Could define architecture direction not encoded elsewhere | medium | Trace roadmap and architecture references; determine if this issue is planning-only or normative | roadmap docs; architecture docs | Batch E: issue canon set |
| `./docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md` | transitional | Directly impacts quickstart/operator behavior | medium | Verify whether proposal became policy in quickstart/runtime flags; detect stale transitional guidance | quickstart docs; source ingestion code/tests | Batch E: issue canon set |
| `./docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md` | transitional | Migration issue may define architecture boundary authority | high | Map migration milestones to architecture-boundary tests/docs; verify if boundary pattern rules are executable | architecture-boundary tests/report; docs/architecture* | Batch E: issue canon set |
| `./docs/issues/RED_TAG.md` | operational | Escalation index may influence release blocking decisions | high | Audit criteria semantics and update discipline; verify linkage with issue validator and workflow behavior | docs/issues.md; validators; PR workflows | Batch E: issue canon set |
| `./docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md` | historical | Evidence artifact may still be cited as current status | low | Trace inbound links from active docs/issues; classify as frozen evidence vs live dashboard | issue references; roadmap/governance links | Batch F: evidence bundle 2026-03-09 |
| `./docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` | historical | Evidence may be interpreted as current gate truth | low | Check usage in active issue status sections; ensure date-bound context is explicit | issue 0013/0014 references | Batch F: evidence bundle 2026-03-09 |
| `./docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md` | historical | Trace log could be mistaken for invariant definition | low | Verify whether any policy docs cite this for normative behavior; classify evidence-only | issue references; invariants docs | Batch F: evidence bundle 2026-03-09 |
| `./docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md` | historical | Same evidence-role ambiguity as above | low | Trace references and decide archival vs active support role | issue references | Batch F: evidence bundle 2026-03-09 |
| `./docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md` | historical | Same evidence-role ambiguity as above | low | Check if reused in current acceptance criteria; mark as snapshot if not | issue references | Batch F: evidence bundle 2026-03-09 |
| `./docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md` | historical | Could overlap with current testing gate policy | low | Compare claims to current `docs/testing.md` and gate script state; classify outdated/active | docs/testing.md; all_green config | Batch F: evidence bundle 2026-03-09 |
| `./docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md` | historical | Might be stale release-governance source | low | Validate whether release docs still cite this note; classify as historical | roadmap/governance docs | Batch F: evidence bundle 2026-03-09 |
| `./docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md` | historical | Potentially stale runtime gate evidence | low | Check cross-links from canonical pipeline/issue 0013 | issue links; architecture docs | Batch F: evidence bundle 2026-03-09 |
| `./docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md` | historical | Could define traceability tagging norms outside canonical matrix | medium | Compare recommendations with canonical traceability matrix tagging section and validators | traceability matrix; validation scripts | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md` | reference | Could influence validator operational handling | medium | Verify whether validator code reflects this fallback policy and whether docs/issues rely on it | `scripts/validate_issue_links.py`; docs/issues.md | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md` | historical | Behavior evidence for specific bug chain may be mistaken as policy | low | Identify if any canonical docs cite this as rule source | issue references | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md` | transitional | Might be active governance dashboard for issue prioritization | medium | Determine update cadence and whether RED_TAG/issues docs depend on it | RED_TAG; issue statuses | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md` | historical | RCA may hold unresolved policy actions | low | Extract any “must” actions and check if they migrated to issues/directives | linked issue docs | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md` | historical | Could contain active decisioning criteria | medium | Compare findings to decision-policy and pipeline docs; check if unresolved items became canonical rules | decision-policy; pipeline docs | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md` | reference | Complexity analysis may influence refactor governance | low | Check whether any roadmap/governance backlog imports this artifact as decision input | governance backlog; roadmap | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/coordination-failure-contract-drift-matrix.md` | transitional | Matrix may duplicate governance drift register functions | medium | Compare matrix fields/owners with governance drift register and remediation backlog | governance docs trio | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md` | historical | Audit snapshot may compete with newer governance audits | medium | Determine whether active docs still point here for authority; add superseded chain if needed | architecture governance audits; issues | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/governance-craap-analysis-main-alignment.md` | reference | Quality-analysis artifact likely non-canonical but could influence policy decisions | low | Trace references and classify advisory quality note vs governance source | issue/governance references | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md` | transitional | May carry freeze-exit criteria not encoded elsewhere | high | Compare exit criteria with freeze contract and issues workflow; verify if any criteria became executable checks | freeze doc; issues workflow; validators | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/governance-open-questions-audit-2026-03-16.md` | transitional | Might define unresolved governance decisions | medium | Extract unresolved items and map to current open issues/backlogs to avoid hidden backlog | issues list; governance backlog | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/governance-stabilization-checklist.md` | transitional | Checklist may act as de facto gating checklist | high | Compare checklist items with actual PR blockers and all_green checks; classify advisory vs blocking | workflows; gate script; freeze docs | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md` | historical | Status note may be stale yet still linked | low | Check inbound links and whether status statements are obsolete | issue/governance links | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/issue-0022-pass-seven-verification-log.md` | historical | Verification log might include untracked governance assertions | low | Verify whether ISSUE-0022 exists and if this file is orphaned or authoritative | docs/issues directory listing and references | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md` | historical | RCA source likely snapshot but may contain standing policy suggestions | low | Check if recommendations were promoted to directives/issues; classify residue as historical | directives/issues cross-links | Batch H: legacy evidence 2026-03-06/08 |
| `./docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md` | historical | Feedback addendum may duplicate above | low | Same as above, with focus on accepted/rejected actions | same as above | Batch H: legacy evidence 2026-03-06/08 |
| `./docs/issues/evidence/open-pr-assessment-2026-03-17.md` | historical | PR-local assessment should not be treated as standing governance | medium | Confirm no canonical docs cite this for live policy; mark as event artifact | architecture/governance docs links | Batch G: evidence bundle 2026-03-10+ |
| `./docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md` | historical | Session log may be misused as behavior contract | low | Trace references; classify pure debug evidence | issue references | Batch H: legacy evidence 2026-03-06/08 |
| `./docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md` | historical | Same as above | low | Same as above | issue references | Batch H: legacy evidence 2026-03-06/08 |
| `./docs/issues/evidence/production-debug-cli-trace-2026-03-07.md` | historical | Trace snapshot may influence interpretation of current runtime behavior | low | Check if cited in current policy docs; if not, classify archival | issue/policy references | Batch H: legacy evidence 2026-03-06/08 |
| `./docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md` | historical | Combined trace notes may duplicate neighboring evidence files | low | Identify duplication and potential consolidation/archive note | neighboring evidence files | Batch H: legacy evidence 2026-03-06/08 |
| `./docs/issues/evidence/sprint-00-kpi-review.md` | historical | KPI review may contain criteria now moved to testing docs | medium | Compare KPI thresholds/modes to current testing policy and gate arguments | docs/testing.md; all_green gate options | Batch H: legacy evidence 2026-03-06/08 |
| `./docs/issues/evidence/work-history-assessment-2026-03-17.md` | historical | Process retrospective may still influence governance decisions | low | Determine if this is referenced by active roadmap/governance docs | roadmap/governance links | Batch G: evidence bundle 2026-03-10+ |
| `./docs/ops.md` | operational | Operations guide can introduce runtime policies not in canonical directives | medium | Audit for normative behavior claims; compare with quickstart/testing/invariants; classify operational-only vs policy | quickstart/testing/directives | Batch I: ops+qa docs |
| `./docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md` | historical | QA audit may overlap with governance audits | medium | Trace whether active docs cite this as current authority; mark historical scope and supersession if needed | architecture governance audits; issues evidence | Batch I: ops+qa docs |
| `./docs/qa/feature-status-report.md` | transitional | Could be active tracker for feature readiness claims | high | Verify update cadence and relationship to roadmap/testing gate outputs; determine if status is authoritative | roadmap docs; testing gate artifacts | Batch I: ops+qa docs |
| `./docs/qa/live-smoke.md` | operational | Live-smoke policy may affect release gating | high | Map commands/rules to test markers and CI usage; separate optional smoke checks from blockers | pytest markers; testing doc; workflows | Batch I: ops+qa docs |
| `./docs/qa/smoke-evidence-contract.md` | operational | Evidence contract may define required release proof | high | Check whether evidence fields are enforced by scripts/templates or advisory only | gate scripts; PR template/workflow | Batch I: ops+qa docs |
| `./docs/regression-progression-audit-8f9317a-to-head.md` | historical | Audit snapshot may be treated as ongoing governance baseline | medium | Determine whether referenced by roadmap/governance trackers; mark archival if superseded | governance/audit docs cross-links | Batch D: historical/admin docs |
| `./docs/roadmap/alignment-drift-technical-debt-2026-03-05.md` | transitional | Time-boxed roadmap debt note may still drive priorities | medium | Compare to current roadmap and backlog docs; identify stale vs active commitments | other roadmap files; governance backlog | Batch J: roadmap docs |
| `./docs/roadmap/current-status-and-next-5-priorities.md` | transitional | Current-status doc can conflict with checklist/issue program authority | high | Trace references from README; compare priority claims to checklist/issues; detect split progress authority | README; checklist; ISSUE-0013 | Batch J: roadmap docs |
| `./docs/roadmap/next-4-sprints-grounded-knowing.md` | transitional | Declares sprint plan and DoD ties to testing; potential governance driver | high | Validate whether stated DoD commands match actual gate expectations; map open items to issue owners | testing docs/scripts; issue program | Batch J: roadmap docs |
| `./docs/roadmap/reflective-milestone-10-sprints.md` | historical/transitional | Long-horizon plan may duplicate active roadmap priorities | medium | Compare milestone commitments to current-status doc and issue tracker; classify planning archive vs active plan | other roadmap docs; issues | Batch J: roadmap docs |
| `./docs/sessions/ISSUE-0014-cross-functional-session-plan.md` | historical | Session-plan artifact may include policy-level actions | low | Extract any unresolved action items and confirm migration into issue/backlog system | related issue docs; governance backlog | Batch D: historical/admin docs |
| `./docs/style-guide.md` | reference | Writing/style policy may be treated as normative for governance docs | low | Determine if enforced by lint/review or advisory only; check overlap with terminology policy | terminology doc; CONTRIBUTING; lint configs | Batch D: historical/admin docs |
| `./docs/testing-triage.md` | operational | Triage runbook can affect incident/review behavior | medium | Map procedures to canonical testing doc and gate script; identify duplicated or conflicting commands/policies | docs/testing.md; all_green gate | Batch I: ops+qa docs |
| `./examples/Experiments.md` | decorative/reference | Example notebook-style content likely non-authoritative but unknown | low | Check whether README or contributor docs route to this as guidance; classify decorative vs operational examples | README links; contributor docs | Batch D: historical/admin docs |
| `./features/README.md` | reference | Feature-writing guidance may define BDD governance | medium | Verify whether it sets mandatory tagging/structure rules conflicting with directives traceability requirements | traceability matrix; behave configs | Batch K: feature/process docs |
| `./src/seem_bot/README.md` | reference/historical | Legacy module README may conflict with current architecture terminology | low | Determine if code path is active and whether README is linked; classify active submodule contract vs legacy leftover | source tree activity; README links | Batch K: feature/process docs |

## 7. Coverage progression summary

| Audit pass | Date | Newly audited Markdown files | Total audited Markdown files after pass | Remaining Markdown files after pass | Notes |
| ---------- | ---- | ---------------------------- | --------------------------------------- | ----------------------------------- | ----- |
| Documentation governance audit (initial) | 2026-03-21 | 11 | 11 | 96 | Established baseline structural-honesty framing and split-authority findings |
| Documentation governance follow-up audit (this pass) | 2026-03-21 | 9 | 20 | 87 | Advanced into README + directives + invariants index + operator/contributor routing docs |

## 8. Minimal next-step sequence

1. **Next batch to audit:** Batch B (`docs/architecture/canonical-turn-pipeline.md`, `docs/invariants/answer-policy.md`, `docs/invariants/pipeline.md`, `artifacts/architecture-boundary-report.current.md`, plus `docs/architecture/behavior-governance.md`).
2. **Why next:** these files define the core runtime contract and executable semantics that all other governance docs should defer to; auditing them will reduce highest-risk canonical-authority uncertainty.
3. **Evidence to gather first:**
   - function/stage anchors in `src/testbot/` for each documented stage/invariant,
   - validator/gate bindings in `scripts/all_green_gate.py`, `scripts/validate_pipeline_stage_conformance.py`, and boundary-report generation path,
   - PR workflow coverage of those checks.
4. **Uncertainty reduced:**
   - whether architecture/invariant canon is actually bound to executable checks,
   - whether traceability matrix and decision policy are synchronized with true runtime behavior,
   - whether current architecture boundary evidence is advisory or release-blocking.

