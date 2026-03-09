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
- Closure of ISSUE-0015 remains blocked until blocker conditions are evidence-satisfied (including ISSUE-0013 AC-0013-11 and ISSUE-0014 Phase 1 behavioral criteria with deterministic evidence + reproducible CLI traces).
- If any blocker is unresolved, keep ISSUE-0015 in the Active red-tag list and avoid resolved-language in related issue files.
- 2026-03-09 lifecycle sync note: latest ISSUE-0014/0013 deterministic evidence bundle plus reproducible CLI identity-continuity closure-proof traces are attached, but dependency evidence remains incomplete because the canonical all-green gate artifact is failing (`product_behave`); lifecycle language across ISSUE-0013/0014/0015/RED_TAG must remain in blocked/open posture until refreshed passing gate evidence is attached.

## Active

- ISSUE-0015 — **Open-issue review identifies ISSUE-0014 quality/governance gaps that could permit partial-fix closure**: Open red-tag governance hardening issue. Lifecycle interpretation: remains open/red until dependency exit conditions are met in ISSUE-0013 AC-0013-11 and ISSUE-0014 Phase 1 (identity semantic preservation, retrieval activation on self-reference recall, and confirmed identity fact promotion at commit).
  - Last reviewed: 2026-03-09
  - Next review due: 2026-03-16
  - KPI evidence: docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md
  - Decision notes: Deterministic phase-1 suites and required reproducible CLI traces are attached, but dependency remains blocked because the referenced canonical all-green gate artifact is failing (`product_behave`). Missing-evidence owners/due dates are tracked below.
- ISSUE-0014 — **CLI self-identity turns are stabilized structurally but semantically misrouted before memory retrieval and durable fact promotion**: Open red-tag regression; evidence indicates rewrite-stage semantic inversion and self-reference misrouting prevent retrieval activation and confirmed-user-fact promotion. This is a blocking dependency for ISSUE-0013 AC-0013-11 and ISSUE-0015 closure gates.
  - Last reviewed: 2026-03-09
  - Next review due: 2026-03-16
  - KPI evidence: docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md
  - Decision notes: Behavioral deterministic checks and required reproducible CLI identity-continuity closure-proof traces are attached, but canonical all-green gate evidence remains failing in the current bundle; issue remains active red-tag pending refreshed passing gate evidence.

Dependency evidence pointer (2026-03-09): `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` with linked behave/pytest pass logs and canonical all-green gate **fail** log (`product_behave`).

## Missing evidence checklist (dependency gate)

- [ ] **Owner: runtime-pipeline** — Resolve `product_behave` failures cited in `docs/issues/evidence/2026-03-09-issue-0014-0013-all-green-gate.log`. **Due: 2026-03-16**.
- [ ] **Owner: platform-qa** — Re-run canonical gate and publish refreshed passing artifacts (`...all-green-gate.log`, `artifacts/all-green-gate-summary.json`). **Due: 2026-03-16**.
- [ ] **Owner: release-governance** — Update lifecycle language in ISSUE-0013/0014/0015/RED_TAG once refreshed evidence confirms AC-0013-11 dependency satisfaction. **Due: 2026-03-17**.

## Resolved

- ISSUE-0007 — **Governance readiness gate traceability is partial for capability-linked issue enforcement**: Closed after deterministic capability-to-issue linkage surfaced in generated feature-status artifacts and validators passed with documented base-ref fallback behavior.
- ISSUE-0001 — **Establish measurable and trackable in-repo issue governance**: Governance is now machine-enforced via canonical validators in the release gate, with auditable failure modes for missing linkage and incomplete issue records.
- ISSUE-0006 — **Operationalize `docs/issues/` and `docs/issues.md` as governed project infrastructure**: Contributor/test guidance and merge validation now enforce the same governance evidence contract, closing the adoption gap.
- ISSUE-0004 — **BDD policy declared but not executable in repository**: Executable baseline BDD coverage now exists, reducing policy-to-practice drift risk to ongoing contract maintenance.

## Archival notes (non-red lifecycle references)

- ISSUE-0008 was previously listed here during its red-severity phase, but its canonical issue file is now `Severity: amber` and `Status: in_progress`; it is intentionally excluded from active/resolved red-tag tracking.
