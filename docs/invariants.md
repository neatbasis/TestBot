# Invariant Registry

This index keeps invariant ontologies separated so traceability remains explicit and non-ambiguous:

- **Pipeline semantics/state-transition invariants (`PINV-*`)** cover canonical ordering plus cross-stage semantic boundary guarantees (observe-before-infer, multiplicity preservation, stabilize-before-route, context/intent authority, typed evidence posture, decision/validation/commit continuity, and trace-backed claim legitimacy) in [`docs/invariants/pipeline.md`](invariants/pipeline.md).
- **Response-policy/UX contract invariants (`INV-*`)** cover citation/marker/fallback answer behavior in [`docs/invariants/answer-policy.md`](invariants/answer-policy.md).

ID namespace rule: `PINV-*` is reserved for canonical pipeline semantics, while `INV-*` is reserved for user-visible response-policy behavior.

Canonical ownership split: pipeline semantics are authoritative in `docs/invariants/pipeline.md`, response-policy invariants are authoritative in `docs/invariants/answer-policy.md`, and `docs/directives/invariants.md` is a mirror-only derivative view.

Program anchor: [`issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md).

## Migration boundary (phase 1)

This split is a **registry and mirror-scope refactor**.

- Canonical mirror sync now targets only response-policy invariants in `docs/invariants/answer-policy.md`.
- Canonical pipeline stage semantics now live in `docs/invariants/pipeline.md`.
- Allowed lagging legacy-reference surfaces during migration are limited to:
  - `docs/ops.md` (schema/history narrative for legacy `INV-*` → `PINV-*` migration notes),
  - `docs/governance/drift-traceability-matrix.md` (historical drift snapshots that may retain prior wording),
  - dated audit records under `docs/architecture/*audit*.md` and `docs/regression-progression-audit-*.md`.
- Exit condition for migration tolerance: all active (non-historical) directive/governance traceability docs reference current `PINV-*` ontology without legacy-ID fallback language, and readiness checks no longer report legacy-ID ontology drift for canonical stage-semantics rows.
