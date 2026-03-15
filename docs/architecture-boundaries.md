# Architecture Boundaries

This document defines static architecture boundaries enforced by `tests/architecture/test_import_boundaries.py`.

## Rule set

1. **Stage modules must not import infrastructure adapters directly.**
   - Canonical stage implementation modules in `src/testbot/` (`observe` through `answer.commit`) must stay independent from infrastructure adapter modules/SDK clients.
2. **Domain type modules must not depend on ES/Ollama/Home Assistant clients.**
   - Core domain/type modules must not import `elasticsearch`, `langchain_ollama`, or `homeassistant_api`.
3. **Only orchestration modules can compose the end-to-end canonical stage order.**
   - Full canonical stage sequence declarations are restricted to orchestration modules.
4. **No direct raw-input-to-render shortcuts outside canonical process flow.**
   - `render_answer(...)` call sites are restricted to canonical rendering flow functions.

## Why these checks exist

- Preserve clean separation between domain logic and infrastructure adapters.
- Keep stage implementations testable and deterministic without direct external-client coupling.
- Avoid accidental drift where stage ordering is redefined outside orchestrators.
- Prevent bypasses that skip validation/commit semantics by rendering directly from raw or partially processed state.

## Deprecated by boundary enforcement

The boundary rules deprecate the following implementation patterns for canonical pipeline work:

- Stage-module direct imports of infrastructure adapters/SDK clients (for example connector clients) for runtime execution paths.
- Domain-type module coupling to external client libraries (`elasticsearch`, `langchain_ollama`, `homeassistant_api`).
- New end-to-end canonical stage-order declarations outside orchestration modules.
- New direct `render_answer(...)` shortcut call sites outside the canonical render flow allowlist.

Existing legacy paths that still use these patterns should be treated as migration debt and removed behind issue-tracked follow-up work rather than expanded.

## Enforcement

Run:

```bash
python -m pytest tests/architecture/test_import_boundaries.py
```

The canonical readiness gate (`python scripts/all_green_gate.py`) includes this test as part of the repository-wide checks.
