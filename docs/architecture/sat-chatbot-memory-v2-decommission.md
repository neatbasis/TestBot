# sat_chatbot_memory_v2 decommission schedule (ISSUE-0013)

This schedule tracks compatibility delegators that remain in `src/testbot/sat_chatbot_memory_v2.py` while canonical ownership moves to orchestration entrypoints and services.

## Inventory of call paths entering `sat_chatbot_memory_v2.py`

| Entering call path | Symbol entered | Classification | Canonical owner |
| --- | --- | --- | --- |
| `src/testbot/entrypoints/sat_cli.py` startup/runtime wiring | `_canonical_runtime_entrypoint_dependencies` | helper utility | `testbot.entrypoints.canonical_runtime_entrypoints` dependency assembly at boundary |
| `tests/test_answer_stage_flow_delegation.py` compatibility coverage | `run_answer_stage_flow` | compatibility shim | `testbot.entrypoints.canonical_runtime_entrypoints.run_canonical_answer_stage_flow_entrypoint` |
| `tests/test_answer_stage_flow_delegation.py` compatibility coverage | `evaluate_alignment_decision` | compatibility shim | `testbot.logic.alignment.evaluate_alignment_decision` |
| Legacy/public imports in tests and older callers | `run_canonical_answer_stage_flow` | compatibility shim | `testbot.entrypoints.canonical_runtime_entrypoints.run_canonical_answer_stage_flow_entrypoint` |
| Legacy/public imports in tests and older callers | `run_chat_loop` | compatibility shim | `testbot.entrypoints.canonical_runtime_entrypoints.run_chat_loop_entrypoint` |
| Supported canonical runtime flow | `run_canonical_answer_stage_flow_entrypoint` | canonical runtime behavior | `src/testbot/entrypoints/canonical_runtime_entrypoints.py` |
| Supported canonical runtime flow | `run_chat_loop_entrypoint` | canonical runtime behavior | `src/testbot/entrypoints/canonical_runtime_entrypoints.py` |

## Compatibility delegator milestones

| Delegator symbol | Status | Milestone date | Removal criteria |
| --- | --- | --- | --- |
| `run_answer_stage_flow` | deprecated compatibility alias | **2026-04-01** | Remove once internal callers and non-compatibility tests only use canonical answer-stage entrypoint. |
| `evaluate_alignment_decision` | deprecated compatibility alias | **2026-04-01** | Remove once callers import directly from `testbot.logic.alignment`. |
| `run_canonical_answer_stage_flow` | deprecated compatibility delegator | **2026-06-30** | Remove once supported callers import from `testbot.entrypoints.canonical_runtime_entrypoints` and compatibility parity tests remain green. |
| `run_chat_loop` | deprecated compatibility delegator | **2026-06-30** | Remove once supported callers import from `testbot.entrypoints.canonical_runtime_entrypoints` and unsupported-path sequencing tests remain green. |

## Removal gate

Delegators above are removable only when all are true:

1. Import-boundary checks report no canonical runtime imports from `testbot.sat_chatbot_memory_v2` in `src/` and `features/`.
2. Path-equivalence tests confirm compatibility outputs remain equal to canonical entrypoints for supported scenarios.
3. Unsupported-path tests prove non-canonical seeded overrides are rejected by canonical entrypoints.
