# Changelog

## Entry template (use for every PR/refactor step)
For each changelog entry, answer these three questions explicitly:

1. **What moved, and where did it land?**
   - Include the old path/symbol, new path/symbol, and whether a delegation shim remains.
2. **What did not change?**
   - State verified non-changes (behavior, public API, wire protocol, session log schema, etc.).
3. **Why this step was taken in this order?**
   - One sentence describing sequencing rationale (dependency order, receiver-first, ambiguity reduction before next extraction, etc.).

## 2026-03-19

### 1) What moved, and where did it land?
- **Old path/symbol:** local helper `_is_definitional_query_form(...)` defined and called in `src/testbot/sat_chatbot_memory_v2.py`.
- **New path/symbol:** shared helper `is_definitional_query_form(...)` from `testbot.retrieval_routing` (imported and used by `sat_chatbot_memory_v2.py`).
- **Delegation shim:** none left behind; the local helper was removed.

### 2) What did not change?
- Definitional-query classification behavior did not intentionally change; this step is a mechanical de-duplication to use the existing canonical helper implementation.
- Public runtime entrypoints and external wire/session-log contracts were not modified by this step.

### 3) Why this step was taken in this order?
- Centralizing call sites onto the canonical retrieval-routing helper first removes ambiguity and drift risk before any further routing or intent-confidence refactors.

### Entry 2

#### 1) What moved, and where did it land?
- **Old path/symbol:** implicit/accidental export surface in `src/testbot/sat_chatbot_memory_v2.py` with several test imports reaching underscored internals (for example `_parse_args`, `_read_runtime_env`, `_resolve_answer_routing_from_decision_object`, `_build_debug_turn_payload`).
- **New path/symbol:** explicit module export contract via `__all__` plus stable façade exports (`parse_args`, `read_runtime_env`, `resolve_mode`, `print_startup_status`, `run_source_ingestion`, `run_chat_loop`, `resolve_answer_routing_from_decision_object`, `build_debug_turn_payload`, `format_debug_turn_trace`, `format_debug_turn_trace_payload`, etc.) in the same module.
- **Delegation shim:** internal underscored implementations remain and are delegated to by public façade functions for compatibility and extraction safety.

#### 2) What did not change?
- Runtime behavior of parsing, mode resolution, routing, chat loop execution, and debug payload formatting did not intentionally change; this step is API-surface stabilization and caller cleanup.
- Canonical runtime entrypoints (`run_canonical_answer_stage_flow`, `run_answer_stage_flow`, `answer_assemble`) and session-log schema semantics were preserved.

#### 3) Why this step was taken in this order?
- Freezing and documenting the supported export surface before further extraction reduces accidental coupling and allows follow-on moves to preserve compatibility by contract rather than by incidental imports.

### Entry 3

#### 1) What moved, and where did it land?
- **Old path/symbol:** high-frequency stage artifact keys were read via raw string lookups (for example `confidence_decision["scored_candidates"]`, `alignment_decision["dimension_inputs"]`, and `commit_receipt["commit_stage"]`) in `src/testbot/sat_chatbot_memory_v2.py`.
- **New path/symbol:** typed fields + accessors were added in `src/testbot/pipeline_state.py` (`ConfidenceDecision.scored_candidates`, `AlignmentDecision.dimension_inputs`, `CommitReceiptArtifact.commit_stage` and related commit metadata), and the main call sites now use those typed accessors/fields.
- **Delegation shim:** `StageArtifact.get(...)` and `extra` remain in place for backward-compatible unknown keys.

#### 2) What did not change?
- Session logging event names and overall payload shape were preserved; only the value-read mechanism shifted from ad-hoc key strings to typed artifacts.
- Unknown artifact keys are still retained through `extra`, so older producers/consumers can continue to round-trip non-contract metadata.

#### 3) Why this step was taken in this order?
- Typing and enforcing the highest-frequency read paths first creates a safer contract surface for subsequent pipeline extraction while minimizing behavior risk in lower-traffic keys.
