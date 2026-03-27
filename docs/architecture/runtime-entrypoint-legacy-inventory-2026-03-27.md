# Runtime/Entrypoint Legacy Inventory (focused pass, post-#643)

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
| `sat_cli.main(...)` bridge import of `build_capability_snapshot` | Legacy bridge hop for capability probing/mode resolution despite extracted canonical service already existing. | `removed_2026-03-27` | Runtime CLI owner (`src/testbot/entrypoints/sat_cli.py`) | `testbot.runtime_capability_service.build_capability_snapshot` direct import. | ✅ Satisfied in this pass (`sat_cli` now imports service directly). | None (service already canonical and covered by extraction tests). | Removed in this PR; keep bridge focused on still-legacy bootstrap/chat-loop utilities. |
| `sat_cli.main(...)` bridge import of `print_startup_status` | Legacy bridge hop for startup status presentation despite extracted presenter already existing. | `removed_2026-03-27` | Runtime CLI owner (`src/testbot/entrypoints/sat_cli.py`) | `testbot.startup_status_presenter.print_startup_status` direct import. | ✅ Satisfied in this pass (`sat_cli` now imports presenter directly). | None (presenter already canonical and shape-compatible). | Removed in this PR; prevents startup-status ownership from drifting back behind bridge wrappers. |
| `entrypoints/runtime_legacy_bridge.py` import of `testbot.sat_chatbot_memory_v2` | Single explicit adapter layer that still delegates runtime bootstrap/chat-loop functions to monolith compatibility exports. | `temporary_keep` | Runtime/entrypoint maintainers (`src/testbot/entrypoints/`) | Direct imports from extracted runtime services/modules with no bridge hop. | Delete once `sat_cli` no longer imports `runtime_legacy_bridge` and all bridge exports are unused. | Completion of extraction for legacy-owned bootstrap/chat-loop functions. | Replace one bridge export at a time in `sat_cli` (start with env/bootstrap utilities) with direct extracted-service imports. |
| Runtime bridge warning (`DeprecationWarning` emitted once on bridge use) | Makes transitional monolith dependency visible at runtime for active callers. | `transitional_warn` | Runtime/entrypoint maintainers (`src/testbot/entrypoints/`) | No warning needed because bridge module is removed. | Remove together with `runtime_legacy_bridge.py` deletion. | Bridge removal depends on extraction/migration listed above. | Keep warning narrow (single emission) and update text only when migration target names change. |
| `sat_cli.main(...)` bridge import of `parse_args` | Legacy bridge hop for CLI argument schema despite extracted canonical owner existing. | `removed_2026-03-27` | Runtime CLI owner (`src/testbot/entrypoints/sat_cli.py`) | `testbot.runtime_cli_args.parse_args` direct import. | ✅ Satisfied in this pass (`sat_cli` now imports runtime CLI arg owner directly). | None (argument schema moved to extracted owner and monolith compat delegates to it). | Removed in this PR; keeps bridge focused on remaining runtime behavior delegation only. |
| `sat_cli.main(...)` using bridge functions (`read_runtime_env`, `build_runtime_memory_store`, `run_chat_loop`, etc.) | Entrypoint composition is extracted, but behavior implementation still relies on bridge delegation for legacy-owned runtime behavior. | `extract_later` | Runtime CLI owner (`src/testbot/entrypoints/sat_cli.py`) | `sat_cli` imports extracted runtime ownership modules directly. | No `from testbot.entrypoints.runtime_legacy_bridge import ...` remains in `sat_cli.py`. | Stable ownership/module boundaries for env/memory/chat-loop helpers. | Convert 1–2 bridge imports per PR to direct replacements and keep parity tests green. |
| `sat_chatbot_memory_v2.main(...)` delegating to `entrypoints.sat_cli.main(...)` | Compatibility entrypoint for historical import/execution paths. | `temporary_keep` | Runtime compatibility owner (`src/testbot/sat_chatbot_memory_v2.py`) | Package entrypoint resolves directly to `entrypoints.sat_cli.main` without monolith shim. | Remove shim once external call sites for `sat_chatbot_memory_v2.main` are confirmed migrated and release note window closes. | External callers/deployment references must be inventoried and migrated first. | Add usage telemetry or call-site inventory evidence, then remove shim in a dedicated compatibility-removal PR. |

## Status updates from this pass

- Confirmed the bridge remains the only intentional entrypoint→monolith import seam in runtime composition.
- Removed stale narrative referring to already-completed `CapabilitySnapshotLike` cleanup so this inventory now tracks only active legacy surfaces.
- Removed three low-blast-radius bridge shims (`build_capability_snapshot`, `print_startup_status`, `parse_args`) now that `sat_cli` imports canonical modules directly.
- Removed corresponding wrapper exports from `runtime_legacy_bridge.py` so bridge ownership is narrower and explicit.
- Added a regression guard in `tests/test_runtime_modes.py` asserting these symbols stay out of bridge imports.
- Runtime config now resolves Home Assistant instance URL from `HA_BASE_URL` only in this CLI/runtime path; legacy `HA_API_URL` env alias support was removed to avoid ambiguous naming.

## Transitional visibility

Remaining legacy surfaces are intentionally visible in code:

1. `sat_cli` keeps all bridge imports in one grouped block.
2. `runtime_legacy_bridge` emits a one-time deprecation warning when exercised.
3. This inventory records concrete replacement/removal conditions for each remaining surface.

## Candidate selection notes (focused follow-up after #643)

Chosen in this PR (implemented):

1. Remove `sat_cli`→bridge dependency for capability snapshot construction.
2. Remove `sat_cli`→bridge dependency for startup status presentation.
3. Remove `sat_cli`→bridge dependency for CLI argument parsing.

Why these over other remaining items:

- They were the cheapest complete removals with zero behavior redesign: all had extracted canonical replacements with matching call signatures.
- They reduce silent coupling because startup capability/probing, status presentation, and argument parsing now resolve to canonical owners directly (no bridge indirection).
- They preserve the #640–#643 boundary shape by keeping interaction planning and mode runners unchanged while shrinking only bridge-era compatibility surface.

Next cheapest candidates after this PR:

1. `read_runtime_env` extraction into a dedicated runtime bootstrap module, then direct `sat_cli` imports.
2. `sat_say` extraction into a narrow satellite output adapter so `sat_runtime_modes` no longer requires bridge-provided speak helper.
