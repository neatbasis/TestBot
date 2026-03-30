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

## 2026-03-30 follow-on update (post-#716 timestamp/snapshot + obligation helper cluster reduction)
### Step 1 inventory (before this slice)
- **Timestamp generation authority (support/control):** runtime-loop pending-obligation creation still sourced `now_iso` from legacy `_utc_now_iso`.
- **Snapshot time-provider authority (support/control):** runtime-loop ingest snapshots still used legacy `_ClockBackedSnapshotTimeProvider`.
- **Obligation-transition emission authority (support/control):** runtime-loop pending-obligation creation still emitted `"created"` transitions through legacy `_emit_obligation_transition(...)`.
- **Pure plumbing (separate deferred seam):** `append_session_log` ownership remained deferred and intentionally separate from this support/control slice.

### Step 2 bounded sub-slice selected
- Selected first-priority seam: **obligation-transition helper ownership**.
- Canonicalized runtime-loop pending-obligation `"created"` transition emission to use canonical runtime background-ingestion owner (`testbot.entrypoints.runtime_background_ingestion.emit_obligation_transition`) instead of legacy `_emit_obligation_transition(...)`.

### Step 3 runtime/background-ingestion dependency reduction
- `runtime_loop.run_chat_loop(...)` now emits pending-obligation creation transitions through canonical `emit_obligation_transition(..., deps=RuntimeBackgroundIngestionDependencies(...))`.
- This removes the selected runtime path's direct dependence on `_legacy_runtime._emit_obligation_transition` while preserving compatibility logging behavior through the same deferred `append_session_log` dependency contract.

### Step 4 proof tests
- Added direct runtime-loop proof that sabotages legacy `_emit_obligation_transition` and still observes `"created"` obligation transitions via canonical runtime background-ingestion helper wiring.
- Updated runtime-loop monolith touchpoint allowlist to confirm `_emit_obligation_transition` is no longer a runtime-loop-owned dependency touchpoint.

### Step 5 deferred scope after this slice
- **Still deferred in this continuity-support cluster:** timestamp/snapshot support ownership (`_utc_now_iso`, `_ClockBackedSnapshotTimeProvider`) remains legacy-routed.
- **Still deferred as separate plumbing seam:** `append_session_log` ownership retirement remains intentionally untouched.
- **Next highest-weight seam after this slice:** timestamp/snapshot continuity-support authority (`_utc_now_iso` and `_ClockBackedSnapshotTimeProvider`) for runtime/background-completion support flows.

## 2026-03-30 follow-on update (post-#717 timestamp/snapshot continuity-support sub-slice)
### Step 1 inventory (before this slice)
- **Timestamp generation authority (support/control):** runtime-loop pending-obligation creation still sourced `now_iso` from legacy `_utc_now_iso`.
- **Snapshot time-provider authority (support/control):** runtime-loop ingest snapshots still depended on legacy `_ClockBackedSnapshotTimeProvider`.
- **Support/control-only usage vs meaning-bearing semantics:**
  - `_ClockBackedSnapshotTimeProvider` usage was support/control-only (snapshot event timing), not unresolved-intent or answer semantics.
  - `_utc_now_iso` in pending-obligation creation was support/control-only for continuity bookkeeping.
- **Pure plumbing vs support ownership:**
  - `append_session_log` remained a separate plumbing seam and was not required to move snapshot provider ownership.

### Step 2 bounded sub-slice selected
- Selected first-priority seam: **snapshot time-provider authority**.
- Canonicalized runtime-loop ingest snapshot time-provider construction into canonical runtime owner (`testbot.entrypoints.runtime_snapshot_support`) and removed runtime-loop dependency on legacy `_ClockBackedSnapshotTimeProvider`.

### Step 3 runtime/background-ingestion dependency reduction
- `runtime_loop.run_chat_loop(...)` now injects ingest snapshot timestamps through canonical `runtime_clock_snapshot_time_provider(clock=...)` instead of `_legacy_runtime._ClockBackedSnapshotTimeProvider(...)`.
- Runtime/background-completion support flow remains behaviorally equivalent because the canonical provider preserves the same `now_iso()` contract backed by runtime clock input.

### Step 4 proof tests
- Added a direct runtime-loop proof test that sabotages legacy `_ClockBackedSnapshotTimeProvider` and still executes ingest snapshot emission + turn pipeline.
- Added a direct assertion that the injected provider type at snapshot time is canonical (`RuntimeClockBackedSnapshotTimeProvider`) rather than a legacy provider.
- Updated monolith-touchpoint allowlist proof to show `_ClockBackedSnapshotTimeProvider` is no longer a runtime-loop `_legacy_runtime` dependency.

### Step 5 deferred scope after this slice
- **Moved in this PR:** runtime-loop snapshot time-provider authority for ingest snapshot timing.
- **Still deferred in timestamp/snapshot cluster:** `_utc_now_iso` ownership for pending-obligation creation timestamps.
- **Still deferred as separate plumbing seam:** `append_session_log` ownership retirement remains intentionally untouched.
- **Next highest-weight seam after this slice:** `_utc_now_iso` current-time ISO helper authority for runtime/background-ingestion continuity-support paths.

## 2026-03-30 follow-on update (post-#718 `_utc_now_iso` continuity-support sub-slice)
### Step 1 inventory (before this slice)
- **Runtime/background-ingestion support/control timing:** pending-ingestion obligation creation in `runtime_loop` still sourced `now_iso` from legacy `_legacy_runtime._utc_now_iso` and computed `deadline_at` through legacy-routed arrow access.
- **Obligation bookkeeping timestamps:** `"created"` transitions for pending-ingestion obligations reused that legacy-generated timestamp pair (`created_at`, `last_polled_at`, `deadline_at`) for continuity bookkeeping.
- **Support/control-only vs meaning-bearing semantics:** this seam was support/control timestamp authority (obligation tracking), not user-answer semantic meaning.

### Step 2 bounded sub-slice selected
- Selected first-priority seam: **pending-ingestion obligation creation current-time ISO helper ownership** for runtime/background-ingestion continuity support.
- Canonicalized this into `testbot.entrypoints.runtime_background_ingestion.register_pending_ingestion_obligation(...)` so runtime-loop obligation creation no longer owns/requests `_utc_now_iso`.

### Step 3 runtime/background-ingestion dependency reduction
- `runtime_loop.run_chat_loop(...)` now delegates pending-ingestion registry creation + `"created"` transition emission to canonical runtime background-ingestion owner.
- Canonical runtime/background-ingestion path no longer depends on `_legacy_runtime._utc_now_iso` (nor legacy arrow access) for this selected obligation-timestamp support path.
- `append_session_log` ownership was intentionally left as-is through the existing dependency contract (separate plumbing seam).

### Step 4 proof tests
- Added direct canonical-owner test for `register_pending_ingestion_obligation(...)` proving canonical timestamp generation and transition emission behavior.
- Strengthened runtime-loop proof by sabotaging legacy `_utc_now_iso` in the compatibility façade while verifying pending-ingestion context creation still succeeds through canonical runtime/background-ingestion ownership.
- Updated runtime-loop monolith touchpoint allowlist to show `_utc_now_iso` and legacy `arrow` are no longer required runtime-loop dependencies.

### Step 5 deferred scope after this slice
- **Moved in this PR:** `_utc_now_iso` authority for runtime-loop pending-ingestion obligation timestamp creation (support/control seam).
- **Still deferred in continuity-support/plumbing:** compatibility wrapper `_utc_now_iso` remains in monolith for legacy callers; `append_session_log` ownership retirement remains intentionally separate and untouched.
- **Next highest-weight seam after this slice:** compatibility-retirement/plumbing seams around runtime background-ingestion logging ownership (with `append_session_log` still explicitly deferred unless inseparable).

## 2026-03-30 follow-on update (post-#719 runtime/background-ingestion logging ownership sub-slice)
### Step 1 inventory (before this slice)
- **Canonical runtime/background-ingestion logging ownership still legacy-routed:**
  - `runtime_loop` assembled `RuntimeBackgroundIngestionDependencies(append_session_log=...)` from `_legacy_runtime.append_session_log`.
  - `runtime_loop` also passed `_legacy_runtime.append_session_log` into canonical `build_source_connector(...)` for background-ingestion dependency wiring.
- **Compatibility-only wrapper logging (explicitly not changed here):**
  - `sat_chatbot_memory_v2.append_session_log` remains as compatibility façade API surface for legacy callers.
- **Telemetry/debug payload generation (already handled elsewhere):**
  - runtime telemetry/debug payload helpers were already canonicalized in prior slices and are not part of this plumbing slice.
- **Pure plumbing vs semantics:**
  - This seam was dependency-wiring authority only (which logger function canonical runtime/background-ingestion is bound to), not answer/continuity semantics.

### Step 2 bounded sub-slice selected
- Selected first-priority seam: **background-ingestion dependency logging ownership** for canonical runtime loop assembly.
- Scope was intentionally limited to the `RuntimeBackgroundIngestionDependencies.append_session_log` path (including connector wiring used by that dependency bundle).

### Step 3 runtime/background-ingestion dependency reduction
- `runtime_loop.run_chat_loop(...)` now binds background-ingestion logging through canonical `testbot.observability.session_log.append_session_log`.
- Canonical runtime/background-ingestion dependency assembly no longer sources this selected logging path from `_legacy_runtime.append_session_log`.

### Step 4 proof tests
- Added a focused runtime-loop proof that:
  - sabotages legacy `sat_chatbot_memory_v2.append_session_log`,
  - verifies the logger embedded in `RuntimeBackgroundIngestionDependencies` is canonical `testbot.observability.session_log.append_session_log`,
  - confirms loop startup/background-ingestion polling path remains functional with that canonical logger ownership.

### Step 5 deferred scope after this slice
- **Moved in this PR:** canonical runtime/background-ingestion dependency logging ownership for the selected `append_session_log` dependency seam.
- **Still deferred intentionally:**
  - other runtime-loop logging call sites that are outside this bounded background-ingestion dependency slice,
  - compatibility façade exposure of `sat_chatbot_memory_v2.append_session_log` for legacy callers.
- **Next highest-weight seam after this slice:** remaining runtime-loop/commit-persistence logging-plumbing authority still sourced from legacy append-session logging paths.

## 2026-03-30 follow-on update (post-#720 runtime commit-persistence logging ownership sub-slice)
### Step 1 inventory (before this slice)
- **Runtime-loop logging ownership (still legacy-routed and deferred in this PR):**
  - direct runtime-loop user-ingest logging (`_legacy_runtime.append_session_log("user_utterance_ingest", ...)`),
  - runtime turn-telemetry dependency wiring (`RuntimeTurnTelemetryDependencies(append_session_log=_legacy_runtime.append_session_log, ...)`),
  - turn-pipeline hook wiring (`RuntimeTurnPipelineHooks(append_session_log=_legacy_runtime.append_session_log, ...)` and answer-assemble injected logger).
- **Commit-persistence logging ownership (selected seam):**
  - `RuntimeCommitPersistenceDependencies` in `runtime_loop` still sourced `append_session_log` from `_legacy_runtime.append_session_log`, making canonical commit persistence logging authority legacy-owned for promoted-context commit logs.
- **Compatibility-only façade logging (explicitly unchanged):**
  - `sat_chatbot_memory_v2.append_session_log` remains a compatibility wrapper API for legacy callers.
- **Already-canonical telemetry/debug ownership (unchanged in this PR):**
  - runtime telemetry payload/build-format owners are already canonicalized from prior slices; this PR does not revisit that ownership.
- **Pure plumbing vs semantic coupling:**
  - selected seam is logger dependency wiring only (`append_session_log` function ownership for commit persistence), not answer semantics or continuity semantics.

### Step 2 bounded sub-slice selected
- Selected first-priority seam: **commit-persistence logging ownership** for `RuntimeCommitPersistenceDependencies`.
- Scope intentionally limited to commit-persistence dependency assembly in canonical runtime loop ownership.

### Step 3 runtime/commit-persistence dependency reduction
- `runtime_loop.run_chat_loop(...)` now binds `RuntimeCommitPersistenceDependencies.append_session_log` to canonical `testbot.observability.session_log.append_session_log`.
- Canonical runtime commit persistence no longer sources this selected logging path from `_legacy_runtime.append_session_log`.

### Step 4 proof tests
- Added focused runtime-loop proof that:
  - sabotages legacy `sat_chatbot_memory_v2.append_session_log`,
  - exercises commit-persistence dependency wiring through runtime background-completion path,
  - verifies commit-persistence dependency logger ownership is canonical (`testbot.observability.session_log.append_session_log`).

### Step 5 deferred scope after this slice
- **Moved in this PR:** commit-persistence logging dependency ownership for canonical runtime loop assembly (`RuntimeCommitPersistenceDependencies.append_session_log`).
- **Still deferred intentionally:**
  - runtime-loop logging callsites that still bind `_legacy_runtime.append_session_log` (user-ingest, telemetry dependency wiring, turn-pipeline hook logging),
  - compatibility façade `sat_chatbot_memory_v2.append_session_log` exposure for legacy callers.
- **Compatibility wrapper posture:** wrappers remain compatibility-only; canonical commit-persistence logging no longer depends on wrapper ownership for this selected slice.
- **Next highest-weight seam after this slice:** remaining runtime-loop logging-plumbing dependency bundle(s) still binding canonical runtime loop logging to `_legacy_runtime.append_session_log` (outside commit persistence).

## 2026-03-30 follow-on update (post-#721 runtime turn-telemetry logging ownership sub-slice)
### Step 1 inventory (before this slice)
- **Telemetry dependency logger ownership seam (selected in this PR):**
  - `runtime_loop.run_chat_loop(...)` wired `RuntimeTurnTelemetryDependencies(append_session_log=_legacy_runtime.append_session_log, ...)`, so canonical runtime-loop telemetry emission depended on monolith logger ownership for that dependency bundle.
- **Telemetry payload/build-format ownership (already canonicalized, unchanged here):**
  - `intent_telemetry_payload(...)`, `user_followup_signal_proxy(...)`, debug payload builder wiring, and telemetry emission sequencing remain under canonical runtime entrypoint/observability ownership and were not semantically changed in this slice.
- **Compatibility-only façade logging (explicitly unchanged):**
  - `sat_chatbot_memory_v2.append_session_log` remains a compatibility API surface for legacy callers.
- **Pure plumbing vs semantics distinction:**
  - this seam is dependency-function ownership only (`append_session_log` binding inside `RuntimeTurnTelemetryDependencies`), not telemetry payload meaning, turn-policy semantics, or debug trace format semantics.

### Step 2 bounded sub-slice selected
- Selected seam: **`RuntimeTurnTelemetryDependencies.append_session_log` ownership in canonical runtime-loop telemetry wiring**.
- Scope intentionally excluded:
  - direct runtime-loop user-ingest logging,
  - turn-pipeline hook logging and answer-assemble injected logger,
  - broad observability/logging cleanup.

### Step 3 runtime telemetry dependency reduction
- `runtime_loop.run_chat_loop(...)` now binds `RuntimeTurnTelemetryDependencies.append_session_log` to canonical `testbot.observability.session_log.append_session_log`.
- Canonical runtime-loop telemetry emission no longer sources this selected dependency logger from `_legacy_runtime.append_session_log`.

### Step 4 proof tests
- Added focused runtime-loop proof covering telemetry dependency ownership:
  - sabotages legacy `sat_chatbot_memory_v2.append_session_log`,
  - captures the telemetry dependency bundle passed from runtime loop into `emit_runtime_turn_telemetry(...)`,
  - verifies the embedded logger is canonical `testbot.observability.session_log.append_session_log`,
  - confirms the selected logger remains callable for compatibility-parity shape.

### Step 5 deferred scope after this slice
- **Moved in this PR:** telemetry dependency logger ownership for canonical runtime-loop telemetry wiring (`RuntimeTurnTelemetryDependencies.append_session_log`).
- **Still deferred intentionally:**
  - direct runtime-loop user-ingest logging path still calling `_legacy_runtime.append_session_log`,
  - turn-pipeline hook logging ownership (`RuntimeTurnPipelineHooks.append_session_log` and answer-assemble injected logger),
  - compatibility façade `sat_chatbot_memory_v2.append_session_log` API exposure for legacy callers.
- **Compatibility wrapper posture:** compatibility wrappers remain intentionally available, but canonical runtime-loop telemetry dependency wiring is no longer owned by the monolith logger path for this selected seam.
- **Next highest-weight seam after this slice:** turn-pipeline hook logging ownership (including answer-assemble injected logger) as the remaining largest runtime-loop logging-plumbing bundle still bound to `_legacy_runtime.append_session_log`.

## 2026-03-30 follow-on update (post-#722 turn-pipeline hook logging ownership sub-slice)
### Step 1 inventory (before this slice)
- **Hook-level runtime logging seam still legacy-routed:**
  - `runtime_loop.run_chat_loop(...)` wired `RuntimeTurnPipelineHooks.append_session_log` from `_legacy_runtime.append_session_log`.
  - The answer-stage assemble hook path injected logger ownership through `answer_assemble_for_turn_service(..., append_session_log=_legacy_runtime.append_session_log)`.
- **Out-of-scope runtime logging (explicitly deferred in this PR):**
  - direct runtime-loop user-ingest logging (`_legacy_runtime.append_session_log("user_utterance_ingest", ...)`),
  - compatibility façade API surface `sat_chatbot_memory_v2.append_session_log` for legacy callers.
- **Semantics boundary:**
  - selected seam is hook dependency ownership/plumbing only; no answer-stage semantic contract changes were included.

### Step 2 bounded sub-slice selected
- Selected seam: **turn-pipeline hook logging ownership bundle**:
  - `RuntimeTurnPipelineHooks.append_session_log`,
  - answer-assemble injected logger inside runtime hook assembly.
- Scope intentionally excluded generic hook redesign and broad runtime logging cleanup.

### Step 3 runtime hook dependency reduction
- `runtime_loop.run_chat_loop(...)` now binds `RuntimeTurnPipelineHooks.append_session_log` to canonical `testbot.observability.session_log.append_session_log`.
- Runtime hook wiring for `answer_assemble_for_turn_service(...)` now injects canonical `testbot.observability.session_log.append_session_log`.
- Canonical runtime-loop no longer sources this selected hook-level logger bundle from `_legacy_runtime.append_session_log`.

### Step 4 proof tests
- Added focused runtime-loop proof that captures runtime turn-pipeline hook dependencies through background-completion replay wiring and verifies:
  - `hooks.append_session_log` is canonical `testbot.observability.session_log.append_session_log`,
  - answer-assemble injected logger argument is canonical when the hook callback is invoked.
- Added explicit source-level ownership guard asserting the selected hook logging bundle no longer binds `_legacy_runtime.append_session_log`.

### Step 5 deferred scope after this slice
- **Moved in this PR:** hook-level logging ownership for `RuntimeTurnPipelineHooks.append_session_log` and answer-assemble injected logger in canonical runtime-loop hook assembly.
- **Still deferred intentionally:**
  - direct runtime-loop user-ingest logging still calls `_legacy_runtime.append_session_log`,
  - compatibility façade exposure of `sat_chatbot_memory_v2.append_session_log` remains for legacy callers.
- **Compatibility wrapper posture:** wrappers remain compatibility-only; canonical runtime hook bundle no longer depends on legacy logger ownership for this selected slice.
- **Next highest-weight seam after this slice:** direct runtime-loop user-ingest logging ownership retirement (with compatibility façade exposure still intentionally separate).
