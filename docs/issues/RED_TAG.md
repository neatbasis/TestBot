# Red-Tag Issues

This file indexes all `severity: red` issues requiring escalated visibility.

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

- ISSUE-0007 — **Governance readiness gate traceability is partial for capability-linked issue enforcement**.
  - Last reviewed: 2026-03-06
  - Next review due: 2026-03-13
  - KPI evidence: docs/issues/evidence/sprint-00-kpi-review.md
  - Decision notes: Reopened as an active governance traceability risk until partial capabilities consistently resolve to open issue records in generated feature-status artifacts.

## Resolved

- ISSUE-0008 — **Intent-grounding gate failures block merge readiness**: Canonical merge gate failures were remediated with deterministic intent-routing/reflection/provenance fixes and regression coverage.
- ISSUE-0001 — **Establish measurable and trackable in-repo issue governance**: Governance is now machine-enforced via canonical validators in the release gate, with auditable failure modes for missing linkage and incomplete issue records.
- ISSUE-0006 — **Operationalize `docs/issues/` and `docs/issues.md` as governed project infrastructure**: Contributor/test guidance and merge validation now enforce the same governance evidence contract, closing the adoption gap.
- ISSUE-0004 — **BDD policy declared but not executable in repository**: Executable baseline BDD coverage now exists, reducing policy-to-practice drift risk to ongoing contract maintenance.
