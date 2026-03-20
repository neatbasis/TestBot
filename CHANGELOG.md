# Changelog

## Entry template (use for every PR/refactor step)
For each changelog entry, answer these three questions explicitly:

1. **What moved, and where did it land?**
   - Include the old path/symbol, new path/symbol, and whether a delegation shim remains.
2. **What did not change?**
   - State verified non-changes (behavior, public API, wire protocol, session log schema, etc.).
3. **Why this step was taken in this order?**
   - One sentence describing sequencing rationale (dependency order, receiver-first, ambiguity reduction before next extraction, etc.).

## 2026-03-20

### Entry 1

#### 1) What moved, and where did it land?
- **Old path/symbol:** call sites/tests expected `CanonicalTurnOrchestrator` to be reachable via `src/testbot/sat_chatbot_memory_v2.py`, but the compatibility façade no longer exposed that symbol.
- **New path/symbol:** `src/testbot/sat_chatbot_memory_v2.py` now provides an explicit compatibility re-export `CanonicalTurnOrchestrator = testbot.canonical_turn_orchestrator.CanonicalTurnOrchestrator`.
- **Delegation shim:** the compatibility module remains a thin façade only; canonical implementation authority remains in `src/testbot/canonical_turn_orchestrator.py`.

#### 2) What did not change?
- `CanonicalTurnOrchestrator` stage-order and runtime behavior did not change; this step restores only import-path compatibility.
- Canonical owner stays `testbot.canonical_turn_orchestrator`, and compatibility intent is documented in-module via `_COMPATIBILITY_REEXPORTS` metadata rather than introducing new orchestration logic in the façade module.

#### 3) Why this step was taken in this order?
- Restoring the missing compatibility export first unblocks existing runtime/test references while preserving the canonical-owner boundary before any further façade-surface pruning.

#### 4) Compatibility decision audit (sat runtime façade expectations)

| Symbol expectation from `sat_chatbot_memory_v2` | Classification | Decision |
|---|---|---|
| `CanonicalTurnOrchestrator` | compatibility re-export | Restored as explicit re-export; canonical owner remains `testbot.canonical_turn_orchestrator`. |
| `run_canonical_answer_stage_flow` | currently supported façade runtime entrypoint | Keep exported from façade for current runtime compatibility; canonical-owner status remains subject to architecture-track decisions. |
| `run_answer_stage_flow` | compatibility re-export (deprecated) | Keep temporary shim with deprecation warning metadata (existing removal target 2026-04-01). |
| `evaluate_alignment_decision` | compatibility re-export (deprecated) | Keep temporary shim with deprecation warning metadata (existing removal target 2026-04-01). |
| `CanonicalTurnContext`, `CanonicalStage` via façade | obsolete expectation | Not re-exported; direct imports from `testbot.canonical_turn_orchestrator` are required. |

## 2026-03-19


### Entry 8

#### 1) What moved, and where did it land?
- **Old path/symbol:** `append_session_log(...)` full implementation in `src/testbot/sat_chatbot_memory_v2.py` (including JSON-safe normalization and schema-version stamping).
- **New path/symbol:** canonical owner is now `src/testbot/observability/session_log.py::append_session_log(...)` with `SESSION_LOG_SCHEMA_VERSION` colocated in the same module.
- **Delegation shim:** `src/testbot/sat_chatbot_memory_v2.py::append_session_log(...)` remains as a compatibility delegator preserving the original call signature and forwarding to the canonical owner.

#### 2) What did not change?
- Session-log row contract remains unchanged (`ts`, `event`, `schema_version`, plus normalized payload keys), and schema version behavior remains `2`.
- Legacy import path (`testbot.sat_chatbot_memory_v2.append_session_log`) remains available while active callers can import the canonical path (`testbot.observability.session_log.append_session_log`).

#### 3) Why this step was taken in this order?
- Moving the telemetry sink first while keeping a stable shim reduces coupling risk for broad call-site migration and preserves backward compatibility for tests/runtime integrations.

#### 4) Lifecycle labels
- `testbot.observability.session_log.append_session_log`: **canonical owner**.
- `testbot.sat_chatbot_memory_v2.append_session_log`: **compatibility delegator**.

### Entry 0

#### 1) What moved, and where did it land?
- **Old path/symbol:** compatibility aliases in `src/testbot/sat_chatbot_memory_v2.py` (`run_answer_stage_flow`, `evaluate_alignment_decision`) had partial deprecation messaging and runtime-internal call paths still touched the alignment shim.
- **New path/symbol:** runtime-internal alignment callers now use canonical owner `_evaluate_alignment_decision` (`testbot.logic.alignment.evaluate_alignment_decision`), and both compatibility aliases now share explicit deprecation metadata (canonical owner, removal target date, removal criteria).
- **Delegation shim:** both aliases remain as temporary re-exports with strict passthrough coverage in `tests/test_answer_stage_flow_delegation.py`.

#### 2) What did not change?
- External compatibility exports remain present in `__all__` for `run_answer_stage_flow` and `evaluate_alignment_decision`; no caller-breaking API removal was performed in this step.
- Canonical answer-stage execution authority remains `run_canonical_answer_stage_flow(...)`, and alignment scoring behavior remains owned by `testbot.logic.alignment`.

#### 3) Why this step was taken in this order?
- Completing deprecation metadata + import-boundary enforcement before symbol deletion creates an auditable, low-risk retirement path and prevents new dependency growth on deprecated aliases.

#### 4) Lifecycle labels
- `run_answer_stage_flow`: **compatibility delegator**, **deprecated**.
- `evaluate_alignment_decision` (shim in monolith): **compatibility delegator**, **deprecated**.

#### Compatibility lifecycle status snapshot

| Symbol | Status | Removal target | Removal-ready criteria |
|---|---|---|---|
| `run_answer_stage_flow` | **compatibility delegator** + **deprecated** | 2026-04-01 | all internal callers and non-compatibility tests import `run_canonical_answer_stage_flow` |
| `evaluate_alignment_decision` shim in `sat_chatbot_memory_v2` | **compatibility delegator** + **deprecated** | 2026-04-01 | all callers import from `testbot.logic.alignment` while compatibility passthrough tests remain green |
| `_run_full_canonical_turn_from_seeded_artifacts` | **fully retired** | removed 2026-03-19 | n/a |

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
- **Delegation shim:** `evaluate_alignment_decision(...)` remains in `src/testbot/sat_chatbot_memory_v2.py` as a temporary re-export shim that emits `DeprecationWarning`; planned removal date is **2026-04-01** after downstream imports fully migrate.

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

#### 4) Lifecycle labels
- `_run_full_canonical_turn_from_seeded_artifacts(...)`: **fully retired**.
- `run_answer_stage_flow(...)`: **compatibility delegator**, **deprecated**.

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

#### 4) Lifecycle labels
- `_TurnPipelineStageHandlers` extraction: **extracted**.
- Seeded answer-stage parallel helper path: **fully retired**.
- `run_answer_stage_flow(...)`: **compatibility delegator**, **deprecated**.

### Entry 13

#### 1) What moved, and where did it land?
- **Old path/symbol:** stale architecture/progress narrative in `docs/pivot.md`, `docs/architecture/system-structure-audit-2026-03-19.md`, and `docs/architecture/plan-execution-checklist.md` still described inline stage-closure capture, partial stage DTO coverage, and pre-schema-version governance status.
- **New path/symbol:** those same documents now describe current `main` behavior: service-layer canonical orchestration via `_TurnPipelineStageHandlers`, all eleven named canonical stage DTO classes present, seeded compatibility routing through `_run_canonical_turn_pipeline(...)`, and schema-versioned verification manifest progress.
- **Delegation shim:** not applicable (documentation-only synchronization update).

#### 2) What did not change?
- No runtime/module behavior changed; this entry only updates planning/audit/checklist documentation to match existing implementation state.
- Public APIs, canonical stage ordering, and session log/runtime contracts are intentionally unchanged by this step.

#### 3) Why this step was taken in this order?
- Keeping planning and audit documents synchronized with already-landed extraction work reduces governance drift and prevents follow-on work from being planned against outdated assumptions.
### Entry 14

#### 1) What moved, and where did it land?
- **Old path/symbol:** canonical-sequence declaration remained implicit in handler construction inside `src/testbot/application/services/turn_service.py`.
- **New path/symbol:** explicit sequence contract `CANONICAL_STAGE_SEQUENCE` now owns the canonical stage ordering and drives stage binding in `turn_service`.
- **Delegation shim:** none required for stage names; existing canonical stage handlers remain unchanged.
- **Old path/symbol:** monolith-owned decision helper implementations in `src/testbot/sat_chatbot_memory_v2.py` (`_selected_decision_from_confidence`, `_resolve_answer_routing_from_decision_object`, `_resolve_answer_routing_for_stage`, `_decision_object_from_assembled`).
- **New path/symbol:** helper ownership moved to `src/testbot/logic/decision_helpers.py`, with monolith wrappers retained for compatibility.
- **Delegation shim:** yes; monolith private helpers now delegate to logic helpers.
- **Old path/symbol:** startup execution logic in `sat_chatbot_memory_v2.main(...)`.
- **New path/symbol:** dedicated entrypoint module `src/testbot/entrypoints/sat_cli.py::main(...)`; runtime `main(...)` now delegates.
- **Delegation shim:** yes; compatibility `main(...)` remains in monolith.

#### 2) What did not change?
- Canonical stage order semantics and stage names were intentionally preserved (`observe.turn` through `answer.commit`).
- Compatibility exports in `sat_chatbot_memory_v2.py` remain available; this step is ownership relocation and wiring refactor, not a caller-breaking API cut.
- Session log schema version and commit receipt wire contract were not intentionally changed in this step.

#### 3) Why this step was taken in this order?
- Establishing explicit sequence ownership and extracting entrypoint/decision helpers first reduces monolith authority while preserving stable runtime symbols for incremental migration.

#### 4) Lifecycle labels
- `CANONICAL_STAGE_SEQUENCE`: **extracted** (explicit canonical owner).
- `sat_chatbot_memory_v2.main(...)`: **compatibility delegator**.
- Monolith decision helper wrappers: **delegated**.

### Entry 15

#### 1) What moved, and where did it land?
- **Old path/symbol:** package script authority in `pyproject.toml` bound `testbot` to monolith startup (`testbot.sat_chatbot_memory_v2:main`).
- **New path/symbol:** package script authority now binds `testbot` to extracted entrypoint module (`testbot.entrypoints.sat_cli:main`) in `[project.scripts]`.
- **Delegation shim:** the monolith `main(...)` symbol still exists for compatibility, but it is no longer the installer-authoritative package script target.
- **Governance/doc updates:** directive traceability and architecture audit evidence lines were updated to reflect that the installer mapping changed now, while preserving historical “at audit time” context where needed.

#### 2) What did not change?
- The extracted entrypoint module itself is **not new in this change**; `testbot.entrypoints.sat_cli` already existed and already delegated into established runtime flow.
- Canonical turn pipeline behavior, stage ordering, and session-log contract were intentionally unchanged; this step changes packaging binding authority rather than runtime policy logic.

#### 3) Why this step was taken in this order?
- Moving package-script authority only after entrypoint extraction exists and is exercised reduces migration risk by switching installers to an already-established boot surface instead of introducing a brand-new runtime path.

#### 4) Lifecycle labels
- Package script mapping to `testbot.entrypoints.sat_cli:main`: **extracted**.
- Monolith `main(...)`: **delegated** and retained as **compatibility delegator**.
