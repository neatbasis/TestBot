# Complexipy hotspot investigation (legacy/canonical mixing)

Date: 2026-03-14

## Scope

- Added `complexipy` to `dev` extras so complexity checks are available in standard editable installs.
- Installed project in editable mode with dev dependencies.
- Ran complexity scan to validate the reported failing functions.

Command used:

```bash
source .venv/bin/activate
complexipy scripts src/testbot tests -mx 15 -f -j
```

## Confirmed hotspots

The complexipy output matches the reported failures (36 functions over threshold), including:

- Canonical orchestrator and policy surfaces:
  - `src/testbot/canonical_turn_orchestrator.py::CanonicalTurnOrchestrator.run` (85)
  - `src/testbot/sat_chatbot_memory_v2.py::_run_canonical_turn_pipeline` (70)
  - `src/testbot/sat_chatbot_memory_v2.py::_build_debug_turn_payload` (58)
  - `src/testbot/sat_chatbot_memory_v2.py::answer_assemble` (43)
- Decision/routing utilities:
  - `src/testbot/reject_taxonomy.py::derive_reject_signal` (28)
  - `src/testbot/answer_policy.py::resolve_answer_routing` (18)
  - `src/testbot/policy_decision.py::decide_from_evidence` (16)
- Governance/validation scripts with large rule trees:
  - `scripts/validate_issue_links.py::*` (multiple)
  - `scripts/validate_pipeline_stage_conformance.py::*` (multiple)
  - `scripts/report_feature_status.py::build_report` (49)

## Observed connection to legacy + canonical mixing

### 1) The monolith still contains both canonical interfaces and legacy-compatible logic

`src/testbot/sat_chatbot_memory_v2.py` includes:

- canonical orchestrator imports and stage flow usage,
- deprecated wrappers,
- compatibility bridge functions,
- duplicated policy helper logic that now exists in dedicated modules.

Examples:

- Deprecated bridge wrapper still present (`_answer_routing_from_decision_object`) while delegating to canonical mapping helper.
- A legacy-specific blocker function (`_derive_response_blocker_reason_legacy`) coexists beside canonical reject taxonomy plumbing.
- Policy universe/alternative reasoning helper trees are duplicated in this file even though `answer_policy.py` now provides dedicated pure policy primitives.

This layering strongly correlates with high branch counts in `_build_debug_turn_payload`, `answer_assemble`, `answer_validate`, and canonical pipeline wrapper functions.

### 2) Canonical orchestrator intentionally encodes many guardrails in one method

`CanonicalTurnOrchestrator.run` centralizes strict stage-order checks, artifact preconditions, semantic fingerprints, and post-stage contracts in one loop. This is desirable for auditability, but cyclomatic complexity rises because many stage-specific invariant branches live in one function.

### 3) Transition-period adapters add complexity tax

Mapping between `DecisionClass` and fallback actions/tokens in the monolith acts as a translation layer from canonical decisions back into legacy answer assembly paths. That adaptation code introduces additional conditionals and compatibility defaults.

### 4) Script hotspots are mostly policy/rule validators

The high-complexity script functions are mostly deterministic validators and report builders that aggregate many cases and edge-paths (schema checks, canonical section extraction, consistency rules), rather than runtime drift bugs by themselves.

## Practical interpretation

The complexity signal appears to be caused primarily by **architectural transition overhead**:

1. Canonical pipeline abstractions exist.
2. Legacy monolith behavior remains active for compatibility.
3. Bridge code duplicates rule selection/metadata formatting across old and new paths.

So yes: there is a credible connection between the complexipy failures and mixed legacy/canonical execution responsibilities.

## Refactor opportunities (non-breaking)

1. Extract/debug payload builders
   - Move `_build_debug_turn_payload` and validation schema logic into a dedicated debug module.
2. Remove duplicate policy helpers in monolith
   - Reuse `answer_policy.py` helper outputs directly for alternatives and reasons.
3. Isolate legacy bridge layer
   - Keep adapters in one `legacy_bridge.py` module, so monolith core no longer carries both forms.
4. Stage-guard decomposition
   - Split `CanonicalTurnOrchestrator.run` pre/post conditions into per-stage validator callables while preserving the same stage order and invariant semantics.
5. Script validator table-driven rules
   - Convert repetitive conditional trees to declarative rule tables where feasible.

These can reduce measured complexity without changing behavior contracts.
