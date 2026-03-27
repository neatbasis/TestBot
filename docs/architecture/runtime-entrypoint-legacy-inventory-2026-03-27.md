# Runtime/Entrypoint Legacy Inventory (focused pass, post-#647)

_Date: 2026-03-27_

## Scope and method

Focused inventory only for still-importable/callable compatibility surfaces adjacent to `testbot.sat_chatbot_memory_v2` in runtime entrypoint paths:

- `src/testbot/sat_chatbot_memory_v2.py`
- `src/testbot/entrypoints/runtime_legacy_bridge.py`
- `src/testbot/entrypoints/sat_cli.py`
- runtime operator docs that still invoke legacy compatibility entrypoints

This pass intentionally avoids repo-wide refactoring and concentrates on narrow removal-oriented cleanup.

## Remaining compatibility surface inventory

| Surface | Current role | Classification | Current owner | Canonical replacement | Removal condition | Blocker | Recommended next PR scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `docs/quickstart.md` and `docs/ops.md` commands invoking `python src/testbot/sat_chatbot_memory_v2.py` | Operator-visible launch path still routes through deprecated monolith compatibility entrypoint. | `remove_now` | Runtime docs owner (`docs/quickstart.md`, `docs/ops.md`) | `python -m testbot.entrypoints.sat_cli` (or `testbot`) | ✅ Completed in this pass by updating those commands to canonical entrypoint module execution. | None. | Keep a regression check that docs do not reintroduce `python src/testbot/sat_chatbot_memory_v2.py`. |
| `testbot.sat_chatbot_memory_v2.main(...)` delegator | Deprecated callable compatibility entrypoint for historical imports/execution. | `transitional_warn` | Runtime compatibility owner (`src/testbot/sat_chatbot_memory_v2.py`) | `testbot.entrypoints.sat_cli.main(...)` | Remove after external call-site inventory demonstrates no active dependency and deprecation window closes. | External/non-repo callers are not fully inventoried yet. | Add lightweight usage telemetry or call-site evidence artifact to support deletion PR. |
| `testbot.entrypoints.runtime_legacy_bridge` delegation layer (`read_runtime_env`, `build_runtime_memory_store`, `run_source_ingestion`, `run_chat_loop`, `sat_say`) | Explicit entrypoint-to-monolith compatibility adapter for runtime bootstrap/chat-loop behavior not yet extracted. | `extract_later` | Runtime/entrypoint maintainers (`src/testbot/entrypoints/`) | Direct imports from extracted runtime ownership modules/services | Remove module after `sat_cli` no longer imports bridge symbols. | Bootstrap/chat-loop helpers still owned by monolith compatibility exports. | Extract one bridge-backed helper at a time (start with runtime env/bootstrap). |
| Bridge one-time warning in `runtime_legacy_bridge._warn_legacy_runtime_bridge` | Keeps temporary bridge dependency visible while migration is active. | `temporary_keep` | Runtime/entrypoint maintainers (`src/testbot/entrypoints/`) | No warning needed once bridge is deleted | Delete together with bridge removal. | Bridge still required for remaining unextracted runtime helpers. | Keep warning text synchronized with next extracted helper so migration target stays concrete. |
| Deprecated alias `run_answer_stage_flow(...)` in `sat_chatbot_memory_v2` | Callable alias retained for compatibility; delegates to canonical flow. | `transitional_warn` | Runtime compatibility owner (`src/testbot/sat_chatbot_memory_v2.py`) | `run_canonical_answer_stage_flow(...)` | Remove when compatibility-only imports/tests are the sole remaining usages and migration evidence is captured. | External consumers may still import alias; removal date remains staged. | Add usage evidence (import census) and then delete alias + compatibility tests in one PR. |
| Compatibility shim `evaluate_alignment_decision(...)` in `sat_chatbot_memory_v2` | Callable shim retained for legacy import path; delegates to logic owner. | `temporary_keep` | Runtime alignment owner (`src/testbot/logic/alignment.py`) + compatibility owner (`sat_chatbot_memory_v2`) | `testbot.logic.alignment.evaluate_alignment_decision` | Remove after all call sites import logic owner directly and compatibility-only coverage is sufficient. | Some tests and downstream imports still use shim path. | Migrate in-repo imports first, then tighten boundary checks before shim removal. |
| Re-export `CanonicalTurnOrchestrator` from `sat_chatbot_memory_v2` | Importable compatibility symbol aliasing canonical orchestrator owner. | `temporary_keep` | Runtime pipeline owner (`src/testbot/canonical_turn_orchestrator.py`) + compatibility owner (`sat_chatbot_memory_v2`) | `testbot.canonical_turn_orchestrator.CanonicalTurnOrchestrator` | Remove after non-compatibility imports and tests stop using monolith path. | Existing compatibility tests and runtime-module-style tests still reference alias. | Migrate runtime-module tests to canonical import and confine compatibility checks to dedicated shim tests. |

## Highest-value next action selected for this pass

**Chosen action:** remove operator-facing legacy runtime launch commands that still invoked `sat_chatbot_memory_v2.py`.

Why this action:

- **Low blast radius:** docs-only command updates.
- **Clear replacement:** canonical entrypoint already exists (`testbot.entrypoints.sat_cli`).
- **Strong simplification:** converts warning-only guidance into concrete caller migration in repository-facing operational docs.

## Status updates from this pass

- Updated quickstart and ops command examples to call the canonical runtime entrypoint module (`python -m testbot.entrypoints.sat_cli`) instead of the deprecated monolith file path.
- Added a minimal regression guard test that fails if those docs reintroduce `python src/testbot/sat_chatbot_memory_v2.py`.
- Added canonical user-facing source-ingestion entry selection (`menu`/`reference`/`freeform`/direct connector) without changing bridge-owned ingestion plumbing.
- Kept the broader runtime bridge and callable compatibility shims unchanged in this pass to maintain narrow scope.
