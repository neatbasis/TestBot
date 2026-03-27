# Runtime/Entrypoint Legacy Inventory (focused pass, post-#640)

_Date: 2026-03-27_

## Scope and method

Focused inventory only for runtime/entrypoint boot and chat-loop composition seams:

- `src/testbot/entrypoints/sat_cli.py`
- `src/testbot/entrypoints/runtime_legacy_bridge.py`
- `src/testbot/entrypoints/sat_runtime_modes.py`
- compatibility entrypoint in `src/testbot/sat_chatbot_memory_v2.py::main(...)`

This pass intentionally avoids repo-wide refactoring and concentrates on visibility, classification, and safe cleanup.

## Classified inventory

| Surface | Current role | Classification | Migration intent / replacement path |
| --- | --- | --- | --- |
| `entrypoints/runtime_legacy_bridge.py` import of `testbot.sat_chatbot_memory_v2` | Explicit adapter layer that still delegates runtime bootstrap/chat-loop functions to monolith compatibility exports. | `temporary_keep` | Keep as the only entrypoint→monolith dependency point until bootstrap/chat-loop behavior is extracted into stable runtime modules, then delete the bridge module. |
| Runtime bridge warning (`DeprecationWarning` on first bridge call) | Makes transitional monolith dependency visible at runtime. | `transitional_warn` | Retain warning until bridge removal so callers see intentional temporary status and migrate toward extracted ownership. |
| `sat_cli.main(...)` using bridge functions (`parse_args`, `read_runtime_env`, `build_runtime_memory_store`, `run_chat_loop`, etc.) | Entrypoint composition is extracted, but implementation still relies on bridge delegation for legacy-owned behavior. | `extract_later` | Replace each bridge call with direct imports from extracted modules/services as ownership migrates; then remove bridge imports from `sat_cli`. |
| `sat_chatbot_memory_v2.main(...)` delegating to `entrypoints.sat_cli.main(...)` | Compatibility entrypoint for historical import/execution paths. | `temporary_keep` | Keep as backward-compatible shim until external callers are confirmed migrated; remove once compatibility window closes. |
| `CapabilitySnapshotLike` protocol exported from `runtime_legacy_bridge` | Shadow typing seam used only by `sat_runtime_modes` annotations, not needed for runtime behavior. | `remove_now` | **Removed in this pass**. `sat_runtime_modes` no longer imports bridge symbols for typing and uses `object` annotation to avoid unnecessary bridge coupling. |

## Cheap/safe cleanup completed now

1. Removed the dead/shadow `CapabilitySnapshotLike` export from `entrypoints/runtime_legacy_bridge.py`.
2. Removed corresponding `sat_runtime_modes` import dependency on the bridge module.
3. Added a small guard test to prevent reintroducing bridge symbol imports in `sat_runtime_modes`.

## Transitional visibility status after this pass

- Transitional runtime seam remains explicit and centralized in `entrypoints/runtime_legacy_bridge.py`.
- Runtime bridge usage still emits a targeted `DeprecationWarning` once per process.
- Replacement path is now clearer:
  1. move ownership out of monolith exports,
  2. switch `sat_cli` imports directly to extracted modules,
  3. retire `runtime_legacy_bridge`,
  4. finally drop monolith `main` compatibility shim.
