# ISSUE-0015: Open-issue review identifies ISSUE-0014 quality/governance gaps that could permit partial-fix closure

- **ID:** ISSUE-0015
- **Title:** Open-issue review identifies ISSUE-0014 quality/governance gaps that could permit partial-fix closure
- **Status:** open
- **Issue State:** governed_execution
- **Severity:** red
- **Owner:** platform-qa
- **Created:** 2026-03-08
- **Target Sprint:** Sprint 6
- **Canonical Cross-Reference:** ISSUE-0014 (defect narrative under review), ISSUE-0013 (primary implementation stream), ISSUE-0012 (delivery-plan governance)
- **Principle Alignment:** contract-first, invariant-driven, traceable, deterministic, ci-enforced, user-centric

## Canonical Cross-Reference

## KPI guardrail mode decision (lifecycle/readiness)

- **Selected mode:** warning mode (`--kpi-guardrail-mode optional`) with explicit debt tracking.
- **Readiness criteria update for ISSUE-0015 closure:** while warning mode remains, unresolved KPI warnings are blocker evidence for this red-tag dependent stream and must remain linked to owner + due date in ISSUE-0015, ISSUE-0014, and `docs/issues/RED_TAG.md` for every review cycle.
- **Current linked warning debt:** `qa_validate_kpi_guardrails` warning at snapshot `2026-03-10T21:36:04Z` -> **Owner: platform-qa**, **Due: 2026-03-21**; lifecycle-language synchronization follow-through -> **Owner: release-governance**, **Due: 2026-03-21**.


- Routing anchor: ISSUE-0013 (**routing anchor** in current execution order; governance close-order stream with open/blocked pending evidence state).
- Execution-order linkage: ISSUE-0008 (**blocker**) -> ISSUE-0011 (**blocker**) -> ISSUE-0012 (**parallel stream**) -> ISSUE-0014 (**blocker**) -> ISSUE-0015 (**dependent**).
- Companion issue references: ISSUE-0014 (defect narrative under review), ISSUE-0012 (delivery-plan governance), ISSUE-0017 (pending-lookup fallback invariant normalization that must stay lifecycle-consistent with ISSUE-0010 policy text).

## Problem Statement

A static code-review pass across all currently open in-repo issues found that ISSUE-0014 is directionally strong as a runtime defect narrative, but still incomplete as a quality-system and governance artifact. The current ISSUE-0014 text captures symptom chain and first-pass hypotheses, yet does not fully constrain causal primacy, stage contracts, test-system blind spots, observability requirements, or closure governance.

This creates a red-tag risk: engineering may ship a local routing patch that improves observed behavior while leaving the defect class and governance escape path intact, allowing premature closure claims for ISSUE-0014 and downstream ISSUE-0013 milestones.

## Scope and Review Plan Executed

Review scope was limited to open issues (`open` or `in_progress`) and issue-governance artifacts under `docs/issues/`.

1. Identify all currently open issue records and active streams.
2. Evaluate ISSUE-0014 against repository issue-quality criteria (`docs/issues.md`) plus canonical pipeline governance expectations.
3. Classify findings by defect taxonomy, contract clarity, testing, observability, and closure discipline.
4. Record actionable acceptance criteria that prevent partial-fix closure and recurrence.

## Open Issues Identified During Review

- ISSUE-0008 — in_progress — intent-grounding router remains partial.
- ISSUE-0009 — open — knowing-mode provenance/recall remains partial.
- ISSUE-0010 — open — unknowing-mode explicit uncertainty contract remains partial.
- ISSUE-0011 — open — turn analytics input coverage silent-drop diagnostics gap.
- ISSUE-0012 — open — canonical turn pipeline delivery-plan governance stream.
- ISSUE-0013 — open — primary canonical turn-pipeline bug-elimination program.
- ISSUE-0014 — open — CLI self-identity semantic routing regression.

## Findings (Code Review)

1. **Primary-vs-cascade cause isolation is under-specified in ISSUE-0014.**
   The issue lists multiple plausible causes, but does not explicitly declare which earliest state transition is the primary invalid transformation and which failures are downstream cascades.

2. **Stage contract boundaries are implied but not formalized.**
   Rewrite, intent, routing, and commit stages are discussed, but issue text does not state strict per-stage contracts in machine-checkable terms that could be asserted in tests and telemetry.

3. **Quality-system gap is not explicit.**
   ISSUE-0014 requests new coverage but does not document why existing BDD/pytest/gates failed to detect or block this class of regression.

4. **Observability debt is not converted into requirements.**
   Existing evidence is cited, but missing trace fields (pre/post rewrite discourse type, retrieval skip rationale, continuity/self-reference decisions, commit-denial reason) are not mandated.

5. **Governance linkage is insufficiently binding.**
   ISSUE-0014 references ISSUE-0013/0012, yet does not explicitly define how ISSUE-0014 findings alter closure discipline for ISSUE-0013 (behavioral proof vs structural progress).

6. **Regression-history framing is missing.**
   ISSUE-0014 does not require determination of whether this is newly introduced regression, pre-existing defect newly visible via instrumentation, or acceptance-criteria under-specification.

7. **Trust/data-integrity impact framing is incomplete.**
   Current impact language notes behavior failure, but under-specifies product trust implications for memory-backed identity continuity and capability-status truthfulness.

## Evidence

- Reviewed issue quality workflow and required issue sections: [`docs/issues.md`](../issues.md)
- Reviewed red-tag index and escalation policy: [`docs/issues/RED_TAG.md`](RED_TAG.md)
- Reviewed open canonical pipeline and behavior streams:
  - [`docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`](ISSUE-0012-canonical-turn-pipeline-delivery-plan.md)
  - [`docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md)
  - [`docs/issues/ISSUE-0014-cli-self-identity-semantic-routing-regression.md`](ISSUE-0014-cli-self-identity-semantic-routing-regression.md)
- Reviewed additional open issues for active-stream inventory:
  - [`docs/issues/ISSUE-0008-intent-grounding-gate-failures-block-merge.md`](ISSUE-0008-intent-grounding-gate-failures-block-merge.md)
  - [`docs/issues/ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md`](ISSUE-0009-knowing-grounded-answers-partial-provenance-gap.md)
  - [`docs/issues/ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md`](ISSUE-0010-unknowing-safe-fallback-partial-contract-gap.md)
  - [`docs/issues/ISSUE-0011-turn-analytics-input-coverage-silent-drop.md`](ISSUE-0011-turn-analytics-input-coverage-silent-drop.md)

## Impact

- High risk of partial remediation (symptom suppression) without elimination of defect class.
- Potential false-green governance outcomes where structural telemetry improvements are over-interpreted as behavioral closure.
- Continued user-facing trust erosion in identity continuity and memory-backed self-reference behavior.
- Increased recurrence risk if invariant and stage-contract expectations remain non-operationalized.

## Acceptance Criteria

1. ISSUE-0014 is amended with an explicit **defect taxonomy** section that distinguishes primary defect stage from cascade stages.
2. ISSUE-0014 is amended with an **earliest-invalid-state declaration** describing the first forbidden transformation in the turn pipeline.
3. ISSUE-0014 includes explicit **stage contract clauses** for rewrite, intent resolution, routing, and commit promotion (each testable).
4. ISSUE-0014 includes a **quality-system gap** section identifying why existing tests/gates did not catch this regression class.
5. ISSUE-0014 includes mandatory **observability fields** for pre/post rewrite discourse type, self-reference detection, continuity-anchor presence, retrieval-skip reason, and commit-promotion denial reason.
6. ISSUE-0014 includes **governance linkage language** that prevents ISSUE-0013 closure on structural evidence alone when identity-continuity behavior remains unresolved.
7. Deterministic regression coverage is specified for identity declaration -> immediate recall continuity and tied to explicit verification commands.
8. RED_TAG and related issue metadata remain consistent after ISSUE-0014 updates.

## Work Plan

1. Update ISSUE-0014 with the missing quality/governance sections required by this issue.
2. Add or refine linked acceptance criteria in ISSUE-0013 where ISSUE-0014 evidence changes closure assumptions.
3. Add any missing telemetry requirements to the relevant issue records and implementation tasks.
4. Run issue-governance validators and regenerate feature-status artifacts to confirm linkage consistency.
5. Record closure evidence in ISSUE-0015 and mark ISSUE-0015 resolved only after ISSUE-0014 governance text is hardened and traceable; ISSUE-0014 itself remains open until its behavioral acceptance criteria and verification evidence are complete.

## Verification

- Command: `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`
  - Expected: pass; issue linkage remains valid after updates.
- Command: `python scripts/validate_issues.py --all-issue-files --base-ref origin/main`
  - Expected: pass; required sections and metadata remain compliant.
- Command: `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json`
  - Expected: updated report reflects ISSUE-0015 and revised ISSUE-0014 governance state without duplicate-root-cause drift.

## Closure Notes

- Lifecycle sync completed on 2026-03-09. Vocabulary synchronized to blocker/dependent/parallel stream/open/blocked pending evidence and AC-0013-11 closure conditions aligned with ISSUE-0014 Phase 1.

- 2026-03-09: Lifecycle posture remains open/blocked pending evidence by dependency gate; see synchronized red-tag triage note below for current blocker state.
- 2026-03-09: Governance readiness snapshot evidence added for discoverability and dependency-state audit trail: `docs/issues/evidence/2026-03-09-governance-readiness-snapshot.md`.

## Red-tag triage note (dependency gate)

- Last reviewed: 2026-03-14
- Next review due: 2026-03-21
- KPI evidence: artifacts/all-green-gate-summary.json
- Decision notes: ISSUE-0015 remains dependent and open/blocked pending evidence while blockers are active; AC-0013-11 and ISSUE-0014 Phase 1 use the same closure condition (identity semantic preservation, retrieval activation on immediate self-reference recall, confirmed identity fact promotion at commit) with deterministic tests, reproducible CLI traces, and canonical gate evidence.

- 2026-03-08: Opened from open-issue review focused on canonical pipeline streams, with ISSUE-0014 assessed as strong runtime narrative but incomplete quality/governance control artifact.


- 2026-03-08: Follow-up review completed after ISSUE-0014/ISSUE-0013 governance hardening and status artifact refresh.

## 2026-03-08 Follow-up Delta (ISSUE-0014 / ISSUE-0013)

### What changed in ISSUE-0014

- Added explicit quality/governance control sections now required by this issue:
  - `Defect Taxonomy` (primary vs cascade failure classes)
  - `Earliest Invalid State`
  - `Stage Contract Clauses` for rewrite/intent/routing/commit
  - `Quality-System Gap Analysis`
  - `Required Observability Fields`
- Added explicit non-closure governance linkage: ISSUE-0013 identity-continuity milestones remain non-closable while ISSUE-0014 behavioral proof is incomplete.
- Verification commands in ISSUE-0014 now explicitly bind deterministic BDD/pytest/all-green evidence expectations to closure claims.

### What changed in ISSUE-0013

- Cross-reference pointers now explicitly include ISSUE-0014 (active red identity-continuity regression) and ISSUE-0015 (active red quality/governance hardening review).
- Acceptance criteria include explicit linkage gate `AC-0013-11`: identity-continuity closure in ISSUE-0013 is dependent on ISSUE-0014 Phase 1 behavioral evidence and cannot be satisfied by structural instrumentation progress alone.
- Closure notes now preserve reopened state and non-overclaim posture, including regenerated feature-status evidence that keeps canonical pipeline slices at `partial` while unresolved behavioral regressions remain.

## Validator Outcomes (Executed from repo root)

1. `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`
   - Result: **pass**
   - Output notes: base ref `origin/main` unavailable in local clone, validator fell back to `HEAD~1`.
2. `python scripts/validate_issues.py --all-issue-files --base-ref origin/main`
   - Result: **pass**
   - Output notes: PR-body validation skipped because `--pr-body-file` was not provided; base ref fallback to `HEAD~1`.
3. `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json`
   - Result: **pass** (artifacts regenerated)
   - Output notes: report warns gate summary is older than one or more source files and recommends refreshing `artifacts/all-green-gate-summary.json` via all-green gate rerun.

## ISSUE-0015 Acceptance Criteria Status (Explicit)

### Satisfied

- **AC1:** satisfied — ISSUE-0014 now includes explicit defect taxonomy.
- **AC2:** satisfied — ISSUE-0014 now declares the earliest invalid state.
- **AC3:** satisfied — ISSUE-0014 now defines testable rewrite/intent/routing/commit stage contracts.
- **AC4:** satisfied — ISSUE-0014 now includes explicit quality-system gap analysis.
- **AC5:** satisfied — ISSUE-0014 now mandates required observability keys.
- **AC8:** satisfied — issue-link and issue-structure validators pass after updates; metadata/linkage consistency preserved.

### Open blockers (red-tag)

- **AC6:** **open/blocked pending evidence** — governance linkage remains active and synchronized to blocker/dependent sequencing.
- **AC7:** **open/blocked pending evidence** — deterministic regression coverage and CLI traces remain required evidence inputs for the shared closure condition.
- **AC9 (dependency gate):** **open/blocked pending evidence** — dependency evaluation remains tied to AC-0013-11 / ISSUE-0014 Phase 1 shared closure condition and close-order sequencing.

### Exit conditions for ISSUE-0015 closure (dependency on ISSUE-0013 / ISSUE-0014)

ISSUE-0015 remains `Status: open` and `Severity: red` until all dependency conditions are true:

1. **ISSUE-0014 behavioral exit condition met:** deterministic evidence confirms identity declaration semantic preservation, retrieval activation on immediate self-reference recall, and confirmed identity fact promotion at commit.
2. **ISSUE-0013 governance exit condition met:** AC-0013-11 is marked complete with linked evidence proving ISSUE-0014 Phase 1 behavior is passing in deterministic tests plus reproducible CLI traces.
3. **Cross-artifact consistency exit condition met:** `docs/issues/RED_TAG.md` plus issue files (`ISSUE-0013`, `ISSUE-0014`, `ISSUE-0015`) reflect the same lifecycle interpretation (blocker/dependent/parallel stream with open/blocked pending evidence and governance close-order sequencing).
4. **Fallback-semantics consistency condition met:** ISSUE-0010 language for unknowing fallback and ISSUE-0017 pending-lookup normalization remain non-contradictory (pending lookup stays non-clarify and does not downgrade red-tag dependency posture by itself).

## Dependency Evaluation Update (snapshot refresh: 2026-03-10T21:36:04Z) (AC6/AC7/AC9)

- Evidence bundle recorded: `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md`.
- Attached command logs:
- Run-environment note: refreshed gate executed with interpreter `/root/.pyenv/versions/3.11.14/bin/python` (not repository `.venv` activation); this matches prior snapshot interpreter family and is recorded for safe snapshot-to-snapshot comparison.
  - `docs/issues/evidence/2026-03-09-issue-0014-0013-behave.log` (**pass**)
  - `docs/issues/evidence/2026-03-09-issue-0014-0013-focused-pytests.log` (**pass**)
  - `artifacts/all-green-gate-summary.json` (**passed** summary at `2026-03-10T21:36:04Z`; non-zero stage: `qa` with first failing command `qa -> /root/.pyenv/versions/3.11.14/bin/python scripts/validate_kpi_guardrails.py --summary logs/turn_analytics_summary.json --config config/kpi_guardrails.json`; warning check: `qa_validate_kpi_guardrails`)
  - First failing command per non-zero stage: `qa -> /root/.pyenv/versions/3.11.14/bin/python scripts/validate_kpi_guardrails.py --summary logs/turn_analytics_summary.json --config config/kpi_guardrails.json`
  - `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md` (**pass**)
  - `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md` (**pass**)
  - `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md` (**pass**)
- Lifecycle interpretation:
  - AC6: open/blocked pending evidence; governance linkage stays synchronized to blocker/dependent sequencing.
  - AC7: open/blocked pending evidence; deterministic coverage and reproducible CLI traces remain required for closure condition verification.
  - AC9: open/blocked pending evidence; dependency gate remains tied to shared AC-0013-11 / ISSUE-0014 Phase 1 closure criteria.
- Result: ISSUE-0015 stays `Status: open`, `Severity: red`, and `open/blocked pending evidence` for governance close-order sequencing until blockers clear. Under `docs/testing.md#kpi-guardrail-mode-policy-authoritative`, optional-mode KPI warnings are blocker evidence for this red-tag dependency chain until linked mitigation ownership and due dates are maintained.


### Missing evidence checklist (owner + due date)

- [x] **Owner: runtime-pipeline** — Resolved prior failure-attribution mismatch and documented corrective dependency evidence update in ISSUE-0014. **Done: 2026-03-09**. Artifact: `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md`.
- [x] **Owner: platform-qa** — Re-ran `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json` and attached updated summary showing passed status at snapshot `2026-03-10T21:36:04Z` (with QA warning-mode KPI non-zero stage details preserved). **Done: 2026-03-10**. Artifact: `artifacts/all-green-gate-summary.json`.
- [x] **Owner: release-governance** — Updated ISSUE-0013/0014/0015 and RED_TAG lifecycle text to the same refreshed-gate sequencing posture from snapshot `2026-03-10T21:36:04Z` for documentation-governance consolidation scope only (not product readiness). Cross-check: `docs/qa/feature-status-report.md` reports `Implemented: 0 | Partial: 9 | Missing: 0`, so capability readiness remains partial. **Done: 2026-03-10**. Artifact: `artifacts/all-green-gate-summary.json`.


## 2026-03-09 Governance validator rerun

- `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main` -> **pass** (`origin/main` unavailable; fallback `HEAD~1`).
- `python scripts/validate_issues.py --all-issue-files --base-ref origin/main` -> **pass** (`--pr-body-file` not provided; `origin/main` unavailable; fallback `HEAD~1`).


Validator output excerpts:
```text
[WARN] Base ref 'origin/main' is unavailable; falling back to 'HEAD~1'.
       This is expected in Codex task containers or shallow CI clones.
       Governance diff checks are running against a reduced baseline.
       For authoritative results, run locally with 'git fetch origin main' first. (Unless you are ChatGPT/Codex!)
Governance validation passed.
[INFO] No --pr-body-file provided; skipping PR description validation.
[WARN] Base ref 'origin/main' is unavailable; falling back to 'HEAD~1'.
       This is expected in Codex task containers or shallow CI clones.
       Governance diff checks are running against a reduced baseline.
       For authoritative results, run locally with 'git fetch origin main' first. (Unless you are ChatGPT/Codex!)
Issue validation passed.
```

## 2026-03-10 Governance validator evidence refresh

- Evidence note: `docs/issues/evidence/2026-03-10-governance-validator-base-ref-fallback-audit.md`
- Scope: reran canonical governance validators with `origin/main`, recorded automatic fallback warning, then reran both commands with explicit `HEAD~1` per `docs/issues.md` fallback guidance.
- Outcome: all validator runs passed; governance readiness remains auditable with explicit base-ref fallback traceability.
