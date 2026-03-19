# Architecture Boundary Report (Current Branch)

Generated: 2026-03-19 UTC

## Command and revision
- Command: `python scripts/architecture_boundary_report.py --pretty --output artifacts/architecture-boundary-report.current.json`
- Branch: `work`
- Commit: `7c3aef136ffd01f4c51a505082419a9873480e29`

## Result snapshot
- Exit code: `0`
- Import edges analyzed: `152`
- Violations: `65`
- Temporary exceptions: `1`
- Deprecated compatibility edges: `2`
- Allowed edges: `84`

## What is enforced
The script statically parses Python imports under `src/testbot`, maps modules to configured architecture areas, and classifies each internal import edge as:
- `allowed`
- `temporary_exception`
- `deprecated_compatibility`
- `violation`

Violation reasons:
- `forbidden_dependency_direction`: importer area is not allowed to depend on imported area.
- `private_surface_import`: dependency direction is allowed, but imported module is not in target area's public surface.
- `expired_temporary_exception`: an exception exists but expiration date has passed.

## Most implicated importers
- `testbot.sat_chatbot_memory_v2`: 26 violations
- `testbot.application.services.turn_service`: 17 violations
- `testbot.application.services.canonical_turn_runtime`: 5 violations

## Violation profile
- `private_surface_import`: 38
- `forbidden_dependency_direction`: 27

## Temporary/deprecated status
- Temporary exception (active):
  - `testbot.sat_chatbot_memory_v2 -> testbot.application.services.turn_service`
  - issue: `ISSUE-0013`, expires: `2026-12-31`
- Deprecated compatibility edges:
  - `testbot.answer_render -> testbot.answer_rendering`
  - `testbot.answer_validate -> testbot.answer_validation`

## Drift readout
- Directional architecture exists and is encoded in `docs/qa/architecture-boundaries.json`.
- Drift remains concentrated in monolith/runtime orchestration (`sat_chatbot_memory_v2`) and service-layer deep imports bypassing area public surfaces.
- Current enforcement mode is advisory for this script (non-blocking); violations are reported but do not fail process exit.

## Suggested fix order
1. Reduce `sat_chatbot_memory_v2` direct imports by moving callers to entrypoint/application facades.
2. Expose stable public surfaces for domain/logic modules currently imported by `application.services.turn_service`.
3. Remove direct `vector_store` imports from entrypoints/application/domain modules via ports/adapters.
4. Eliminate domain-to-logic imports in `domain/canonical_dtos.py`.
5. Ratchet report from warning mode toward blocking once policy criteria are satisfied.
