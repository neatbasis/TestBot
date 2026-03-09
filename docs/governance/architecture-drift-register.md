# Architecture Drift Register

This register captures architecture-contract drift found by reviewing module dependencies and control-flow paths in `src/testbot/` against `docs/architecture.md`.

## Review scope

- Contract source: `docs/architecture.md`.
- Runtime scope reviewed: `src/testbot/` (with focus on response-intent behavior, orchestration/core boundaries, and policy/invariant enforcement paths).
- Analysis method: static dependency and control-flow inspection.

## Drift findings

| Violated architecture rule | Actual dependency/path observed | Impact/risk | Required remediation | Related issue ID |
| --- | --- | --- | --- | --- |
| `policy.decide` is the canonical stage that selects semantic response class after evidence retrieval (`observe.turn` → ... → `policy.decide` ...). | In `_run_canonical_turn_pipeline`, `_intent_resolve` computes and stores `policy_decision` (retrieval branch + posture) before `retrieve.evidence`, then `_policy_decide` recomputes/overwrites parts of the decision after rerank. This splits policy authority across `intent.resolve` and `policy.decide` instead of containing it in `policy.decide`. | Response-intent routing can drift because policy semantics are partially pre-committed before evidence is collected/scored. This weakens stage auditability and makes intent/policy regressions harder to triage deterministically. | Move retrieval-branch and policy posture selection entirely into `policy.decide`. Keep `intent.resolve` limited to intent artifacts/rationale only. Ensure `retrieve.evidence` depends on an intent artifact, not a precomputed policy artifact. Add regression coverage proving no policy mutation before `policy.decide`. | ISSUE-0013 |
| Stage boundaries require `answer.assemble`, `answer.validate`, `answer.render`, and `answer.commit` as distinct phases with explicit contracts. | **Resolved (2026-03-09):** canonical `_answer_assemble` now uses assemble-only helper(s); `answer.validate`, `answer.render`, and `answer.commit` execute in their own canonical stages and no longer run implicitly via `stage_answer(...)`. | Stage ownership is now explicit and auditable; prevents hidden double-validation/double-commit semantics in canonical orchestration. | Keep stage-boundary regression tests active to prevent reintroduction of cross-stage side effects from `answer.assemble`. | ISSUE-0013 |
| Citation/provenance guardrails are part of answer validation contract before final output is returned. | **Resolved (2026-03-09):** canonical `answer.validate` now runs the legacy guardrail validator through stage-scoped helper wiring, then applies `validate_answer_assembly_boundary(...)` before render/commit. | Validation ownership is centralized at canonical stage boundary; provenance/fallback guardrails no longer depend on implicit execution from `answer.assemble`. | Maintain stage-contract and guardrail regression coverage (`tests/test_pipeline_semantic_contracts.py`, answer contract suites). | ISSUE-0009 (provenance), ISSUE-0010 (unknowing fallback), ISSUE-0013 |
| Runtime flow contract is canonical 11-stage execution for turn behavior; helper flows should not bypass continuity semantics for intent decisions used in user behavior. | `resolve_turn_intent(...)` runs an out-of-band mini-pipeline (`observe_turn` → `encode_turn_candidates` → `stabilize_pre_route` → `resolve_context` → `resolve_intent`) with `store=None` and no `answer.commit` continuity persistence. | Parallel control-flow path can diverge from canonical turn semantics and produce different intent outcomes from the main orchestrated flow, especially for continuity-anchored memory recall behaviors. | Restrict `resolve_turn_intent` to non-authoritative/offline diagnostics, or route it through canonical orchestration artifacts with explicit labeling. Add tests asserting parity (or explicit non-authority constraints) against canonical intent outcomes. | ISSUE-0013, ISSUE-0014 |

## Notes

- Findings are architecture-drift observations, not direct runtime-failure claims.
- Prioritized items above are ordered by likelihood of affecting response-intent correctness and invariant enforcement traceability.
