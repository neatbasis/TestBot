# Red-Tag Issues

This file indexes all `severity: red` issues requiring escalated visibility.

## Representation policy

- `RED_TAG.md` is authoritative only for issues whose canonical file currently declares `Severity: red`.
- If an issue is reopened or rescoped as non-red (for example, `amber`), remove it from `Active`/`Resolved` red-tag lists immediately.
- Non-red follow-up lifecycle history may be captured in an archival note section, but that section must be explicitly labeled as out-of-scope for active red-tag status.

## Canonical pipeline routing note

- Canonical pipeline defects must be tagged and escalated against ISSUE-0013 first; link dependent issue IDs only after ISSUE-0013 routing is recorded.

## Recurring triage note template

Use this note under each red-tag issue entry whenever status changes or during scheduled triage:

```
- Last reviewed: YYYY-MM-DD
- Next review due: YYYY-MM-DD
- KPI evidence: docs/issues/evidence/sprint-<NN>-kpi-review.md
- Decision notes: <decision, rationale, and any escalation/rollback updates>
```

KPI evidence updates are mandatory for red-tag triage. If any KPI guardrail fails, include owner + due date and escalation/rollback intent in both the evidence note and decision notes.

## Active

- ISSUE-0014 — **CLI self-identity turns are stabilized structurally but semantically misrouted before memory retrieval and durable fact promotion**: Open red-tag regression; evidence indicates rewrite-stage semantic inversion and self-reference misrouting prevent retrieval activation and confirmed-user-fact promotion.

## Resolved

- ISSUE-0007 — **Governance readiness gate traceability is partial for capability-linked issue enforcement**: Closed after deterministic capability-to-issue linkage surfaced in generated feature-status artifacts and validators passed with documented base-ref fallback behavior.
- ISSUE-0001 — **Establish measurable and trackable in-repo issue governance**: Governance is now machine-enforced via canonical validators in the release gate, with auditable failure modes for missing linkage and incomplete issue records.
- ISSUE-0006 — **Operationalize `docs/issues/` and `docs/issues.md` as governed project infrastructure**: Contributor/test guidance and merge validation now enforce the same governance evidence contract, closing the adoption gap.
- ISSUE-0004 — **BDD policy declared but not executable in repository**: Executable baseline BDD coverage now exists, reducing policy-to-practice drift risk to ongoing contract maintenance.

## Archival notes (non-red lifecycle references)

- ISSUE-0008 was previously listed here during its red-severity phase, but its canonical issue file is now `Severity: amber` and `Status: in_progress`; it is intentionally excluded from active/resolved red-tag tracking.
