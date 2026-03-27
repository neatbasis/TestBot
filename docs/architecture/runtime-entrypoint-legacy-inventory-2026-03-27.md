# Runtime/Entrypoint Legacy Inventory (focused pass, post-#642)

_Date: 2026-03-27_

## Scope and method

Focused inventory only for runtime/entrypoint boot and chat-loop composition seams:

- `src/testbot/entrypoints/sat_cli.py`
- `src/testbot/entrypoints/runtime_legacy_bridge.py`
- `src/testbot/entrypoints/sat_runtime_modes.py`
- compatibility entrypoint in `src/testbot/sat_chatbot_memory_v2.py::main(...)`

This pass intentionally avoids repo-wide refactoring and concentrates on visibility, classification, and safe cleanup.

## Actionable remaining inventory

The table below is the source of truth for *remaining* legacy surfaces in this touched path.

| Surface | Current role | Classification | Current owner | Intended canonical replacement | Removal condition | Blocking dependency | Recommended next PR scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `entrypoints/runtime_legacy_bridge.py` import of `testbot.sat_chatbot_memory_v2` | Single explicit adapter layer that still delegates runtime bootstrap/chat-loop functions to monolith compatibility exports. | `temporary_keep` | Runtime/entrypoint maintainers (`src/testbot/entrypoints/`) | Direct imports from extracted runtime services/modules with no bridge hop. | Delete once `sat_cli` no longer imports `runtime_legacy_bridge` and all bridge exports are unused. | Completion of extraction for legacy-owned bootstrap/chat-loop functions. | Replace one bridge export at a time in `sat_cli` (start with env/bootstrap utilities) with direct extracted-service imports. |
| Runtime bridge warning (`DeprecationWarning` emitted once on bridge use) | Makes transitional monolith dependency visible at runtime for active callers. | `transitional_warn` | Runtime/entrypoint maintainers (`src/testbot/entrypoints/`) | No warning needed because bridge module is removed. | Remove together with `runtime_legacy_bridge.py` deletion. | Bridge removal depends on extraction/migration listed above. | Keep warning narrow (single emission) and update text only when migration target names change. |
| `sat_cli.main(...)` using bridge functions (`parse_args`, `read_runtime_env`, `build_runtime_memory_store`, `run_chat_loop`, etc.) | Entrypoint composition is extracted, but behavior implementation still relies on bridge delegation for legacy-owned runtime behavior. | `extract_later` | Runtime CLI owner (`src/testbot/entrypoints/sat_cli.py`) | `sat_cli` imports extracted runtime ownership modules directly. | No `from testbot.entrypoints.runtime_legacy_bridge import ...` remains in `sat_cli.py`. | Stable ownership/module boundaries for parse/env/memory/chat-loop helpers. | Convert 1–2 bridge imports per PR to direct replacements and keep parity tests green. |
| `sat_chatbot_memory_v2.main(...)` delegating to `entrypoints.sat_cli.main(...)` | Compatibility entrypoint for historical import/execution paths. | `temporary_keep` | Runtime compatibility owner (`src/testbot/sat_chatbot_memory_v2.py`) | Package entrypoint resolves directly to `entrypoints.sat_cli.main` without monolith shim. | Remove shim once external call sites for `sat_chatbot_memory_v2.main` are confirmed migrated and release note window closes. | External callers/deployment references must be inventoried and migrated first. | Add usage telemetry or call-site inventory evidence, then remove shim in a dedicated compatibility-removal PR. |

## Status updates from this pass

- Confirmed the bridge remains the only intentional entrypoint→monolith import seam in runtime composition.
- Removed stale narrative referring to already-completed `CapabilitySnapshotLike` cleanup so this inventory now tracks only active legacy surfaces.

## Transitional visibility

Remaining legacy surfaces are intentionally visible in code:

1. `sat_cli` keeps all bridge imports in one grouped block.
2. `runtime_legacy_bridge` emits a one-time deprecation warning when exercised.
3. This inventory records concrete replacement/removal conditions for each remaining surface.
