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

## Semantic authority moved/clarified in this PR
- Moved assemble-stage clarifier wording/policy and special-answer constants from legacy per-call injection to canonical ownership in `testbot.answer_stage_semantics` via `AnswerStageSemanticContract`.
- Runtime loop is less responsible for answer-stage semantic composition because it no longer injects those semantic collaborators.

## Deferred telemetry/logging scope after this slice
- **Reduced in this PR:** runtime-loop telemetry payload/follow-up proxy/debug payload routing no longer depends on `_legacy_runtime` semantic ownership.
- **Still deferred in telemetry/logging cluster:** canonicalization of runtime-loop `append_session_log` ownership remains separate from this slice.
- **Next remaining cluster after this slice:** background-ingestion dependency authority (`_build_source_connector`, `SourceIngestor`, `_run_canonical_turn_pipeline`, `PipelineState`, `IntentType`) and state-continuity/unresolved-intent authority.
