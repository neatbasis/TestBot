# Documentation Governance Follow-up Audit — Structural Honesty (2026-03-21, Continuation Pass)

## 1. Scope accounting

This continuation pass keeps the audit ledger accurate **and** materially expands structural-honesty analysis into a new set of previously unaudited Markdown files.

- Total Markdown files currently in repository: **108**
- Previously audited Markdown files (before this pass): **20**
- Remaining unaudited Markdown files before this pass: **88**
- Newly audited Markdown files in this pass: **5**
- Remaining unaudited Markdown files after this pass: **83**

Non-Markdown artifacts reviewed as evidence in this pass:
- `scripts/all_green_gate.py`
- `scripts/smoke/run_live_smoke.py`
- `scripts/smoke/run_live_smoke.sh`
- `scripts/triage_router.py`
- `docs/qa/triage-routing.yaml`

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
- `./README.md`
- `./docs/invariants.md`
- `./docs/directives/CHANGE_POLICY.md`
- `./docs/directives/decision-policy.md`
- `./docs/directives/invariants.md`
- `./docs/directives/product-principles.md`
- `./docs/directives/traceability-matrix.md`
- `./docs/quickstart.md`
- `./docs/terminology.md`

### 1.2 Remaining unaudited Markdown files before this pass

- `./AGENTS.md`
- `./CHANGELOG.md`
- `./artifacts/architecture-boundary-report.current.md`
- `./docs/architecture/behavior-governance.md`
- `./docs/architecture/canonical-turn-pipeline.md`
- `./docs/architecture/commit-drift-audit-2026-03-19.md`
- `./docs/architecture/documentation-governance-audit-2026-03-21.md`
- `./docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`
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

### 1.3 Newly selected files for this pass

- `./docs/ops.md` — High governance impact: embeds KPI thresholds, log schema policy, and release-gate rollout language that can override testing/directive authority if not bounded.
- `./docs/qa/live-smoke.md` — Directly influences release-confidence behavior by defining required env/config and ISSUE-0013 routing expectations for smoke outcomes.
- `./docs/qa/smoke-evidence-contract.md` — Defines artifact schema consumed in triage/review decisions; critical to determine whether it is canonical operational contract or advisory note.
- `./docs/testing-triage.md` — Specifies owner/escalation routing and introduces automation hooks (`triage_router.py`) that can become de facto incident-governance authority.
- `./features/README.md` — Contributor-facing BDD authoring rules; potentially duplicates or diverges from directives traceability and testing policy expectations.

### 1.4 Remaining unaudited Markdown files after this pass

- `./AGENTS.md`
- `./CHANGELOG.md`
- `./artifacts/architecture-boundary-report.current.md`
- `./docs/architecture/behavior-governance.md`
- `./docs/architecture/canonical-turn-pipeline.md`
- `./docs/architecture/commit-drift-audit-2026-03-19.md`
- `./docs/architecture/documentation-governance-audit-2026-03-21.md`
- `./docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`
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
- `./docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md`
- `./docs/qa/feature-status-report.md`
- `./docs/regression-progression-audit-8f9317a-to-head.md`
- `./docs/roadmap/alignment-drift-technical-debt-2026-03-05.md`
- `./docs/roadmap/current-status-and-next-5-priorities.md`
- `./docs/roadmap/next-4-sprints-grounded-knowing.md`
- `./docs/roadmap/reflective-milestone-10-sprints.md`
- `./docs/sessions/ISSUE-0014-cross-functional-session-plan.md`
- `./docs/style-guide.md`
- `./examples/Experiments.md`
- `./src/seem_bot/README.md`

### 1.5 Scope-accounting notes

- The previous audit scope was reconstructed from two prior governance audit artifacts in `docs/architecture/` (initial pass + earlier follow-up content).
- `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` is counted in repository inventory and remaining scope when unaudited, but it is **explicitly excluded** from newly audited substantive scope for this pass.
- No non-Markdown files were counted toward audit coverage percentages; scripts were evidence only.

## 2. Scope selection rationale

This pass prioritized remaining files that can **change day-to-day operational/review behavior** instead of archival artifacts. The selected set was chosen to reduce uncertainty about whether live operational docs (`docs/ops.md`, `docs/qa/*`, `docs/testing-triage.md`) are quietly functioning as policy authorities that compete with already-audited directives and testing canon. `features/README.md` was included because contributor BDD authoring guidance can fragment traceability governance if it diverges from directive requirements.

These files were selected ahead of evidence logs and historical audits because they are directly linked from contributor/operator paths or define current execution/triage expectations that influence release decisions.

## 3. Executive summary

This continuation pass substantively audited **5 previously unaudited Markdown files** (`docs/ops.md`, `docs/qa/live-smoke.md`, `docs/qa/smoke-evidence-contract.md`, `docs/testing-triage.md`, `features/README.md`) while also completing ledger maintenance. The new analysis reduced uncertainty about where smoke readiness, triage ownership, and BDD authoring standards are actually governed in practice, and surfaced new split-authority/decorative-risk findings: (1) operational smoke docs behave as de facto release-governance policy without clearly bounded precedence versus `docs/testing.md`; (2) ISSUE-0013 routing language is replicated across multiple QA/ops docs, creating governance fan-out; and (3) `features/README.md` carries potentially normative conventions that are not explicitly tied to canonical directive ownership. The most important next batch is architecture+invariant enforcement docs (`docs/architecture/canonical-turn-pipeline.md`, `docs/invariants/answer-policy.md`, `docs/invariants/pipeline.md`, boundary artifacts), because that batch determines whether documentation authority is actually executable.

Scope bookkeeping was completed (counts, prior/new/remaining set separation), **and** new governance frontier analysis was completed (five newly audited files with new findings and remediation).

## 4. Audit findings for newly audited files

| Document | Claimed purpose | Actual role in practice | Evidence | Classification | Governance risk | Action |
| -------- | --------------- | ----------------------- | -------- | -------------- | --------------- | ------ |
| `./docs/ops.md` | Operations and troubleshooting guidance | De facto operational policy surface containing KPI guardrail thresholds, gate-mode rollout language, and telemetry contract statements that influence release interpretation | Contains explicit “authoritative” KPI mode policy and threshold text; references `all_green_gate.py` behavior and issue evidence obligations | `operational` | High: policy-in-ops can drift from canonical testing/directive owners | Move normative KPI policy ownership to one canonical governance doc; keep `ops.md` procedural and link out for policy truth |
| `./docs/qa/live-smoke.md` | Configure and run live smoke checks | Operational runbook that also imposes sequencing/issue-routing rules via ISSUE-0013 | Prescribes routing failures through ISSUE-0013 and defines required env/check classes used in release confidence decisions | `operational` | Medium-high: embeds governance routing that may bypass canonical issue workflow precedence | Keep execution instructions here, but centralize escalation precedence in `docs/issues.md` and reference from this file |
| `./docs/qa/smoke-evidence-contract.md` | Define smoke output schema contract | Canonical-ish evidence schema for smoke artifacts used by triage/review, but ownership boundary vs QA/testing canon is implicit | Defines artifact fields, failure categories, and ISSUE-0013 linkage expectations; consumed by smoke scripts and reviewers | `transitional` | High: can become shadow canonical source if not explicitly owned and versioned | Declare explicit owner and versioning authority; add machine validation linkage and precedence note vs `docs/testing.md` |
| `./docs/testing-triage.md` | Map test failures to owner/actions | Active operational governance for incident ownership routing with automation hook (`triage_router.py`) | Defines owner/escalation table and post-gate integration path; references issue lifecycle and red-tag process | `operational` | Medium: owner routing can diverge from issue workflow policy and create inconsistent escalation | Add precedence clause (“issues.md governs lifecycle”) and keep table strictly as routing defaults |
| `./features/README.md` | Guide writing/running BDD features | Contributor-facing reference that can influence mandatory BDD structure/tags; partially normative in practice | Referenced as feature authoring guidance; content shapes how contributors encode scenarios used by gate evidence | `reference` | Medium: undocumented precedence with directives traceability may fragment behavior-contract ownership | Add explicit linkage to traceability/decision-policy docs and label which conventions are required vs examples |

## 5. Newly surfaced governance findings

| Topic | Newly audited documents involved | Interaction with existing authorities | Why this creates ambiguity or drift risk | Canonical owner | Required action |
| ----- | -------------------------------- | ------------------------------------- | ---------------------------------------- | --------------- | --------------- |
| Smoke governance split across QA/testing/issue program | `docs/qa/live-smoke.md`, `docs/qa/smoke-evidence-contract.md`, `docs/ops.md` | Intersects with previously audited `docs/testing.md` and `docs/issues.md` | Smoke docs define execution + evidence + ISSUE routing, but precedence against testing canon is implicit, so teams can follow different “truth” docs | `docs/testing.md` for gate policy; `docs/issues.md` for escalation lifecycle | Add explicit precedence block in each smoke doc and trim duplicated escalation prose |
| ISSUE-0013 as duplicated governance anchor | `docs/ops.md`, `docs/qa/live-smoke.md`, `docs/qa/smoke-evidence-contract.md` | Interacts with audited issue workflow docs and directives | Repeated “route via ISSUE-0013” language creates single-issue dependency and fan-out if issue status changes or closes | `docs/issues.md` + program issue metadata | Replace hard-coded issue-routing text with pointer to canonical issue-workflow section that names current program anchor |
| Triage routing defaults vs lifecycle authority | `docs/testing-triage.md` | Interacts with audited `docs/issues.md` and red-tag governance | Owner/escalation table may be interpreted as policy override instead of default mapping, causing inconsistent incident handling | `docs/issues.md` | Add explicit non-override statement and require triage-router output to include source-of-truth links |

## 6. Concrete remediation changes implied by this pass

| Finding | Current problem | Smallest concrete remediation | Why this reduces ambiguity |
| ------- | --------------- | ----------------------------- | -------------------------- |
| Smoke docs carry unbounded governance language | Runbooks mix operational steps with escalation authority and issue-program mandates | Add a standardized “Governance precedence” front-matter block to `docs/qa/live-smoke.md` and `docs/qa/smoke-evidence-contract.md` pointing to `docs/testing.md` (gate policy) and `docs/issues.md` (lifecycle/escalation) | Readers can distinguish runnable procedure from policy authority immediately, reducing split-follow behavior |
| KPI policy embedded in ops runbook | `docs/ops.md` includes “authoritative” KPI mode policy text that may drift from canonical governance docs | Move KPI mode policy paragraph to a single canonical policy doc (testing or directives), then replace with short link in `docs/ops.md` | Prevents policy drift while preserving practical troubleshooting workflow |
| Triage defaults may be mistaken for mandatory governance | `docs/testing-triage.md` does not clearly state precedence against issue lifecycle canon | Add explicit sentence: “Routing table is default guidance; `docs/issues.md` controls severity/state lifecycle decisions” and include this in triage-router output metadata | Keeps automation recommendations subordinate to canonical workflow, reducing conflicting reviewer decisions |

## 7. Remaining-document task planning table

| Remaining document | Suspected role | Why it still needs audit | Priority | Audit tasks required | Dependencies / prerequisite evidence | Recommended future audit batch |
| ------------------ | -------------- | ------------------------ | -------- | -------------------- | ------------------------------------ | ------------------------------ |
| `./AGENTS.md` | reference | Potentially low-centrality doc still may affect contributor behavior if linked from primary entrypoints. | low | Check inbound links from README/CONTRIBUTING/task prompts and decide active guidance vs archival artifact. | README, CONTRIBUTING, developer tooling prompts | Batch D: historical/admin docs |
| `./CHANGELOG.md` | reference | Potentially low-centrality doc still may affect contributor behavior if linked from primary entrypoints. | low | Check inbound links from README/CONTRIBUTING/task prompts and decide active guidance vs archival artifact. | README, CONTRIBUTING, developer tooling prompts | Batch D: historical/admin docs |
| `./artifacts/architecture-boundary-report.current.md` | reference | Architecture/invariant artifact may define executable truth and must be reconciled with runtime enforcement. | high | Trace claims to runtime functions/tests and validator scripts; mark descriptive-only sections and verify whether disappearance would break decisions. | src/testbot/*, tests/features, validation scripts | Batch B: architecture + invariant enforcement |
| `./docs/architecture/behavior-governance.md` | reference | Architecture/invariant artifact may define executable truth and must be reconciled with runtime enforcement. | high | Trace claims to runtime functions/tests and validator scripts; mark descriptive-only sections and verify whether disappearance would break decisions. | src/testbot/*, tests/features, validation scripts | Batch B: architecture + invariant enforcement |
| `./docs/architecture/canonical-turn-pipeline.md` | canonical | Architecture/invariant artifact may define executable truth and must be reconciled with runtime enforcement. | high | Trace claims to runtime functions/tests and validator scripts; mark descriptive-only sections and verify whether disappearance would break decisions. | src/testbot/*, tests/features, validation scripts | Batch B: architecture + invariant enforcement |
| `./docs/architecture/commit-drift-audit-2026-03-19.md` | reference | Architecture/invariant artifact may define executable truth and must be reconciled with runtime enforcement. | high | Trace claims to runtime functions/tests and validator scripts; mark descriptive-only sections and verify whether disappearance would break decisions. | src/testbot/*, tests/features, validation scripts | Batch B: architecture + invariant enforcement |
| `./docs/architecture/documentation-governance-audit-2026-03-21.md` | reference | Architecture/invariant artifact may define executable truth and must be reconciled with runtime enforcement. | high | Trace claims to runtime functions/tests and validator scripts; mark descriptive-only sections and verify whether disappearance would break decisions. | src/testbot/*, tests/features, validation scripts | Batch B: architecture + invariant enforcement |
| `./docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md` | historical | Meta audit artifact; excluded from substantive-counting but still unaudited as a governed Markdown object. | medium | Confirm progression linkage and add explicit pointer to next follow-up pass so audit chain remains navigable. | prior governance audit files and architecture index links | Batch D: audit-artifact governance |
| `./docs/architecture/system-structure-audit-2026-03-19.md` | reference | Architecture/invariant artifact may define executable truth and must be reconciled with runtime enforcement. | high | Trace claims to runtime functions/tests and validator scripts; mark descriptive-only sections and verify whether disappearance would break decisions. | src/testbot/*, tests/features, validation scripts | Batch B: architecture + invariant enforcement |
| `./docs/governance/architecture-drift-register.md` | transitional | Governance tracker/checklist may duplicate canonical directives or testing gates. | high | Compare each obligation with enforced checks and canonical owners; split tracker metadata from normative policy text. | docs/directives/*, docs/testing.md, scripts/all_green_gate.py | Batch C: governance trackers |
| `./docs/governance/code-review-governance-automation-dependency-boundaries.md` | transitional | Governance tracker/checklist may duplicate canonical directives or testing gates. | high | Compare each obligation with enforced checks and canonical owners; split tracker metadata from normative policy text. | docs/directives/*, docs/testing.md, scripts/all_green_gate.py | Batch C: governance trackers |
| `./docs/governance/drift-remediation-backlog.md` | transitional | Governance tracker/checklist may duplicate canonical directives or testing gates. | high | Compare each obligation with enforced checks and canonical owners; split tracker metadata from normative policy text. | docs/directives/*, docs/testing.md, scripts/all_green_gate.py | Batch C: governance trackers |
| `./docs/governance/drift-traceability-matrix.md` | transitional | Governance tracker/checklist may duplicate canonical directives or testing gates. | high | Compare each obligation with enforced checks and canonical owners; split tracker metadata from normative policy text. | docs/directives/*, docs/testing.md, scripts/all_green_gate.py | Batch C: governance trackers |
| `./docs/governance/issue-implementation-audit.md` | transitional | Governance tracker/checklist may duplicate canonical directives or testing gates. | high | Compare each obligation with enforced checks and canonical owners; split tracker metadata from normative policy text. | docs/directives/*, docs/testing.md, scripts/all_green_gate.py | Batch C: governance trackers |
| `./docs/governance/mission-vision-alignment.md` | transitional | Governance tracker/checklist may duplicate canonical directives or testing gates. | high | Compare each obligation with enforced checks and canonical owners; split tracker metadata from normative policy text. | docs/directives/*, docs/testing.md, scripts/all_green_gate.py | Batch C: governance trackers |
| `./docs/governance/python-code-review-checklist-dependency-boundaries.md` | transitional | Governance tracker/checklist may duplicate canonical directives or testing gates. | high | Compare each obligation with enforced checks and canonical owners; split tracker metadata from normative policy text. | docs/directives/*, docs/testing.md, scripts/all_green_gate.py | Batch C: governance trackers |
| `./docs/invariants/answer-policy.md` | canonical | Architecture/invariant artifact may define executable truth and must be reconciled with runtime enforcement. | high | Trace claims to runtime functions/tests and validator scripts; mark descriptive-only sections and verify whether disappearance would break decisions. | src/testbot/*, tests/features, validation scripts | Batch B: architecture + invariant enforcement |
| `./docs/invariants/pipeline.md` | canonical | Architecture/invariant artifact may define executable truth and must be reconciled with runtime enforcement. | high | Trace claims to runtime functions/tests and validator scripts; mark descriptive-only sections and verify whether disappearance would break decisions. | src/testbot/*, tests/features, validation scripts | Batch B: architecture + invariant enforcement |
| `./docs/issues/ISSUE-0001-issue-governance-trackable-measurable.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0002-behave-dev-deps-reminders.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0003-readme-layout-drift.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0004-bdd-policy-not-yet-executable.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0005-eval-runtime-logic-divergence-risk.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0006-operationalize-docs-issues-area.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | high | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0015-open-issue-review-and-issue-0014-quality-governance-hardening.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0016-startup-degraded-mode-bdd-coverage-gap.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0017-invariant-boundary-ambiguity-answer-commit-regression.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | high | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0018-dual-trigger-event-loop-for-proactive-ingestion-lifecycle.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0019-channel-agnostic-conversation-engine-and-shared-history.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0020-source-ingestion-quickstart-env-toggle-deprecation-proposal.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | medium | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/RED_TAG.md` | transitional | Issue artifact may be acting as policy authority instead of tracker-only record. | high | Map acceptance criteria/status rules to canonical docs and CI validators; identify any normative rules that must migrate out of issue text. | docs/issues.md, validators, and linked workflows | Batch E: issue canon set |
| `./docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/coordination-failure-contract-drift-matrix.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/governance-craap-analysis-main-alignment.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/governance-open-questions-audit-2026-03-16.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/governance-stabilization-checklist.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/issue-0022-pass-seven-verification-log.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/open-pr-assessment-2026-03-17.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/production-debug-cli-trace-2026-03-07.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/sprint-00-kpi-review.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/issues/evidence/work-history-assessment-2026-03-17.md` | historical | Evidence note may still be cited as active policy or gate truth. | low | Trace inbound links from active docs/issues, classify as archival vs active, and add explicit superseded/date-bounded status if still referenced. | docs/issues.md plus referencing issue records | Batch F/G/H: issue evidence bundles |
| `./docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md` | operational | QA doc may define release-readiness obligations not backed by automation. | medium | Map required evidence/commands to CI and gate outputs; downgrade unenforced blockers to advisory or automate them. | docs/testing.md, scripts/all_green_gate.py, workflows | Batch I: QA operational docs |
| `./docs/qa/feature-status-report.md` | operational | QA doc may define release-readiness obligations not backed by automation. | high | Map required evidence/commands to CI and gate outputs; downgrade unenforced blockers to advisory or automate them. | docs/testing.md, scripts/all_green_gate.py, workflows | Batch I: QA operational docs |
| `./docs/regression-progression-audit-8f9317a-to-head.md` | reference | Potentially low-centrality doc still may affect contributor behavior if linked from primary entrypoints. | low | Check inbound links from README/CONTRIBUTING/task prompts and decide active guidance vs archival artifact. | README, CONTRIBUTING, developer tooling prompts | Batch D: historical/admin docs |
| `./docs/roadmap/alignment-drift-technical-debt-2026-03-05.md` | transitional | Roadmap/status docs may conflict with issue or checklist authority on “current priorities”. | medium | Verify update cadence and precedence against issue program/checklists; classify plan-of-record vs historical planning note. | README routing and issue program anchors | Batch J: roadmap docs |
| `./docs/roadmap/current-status-and-next-5-priorities.md` | transitional | Roadmap/status docs may conflict with issue or checklist authority on “current priorities”. | medium | Verify update cadence and precedence against issue program/checklists; classify plan-of-record vs historical planning note. | README routing and issue program anchors | Batch J: roadmap docs |
| `./docs/roadmap/next-4-sprints-grounded-knowing.md` | transitional | Roadmap/status docs may conflict with issue or checklist authority on “current priorities”. | medium | Verify update cadence and precedence against issue program/checklists; classify plan-of-record vs historical planning note. | README routing and issue program anchors | Batch J: roadmap docs |
| `./docs/roadmap/reflective-milestone-10-sprints.md` | transitional | Roadmap/status docs may conflict with issue or checklist authority on “current priorities”. | medium | Verify update cadence and precedence against issue program/checklists; classify plan-of-record vs historical planning note. | README routing and issue program anchors | Batch J: roadmap docs |
| `./docs/sessions/ISSUE-0014-cross-functional-session-plan.md` | reference | Potentially low-centrality doc still may affect contributor behavior if linked from primary entrypoints. | low | Check inbound links from README/CONTRIBUTING/task prompts and decide active guidance vs archival artifact. | README, CONTRIBUTING, developer tooling prompts | Batch D: historical/admin docs |
| `./docs/style-guide.md` | reference | Potentially low-centrality doc still may affect contributor behavior if linked from primary entrypoints. | low | Check inbound links from README/CONTRIBUTING/task prompts and decide active guidance vs archival artifact. | README, CONTRIBUTING, developer tooling prompts | Batch D: historical/admin docs |
| `./examples/Experiments.md` | reference | Potentially low-centrality doc still may affect contributor behavior if linked from primary entrypoints. | low | Check inbound links from README/CONTRIBUTING/task prompts and decide active guidance vs archival artifact. | README, CONTRIBUTING, developer tooling prompts | Batch D: historical/admin docs |
| `./src/seem_bot/README.md` | reference | Unaudited markdown may still influence behavior through contributor routing. | medium | Trace inbound references and compare normative language with canonical owners; classify and scope-limit as needed. | README and canonical policy docs | Batch D: mixed governance remainder |

## 8. Coverage progression summary

| Audit pass | Date | Newly audited Markdown files in pass | Total audited Markdown files after pass | Remaining Markdown files after pass | Material uncertainty reduced |
| ---------- | ---- | ------------------------------------ | --------------------------------------- | ----------------------------------- | ---------------------------- |
| Documentation governance audit (initial) | 2026-03-21 | 11 | 11 | 97 | Established baseline split-authority map across architecture/testing/issues/checklist entrypoints |
| Documentation governance follow-up (pass 1) | 2026-03-21 | 9 | 20 | 88 | Reduced uncertainty across README + directives + invariants index authority and enforcement linkage |
| Documentation governance follow-up (this continuation pass) | 2026-03-21 | 5 | 25 | 83 | Reduced uncertainty in operational smoke/triage/BDD-authoring governance and surfaced new fan-out + precedence gaps |

## 9. Minimal next-step sequence

1. **Next batch:** Batch B (`docs/architecture/canonical-turn-pipeline.md`, `docs/invariants/answer-policy.md`, `docs/invariants/pipeline.md`, `artifacts/architecture-boundary-report.current.md`, `docs/architecture/behavior-governance.md`).
2. **Why next:** this batch controls executable behavior truth; auditing it determines whether current policy docs are grounded in runtime/validator reality or only documentary claims.
3. **Evidence to gather first:**
   - stage/invariant enforcement anchors in `src/testbot/` and deterministic tests/features,
   - validator usage paths in `scripts/all_green_gate.py`, `scripts/validate_pipeline_stage_conformance.py`, and boundary-report generation tooling,
   - CI workflow references to those validators and artifact expectations.
4. **Uncertainty reduced by that next pass:**
   - whether architecture/invariant docs are genuinely canonical or partially decorative,
   - whether traceability and decision-policy mappings are executable end-to-end,
   - and whether boundary/audit artifacts are release-relevant evidence or informational-only outputs.
