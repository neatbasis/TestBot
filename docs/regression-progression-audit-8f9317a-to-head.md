# Regression/Progression Audit: `8f9317a..HEAD`

## Scope

This audit reviews:

- The aggregate diff from `8f9317aa90ee0824836d4e728a6a4ac69a377fbb` to current `HEAD`.
- The commits in that interval, with emphasis on:
  - retiring legacy answer-stage behavior,
  - implementing canonical pipeline changes in runtime and tests,
  - converging on one source of truth for stage flow and response contracts.

## Progression signals

1. **Validation-failure behavior is now explicit and contract-bound rather than implicit.**
   - `answer_rendering.render_answer` now emits typed degraded responses (`degraded_deny_safety_only`, `degraded_targeted_clarifier`, `degraded_capability_alternatives`) when validation fails, instead of a generic placeholder.
   - `answer_commit.commit_answer_stage` now accepts failed validation only when the rendered artifact is explicitly degraded, and rejects inconsistent combinations.
   - This increases observability and removes ambiguity around what is allowed after failed validation.

2. **Canonical answer-stage entrypoint is now the dominant path; legacy flow is deprecated.**
   - `run_canonical_answer_stage_flow(...)` is introduced as the canonical route.
   - `run_answer_stage_flow(...)` remains as a deprecation wrapper with `DeprecationWarning`, reducing immediate breakage while steering callers toward canonical flow.

3. **Boundary hardening for architecture and composition is materially improved.**
   - New architecture boundary tests (`tests/architecture/test_import_boundaries.py`) enforce stage-module isolation from infrastructure adapters and constrain where end-to-end stage composition is allowed.
   - The render-path allowlist prevents ad hoc `render_answer` shortcuts outside sanctioned canonical scopes.

4. **Canonical pipeline semantics are now better synchronized across runtime, tests, and docs.**
   - Pipeline invariants now include explicit failed-validation safety boundary semantics (`PINV-004`).
   - Canonical turn pipeline architecture docs now mirror degraded render/commit constraints.
   - Stage contract tests were expanded to validate failed-validation degraded behavior end-to-end.

## Regression / risk signals

1. **Softened render-stage precondition is implemented, but architectural intent is not yet explicitly ratified.**
   - `canonical_turn_orchestrator` removed the strict requirement that `answer_validation_contract.passed` must be true before `answer.render`.
   - Treat this as a boundary change currently in effect, but **not yet settled architectural doctrine**; prior approval occurred unintentionally and should not be interpreted as final ratification.
   - Follow-up should make an explicit decision between two coherent models:
     - **Ratify softening end-to-end**: keep degraded rendering in the render stage and codify all related invariants/ownership boundaries accordingly, or
     - **Restore strict separation**: require validation pass before render and keep render presentation-only responsibility.
   - Until that decision is recorded, risk remains that mixed assumptions across modules/docs/tests could reintroduce failed-validation leakage or boundary drift.

2. **Legacy API still exists (deprecated, not removed).**
   - `run_answer_stage_flow(...)` remains available and callable.
   - This is intentional for migration safety, but is also a continuing surface area for drift if callers ignore deprecation warnings.

3. **Selected decision override path can bypass normal policy-decide derivation.**
   - `_selected_decision_from_confidence(...)` enables injecting a preselected `DecisionObject` from `confidence_decision` in canonical execution.
   - Useful for deterministic tests and controlled routing, but can become a bypass if used outside constrained contexts.
   - Risk control should remain explicit: production call-sites should gate or trace this override path.

## One-source-of-truth status

Overall status: **improving, but not fully complete**.

- Positive:
  - Stage order is centralized and reused in metrics (`pipeline.metrics` imports canonical stage order from orchestrator).
  - Architectural boundaries now actively test where composition and rendering are allowed.
- Remaining gap:
  - The deprecated legacy wrapper remains present.
  - Some truth duplication still exists in tests/docs by design for policy assertion (acceptable if kept synchronized).

## Suggested next hardening steps

1. Open/attach an explicit architecture decision record (or issue-decision note) that resolves the render-boundary choice: ratify softened degraded-render contract vs restore presentation-only render semantics.
2. Add runtime telemetry when deprecated `run_answer_stage_flow(...)` is called (counter/event) so removal readiness can be measured.
3. Add a guardrail test ensuring no production path sets `selected_decision_object` without explicit test/migration context.
4. Add an issue-linked removal milestone for deleting `run_answer_stage_flow(...)` once call-site usage reaches zero.

## Local validation executed for this audit

- `python -m pytest tests/pipeline/test_stage_contracts.py tests/test_alignment_transitions.py -q`
  - Result: pass (42 tests).
