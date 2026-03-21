# Documentation Governance Follow-up Audit — Continuation Pass 15 (2026-03-21)

Anchor document used before scope selection: `docs/architecture/documentation-governance-audit-2026-03-21.md`.

This pass continues the anchor backlog rather than redefining scope. Method, classification style, and remaining-scope accounting are inherited from the anchor audit.

## 1. Scope accounting

- **Total Markdown files currently in repo:** 108.
- **Markdown files already covered by previous documentation governance audits (before this pass):** 90.
- **Markdown files newly selected for this audit pass:** 6.
- **Markdown files still not yet audited after selection in this pass:** 12.
- **Non-Markdown enforcement artifacts reviewed for evidence in this pass:** `scripts/all_green_gate.py`, `scripts/report_feature_status.py`, `.github/workflows/issue-link-validation.yml`, plus repository-wide inbound-link scans.

Repository-change accounting relative to anchor backlog:
- The anchor out-of-scope list (96 files) was treated as the authoritative follow-up backlog seed.
- Current-repo comparison found **no removed/renamed** anchor-backlog Markdown files.
- No new anchor-backlog candidates were introduced; this pass strictly advances the existing remainder.

### 1.1 Previously audited Markdown files

- `.github/PULL_REQUEST_TEMPLATE.md`
- `AGENTS.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `README.md`
- `artifacts/architecture-boundary-report.current.md`
- `docs/architecture-boundaries.md`
- `docs/architecture.md`
- `docs/architecture/architecture-governance-audit-2026-03-20.md`
- `docs/architecture/behavior-governance.md`
- `docs/architecture/canonical-turn-pipeline.md`
- `docs/architecture/commit-drift-audit-2026-03-19.md`
- `docs/architecture/documentation-governance-audit-2026-03-21.md`
- `docs/architecture/documentation-governance-follow-up-audit-2026-03-21.md`
- `docs/architecture/plan-execution-checklist.md`
- `docs/architecture/system-structure-audit-2026-03-19.md`
- `docs/directives/CHANGE_POLICY.md`
- `docs/directives/decision-policy.md`
- `docs/directives/invariants.md`
- `docs/directives/product-principles.md`
- `docs/directives/traceability-matrix.md`
- `docs/governance/architecture-drift-register.md`
- `docs/governance/code-review-governance-automation-dependency-boundaries.md`
- `docs/governance/drift-remediation-backlog.md`
- `docs/governance/drift-traceability-matrix.md`
- `docs/governance/issue-implementation-audit.md`
- `docs/governance/mission-vision-alignment.md`
- `docs/governance/python-code-review-checklist-dependency-boundaries.md`
- `docs/invariants.md`
- `docs/invariants/answer-policy.md`
- `docs/invariants/pipeline.md`
- `docs/issues.md`
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
- `docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md`
- `docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md`
- `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md`
- `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md`
- `docs/issues/evidence/2026-03-14-active-issue-triage-matrix.md`
- `docs/issues/evidence/coordination-failure-contract-drift-matrix.md`
- `docs/issues/evidence/governance-control-surface-completion-audit-2026-03-16.md`
- `docs/issues/evidence/governance-freeze-exit-closure-investigation-2026-03-16.md`
- `docs/issues/evidence/governance-open-questions-audit-2026-03-16.md`
- `docs/issues/evidence/governance-stabilization-checklist.md`
- `docs/issues/evidence/governance-stabilization-status-note-2026-03-16.md`
- `docs/issues/evidence/issue-0022-pass-seven-verification-log.md`
- `docs/issues/evidence/sprint-00-kpi-review.md`
- `docs/issues/governance-control-surface-contract-freeze.md`
- `docs/ops.md`
- `docs/pivot.md`
- `docs/qa/alignment-tensions-architecture-rule-governance-issues-features-bdd-evidence-2026-03-08.md`
- `docs/qa/feature-status-report.md`
- `docs/qa/live-smoke.md`
- `docs/qa/smoke-evidence-contract.md`
- `docs/quickstart.md`
- `docs/regression-progression-audit-8f9317a-to-head.md`
- `docs/roadmap/alignment-drift-technical-debt-2026-03-05.md`
- `docs/roadmap/current-status-and-next-5-priorities.md`
- `docs/roadmap/next-4-sprints-grounded-knowing.md`
- `docs/roadmap/reflective-milestone-10-sprints.md`
- `docs/sessions/ISSUE-0014-cross-functional-session-plan.md`
- `docs/style-guide.md`
- `docs/terminology.md`
- `docs/testing-triage.md`
- `docs/testing.md`
- `examples/Experiments.md`
- `features/README.md`
- `plan.md`
- `src/seem_bot/README.md`

### 1.2 Candidate remaining Markdown files

These were the still-unaddressed anchor-backlog files before this pass:

- `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md`
- `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md`
- `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md`
- `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md`
- `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md`
- `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md`
- `docs/issues/evidence/governance-craap-analysis-main-alignment.md`
- `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md`
- `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md`
- `docs/issues/evidence/open-pr-assessment-2026-03-17.md`
- `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md`
- `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md`
- `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md`
- `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md`
- `docs/issues/evidence/work-history-assessment-2026-03-17.md`

### 1.3 Newly selected files for this audit pass

- `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md`
- `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md`
- `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md`
- `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md`

Selection rationale: this batch was prioritized because these files are directly linked from active issue records (`ISSUE-0013`/`0014`/`0015`) and can most easily be misread as current behavioral authority (acceptance-criteria proof), not merely historical evidence.

### 1.4 Remaining files not audited in this pass

- `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md`
- `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md`
- `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md`
- `docs/issues/evidence/governance-craap-analysis-main-alignment.md`
- `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md`
- `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md`
- `docs/issues/evidence/open-pr-assessment-2026-03-17.md`
- `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md`
- `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md`
- `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md`
- `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md`
- `docs/issues/evidence/work-history-assessment-2026-03-17.md`

## 2. Scope selection rationale

Why this scope now:
- The selected six files are currently cross-linked from active issue governance records and are used as closure evidence for acceptance criteria.
- They contain “PASS/FAIL” and contract-chain language likely to influence reviewer decisions if readers skip canonical owners.
- They therefore carry higher near-term governance ambiguity risk than retrospective debug logs and PR-local assessments still in the remainder.

Why these over the other remaining 12:
- The unselected remainder is mostly RCA, retrospective, PR-local, or debug-session evidence with lower direct influence on current issue closure paths.
- This pass targets the highest-leverage reduction in “evidence doc mistaken as live policy” risk.

Uncertainty this pass reduces:
- Whether ISSUE-0014 trace artifacts currently function as de facto behavior authority.
- Whether feature traceability evidence is authoritative vs merely documenting a one-time script run.

## 3. Executive summary

Repository documentation-governance coverage is now **96/108 Markdown files (88.9%)**, with this pass auditing six additional previously unaudited files from the anchor backlog. The most governance-relevant documents audited now are the four ISSUE-0014 trace/verification files and the repair-offer chain evidence, because they are directly cited in active issue acceptance-criteria sections and could be mistaken for standing behavioral contract authority. New split-authority findings show evidence logs presenting test outcomes and behavioral conclusions without persistent canonical-owner banners, creating review-path ambiguity. The most important next tasks are to audit the remaining 12 evidence documents (starting with RCA + continuity artifacts), then finish explicit archival/non-authoritative labeling recommendations so no anchor-backlog document remains role-ambiguous.

## 4. Audit findings for newly selected documents

| Document | Claimed purpose | Actual role in practice | Evidence | Classification | Governance risk | Action |
| -------- | --------------- | ----------------------- | -------- | -------------- | --------------- | ------ |
| `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` | Phase-1 deterministic verification evidence for ISSUE-0014/0013 dependency gating. | Historical verification snapshot used as issue-linked evidence, not ongoing readiness authority. | Contains dated command outcomes including all-green gate failure; referenced from `ISSUE-0013`, `ISSUE-0014`, `ISSUE-0015`; no CI workflow/script consumes it directly. | historical | high | Add explicit top-line banner: “historical evidence snapshot; canonical readiness truth lives in docs/testing + all_green_gate outputs.” |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md` | CLI trace proving confirmed identity fact promotion behavior. | Historical single-test trace artifact supporting one acceptance criterion. | File is a one-command pytest transcript; inbound links originate from ISSUE-0014/0015 evidence bullets only; no policy docs route to it first. | historical | medium | Keep as immutable trace evidence; add one-line non-authoritative/canonical-owner pointer. |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md` | CLI trace proving semantic preservation for identity follow-ups. | Historical test transcript backing issue closure discussion. | Contains one test invocation + pass output; referenced from ISSUE-0014/0015 acceptance-criteria evidence entries; not wired to gate scripts/workflows. | historical | medium | Keep archival; clarify it does not supersede runtime/test canon. |
| `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md` | CLI trace proving retrieval-path activation for self-reference turn family. | Historical point-in-time proof artifact for issue discussion. | One pytest transcript only; referenced from ISSUE-0014/0015 docs; no enforcement linkage discovered. | historical | medium | Add “evidence only” marker and reference to canonical behavior owners. |
| `docs/issues/evidence/2026-03-10-feature-traceability-tagging-memory-recall.md` | Report scenario-tagging remediation for memory_recall feature traceability. | Transitional operational evidence for a completed script run; can be misread as ongoing governance source. | Documents before/after outputs from `scripts/report_feature_status.py`; not directly used by CI; relates to `docs/qa/feature-status-report.md` generation. | transitional | medium | Add scope bound (“this note documents one remediation run”) and pointer to canonical feature-status/report script owners. |
| `docs/issues/evidence/2026-03-10-issue-0014-repair-offer-followup-chain.md` | Demonstrate repair-offer continuity chain behavior across tests and classification checks. | Transitional evidence note combining deterministic results and environment limitation statement. | Referenced in ISSUE-0013/0014 as supporting evidence; includes “not executed” live replay caveat; no direct enforcement binding. | transitional | high | Add canonical-owner matrix at top (`tests/*`, `all_green_gate`, relevant canonical docs) and mark live-replay caveat as dated context. |

## 5. Newly discovered split-authority or duplication findings

| Topic | Newly selected documents involved | Interaction with previously audited authorities | Why this creates ambiguity | Canonical owner | Required action |
| ----- | --------------------------------- | ----------------------------------------------- | -------------------------- | --------------- | --------------- |
| Acceptance-criteria evidence vs standing behavior contract | `2026-03-09-issue-0014-0013-phase1-deterministic-verification.md`, all three 2026-03-09 ISSUE-0014 trace files | Overlaps with `docs/testing.md`, `docs/architecture/canonical-turn-pipeline.md`, and executable tests. | Issue readers can treat a dated pass transcript as current contract truth. | Canonical docs + executable tests/gates | Add explicit “dated evidence, non-authoritative” preface and canonical-owner links in each trace doc. |
| Repair-offer continuity narrative vs executable owner set | `2026-03-10-issue-0014-repair-offer-followup-chain.md` | Interacts with ISSUE-0013/0014 issue docs and test files that actually enforce behavior. | Mixed narrative + test summary + environment caveat makes authority boundary unclear. | `tests/*` + `scripts/all_green_gate.py` + canonical architecture/testing docs | Keep narrative as evidence, but add owner map and bounded-time context marker. |
| Feature-traceability remediation note vs ongoing reporting authority | `2026-03-10-feature-traceability-tagging-memory-recall.md` | Interacts with `docs/qa/feature-status-report.md` and `scripts/report_feature_status.py`. | Remediation note could be interpreted as durable policy rather than one run report. | `scripts/report_feature_status.py` + generated report artifacts | Add explicit “run-specific evidence” boundary and policy-owner pointer. |

## 6. Remaining-document task planning table

| Remaining document | Suspected role | Why it still needs audit | Priority | Audit tasks required | Dependencies / prerequisite evidence | Recommended future audit batch |
| ------------------ | -------------- | ------------------------ | -------- | -------------------- | ------------------------------------ | ------------------------------ |
| `docs/issues/evidence/2026-03-16-seem-bot-speaker-attribution-rca.md` | historical RCA evidence | RCA conclusions may still be read as active policy. | high | Trace recommendations against current invariants/tests; verify whether any recommendation became executable checks; classify residual governance influence. | `docs/invariants*`, related tests, link scan from `ISSUE-*` | Batch 15A |
| `docs/issues/evidence/2026-03-17-issue-0013-decisioning-temporal-followup-continuity.md` | transitional issue-continuity evidence | Referenced from active ISSUE-0013 context; may shape sequencing decisions. | high | Map all inbound links; compare its guidance against current checklist + ISSUE-0013 state; determine superseded vs still-relied-on claims. | `docs/issues/ISSUE-0013*`, `docs/architecture/plan-execution-checklist.md` | Batch 15A |
| `docs/issues/evidence/complexipy-hotspots-legacy-canonical-analysis-2026-03-14.md` | transitional/historical technical-debt evidence | Linked by ISSUE-0012/0013 tasks and may affect prioritization claims. | high | Reconcile listed task/debt assertions with current issue statuses; determine whether any claim shadows canonical architecture/debt trackers. | `docs/issues/ISSUE-0012*`, `ISSUE-0013*`, governance docs | Batch 15A |
| `docs/issues/evidence/governance-craap-analysis-main-alignment.md` | historical governance assessment | Might still be cited in governance alignment arguments. | medium | Identify active references; test whether any canonical process/checklist relies on this file; classify archival role and stale-risk level. | repo reference graph (`rg -n`) | Batch 15A |
| `docs/issues/evidence/memory-recall-root-cause-review-2026-03-06.md` | historical RCA | Could contain unresolved normative directives not reflected in canon. | high | Extract all recommendation statements; compare to current invariants/tests/issues; mark implemented vs orphaned directives. | invariants, tests, ISSUE-0009/0010 docs | Batch 15A |
| `docs/issues/evidence/memory-recall-root-cause-review-feedback-2026-03-06.md` | historical RCA feedback | Companion feedback may carry actionable governance instructions. | high | Crosswalk feedback items to root-cause doc and current canonical owners; identify unresolved governance deltas. | companion RCA doc + canonical docs/tests | Batch 15A |
| `docs/issues/evidence/open-pr-assessment-2026-03-17.md` | historical PR-local evidence | PR-local recommendations can be mistaken for standing process. | low | Verify no canonical doc links it as policy; classify PR-local historical and define labeling recommendation if needed. | contributor docs + link scan | Batch 15B |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md` | historical debug notes | Debug notes are linked from session/issue docs and could be over-read as contract proof. | medium | Check inbound links and surrounding phrasing; confirm no canonical-owner substitution; classify debug-only role. | `docs/sessions/*`, `docs/issues/ISSUE-0014*` | Batch 15B |
| `docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md` | historical debug notes | Same ambiguity risk as paired session log. | medium | Perform identical link/context audit and classify debug-only governance role. | same as above | Batch 15B |
| `docs/issues/evidence/production-debug-cli-trace-2026-03-07.md` | historical debug trace | Referenced by ISSUE-0009/0010 acceptance text; may still influence contract interpretation. | medium | Trace ISSUE-0009/0010 references; verify whether deterministic tests supersede this trace; classify and propose boundary banner. | `ISSUE-0009`, `ISSUE-0010`, relevant tests | Batch 15B |
| `docs/issues/evidence/production-debug-cli-trace-and-session-log-2026-03-08.md` | historical debug trace bundle | Potential overlap with newer traces/session notes creates evidence duplication ambiguity. | low | Compare with other debug artifacts; decide whether this is superseded aggregate evidence and document role. | related debug evidence files + issue links | Batch 15B |
| `docs/issues/evidence/work-history-assessment-2026-03-17.md` | historical retrospective narrative | Retrospective may still influence roadmap priority narratives. | low | Scan roadmap/plan/issues for dependencies; classify purely historical vs active-planning reference. | `plan.md`, `docs/roadmap/*`, issue links | Batch 15B |

## 7. Coverage progression summary

| Audit pass | Date | Newly audited Markdown files | Total audited Markdown files after pass | Remaining Markdown files after pass | Notes |
| ---------- | ---- | ---------------------------- | --------------------------------------- | ----------------------------------- | ----- |
| Anchor audit | 2026-03-21 | 11 | 11 | 96 | Established method and initial out-of-scope backlog seed. |
| Follow-up pass 1 | 2026-03-21 | 9 | 20 | 87 | Entrypoint/directives/quickstart/invariants tranche. |
| Follow-up pass 2 | 2026-03-21 | 5 | 25 | 82 | Canonical pipeline + boundary contract tranche. |
| Follow-up pass 3 | 2026-03-21 | 7 | 32 | 75 | Governance tracker layer (`docs/governance/*`). |
| Follow-up pass 4 | 2026-03-21 | 6 | 38 | 69 | `RED_TAG` and active issue contract layer (part 1). |
| Follow-up pass 5 | 2026-03-21 | 5 | 43 | 64 | Foundational issue-governance origin set. |
| Follow-up pass 6 | 2026-03-21 | 6 | 49 | 59 | Active issue-control tranche (`ISSUE-0006`..`0011`). |
| Follow-up pass 7 | 2026-03-21 | 5 | 54 | 54 | Remaining active issue-control tranche. |
| Follow-up pass 8 | 2026-03-21 | 6 | 60 | 48 | QA + operations runbook/status tranche. |
| Follow-up pass 9 | 2026-03-21 | 3 | 63 | 45 | Architecture/governance audit-history tranche. |
| Follow-up pass 10 | 2026-03-21 | 4 | 67 | 41 | Contributor/process authority tranche. |
| Follow-up pass 11 | 2026-03-21 | 5 | 72 | 36 | Roadmap/status + BDD/session/audit narrative tranche. |
| Follow-up pass 12 | 2026-03-21 | 6 | 78 | 30 | Started issue-evidence de-authority sweep. |
| Follow-up pass 13 | 2026-03-21 | 6 | 84 | 24 | Closed non-evidence remainder and freeze-era synthesis tranche. |
| Follow-up pass 14 | 2026-03-21 | 6 | 90 | 18 | Dependency-gate progress notes + freeze coordination/status + verification-log tranche. |
| Follow-up pass 15 (this pass) | 2026-03-21 | 6 | 96 | 12 | ISSUE-0014 trace/verification + feature-traceability + repair-offer continuity tranche. |

## 8. Minimal next-step sequence

1. **Audit next batch:** Batch 15A (six files): speaker-attribution RCA, ISSUE-0013 temporal continuity evidence, complexipy hotspot analysis, CRAAP alignment note, and both memory-recall RCA documents.
2. **Why this batch next:** these files have the highest residual chance of being interpreted as active decision guidance (RCA recommendations, ongoing debt/continuity framing).
3. **Evidence to gather first:**
   - inbound-reference map from `docs/issues/ISSUE-*.md`, `docs/issues/RED_TAG.md`, `docs/architecture/plan-execution-checklist.md`, and `docs/testing.md`;
   - executable-binding scan across `.github/workflows/*.yml`, `scripts/*.py`, and test paths named in each document;
   - update-history comparison for docs that still describe “active” state.
4. **Repository-level uncertainty reduced:** whether any remaining RCA/analysis documents still operate as de facto governance authority instead of historical evidence.

Practical completeness check for this pass:
- Prior scope, current scope, and remaining scope are explicitly separated.
- Coverage advanced only into previously unaudited anchor-backlog Markdown files.
- Every remaining anchor-backlog Markdown file has a concrete future audit task.
