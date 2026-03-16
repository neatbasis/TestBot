# Mission/Vision alignment map (behavior → executable coverage)

This map translates the mission/vision-aligned product principles into concrete behavior expectations and executable artifacts.

Source of truth for principles: [`docs/directives/product-principles.md`](../directives/product-principles.md).

## Principle coverage matrix

| Principle | Expected stakeholder-visible behavior | BDD scenarios in `features/` | Deterministic tests in `tests/` | Implementation entry points in `src/testbot/` | Coverage status |
| --- | --- | --- | --- | --- | --- |
| **P1. Reduce unresolved obligations turn-over-turn** | Users see durable continuity: memory claims are observed, committed, and reused in later turns (not fabricated in the same turn). | `features/testbot/memory_recall.feature`:<br>- `observe.turn stores user claims only as observation artifacts in-turn`<br>- `committed claims become retrievable memory only in a later turn`<br>- `same-turn retrieval that returns a just-observed claim is rejected` | `tests/test_answer_commit_identity_promotion.py`<br>`tests/test_pipeline_state_artifacts.py`<br>`tests/test_pipeline_semantic_contracts.py` | `src/testbot/pipeline_state.py`<br>`src/testbot/answer_commit.py`<br>`src/testbot/sat_chatbot_memory_v2.py` (`stage_observe_turn`, `stage_commit`) | **Covered** |
| **P2. Improve recall continuity before introducing novelty** | Follow-up prompts prefer anchored continuity (temporal/pronoun bridge, segment continuity, semantic-memory preference) before unrelated novelty paths. | `features/testbot/memory_recall.feature`:<br>- `pronoun temporal follow-up resolves anchor before routing`<br>- `segment-aware continuity groups multi-turn self-profile memory`<br>- `strata-aware retrieval prefers semantic memory over episodic utterance` | `tests/test_eval_runtime_parity.py`<br>`tests/test_memory_segments_and_strata.py`<br>`tests/test_history_packer.py` | `src/testbot/context_resolution.py`<br>`src/testbot/memory_strata.py`<br>`src/testbot/history_packer.py`<br>`src/testbot/sat_chatbot_memory_v2.py` (`stage_retrieve`) | **Covered** |
| **P3. Prefer clarifying guidance over opaque refusal** | When evidence is insufficient/ambiguous, users get explicit uncertainty + clarifier/assistive guidance instead of unexplained refusal. | `features/testbot/answer_contract.feature` uncertainty/fallback scenarios.<br>`features/testbot/memory_recall.feature`:<br>- `progressive assist fallback path`<br>- `equivalent candidates remain ambiguous after tie-break` | `tests/test_reflection_policy.py`<br>`tests/test_answer_contract.py`<br>`tests/test_runtime_logging_events.py` | `src/testbot/reflection_policy.py`<br>`src/testbot/answer_validation.py`<br>`src/testbot/answer_rendering.py`<br>`src/testbot/sat_chatbot_memory_v2.py` (`stage_answer`) | **Covered** |
| **P4. Avoid dependency-promoting defaults** | Users get truthful runtime capability/degraded-mode messaging; system degrades safely and deterministically when optional dependencies are unavailable. | `features/testbot/capabilities.feature` validates user-visible runtime capability statements.<br>**Gap:** no explicit BDD scenario yet for startup degraded-mode messaging contract. | `tests/test_runtime_modes.py`<br>`tests/test_startup_status.py`<br>`tests/test_capabilities_runtime_status.py` | `src/testbot/sat_chatbot_memory_v2.py` (`_resolve_mode`, `_print_startup_status`, `build_capability_snapshot`) | **Partial (BDD startup messaging gap)** |

## Backlog opened for uncovered executable coverage

Because P4 still has a startup degraded-mode messaging BDD gap, backlog issue **ISSUE-0016** is opened:

- `docs/issues/ISSUE-0016-startup-degraded-mode-bdd-coverage-gap.md`
- Scope includes:
  1. Add `features/*.feature` scenarios first for startup degraded-mode messaging behavior.
  2. Add aligned deterministic tests in `tests/`.
  3. Apply minimal implementation updates in `src/testbot/` only as needed.
  4. Update related docs to remove behavior-policy contradictions.

## Maintenance rule

When any mission/vision principle, scenario set, or runtime entry point changes, update this file in the same change set so governance traceability remains auditable.
