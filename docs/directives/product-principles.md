# Product principles (testable)

This policy-facing directive defines a compact set of product principles that translate Mission/Vision claims into enforceable checks.

Each principle below must map to at least one deterministic signal so claims can be verified via existing BDD, pytest, or gate artifacts.

## Principle matrix

| Principle | Product intent | Existing enforcement signals |
| --- | --- | --- |
| **P1. Reduce unresolved obligations turn-over-turn** | TestBot should preserve and surface user commitments, pending obligations, and repair state so the next turn starts from durable continuity state instead of guesswork. | Commit/next-turn continuity scenarios in `features/testbot/memory_recall.feature` (same-turn vs later-turn retrieval and committed-context reuse); commit-layer continuity checks in `tests/test_answer_commit_identity_promotion.py`; canonical stage conformance in `scripts/validate_pipeline_stage_conformance.py` (`answer.commit` required). |
| **P2. Improve recall continuity before introducing novelty** | When users ask follow-ups, TestBot should preferentially recover prior anchored facts/identity and maintain conversational continuity rather than reclassifying into unrelated answer paths. | Recall continuity behavior scenarios in `features/testbot/memory_recall.feature` (pronoun/temporal follow-up and segment continuity); context/continuity contract checks in `tests/test_pipeline_semantic_contracts.py`; eval/runtime parity guard in `tests/test_eval_runtime_parity.py`. |
| **P3. Prefer clarifying guidance over opaque refusal** | If evidence is insufficient or ambiguous, TestBot should ask a targeted clarifier or offer capability-based alternatives before defaulting to terse refusal. | Progressive fallback scenarios in `features/testbot/memory_recall.feature`; answer-contract uncertainty/fallback scenarios in `features/testbot/answer_contract.feature`; policy determinism checks in `tests/test_reflection_policy.py`; stakeholder obligations rows (Product/Safety) in `docs/testing.md` under `## All-systems-green definition`. |
| **P4. Avoid dependency-promoting defaults** | Default behavior should remain deterministic, offline-first, and policy-explainable; missing optional runtime dependencies must degrade safely instead of masking failures. | Canonical merge gate orchestration in `scripts/all_green_gate.py`; dependency and deterministic test-layer policy in `docs/testing.md`; startup degradation checks in `tests/test_runtime_modes.py` and `tests/test_startup_status.py`; QA/Ops obligation checks in `docs/testing.md` under `## All-systems-green definition`. |

## Usage in policy and review

- Treat this file as the Mission/Vision enforcement index for product-level claims.
- When proposing stakeholder-visible behavior changes, include a short note indicating which principle(s) are impacted and which mapped signal(s) were run.
- If a new product claim cannot be mapped to an existing signal, add/extend BDD or pytest coverage in the same change set.
