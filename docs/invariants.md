# Invariant Registry

This index keeps invariant ontologies separated so traceability remains explicit and non-ambiguous:

- **Pipeline semantics/state-transition invariants (`PINV-*`)** cover stage ordering, artifact preconditions, and anti-projection safeguards in [`docs/invariants/pipeline.md`](invariants/pipeline.md).
- **Response-policy/UX contract invariants (`INV-*`)** cover citation/marker/fallback answer behavior in [`docs/invariants/answer-policy.md`](invariants/answer-policy.md).

ID namespace rule: `PINV-*` is reserved for canonical pipeline semantics, while `INV-*` is reserved for user-visible response-policy behavior.

Canonical ownership split: pipeline semantics are authoritative in `docs/invariants/pipeline.md`, response-policy invariants are authoritative in `docs/invariants/answer-policy.md`, and `docs/directives/invariants.md` is a mirror-only derivative view.

Program linkage: [`ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md) is the project's **primary bug-elimination program** in the current state; contributors should triage canonical pipeline defects and follow-on work against ISSUE-0013 first, with ISSUE-0012 treated as linked delivery planning context in [`ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`](issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md).

## Migration boundary (phase 1)

This split is a **registry and mirror-scope refactor**.

- Canonical mirror sync now targets only response-policy invariants in `docs/invariants/answer-policy.md`.
- Canonical pipeline stage semantics now live in `docs/invariants/pipeline.md`.
- Some downstream directive/report artifacts may still reference legacy IDs during migration; those references are intentionally deferred follow-up work and must not be interpreted as mixed-ontology canonical design.
