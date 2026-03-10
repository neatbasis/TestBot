# Red-Tag Issues

This file indexes all `severity: red` issues requiring escalated visibility.

## Representation policy

- `RED_TAG.md` is authoritative only for issues whose canonical file currently declares `Severity: red`.
- If an issue is reopened or rescoped as non-red (for example, `amber`), remove it from `Active`/`Resolved` red-tag lists immediately.
- Non-red follow-up lifecycle history may be captured in an archival note section, but that section must be explicitly labeled as out-of-scope for active red-tag status.

## Canonical pipeline routing note

- Canonical pipeline defects must be tagged and escalated against ISSUE-0013 first; link dependent issue IDs only after ISSUE-0013 routing is recorded.
- ISSUE-0013 may remain `Severity: amber` while still acting as canonical routing anchor; only `Severity: red` issues belong in Active/Resolved lists below.

## Recurring triage note template

Use this note under each red-tag issue entry whenever status changes or during scheduled triage:

```
- Last reviewed: YYYY-MM-DD
- Next review due: YYYY-MM-DD
- KPI evidence: docs/issues/evidence/sprint-<NN>-kpi-review.md
- Decision notes: <decision, rationale, and any escalation/rollback updates>
```

KPI evidence updates are mandatory for red-tag triage. If any KPI guardrail fails, include owner + due date and escalation/rollback intent in both the evidence note and decision notes.


## Active dependency gate (consistency contract)

- Dependency order/state terminology must match ISSUE-0013 current execution order: ISSUE-0008 (**blocker**) -> ISSUE-0011 (**blocker**) -> ISSUE-0012 (**parallel stream**) -> ISSUE-0014 (**blocker**) -> ISSUE-0015 (**dependent**).
- ISSUE-0013 is the routing anchor for this chain; all linked issue files and RED_TAG entries must use the same blocker/dependent/parallel-stream labels.
- Closure of ISSUE-0015 remains open/blocked pending evidence until blocker conditions are met (ISSUE-0013 AC-0013-11 and ISSUE-0014 Phase 1 share one closure condition: deterministic evidence for identity semantic preservation, retrieval activation on immediate self-reference recall, and confirmed identity fact promotion at commit, plus reproducible CLI traces and canonical gate evidence).
- If any blocker is unresolved, keep ISSUE-0015 in the Active red-tag list and avoid resolved-language in related issue files.
- 2026-03-09 lifecycle sync note: refreshed ISSUE-0014/0013 deterministic evidence plus reproducible CLI identity-continuity traces and canonical all-green gate artifacts are attached; lifecycle language across ISSUE-0013/0014/0015/RED_TAG is synchronized to blocker/dependent/parallel stream and open/blocked pending evidence posture.
- ISSUE-0017 (amber) tracks pending-lookup fallback normalization for answer-commit invariants and must stay text-consistent with ISSUE-0010/INV-002 wording; this does not alter the active red-tag blocker/dependent chain unless ISSUE-0013 dependency evidence changes.

## Active

- Lifecycle sync completed on 2026-03-09 (vocabulary normalized to blocker/dependent/parallel stream/open/blocked pending evidence).

- ISSUE-0015 — **Open-issue review identifies ISSUE-0014 quality/governance gaps that could permit partial-fix closure**: Open red-tag governance hardening issue. Lifecycle interpretation: remains open/red until dependency exit conditions are met in ISSUE-0013 AC-0013-11 and ISSUE-0014 Phase 1 (identity semantic preservation, retrieval activation on self-reference recall, and confirmed identity fact promotion at commit).
  - Last reviewed: 2026-03-09
  - Next review due: 2026-03-16
  - KPI evidence: docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md
  - Decision notes: Dependency chain vocabulary synchronized to blocker/dependent/parallel stream; ISSUE-0015 remains open/blocked pending evidence while closure-condition evidence is tracked against AC-0013-11 and ISSUE-0014 Phase 1 using identical criteria.
- ISSUE-0014 — **CLI self-identity turns are stabilized structurally but semantically misrouted before memory retrieval and durable fact promotion**: Open red-tag regression; evidence indicates rewrite-stage semantic inversion and self-reference misrouting prevent retrieval activation and confirmed-user-fact promotion. This is a blocking dependency for ISSUE-0013 AC-0013-11 and ISSUE-0015 closure gates.
  - Last reviewed: 2026-03-09
  - Next review due: 2026-03-16
  - KPI evidence: docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md
  - Decision notes: ISSUE-0014 remains a blocker in the active chain; lifecycle wording is open/blocked pending evidence until AC-0013-11 and ISSUE-0014 Phase 1 meet the identical closure condition and dependent governance sequencing completes.

Dependency evidence pointer (2026-03-09): `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` with linked behave/pytest logs, reproducible CLI traces, and canonical gate artifacts used for open/blocked pending evidence tracking.

## Missing evidence checklist (dependency gate)

- [x] **Owner: runtime-pipeline** — Resolved prior failure attribution mismatch in `docs/issues/evidence/2026-03-09-issue-0014-0013-all-green-gate.log` and documented corrective note. **Done: 2026-03-09**. Artifact: `docs/issues/evidence/2026-03-09-runtime-pipeline-dependency-gate-progress.md`.
- [x] **Owner: platform-qa** — Re-ran canonical gate and published refreshed passing artifacts (`docs/issues/evidence/2026-03-09-issue-0014-0013-all-green-gate.log`, `artifacts/all-green-gate-summary.json`). **Done: 2026-03-09**. Artifact: `docs/issues/evidence/2026-03-09-platform-qa-dependency-gate-progress.md`.
- [x] **Owner: release-governance** — Updated lifecycle language in ISSUE-0013/0014/0015/RED_TAG after refreshed evidence confirmed AC-0013-11 dependency satisfaction. **Done: 2026-03-09**. Artifact: `docs/issues/evidence/2026-03-09-release-governance-dependency-gate-progress.md`.

## Resolved

- ISSUE-0007 — **Governance readiness gate traceability is partial for capability-linked issue enforcement**: Closed after deterministic capability-to-issue linkage surfaced in generated feature-status artifacts and validators passed with documented base-ref fallback behavior.
- ISSUE-0001 — **Establish measurable and trackable in-repo issue governance**: Governance is now machine-enforced via canonical validators in the release gate, with auditable failure modes for missing linkage and incomplete issue records.
- ISSUE-0006 — **Operationalize `docs/issues/` and `docs/issues.md` as governed project infrastructure**: Contributor/test guidance and merge validation now enforce the same governance evidence contract, closing the adoption gap.
- ISSUE-0004 — **BDD policy declared but not executable in repository**: Executable baseline BDD coverage now exists, reducing policy-to-practice drift risk to ongoing contract maintenance.

## Archival notes (non-red lifecycle references)

- ISSUE-0008 was previously listed here during its red-severity phase, but its canonical issue file is now `Severity: amber` and `Status: in_progress`; it is intentionally excluded from active/resolved red-tag tracking.
