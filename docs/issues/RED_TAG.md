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

- ISSUE-0015, ISSUE-0014, and ISSUE-0013 must report a consistent lifecycle state for the identity-continuity dependency chain.
- Closure of ISSUE-0015 is blocked until ISSUE-0013 AC-0013-11 exit conditions and ISSUE-0014 Phase 1 behavioral exit conditions are both satisfied with deterministic evidence + reproducible CLI traces.
- If any dependency is unresolved, keep ISSUE-0015 in the Active red-tag list and avoid resolved-language in related issue files.
- 2026-03-09 lifecycle sync note: latest ISSUE-0014/0013 deterministic evidence bundle shows targeted suites passing and canonical all-green gate passing under warning-mode KPI policy; dependency chain remains unresolved because reproducible CLI identity-continuity closure-proof traces and cross-artifact closure-language synchronization are still pending, so ISSUE-0015/0014 stay active red-tag.

## Active

- ISSUE-0015 — **Open-issue review identifies ISSUE-0014 quality/governance gaps that could permit partial-fix closure**: Open red-tag governance hardening issue. Lifecycle interpretation: remains open/red until dependency exit conditions are met in ISSUE-0013 AC-0013-11 and ISSUE-0014 Phase 1 (identity semantic preservation, retrieval activation on self-reference recall, and confirmed identity fact promotion at commit).
  - Last reviewed: 2026-03-09
  - Next review due: 2026-03-16
  - KPI evidence: docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md
  - Decision notes: Deterministic phase-1 suites and canonical all-green gate are passing under warning-mode KPI policy; keep red-tag open until reproducible CLI identity-continuity closure-proof traces are attached and lifecycle language is synchronized across ISSUE-0013/0014/0015 and RED_TAG.
- ISSUE-0014 — **CLI self-identity turns are stabilized structurally but semantically misrouted before memory retrieval and durable fact promotion**: Open red-tag regression; evidence indicates rewrite-stage semantic inversion and self-reference misrouting prevent retrieval activation and confirmed-user-fact promotion. This is a blocking dependency for ISSUE-0013 AC-0013-11 and ISSUE-0015 closure gates.
  - Last reviewed: 2026-03-09
  - Next review due: 2026-03-16
  - KPI evidence: docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md
  - Decision notes: Behavioral deterministic checks are passing and canonical gate is passing under warning-mode KPI policy, but closure remains blocked pending reproducible CLI identity-continuity closure-proof traces and synchronized dependency language across ISSUE-0013/0014/0015 and RED_TAG.

Dependency evidence pointer (2026-03-09): `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` with linked behave/pytest pass logs and canonical all-green gate pass-with-warning log.

## Resolved

- ISSUE-0007 — **Governance readiness gate traceability is partial for capability-linked issue enforcement**: Closed after deterministic capability-to-issue linkage surfaced in generated feature-status artifacts and validators passed with documented base-ref fallback behavior.
- ISSUE-0001 — **Establish measurable and trackable in-repo issue governance**: Governance is now machine-enforced via canonical validators in the release gate, with auditable failure modes for missing linkage and incomplete issue records.
- ISSUE-0006 — **Operationalize `docs/issues/` and `docs/issues.md` as governed project infrastructure**: Contributor/test guidance and merge validation now enforce the same governance evidence contract, closing the adoption gap.
- ISSUE-0004 — **BDD policy declared but not executable in repository**: Executable baseline BDD coverage now exists, reducing policy-to-practice drift risk to ongoing contract maintenance.

## Archival notes (non-red lifecycle references)

- ISSUE-0008 was previously listed here during its red-severity phase, but its canonical issue file is now `Severity: amber` and `Status: in_progress`; it is intentionally excluded from active/resolved red-tag tracking.
