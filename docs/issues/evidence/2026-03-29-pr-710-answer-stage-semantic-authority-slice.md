# 2026-03-29 PR-710/next answer-stage semantic authority slice

## Scope
Bounded seam reduction for assemble-stage special-answer authority.

## Findings (pre-change after #710)
- Validate-path semantics were canonicalized in #710, but `answer_assemble_for_turn_service(...)` still accepted legacy-injected special-answer constants and `build_partial_memory_clarifier`.
- Runtime-loop answer-stage wiring still pulled those assemble semantics from `sat_chatbot_memory_v2`, preserving split authority between assemble and validate.

## Canonical vs transitional authority after this slice
- **Canonical now**:
  - `testbot.answer_stage_semantics` now owns partial-memory clarifier construction policy (`build_partial_memory_clarifier`) and the assembly/validation special-answer contract values.
  - `answer_assemble_for_turn_service(...)` now consumes a canonical `AnswerStageSemanticContract` instead of per-call legacy answer constants/clarifier builder.
  - `answer_validate_for_turn_service(...)` and `stage_transitions` continue to consume the same canonical semantic contract/expectation owner from #710.
- **Still transitional/deferred**:
  - **Runtime telemetry/logging authority cluster**: runtime turn telemetry payload/build formatting and related debug plumbing remain legacy-routed (`_intent_telemetry_payload`, `_build_debug_turn_payload`, `_format_debug_turn_trace_payload`, `_user_followup_signal_proxy`).
  - **Background-ingestion dependency authority cluster**: runtime background ingestion still depends on legacy-owned connector/ingestor/pipeline collaborators (`_build_source_connector`, `SourceIngestor`, `_run_canonical_turn_pipeline`, `PipelineState`, `IntentType`).
  - **State continuity + unresolved-intent authority cluster**: unresolved follow-up carryover and continuity helpers remain legacy-routed (`is_clarification_answer`, `_is_capabilities_help_answer`, `_ClockBackedSnapshotTimeProvider`, `_utc_now_iso`, obligation transition helpers).

## 2026-03-29 follow-on update (post-#711 presentation seam retirement)
- `runtime_loop` now sources answer-stage presentation collaborators from canonical `testbot.application.services.answer_stage_presentation` (`ANSWER_PROMPT`, `render_context`) instead of pulling them from `sat_chatbot_memory_v2`.
- `sat_chatbot_memory_v2` keeps compatibility re-exports for `ANSWER_PROMPT` and `render_context`, but canonical presentation ownership no longer depends on legacy runtime injection in `run_chat_loop`.

## 2026-03-30 follow-on update (post-#712 runtime telemetry authority slice)
- `runtime_loop` now binds telemetry composition through canonical runtime telemetry owners:
  - `testbot.entrypoints.runtime_turn_telemetry.intent_telemetry_payload`
  - `testbot.entrypoints.runtime_turn_telemetry.user_followup_signal_proxy`
  - `testbot.observability.turn_debug_payload.build_debug_turn_payload`
  - `testbot.observability.turn_debug_payload.format_debug_turn_trace_payload`
- `sat_chatbot_memory_v2` retains compatibility wrappers for `_intent_telemetry_payload` and `_user_followup_signal_proxy`, but these wrappers now delegate to canonical runtime telemetry owners.
- Runtime-loop telemetry/debug authority is no longer semantically owned by `_legacy_runtime` for payload projection/follow-up projection/debug trace formatting.

## 2026-03-30 follow-on update (post-#713 background-ingestion dependency ownership slice)
### Step 1 inventory (before this slice)
- **Infrastructure / adapter ownership (deferred cluster target):**
  - `_build_source_connector`
  - `SourceIngestor`
  - `append_session_log` (still deferred separately)
- **Orchestration / control-flow ownership (still deferred in this PR):**
  - `_run_canonical_turn_pipeline`
- **Semantic / state authority (explicitly deferred in this PR):**
  - `PipelineState`
  - `IntentType.KNOWLEDGE_QUESTION.value`
  - unresolved-intent/continuity behavior around background-completion replay.

### Bounded sub-slice selected
- Canonicalized **source connector / ingestor dependency ownership** for runtime-loop background ingestion assembly.
- `runtime_loop` now binds background ingestion connector construction to canonical `testbot.source_ingestion_startup.build_source_connector` and ingestor class ownership to canonical `testbot.source_ingest.SourceIngestor`, rather than sourcing either collaborator from `sat_chatbot_memory_v2`.

### What remains deferred inside background ingestion
- Background completion replay still routes pipeline invocation through `_run_canonical_turn_pipeline`.
- Background completion replay state/intention contract remains legacy-routed (`PipelineState`, `IntentType` value).
- `append_session_log` ownership remains deferred and intentionally unchanged in this slice.

### Highest-weight next seam after this slice
- Remaining highest-weight background-ingestion seam is now the **pipeline invocation + state/intention contract cluster** (`_run_canonical_turn_pipeline`, `PipelineState`, `IntentType`), with state continuity/unresolved-intent and deferred logging ownership still outside this bounded slice.

## 2026-03-30 follow-on update (post-#714 replay/invocation authority slice)
### Step 1 inventory (before this slice)
- **Orchestration / invocation authority:**
  - background completion replay invoked `_run_canonical_turn_pipeline` through background-ingestion dependencies.
- **State construction / contract authority:**
  - background completion replay depended on injected `PipelineState` and `IntentType.KNOWLEDGE_QUESTION.value` to assemble replay input.
- **Semantic continuity authority (intentionally out of scope for this slice):**
  - unresolved-intent carryover and continuity behavior remained legacy-routed (`is_clarification_answer`, `_is_capabilities_help_answer`, `_ClockBackedSnapshotTimeProvider`, `_utc_now_iso`).

### Bounded sub-slice selected
- Canonicalized **background-completion replay invocation ownership** by introducing a canonical replay request contract (`BackgroundIngestionReplayRequest`) plus a single replay callable boundary (`replay_background_completion_turn`) for background-ingestion completion handling.
- Runtime-loop background-ingestion assembly now binds replay through canonical `run_runtime_turn_pipeline` ownership, with compatibility-only replay wrappers retained in `sat_chatbot_memory_v2`.

### What moved in this PR
- `process_background_ingestion_completion(...)` no longer owns turn-state construction/pipeline invocation wiring directly (`run_canonical_turn_pipeline`, `PipelineState`, `IntentType` inputs were removed from the dependency contract).
- Runtime/background-ingestion now consumes a narrower canonical replay callable contract, reducing direct dependency on `_legacy_runtime._run_canonical_turn_pipeline` in canonical runtime-loop assembly.

### What remains deferred inside background ingestion
- `append_session_log` ownership remains deferred.
- Continuity/unresolved-intent semantics remain intentionally untouched in this slice.
- Canonical runtime-loop replay invocation no longer depends on legacy `_run_canonical_turn_pipeline`.
- Compatibility replay remains monolith-hosted in `sat_chatbot_memory_v2` for legacy callers (`_replay_background_completion_turn_compat` still constructs replay `PipelineState`/`IntentType` via compatibility symbols).

### Highest-weight next seam after this slice
- **Next semantic seam:** continuity + unresolved-intent semantic authority cluster inside runtime-loop/background-completion interactions.
- **Separate plumbing seam:** deferred `append_session_log` ownership retirement.

## Semantic authority moved/clarified in this PR
- Moved assemble-stage clarifier wording/policy and special-answer constants from legacy per-call injection to canonical ownership in `testbot.answer_stage_semantics` via `AnswerStageSemanticContract`.
- Runtime loop is less responsible for answer-stage semantic composition because it no longer injects those semantic collaborators.

## Deferred telemetry/logging scope after this slice
- **Reduced in this PR:** runtime-loop telemetry payload/follow-up proxy/debug payload routing no longer depends on `_legacy_runtime` semantic ownership.
- **Still deferred in telemetry/logging cluster:** canonicalization of runtime-loop `append_session_log` ownership remains separate from this slice.
- **Next remaining cluster after this slice:** background-ingestion dependency authority (`_build_source_connector`, `SourceIngestor`, `_run_canonical_turn_pipeline`, `PipelineState`, `IntentType`) and state-continuity/unresolved-intent authority.

## 2026-03-30 follow-on update (post-#715 continuity/unresolved-intent semantic authority slice)
### Step 1 inventory (before this slice)
- **Answer-category interpretation authority (semantic):** runtime loop unresolved-intent carryover still depended on legacy answer-category helpers (`is_clarification_answer`, `_is_capabilities_help_answer`) to decide whether to preserve prior unresolved intent.
- **Unresolved-intent carryover authority (semantic):** user-turn and replay-turn continuity outcomes were shaped by legacy-routed answer classification semantics rather than a canonical continuity policy owner.
- **Timestamp/snapshot continuity support (deferred for this slice):** `_ClockBackedSnapshotTimeProvider` and `_utc_now_iso` remained legacy-routed helpers supporting snapshot/obligation timestamps.
- **Pure plumbing (separate deferred seam):** `append_session_log` ownership remained deferred and intentionally outside this semantic slice.

### Bounded sub-slice selected
- Selected first-priority seam: **unresolved-intent carryover authority**.
- Canonicalized continuity semantics by introducing a runtime-owned continuity policy helper (`testbot.application.services.continuity_runtime`) that classifies continuity-preserving answers and applies unresolved-intent carryover updates.
- Capabilities-help continuity classification now prefers canonical structured intent (`resolved_intent == capabilities_help`) and keeps a text-shape check only as an explicitly transitional compatibility heuristic when structured intent is missing.

### What moved in this PR
- Runtime user-turn unresolved-intent carryover in `runtime_loop` no longer calls legacy `is_clarification_answer(...)` / `_is_capabilities_help_answer(...)`; it now uses canonical `apply_unresolved_intent_carryover(...)`.
- Background-completion replay completion processing now applies the same canonical unresolved-intent carryover policy before emitting/committing replayed answers.
- Legacy compatibility wrappers remain, but canonical runtime/background-completion continuity behavior no longer depends on `_legacy_runtime` for this selected semantic decision.
- Legacy `_is_capabilities_help_answer(...)` remains compatibility-only and now delegates to canonical continuity owner logic.

### What remains deferred inside the continuity cluster
- Timestamp/snapshot continuity-support helpers (`_ClockBackedSnapshotTimeProvider`, `_utc_now_iso`) are intentionally left untouched in this bounded slice.
- Obligation transition emission helper wiring remains transitional around runtime-loop assembly.
- `append_session_log` ownership retirement remains a separate plumbing seam and was not mixed into this semantic slice.

### Highest-weight next seam after this slice
- Remaining highest-weight continuity-adjacent seam is **timestamp/snapshot continuity-support authority + obligation-transition helper ownership** (while keeping deferred `append_session_log` retirement separate unless inseparable).
