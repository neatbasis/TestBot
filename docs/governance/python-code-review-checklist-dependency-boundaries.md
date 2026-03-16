# Python Code Review Checklist
## Focus: Dependency Coupling & Boundary Clarity

Use this checklist to run per-module reviews, prioritizing integration seams first.

---

### 1. Module & Package Boundaries

- [ ] Every module has a single, clearly named responsibility (matches its filename/docstring)
- [ ] No module imports from a sibling that "shouldn't know about it" — imports only flow in declared directions
- [ ] `__init__.py` files expose only the intended public API (no accidental re-exports)
- [ ] No circular imports — verified with `pydeps` or `importlib` tracing
- [ ] Internal implementation details are prefixed `_` or live in a `_internal/` subpackage

---

### 2. Dependency Direction

- [ ] A dependency graph exists (or can be generated) — arrows never form a cycle
- [ ] High-level policy modules do **not** import low-level infrastructure directly (Dependency Inversion)
- [ ] Infrastructure adapters (DB, MQTT, HTTP) are behind an abstract interface (`Protocol` or `ABC`)
- [ ] No "god module" imported by nearly everything — if one exists, it's flagged for decomposition
- [ ] Third-party dependencies are wrapped at the boundary (for example, `from myapp.infra.es import ESClient`, not raw vendor imports everywhere)
- [ ] No leaky abstractions — boundary interfaces do not expose vendor-, transport-, or storage-specific details unless explicitly intended
- [ ] Imports are side-effect safe — importing a module does not perform network I/O, registration, or runtime mutation unless it is explicitly designated bootstrap code

---

### 3. Interface & Contract Explicitness

- [ ] Public functions/classes have type annotations on all parameters and return values
- [ ] Pydantic models (v2) or dataclasses define data contracts at every boundary crossing
- [ ] No `dict` or `Any` passing across module lines without a named schema
- [ ] Pre/post-conditions or invariants are either in docstrings, `assert` statements, or `contracts.py`
- [ ] Side effects are isolated and declared (no silent global state mutation in utility functions)
- [ ] Public APIs match established package and boundary conventions; similar seams use similar shapes, names, and failure semantics
- [ ] Boundary adapters and public entrypoints validate required inputs early and fail with specific, intentional errors
- [ ] Boundary failures use specific exception types; broad catches are justified and translated intentionally
- [ ] When re-raising across boundaries, exception chaining (`raise ... from e`) preserves provenance

---

### 4. Coupling Smell Audit

- [ ] No feature envy: functions that manipulate another module's data more than their own
- [ ] No shotgun surgery risk: a single logical change requires edits in 3+ unrelated files → flag for consolidation
- [ ] No inappropriate intimacy: modules accessing `_private` members of other modules
- [ ] `from module import *` is absent everywhere
- [ ] No hardcoded peer-module paths in string literals (for example, dynamic imports by string)

---

### 5. Governance & Legacy Hygiene

- [ ] Each module has an owner or `# TODO(owner):` annotation for orphaned code
- [ ] Dead code is identified (`vulture` or manual search for unreferenced symbols)
- [ ] Deprecated paths are marked with `warnings.warn(..., DeprecationWarning)`, not just a comment
- [ ] All `# FIXME`, `# HACK`, `# XXX` comments are logged as tracked issues, not buried
- [ ] Legacy shim/adapter layers are explicitly labelled and have a removal milestone

---

### 6. Test Coverage at Boundaries

- [ ] Every public interface has at least one unit test that crosses the boundary
- [ ] Mocks/stubs replace infrastructure at boundary seams — tests don't hit real DBs or brokers
- [ ] Contract tests exist for any external service integration (MQTT, ES, HTTP APIs)
- [ ] Behaviour specs (`.feature` files) cover the primary domain flows end-to-end
- [ ] CI enforces a minimum branch coverage threshold at boundary modules specifically
- [ ] Boundary tests are independent, deterministic, and do not rely on execution order or shared mutable state
- [ ] The same seam behavior is not redundantly asserted in multiple unrelated test files without a clear reason

---

### 7. CI / Static Analysis Gates

- [ ] `mypy --strict` (or equivalent config) passes with zero errors on boundary modules
- [ ] `ruff` linting is clean — no suppressed rules without a justification comment
- [ ] `pydeps` or `import-linter` rules are declared and enforced in CI
- [ ] Pre-commit hooks cover formatting, type checking, and import ordering
- [ ] A failing boundary test blocks merge — no bypass without a documented exception

---


### 8. Review Red Flags (Final Scan)

- [ ] Shotgun surgery: one logical change requires edits in many unrelated places
- [ ] Divergent change: one module is changing for multiple unrelated reasons
- [ ] Fragile tests: seam tests fail due to unrelated internal refactors
- [ ] Import side effects: module import triggers unexpected runtime work

---

### Review Severity Key

| Label | Meaning |
|---|---|
| 🔴 **Blocker** | Coupling or contract violation that will cause runtime failures or data corruption |
| 🟠 **Major** | Boundary smell that will compound into architectural debt within one sprint |
| 🟡 **Minor** | Style or naming issue that blurs intent but doesn't break contracts |
| 🟢 **Suggestion** | Refactor opportunity, no urgency |

---

**Tip:** Run this checklist per-module, not per-PR. Prioritize modules at integration seams first (for example: source ingestors, Ask integration, Home Assistant integration, MQTT handlers, ES indexers, API routers). Those boundaries are where coupling damage compounds fastest.
