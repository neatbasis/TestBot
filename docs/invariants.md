# Invariant Registry

This index keeps invariant ontologies separated so traceability remains explicit and non-ambiguous:

- **Pipeline semantics/state-transition invariants** (stage ordering, artifact preconditions, anti-projection guard): [`docs/invariants/pipeline.md`](invariants/pipeline.md).
- **Response-policy/UX contract invariants** (citation/marker/fallback answer behavior): [`docs/invariants/answer-policy.md`](invariants/answer-policy.md).

`docs/invariants/answer-policy.md` is the canonical source for the mirrored directive block in `docs/directives/invariants.md`.

Program linkage: [`ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md) is the project's **primary bug-elimination program** in the current state; contributors should triage canonical pipeline defects and follow-on work against ISSUE-0013 first, with ISSUE-0012 treated as linked delivery planning context in [`ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`](issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md).
