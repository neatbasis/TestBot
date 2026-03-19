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

### Entry 4

#### 1) What moved, and where did it land?
- **Old path/symbol:** the architecture audit language in `docs/architecture/system-structure-audit-2026-03-19.md` described `run_answer_stage_flow` as a parallel runner and framed the next step as ambiguity resolution.
- **New path/symbol:** the same audit now records `run_answer_stage_flow` as a **deprecated alias** delegating to `run_canonical_answer_stage_flow`, includes an as-of evidence note with symbol names and approximate source line ranges, and updates the next step to removal-timeline + import migration planning.
- **Delegation shim:** runtime delegation remains in code (`run_answer_stage_flow(...) -> run_canonical_answer_stage_flow(...)`) while migration proceeds.

#### 2) What did not change?
- Runtime answer-stage execution behavior did not change in this step; the update is documentation-only and aligns architectural narrative with existing code behavior.
- No runtime wire/session-log contracts were modified by this documentation correction.

#### 3) Why this step was taken in this order?
- Locking audit text to current code evidence first keeps refactor sequencing auditable and ensures the next extraction step is a concrete alias-removal/migration plan rather than rediscovery.

### Entry 5

#### 1) What moved, and where did it land?
- **Old path/symbol:** `_run_canonical_turn_pipeline(...)` in `src/testbot/sat_chatbot_memory_v2.py` contained inline canonical stage-closure orchestration.
- **New path/symbol:** canonical turn-stage closure execution moved into application-layer service `src/testbot/application/services/turn_service.py` via `run_canonical_turn_pipeline_service(...)` with `TurnPipelineDependencies` receiver wiring.
- **Delegation shim:** `_run_canonical_turn_pipeline(...)` remains in `sat_chatbot_memory_v2.py` as a thin façade that builds dependencies and delegates.

#### 2) What did not change?
- The existing runtime façade symbol set (`__all__`) in `sat_chatbot_memory_v2.py` remains unchanged; existing import surfaces stay compatible.
- Canonical stage ordering and session-log event semantics are intended to remain unchanged; this extraction step rehomes orchestration logic without policy changes.

#### 3) Why this step was taken in this order?
- Extracting stage-closure execution behind a dependency-receiver boundary first reduces monolith complexity while preserving stable runtime entrypoints for follow-on package-map refactors.

### Entry 6

#### 1) What moved, and where did it land?
- **Old path/symbol:** `append_pipeline_snapshot(...)` in `src/testbot/pipeline_state.py` directly imported `utc_now_iso` from `testbot.memory_cards`.
- **New path/symbol:** `append_pipeline_snapshot(...)` now accepts a domain-local `SnapshotTimeProvider` boundary (defaulting to `UtcSnapshotTimeProvider` in the same module), and clock-aware callers in `src/testbot/application/services/turn_service.py` and `src/testbot/sat_chatbot_memory_v2.py` pass clock-backed providers through that boundary.
- **Delegation shim:** compatibility is retained because `append_pipeline_snapshot(...)` still works without caller changes via the default `UtcSnapshotTimeProvider`.

#### 2) What did not change?
- Pipeline snapshot schema/event contract remains unchanged for consumers (`event`, `schema_version`, `stage`, and `state` payload structure are unchanged); only timestamp sourcing was decoupled from `memory_cards`.
- Existing timestamped snapshot behavior is preserved at a parity level by tests that verify snapshot writing still includes `ts` and supports deterministic injected time values.

#### 3) Why this step was taken in this order?
- Isolating timestamp sourcing behind a small domain-local interface first removes an explicit adapter dependency with minimal surface-area change before broader `pipeline_state` and boundary-enforcement refactors.

### Entry 7

#### 1) What moved, and where did it land?
- **Old path/symbol:** mixed stabilization decision + persistence orchestration in `src/testbot/stabilization.py` (`stabilize_pre_route(...)` performed planning and storage writes in one flow).
- **New path/symbol:** `build_stabilization_plan(...)` now computes deterministic stabilization artifacts and next-state transitions as pure logic, while `persist_stabilization_records(...)` handles adapter-facing writes; `stabilize_pre_route(...)` delegates to those seams.
- **Delegation shim:** `stabilize_pre_route(...)` remains the compatibility entrypoint and now acts as a thin orchestrator.
- **Old path/symbol:** retrieval bundling logic in `src/testbot/evidence_retrieval.py` depended directly on provider-native `Document` mapping in the same path.
- **New path/symbol:** domain-level `RetrievalInputRecord` plus pure logic functions (`evidence_record_from_input`, `route_record_channel`, `build_evidence_bundle_from_input_records`) now hold retrieval decision/bundling behavior; `Document` inputs are mapped through adapter-facing entrypoints.
- **Delegation shim:** existing `build_evidence_bundle_from_docs_and_scores(...)` and `build_evidence_bundle_from_hits(...)` remain available and delegate through the new domain input seam.

#### 2) What did not change?
- Retrieval posture semantics (`empty_evidence`, `scored_empty`, `scored_non_empty`) and policy-consumption channel ordering were intentionally preserved.
- Stage contract behavior for pre-route stabilization (candidate facts, same-turn exclusion, and retrieval constraints) was intentionally preserved at API level.
- No new backend dependency was introduced; deterministic tests continue to run without concrete vector/provider services.

#### 3) Why this step was taken in this order?
- Introducing pure-logic seams before port/protocol extraction reduces coupling risk early while keeping existing runtime call sites stable for subsequent `ISSUE-0013` boundary work.

### Entry 8

#### 1) What moved, and where did it land?
- **Old path/symbol:** `commit_answer_stage(...)` in `src/testbot/answer_commit.py` directly consumed `ValidatedAnswer` + `RenderedAnswer` and co-owned translation into commit persistence fields.
- **New path/symbol:** narrow commit application entry `AnswerCommitService.commit(...)` now consumes `CommitStageInputs` (`CommitValidationPayload` + `CommitRenderingPayload`), while upstream translation is isolated in `build_commit_stage_inputs(...)`.
- **Delegation shim:** `commit_answer_stage(...)` remains as a compatibility wrapper delegating to `AnswerCommitService`.
- **Call-site movement:** orchestration paths now build commit inputs before commit in `src/testbot/application/services/turn_service.py` and `src/testbot/sat_chatbot_memory_v2.py`.

#### 2) What did not change?
- Commit guardrail semantics are intentionally unchanged (failed validation still requires explicit degraded rendering contract; validated answers still reject degraded commit contract).
- Commit receipt shape and stage-log contract fields are intentionally unchanged in this step; this is an internal seam extraction, not a wire/schema redesign.
- This step does **not** claim full package-layer enforcement or full `answer_commit.py` decomposition beyond the commit-input seam.

#### 3) Why this step was taken in this order?
- Introducing a receiver-style commit seam before deeper module/package relocation enables deterministic service tests with fakes while minimizing runtime regression risk.

### Entry 9

#### 1) What moved, and where did it land?
- **Old path/symbol:** alignment scoring logic lived in `src/testbot/sat_chatbot_memory_v2.py` (`evaluate_alignment_decision`, `response_contains_claims`, `raw_claim_like_text_detected`, `has_required_memory_citation`, and related general-knowledge alignment helpers/constants).
- **New path/symbol:** alignment scoring now lives in `src/testbot/logic/alignment.py`, with package export at `src/testbot/logic/__init__.py`.
- **Delegation shim:** `evaluate_alignment_decision(...)` remains in `src/testbot/sat_chatbot_memory_v2.py` as a temporary re-export shim that emits `DeprecationWarning`; planned removal date is **2026-06-30** after downstream imports fully migrate.

#### 2) What did not change?
- Alignment decision payload structure (`objective_version`, `dimensions`, `dimension_inputs`, `final_alignment_decision`) and contract semantics were preserved.
- Canonical answer-stage behavior and invariants were validated without intentional policy-threshold changes.
- Existing helper imports from `sat_chatbot_memory_v2.py` remain available during this migration step.

#### 3) Why this step was taken in this order?
- Extracting pure scoring logic first while preserving a temporary shim minimizes blast radius and enables receiver-first import migration in tests and downstream callsites before removing legacy exports.

### Entry 10

#### 1) What moved, and where did it land?
- **Old path/symbol:** `_run_full_canonical_turn_from_seeded_artifacts(...)` in `src/testbot/sat_chatbot_memory_v2.py` acted as a second seeded answer-stage runtime path.
- **New path/symbol:** removed; canonical seeded answer-stage execution authority is now solely `run_canonical_answer_stage_flow(...) -> _run_answer_stages_from_supplied_artifacts(...)`.
- **Delegation shim:** `run_answer_stage_flow(...)` remains as a deprecated alias and delegates to `run_canonical_answer_stage_flow(...)`.

#### 2) What did not change?
- Public canonical answer-stage behavior did not intentionally change; `run_canonical_answer_stage_flow(...)` remains the authoritative seeded-artifact execution entrypoint.
- Backward compatibility for callers still importing `run_answer_stage_flow(...)` is preserved through the existing `DeprecationWarning` + delegation shim.

#### 3) Why this step was taken in this order?
- Removing the unused parallel seeded-turn helper first eliminates runtime authority overlap before alias retirement, making the remaining migration path measurable and testable.

#### Lifecycle status and removal/migration criteria
- **`_run_full_canonical_turn_from_seeded_artifacts(...)`:** **Removed on 2026-03-19**. No compatibility API retained; restoration is disallowed unless a new audit-approved issue reintroduces it as explicitly non-authoritative test-only helper.
- **`run_answer_stage_flow(...)` deprecation shim:** keep until all are true, then remove in the next release cut:
  1. repository search returns zero non-test call sites importing/calling `run_answer_stage_flow(...)`;
  2. CI includes a delegation-contract test proving alias passthrough to `run_canonical_answer_stage_flow(...)` while shim exists;
  3. changelog + architecture audit record the explicit removal date/release for the alias.

### Entry 11

#### 1) What moved, and where did it land?
- **Old path/symbol:** `plan.md` Phase and Workstream sections described all major tracks as future-state work without current completion status.
- **New path/symbol:** `plan.md` now includes explicit status annotations in Section 10 (Phases 1–6), status-prefixed lines for each Section 16 Workstream (A–H), and a new Section 15 risk entry (`Risk 7: Changelog describes intent, not evidence`).
- **Delegation shim:** not applicable (documentation/state-layer update only).

#### 2) What did not change?
- The four-category framing, phase sequence ordering, workstream labels, Section 17 “done” definition, and existing six risk descriptions were intentionally preserved.
- This step does not claim code extraction completion; it records current partial status to avoid rework drift and parallel-implementation risk.

#### 3) Why this step was taken in this order?
- Correcting the plan’s status layer before additional extraction work prevents agents from redoing partially completed refactors from scratch and preserves receiver-first migration discipline.

### Entry 12

#### 1) What moved, and where did it land?
- **Old path/symbol:** lambda/closure stage-runtime captures in `run_canonical_turn_pipeline_service(...)` (`CanonicalStage(..., lambda ctx: ...stage_runtime...)`) inside `src/testbot/application/services/turn_service.py`.
- **New path/symbol:** explicit dependency receiver `_TurnPipelineStageHandlers(runtime=...)` with named bound handlers and `canonical_stages()` in the same module.
- **Delegation shim:** none required; stage names and canonical sequence remain unchanged.
- **Old path/symbol:** seeded answer-stage orchestration helpers in `src/testbot/sat_chatbot_memory_v2.py` (`_run_answer_stages_from_supplied_artifacts(...)` and compatibility execution through `run_canonical_answer_stage_flow(...)`).
- **New path/symbol:** removed/retired; runtime raw-utterance processing authority is the canonical turn pipeline via `_run_canonical_turn_pipeline(...)` and `run_chat_loop(...)`.
- **Delegation shim:** `run_answer_stage_flow(...)` remains as a deprecation shim that delegates to `run_canonical_answer_stage_flow(...)`; seeded inputs are now routed through `_run_canonical_turn_pipeline(...)` instead of executing a parallel answer-stage flow.

#### 2) What did not change?
- The canonical 11-stage order itself did not change (`observe.turn` through `answer.commit`), and the orchestrator remains the single authority for stage sequencing.
- CLI/satellite chat loop turn execution still routes user utterances through `_run_canonical_turn_pipeline(...)`; this step removes alternate seeded answer-stage execution rather than changing loop routing contracts.
- Session log schema version and commit receipt contract were not intentionally changed in this migration step.

#### 3) Why this step was taken in this order?
- Eliminating duplicated answer-stage orchestration and closure-capture wiring first establishes a single auditable runtime path before further entrypoint/package migration work.
