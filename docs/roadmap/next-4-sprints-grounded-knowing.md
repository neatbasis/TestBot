# Next 4 Sprints Roadmap: Grounded Knowing

## Scope and intent

This roadmap operationalizes the top-5 grounded-knowing priorities over four sprints. Each sprint includes explicit goals, measurable exits, and rollback criteria so delivery remains deterministic, testable, and reversible.

## Priority stack (ordered)

1. **P1: Source connector interface + ingestion pipeline**
2. **P2: Evidence normalization/ranking for mixed sources**
3. **P3: Knowing/unknowing decision policy with confidence calibration**
4. **P4: Citation UX + provenance explainability output format**
5. **P5: Feedback loop using follow-up signals and offline eval replay**

---

## Sprint 1 — Foundation: connectors + ingestion contract (P1)

### Goals
- Define a stable source connector interface for heterogeneous memory/evidence sources.
- Implement deterministic ingestion pipeline stages (fetch → normalize envelope → persist candidate records).
- Add ingestion observability signals needed by downstream ranking and policy layers.

### Measurable exits
- At least one connector implementation can ingest a fixture-backed source end-to-end with deterministic outputs.
- Ingestion emits structured records containing required fields (`source_id`, `doc_id`, `ts`, `content`, `metadata`).
- BDD and deterministic tests verify successful ingestion and failure-mode handling (bad payload, missing timestamps).

### Rollback criteria
- If connector abstraction causes regression in existing retrieval flow, feature-flag new ingestion path off and revert to current pipeline defaults.
- If ingestion schema instability breaks ranking tests, freeze schema to previous known-good envelope and defer non-essential fields.

---

## Sprint 2 — Mixed-source evidence ranking (P2)

### Goals
- Normalize evidence from connector outputs into a single ranking-ready representation.
- Extend rerank objective to support mixed sources while preserving deterministic ordering guarantees.
- Add traceable per-component score attribution (semantic, temporal, source/type priors).

### Measurable exits
- Ranking pipeline accepts mixed-source candidate sets without schema conversion errors.
- Deterministic tests show stable ordering/top-1 selection across fixed fixtures for mixed-source cases.
- Eval/runtime parity checks pass for added mixed-source scenarios.

### Rollback criteria
- If mixed-source ranking reduces baseline recall/precision beyond accepted threshold, disable mixed-source weighting and use existing single-source scoring path.
- If attribution output is inconsistent run-to-run, remove non-deterministic components before merge.

---

## Sprint 3 — Knowing policy + citation/provenance contract (P3, P4)

### Goals
- Implement explicit knowing/unknowing decision policy with calibrated confidence thresholds.
- Guarantee fallback behavior remains exact when evidence is insufficient.
- Add citation/provenance explainability output contract for user-visible responses.

### Measurable exits
- Policy returns deterministic know/unknown decisions for fixture-defined confidence bands.
- BDD scenarios pass for both grounded answers and exact fallback (`I don't know from memory.`).
- Response contract includes citation/provenance fields aligned to runtime state (`doc_id`, `ts`, `provenance_types`, `used_memory_refs`, `used_source_evidence_refs`, `source_evidence_attribution`, `basis_statement`).

### Rollback criteria
- If calibration induces overconfident false-positive “knowing” behavior, raise threshold to conservative default and re-enable strict fallback.
- If citation/provenance output breaks answer contract compatibility, revert to prior response schema while preserving internal traces.

---

## Sprint 4 — Feedback loop + offline replay hardening (P5 + stabilization)

### Goals
- Introduce feedback-loop ingestion for follow-up signals (clarifications, corrections, confirmations).
- Build offline eval replay workflow to compare policy/ranking deltas across versions.
- Finalize release gating integration for new grounded-knowing checks.

### Measurable exits
- Follow-up signals are captured in deterministic fixtures and influence replay metrics.
- Offline replay reports comparable before/after metrics for knowing decisions and citation correctness.
- Canonical gate includes replay-sensitive deterministic checks for regression detection.

### Rollback criteria
- If feedback signals introduce unstable behavior or drift in deterministic tests, isolate feedback weighting behind a disabled-by-default flag.
- If replay metrics conflict with runtime parity expectations, freeze promotion and revert to previous policy/ranking package.

---

## Priority-to-implementation mapping

_Last verified: 2026-03-06_

| Priority | Implementation files (likely `src/testbot/*`) | BDD scenarios (`features/*`) | Deterministic tests (`tests/*`) |
| --- | --- | --- | --- |
| **P1** Source connector interface + ingestion pipeline | `src/testbot/source_connectors.py`, `src/testbot/source_ingest.py`, `src/testbot/pipeline_state.py`, `src/testbot/config.py` | `features/source_ingestion.feature`, `features/capabilities.feature` | `tests/test_source_connectors.py`, `tests/test_source_ingest.py`, `tests/test_source_fusion.py` |
| **P2** Evidence normalization/ranking for mixed sources | `src/testbot/rerank.py`, `src/testbot/vector_store.py`, `src/testbot/eval_fixtures.py` | `features/memory_recall.feature`, `features/intent_grounding.feature` | `tests/test_rerank.py`, `tests/test_vector_store.py`, `tests/test_eval_runtime_parity.py` |
| **P3** Knowing/unknowing decision policy with confidence calibration | `src/testbot/intent_router.py`, `src/testbot/promotion_policy.py`, `src/testbot/reflection_policy.py` | `features/answer_contract.feature`, `features/intent_grounding.feature` | `tests/test_intent_router.py`, `tests/test_promotion_policy.py`, `tests/test_reflection_policy.py` |
| **P4** Citation UX + provenance explainability output format | `src/testbot/sat_chatbot_memory_v2.py`, `src/testbot/history_packer.py`, `src/testbot/memory_cards.py` | `features/answer_contract.feature`, `features/memory_recall.feature` | `tests/test_history_packer.py`, `tests/test_runtime_logging_events.py`, `tests/test_capabilities_help.py` |
| **P5** Feedback loop using follow-up signals and offline eval replay | `src/testbot/stage_transitions.py`, `src/testbot/time_reasoning.py`, `src/testbot/eval_fixtures.py` | `features/time_awareness.feature`, `features/memory_recall.feature` | `tests/test_time_reasoning.py`, `tests/test_eval_recall.py`, `tests/test_eval_runtime_parity.py` |

---

## Definition of Done (tied to `docs/testing.md` commands)

| DoD checkpoint | Required command | Evidence expectation |
| --- | --- | --- |
| BDD acceptance scenarios pass for changed behavior | `python -m behave` | No failed/undefined steps for affected features. |
| Deterministic unit/component checks pass | `python -m pytest -m "not live_smoke"` | Exit code `0`; no network-bound flakes. |
| Eval/runtime parity remains aligned after roadmap changes | `python -m pytest tests/test_eval_runtime_parity.py` | Ordering/top-1/fallback parity preserved. |
| Canonical contributor gate is green | `python scripts/release_gate.py` | Full deterministic merge gate passes in required order. |
