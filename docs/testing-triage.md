# Testing Failure Triage Map

This document defines the default owner/action mapping for common readiness failures observed in deterministic tests, BDD checks, and canonical gate runs.

Use this map with the canonical issue workflow in [`docs/issues.md`](issues.md) for escalation, ownership assignment, and closure tracking.

## Failure type to owner/action mapping

| Failure type | Typical signal | Primary owner | Immediate action | Escalation + tracking |
| --- | --- | --- | --- | --- |
| Intent classification drift | `intent.resolve` branch differs from expected intent class in BDD/unit matrix tests. | Runtime pipeline owner (intent/stage logic maintainer) | Reproduce with deterministic scenario, confirm expected intent class from directives/invariants, and patch classifier/rules plus tests in the same change set. | Open/update an issue in `docs/issues/` with severity based on user-facing impact; if contract risk exists, mark red-tag per `docs/issues.md` and index in `docs/issues/RED_TAG.md`. |
| Retrieval branch mismatch | `retrieve.evidence` path or evidence-state branch differs from decision matrix expectation. | Retrieval/evidence owner | Re-run failing retrieval matrix test, inspect candidate/evidence fixture alignment, and fix routing or fixture assumptions to restore deterministic branch selection. | Track as issue record with verification commands; escalate to red-tag when mismatch can produce incorrect user-grounding behavior. |
| Policy matrix break | `policy.decide` action class deviates from matrix contract (for example clarify vs answer vs abstain). | Policy/decisioning owner | Execute the failing policy matrix regression test, identify violated rule row, and restore matrix determinism with updated tests and directive sync if policy changed intentionally. | File/update issue and include acceptance criteria tied to policy matrix tests; follow lifecycle and closure evidence in `docs/issues.md`. |
| Provenance/grounding regression | Output lacks required provenance fields, grounding checks fail, or answer assembly violates grounding invariants. | Answer assembly/validation owner | Reproduce via failing answer contract test, verify provenance binding (`doc_id`, timestamps, citation evidence), and correct assembly/validation logic without weakening checks. | Open/update issue with explicit impact on trust/auditability; treat as red-tag when invariant violation risk is present and track mitigation in `Work Plan`. |
| Commit state inconsistency | `answer.commit`/state promotion checks fail (committed state differs from rendered/validated state or identity promotion contract breaks). | Runtime state/commit owner | Reproduce using commit-state invariant test, inspect stage transition artifact consistency, and fix state write/promotion path to preserve canonical commit contract. | Create/update issue with reproduction evidence and invariant reference; escalate when inconsistency impacts traceability or release gating. |

## Standard issue template fields for testing failures

When creating/updating an issue for any triage event, include these fields in addition to the canonical sections required by [`docs/issues.md`](issues.md):

- **Intent class:** Expected vs observed intent class (`knowing` or `unknowing`, plus any internal subclass used by the failing test).
- **Stage:** Canonical stage where the failure first manifests (for example `intent.resolve`, `retrieve.evidence`, `policy.decide`, `answer.validate`, `answer.commit`).
- **Invariant violated:** Link/name of the violated invariant from `docs/invariants.md` or `docs/directives/`.
- **Reproduction test ID:** Stable test/scenario identifier (for example `tests/test_eval_runtime_parity.py::test_<name>` or `features/<file>.feature:<scenario>`).

## Escalation workflow reference

For escalation and tracking:

1. Create or update the issue record under `docs/issues/` using canonical fields and the testing triage fields above.
2. Classify severity (`red`/`amber`/`green`) and status (`open`, `in_progress`, etc.) per `docs/issues.md`.
3. If severity is `red`, ensure `docs/issues/RED_TAG.md` is updated with owner, sprint, and mitigation/rollback notes.
4. Record verification commands and closure evidence before moving issue status to `resolved`/`closed`.

See [`docs/issues.md`](issues.md) for the authoritative lifecycle, red-tag policy, and PR issue-link requirements.
