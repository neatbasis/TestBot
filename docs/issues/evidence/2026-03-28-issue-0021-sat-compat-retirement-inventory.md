# 2026-03-28 — ISSUE-0021 SAT compatibility façade retirement inventory

- **Issue:** `ISSUE-0021`
- **Scope:** `src/testbot/sat_chatbot_memory_v2.py` public `__all__` compatibility surface.
- **Goal:** classify every export into retirement-readiness buckets and identify authoritative callers that still depend on the façade.

## What is done in this note

1. Enumerated all `45` exported symbols from `sat_chatbot_memory_v2.__all__`.
2. Ran an in-repo caller census for `testbot.sat_chatbot_memory_v2` imports across `src/`, `tests/`, `docs/`, and `scripts/`.
3. Classified each export into one of four buckets:
   - **A**: keep temporarily
   - **B**: migrate now
   - **C**: remove now
   - **D**: decide later (missing usage evidence)
4. Defined a two-PR migration/removal sequence.

## Authoritative caller census (repo)

### Runtime / production path (authoritative)

- `src/testbot/entrypoints/runtime_legacy_bridge.py` imports `sat_chatbot_memory_v2` as an explicit transitional bridge.
- This is the only non-test in-repo runtime import path still depending on the façade.

### Docs / scripts usage (authoritative-adjacent)

- No active docs or scripts import the façade module as executable authority in current in-repo scan.
- Existing docs references are descriptive/governance mentions, not launch-path imports.

### Test usage split

- **Compatibility-only tests** (explicitly façade-compat intent by naming):
  - `tests/test_sat_runtime_compat_facade.py`
  - `tests/test_answer_stage_runtime_compat_wrappers.py`
  - `tests/test_answer_stage_flow_delegation.py`
  - `tests/test_canonical_orchestrator_compatibility_exports.py`
  - `tests/test_session_log_compatibility.py`

- **Non-compatibility tests currently importing façade symbols** (migration candidates):
  - intent/routing/assertion suites (`tests/test_intent_router.py`, `tests/test_decisioning_stages.py`, `tests/test_pipeline_semantic_contracts.py`, `tests/test_answer_routing_bridge.py`, `tests/test_canonical_turn_orchestrator.py`)
  - runtime behavior suites (`tests/test_answer_contract.py`, `tests/test_runtime_logging_events.py`, `tests/test_runtime_modes.py`, `tests/test_time_reasoning.py`, `tests/test_eval_runtime_parity.py`, `tests/test_capabilities_help.py`, `tests/test_capabilities_runtime_status.py`, `tests/test_startup_status.py`)
  - source/debug/helper suites (`tests/test_source_fusion.py`, `tests/test_source_ingestion_runtime_pipeline.py`, `tests/test_structured_debug_payload.py`, `tests/test_debug_turn_trace.py`, `tests/test_turn_debug_payload_module.py`, `tests/test_reject_taxonomy.py`)
  - selected integration/live-smoke suites still import façade APIs.

## Export inventory and retirement bucketing

> `Target issue/date` values below use the active deprecation anchor `ISSUE-0021` with phased windows.

| Symbol | Canonical owner | Why symbol still exists today | Caller class | Bucket | Removal condition | Target issue/date |
|---|---|---|---|---|---|---|
| `main` (legacy entrypoint) | `testbot.entrypoints.cli.main` | historical executable/import compatibility surface | runtime bridge + external unknown | A keep temporarily | remove after bridge + external migration evidence | ISSUE-0021 / review 2026-06-30 |
| `parse_args` | `testbot.runtime_cli_args.parse_args` | compatibility import path in runtime-mode tests | tests (non-compat) | B migrate now | move tests/callers to canonical args module | ISSUE-0021 / 2026-04-15 |
| `resolve_mode` | `testbot.runtime_capability_service.resolve_mode` | compatibility import path in runtime-mode tests | tests (non-compat) | B migrate now | import canonical runtime capability service directly | ISSUE-0021 / 2026-04-15 |
| `read_runtime_env` | runtime env helpers in façade/startup stack | retained for live-smoke/runtime bootstrap checks | tests (live-smoke) + external unknown | D decide later | confirm external usage + extract owner module if retained | ISSUE-0021 / 2026-04-30 |
| `build_runtime_memory_store` | `testbot.adapters.memory_store_factory.build_memory_store` | compatibility wiring helper | unknown/external + no direct in-repo import | D decide later | prove no external callers or add explicit replacement path | ISSUE-0021 / 2026-04-30 |
| `run_source_ingestion` | `testbot.source_ingestion_startup.run_source_ingestion` | compatibility wrapper used in runtime pipeline tests | tests (non-compat) | B migrate now | import startup ingestion owner directly | ISSUE-0021 / 2026-04-15 |
| `print_startup_status` | `testbot.startup_status_presenter.print_startup_status` | compatibility wrapper used by startup tests | tests (non-compat) | B migrate now | import presenter directly | ISSUE-0021 / 2026-04-15 |
| `run_chat_loop` | façade runtime loop helper | still used in source-ingestion runtime test harness | tests (non-compat) + external unknown | D decide later | extract owner or migrate tests to narrower canonical orchestration seam | ISSUE-0021 / 2026-04-30 |
| `run_canonical_answer_stage_flow` | canonical turn runtime service path | currently central callable used across runtime tests | tests (non-compat/live-smoke) | A keep temporarily | keep until test migration lands on canonical service entry API | ISSUE-0021 / review 2026-05-15 |
| `run_answer_stage_flow` | alias to `run_canonical_answer_stage_flow` | explicit deprecated compatibility alias | compatibility + possible external legacy | A keep temporarily | remove per deprecation criteria once imports/tests migrated | ISSUE-0021 / removal target 2026-04-01* |
| `evaluate_alignment_decision` | `testbot.logic.alignment.evaluate_alignment_decision` | explicit deprecated shim | compatibility + possible external legacy | A keep temporarily | remove per existing deprecation criteria | ISSUE-0021 / removal target 2026-04-01* |
| `CanonicalTurnOrchestrator` | `testbot.canonical_turn_orchestrator.CanonicalTurnOrchestrator` | governed compatibility re-export | compatibility tests + legacy import stability | A keep temporarily | remove after in-repo and external import migration evidence | ISSUE-0021 / review 2026-06-30 |
| `resolve_answer_routing_from_decision_object` | `testbot.logic.decision_helpers.resolve_answer_routing_from_decision_object` | compatibility bridge helper | tests (non-compat) | B migrate now | import from decision helper module directly | ISSUE-0021 / 2026-04-15 |
| `decision_object_from_assembled` | `testbot.logic.decision_helpers.decision_object_from_assembled` | compatibility bridge helper | unknown (no direct imports found) | D decide later | remove if no external imports; otherwise migrate | ISSUE-0021 / 2026-04-30 |
| `build_debug_turn_payload` | `testbot.observability.turn_debug_payload.build_debug_turn_payload` | compatibility re-export for debug tests | tests (non-compat) | B migrate now | migrate tests/importers to observability owner | ISSUE-0021 / 2026-04-15 |
| `format_debug_turn_trace` | `testbot.observability.turn_debug_payload.format_debug_turn_trace` | compatibility re-export for debug tests | tests (non-compat) | B migrate now | migrate imports to observability owner | ISSUE-0021 / 2026-04-15 |
| `format_debug_turn_trace_payload` | `testbot.observability.turn_debug_payload.format_debug_turn_trace_payload` | compatibility re-export for debug tests | tests (non-compat) | B migrate now | migrate imports to observability owner | ISSUE-0021 / 2026-04-15 |
| `append_session_log` | `testbot.observability.session_log.append_session_log` | compatibility re-export for legacy call sites | unknown (no direct imports found) | D decide later | evidence no callers -> remove; else migrate to observability import | ISSUE-0021 / 2026-04-30 |
| `build_capability_snapshot` | `testbot.runtime_capability_service.build_capability_snapshot` | compatibility wrapper used in tests | tests (non-compat + live-smoke) | B migrate now | direct-import runtime capability service | ISSUE-0021 / 2026-04-15 |
| `CapabilitySnapshot` | `testbot.runtime_capability_service.CapabilitySnapshotData` | type compatibility export | tests (non-compat) | B migrate now | import type from runtime capability service | ISSUE-0021 / 2026-04-15 |
| `RuntimeCapabilityStatus` | `testbot.runtime_capability_service.RuntimeCapabilityStatusData` | type compatibility export | tests (non-compat) | B migrate now | import type from runtime capability service | ISSUE-0021 / 2026-04-15 |
| `ASSIST_ALTERNATIVES_ANSWER` | façade fallback policy constants | test assertions depend on exact value | tests (non-compat) | D decide later | move constants to dedicated policy/constants owner then migrate imports | ISSUE-0021 / 2026-04-30 |
| `CLARIFY_ANSWER` | façade fallback policy constants | test assertions depend on exact value | tests (non-compat) | D decide later | same as above | ISSUE-0021 / 2026-04-30 |
| `DENY_ANSWER` | façade fallback policy constants | external compatibility/public constant surface | unknown | D decide later | establish canonical constants owner or remove if unused | ISSUE-0021 / 2026-04-30 |
| `FALLBACK_ANSWER` | façade fallback policy constants | test assertions depend on exact value | tests (non-compat) | D decide later | move to canonical constants owner | ISSUE-0021 / 2026-04-30 |
| `NON_KNOWLEDGE_UNCERTAINTY_ANSWER` | façade fallback policy constants | test assertions depend on exact value | tests (non-compat) | D decide later | move to canonical constants owner | ISSUE-0021 / 2026-04-30 |
| `ROUTE_TO_ASK_ANSWER` | façade fallback policy constants | test assertions depend on exact value | tests (non-compat) | D decide later | move to canonical constants owner | ISSUE-0021 / 2026-04-30 |
| `resolve_turn_intent` | intent-routing runtime helper in façade | still referenced by intent/runtime tests | tests (non-compat) | A keep temporarily | extract/declare canonical intent-runtime entry and migrate tests | ISSUE-0021 / review 2026-05-15 |
| `validate_answer_contract` | `testbot.logic.alignment.validate_answer_contract` | compatibility re-export for answer contract tests | tests (non-compat) | B migrate now | direct-import from logic alignment | ISSUE-0021 / 2026-04-15 |
| `has_required_memory_citation` | `testbot.logic.alignment.has_required_memory_citation` | compatibility re-export for answer contract tests | tests (non-compat) | B migrate now | direct-import from logic alignment | ISSUE-0021 / 2026-04-15 |
| `raw_claim_like_text_detected` | `testbot.logic.alignment.raw_claim_like_text_detected` | compatibility re-export for answer contract tests | tests (non-compat) | B migrate now | direct-import from logic alignment | ISSUE-0021 / 2026-04-15 |
| `response_contains_claims` | `testbot.logic.alignment.response_contains_claims` | compatibility re-export for answer contract tests | tests (non-compat) | B migrate now | direct-import from logic alignment | ISSUE-0021 / 2026-04-15 |
| `has_sufficient_context_confidence` | `testbot.rerank.has_sufficient_context_confidence_from_objective` | compatibility re-export for parity tests | tests (non-compat) | B migrate now | import from rerank module directly | ISSUE-0021 / 2026-04-15 |
| `build_provenance_metadata` | façade/source fusion helper | used by source-fusion + runtime logging tests | tests (non-compat) | A keep temporarily | extract to canonical provenance module first | ISSUE-0021 / review 2026-05-15 |
| `collect_used_source_evidence_refs` | façade/source fusion helper | used by source-fusion tests | tests (non-compat) | A keep temporarily | extract to canonical provenance module first | ISSUE-0021 / review 2026-05-15 |
| `render_context` | façade rendering helper | used by answer-contract tests | tests (non-compat) | D decide later | identify canonical rendering owner or remove if obsolete | ISSUE-0021 / 2026-04-30 |
| `generate_reflection_yaml` | façade helper | used in runtime logging tests | tests (non-compat) | D decide later | identify canonical owner + migrate imports | ISSUE-0021 / 2026-04-30 |
| `answer_assemble` | `testbot.application.services.answer_stage_runtime.answer_assemble` | compatibility callable export | unknown direct imports | D decide later | remove if no callers; otherwise migrate to service import | ISSUE-0021 / 2026-04-30 |
| `AnswerAssembleResult` | `testbot.application.services.answer_stage_runtime.AnswerAssembleResult` | compatibility type export | tests (non-compat) | B migrate now | import type from canonical answer stage runtime module | ISSUE-0021 / 2026-04-15 |
| `AnswerValidateResult` | `testbot.application.services.answer_stage_runtime.AnswerValidateResult` | compatibility type export | unknown direct imports | C remove now | drop from façade export set if no caller evidence | ISSUE-0021 / 2026-04-05 |
| `ambiguity_score` | façade/runtime helper | no direct in-repo imports found | unknown/external | C remove now | remove from `__all__`; keep private only if still internally required | ISSUE-0021 / 2026-04-05 |
| `intent_label` | façade wrapper over decision helper | no direct in-repo imports found | unknown/external | C remove now | remove from `__all__` once compatibility check confirms no external dependency | ISSUE-0021 / 2026-04-05 |
| `derive_response_blocker_reason` | façade helper | no direct in-repo imports found | unknown/external | C remove now | remove from `__all__` (keep internal helper as needed) | ISSUE-0021 / 2026-04-05 |
| `stage_rerank` | façade stage helper | used by time-reasoning tests | tests (non-compat) | A keep temporarily | migrate to canonical stage owner before pruning | ISSUE-0021 / review 2026-05-15 |
| `stage_rewrite_query` | façade stage helper | used by runtime logging tests | tests (non-compat) | A keep temporarily | migrate to canonical stage owner before pruning | ISSUE-0021 / review 2026-05-15 |
| `user_followup_signal_proxy` | façade helper | no direct in-repo imports found | unknown/external | C remove now | remove from `__all__` with compatibility note in release docs | ISSUE-0021 / 2026-04-05 |

\* Existing in-code metadata still states `2026-04-01` targets for selected deprecated aliases; if unmet by that date, update metadata and ISSUE-0021 status with explicit rationale.

## Ordered migration/removal sequence

1. **PR-1 (authoritative caller migration):**
   - migrate non-compatibility tests importing clear canonical owners (`logic.alignment`, `observability.turn_debug_payload`, `runtime_capability_service`, `runtime_cli_args`, `source_ingestion_startup`, `rerank`, `decision_helpers`);
   - keep dedicated compatibility tests unchanged.

2. **PR-2 (safe façade prune):**
   - remove Bucket C exports from `__all__` and tighten compatibility docstring/governance notes;
   - if any Bucket D symbols remain unresolved, either (a) promote to temporary keep with explicit owner/evidence or (b) remove with release-note callout.

3. **PR-3 (bridge + legacy entry retirement):**
   - retire `entrypoints/runtime_legacy_bridge.py` and `sat_chatbot_memory_v2.main` only after runtime caller evidence is clean and compatibility window closes.

## What remains after this note

- Execute PR-1 caller migration.
- Re-run import census; verify remaining façade imports are compatibility-only or explicitly grandfathered.
- Then execute PR-2 export prune with deterministic regression checks.

## 2026-03-28 update — PR-2 Bucket C prune execution evidence

- Re-ran targeted caller census for Bucket C symbol imports from `testbot.sat_chatbot_memory_v2`:
  - `rg -n "from testbot\\.sat_chatbot_memory_v2 import .*\\b(AnswerValidateResult|ambiguity_score|intent_label|derive_response_blocker_reason|user_followup_signal_proxy)\\b" src tests docs features scripts`
  - Result: no direct in-repo importers found for the listed Bucket C symbols.
- Applied safe façade surface prune:
  - removed `AnswerValidateResult`, `ambiguity_score`, `intent_label`, `derive_response_blocker_reason`, and `user_followup_signal_proxy` from `sat_chatbot_memory_v2.__all__`;
  - retained internal/helper definitions to avoid behavior churn in this step.

## 2026-03-28 update — provenance seam extraction evidence

- Extracted provenance assembly helpers to canonical owner `testbot.logic.provenance`:
  - `build_provenance_metadata`
  - `collect_used_source_evidence_refs`
  - coupled helper `collect_used_memory_refs`
- Updated answer-stage validation wiring to use canonical provenance owner directly (no longer passes façade wrapper as primary dependency).
- Kept façade exports as compatibility wrappers delegating to `testbot.logic.provenance`.
- Added wrapper-parity regression coverage to prove façade wrappers return byte-for-byte equivalent outputs relative to canonical logic owner.

Status impact for retirement inventory:

- `build_provenance_metadata`: moved from **A keep temporarily** to **B migrated (wrapper retained)**.
- `collect_used_source_evidence_refs`: moved from **A keep temporarily** to **B migrated (wrapper retained)**.

Done vs Deferred (naming/responsibility truth):

- **Done:** established `testbot.logic.provenance` as the canonical owner for provenance assembly plus evidence-ref collection, and reduced façade ownership to compatibility wrappers.
- **Deferred:** reassess whether `build_provenance_metadata` is accurately named or should be renamed/split now that the seam is explicit, because current behavior includes evidence collection + provenance interpretation/summary (not only metadata serialization).

## 2026-03-28 update — answer contract constants canonicalization evidence

- Established canonical owner module: `testbot.answer_contract_constants`.
- Migrated duplicated answer/fallback literals to canonical imports in:
  - `testbot.sat_chatbot_memory_v2` (compatibility façade now re-exports canonical constants);
  - `testbot.logic.alignment` (contract checks now consume canonical constants);
  - `testbot.stage_transitions` (transition guards now consume canonical constants).

Status impact for retirement inventory:

- `ASSIST_ALTERNATIVES_ANSWER`: moved from **D decide later** to **B migrated (wrapper retained)**.
- `CLARIFY_ANSWER`: moved from **D decide later** to **B migrated (wrapper retained)**.
- `DENY_ANSWER`: moved from **D decide later** to **B migrated (wrapper retained)**.
- `FALLBACK_ANSWER`: moved from **D decide later** to **B migrated (wrapper retained)**.
- `NON_KNOWLEDGE_UNCERTAINTY_ANSWER`: moved from **D decide later** to **B migrated (wrapper retained)**.
- `ROUTE_TO_ASK_ANSWER`: moved from **D decide later** to **B migrated (wrapper retained)**.

Done vs Deferred:

- **Done:** canonicalized stable answer-stage contract strings under a single owner and reduced façade constants to compatibility export behavior.
- **Deferred:** broader answer-stage API cleanup (e.g., token-to-string mapping centralization and remaining façade call-site migration) remains tracked under ISSUE-0021 follow-on steps.

## 2026-03-28 update — runtime bootstrap ownership seam extraction evidence

- Established canonical bootstrap owner module: `testbot.entrypoints.runtime_bootstrap`.
- Extracted bootstrap ownership symbols:
  - `read_runtime_env`
  - `build_runtime_memory_store`
- Updated canonical CLI entrypoint (`testbot.entrypoints.cli`) to import these symbols directly from the bootstrap owner, reducing authority held by `entrypoints/runtime_legacy_bridge.py`.
- Kept compatibility behavior intact:
  - `testbot.sat_chatbot_memory_v2` façade exports now delegate to canonical bootstrap owner.
  - `testbot.entrypoints.runtime_legacy_bridge` wrappers still expose the same symbol names and deprecation warning behavior.

Status impact for retirement inventory:

- `read_runtime_env`: moved from **D decide later** to **B migrated (wrapper retained)**.
- `build_runtime_memory_store`: moved from **D decide later** to **B migrated (wrapper retained)**.

Done vs Deferred:

- **Done:** canonical bootstrap ownership is explicit under `entrypoints/runtime_bootstrap.py`, and bridge/façade ownership was reduced without behavioral broadening.
- **Deferred:** `run_chat_loop` and `sat_say` remain compatibility-owned by `runtime_legacy_bridge`/`sat_chatbot_memory_v2`; extracting those seams is intentionally out of scope for this narrow step.

## 2026-03-28 update — runtime loop ownership seam extraction evidence

- Established canonical runtime loop owner module: `testbot.entrypoints.runtime_loop`.
- Extracted canonical ownership symbols:
  - `run_chat_loop`
  - `sat_say`
- Updated canonical CLI entrypoint (`testbot.entrypoints.cli`) to import runtime loop symbols from `entrypoints/runtime_loop` directly, removing launch-path dependency on `entrypoints/runtime_legacy_bridge`.
- Reduced transitional bridge authority:
  - `testbot.entrypoints.runtime_legacy_bridge` now delegates loop/output wrappers to canonical `runtime_loop` owner while preserving deprecation warning behavior.
  - `testbot.entrypoints.runtime_legacy_bridge` remains compatibility-facing for transitional callers only.
- Added focused regression coverage for seam behavior:
  - canonical runtime loop owner delegates to compatibility façade implementation;
  - legacy bridge delegates to canonical runtime loop owner and still emits deprecation warning.

Status impact for retirement inventory:

- `run_chat_loop`: moved from **D decide later** to **B migrated (wrapper retained)**.
- `sat_say`: newly tracked as **B migrated (wrapper retained)** under runtime loop ownership.

Done vs Deferred:

- **Done:** stable runtime loop import surface now exists under `entrypoints/runtime_loop.py`, CLI runtime path is migrated to it, and bridge ownership is reduced.
- **Deferred:** full implementation extraction out of `sat_chatbot_memory_v2` into non-façade runtime services remains follow-on work; current step is ownership and wiring extraction only.

## 2026-03-28 update — Home Assistant satellite outbound transport extraction evidence

- Established canonical Home Assistant satellite outbound transport owner module:
  - `testbot.adapters.ha_satellite_output`
- Extracted HA transport implementation details:
  - `assist_satellite.start_conversation` service invocation
  - outbound payload details (`entity_id`, `start_message`, `preannounce=False`)
- Updated canonical runtime launch wiring:
  - `testbot.entrypoints.cli` now injects `send_satellite_output` directly into `run_satellite_mode(...)`.
- Reduced compatibility/legacy authority:
  - `testbot.entrypoints.runtime_loop.sat_say` now delegates to the HA satellite adapter owner (wrapper retained for compatibility import surface).
  - `testbot.sat_chatbot_memory_v2.sat_say` now delegates to the HA satellite adapter owner (compatibility façade wrapper retained).
- Added focused regression coverage:
  - adapter-level service call contract test for `send_satellite_output`;
  - runtime-loop `sat_say` wrapper delegation test to adapter;
  - CLI import/wiring expectation updated to canonical HA outbound adapter.

Status impact for retirement inventory:

- `sat_say`: remains **B migrated (wrapper retained)** with ownership narrowed further:
  - runtime/orchestration no longer owns HA outbound service details;
  - compatibility wrappers delegate to canonical adapter owner.

Done vs Deferred:

- **Done:** direct HA satellite output transport details are removed from runtime-loop/monolith ownership and placed under a narrow canonical adapter.
- **Deferred:** Ask-backed outbound output ownership design and full compatibility-wrapper retirement remain out of scope.

## 2026-03-28 follow-up — runtime loop ownership truth-alignment after HA outbound extraction

- Re-aligned runtime loop ownership wording to match post-extraction reality:
  - `testbot.entrypoints.runtime_loop` is the canonical runtime-loop import surface;
  - `run_chat_loop` remains a compatibility delegation seam into `sat_chatbot_memory_v2`;
  - satellite outbound transport ownership remains in `testbot.adapters.ha_satellite_output`.
- Reclassified `sat_say` as compatibility-only wrapper surface (not a primary architectural seam).
- Captured current caller census for wrapper retirement planning:
  - `testbot.entrypoints.runtime_loop.sat_say`: referenced by `testbot.entrypoints.runtime_legacy_bridge.sat_say` and runtime-loop delegation tests;
  - `testbot.sat_chatbot_memory_v2.sat_say`: no direct in-repo callers/importers found (compatibility façade export only).
- Confirmed Ask/transport boundary split from current in-repo evidence:
  - Ask-backed runtime interaction currently owns input/spec/channel-resolution concerns via `AskGateway`;
  - no canonical Ask-backed outbound satellite speaking API is currently evidenced in-repo.
- Confirmed next substantive extraction target:
  - `run_chat_loop` implementation still lives in `testbot.sat_chatbot_memory_v2` and remains the primary remaining runtime seam.

Status impact for retirement inventory:

- `sat_say`: remains **B migrated (wrapper retained)**, now explicitly tracked as compatibility-only wrapper over `send_satellite_output`.
- `run_chat_loop`: remains **B migrated (wrapper retained)**, with follow-up extraction prioritized as the next architectural step.

Done vs Deferred:

- **Done:** repository wording/evidence now reflects the resolved ownership split (adapter owns outbound transport, runtime_loop owns import seam only).
- **Deferred:** full extraction of `run_chat_loop` implementation out of `sat_chatbot_memory_v2` into canonical runtime-loop ownership, including future decisions on whether any outbound surface should be promoted under Ask-backed ownership.

## 2026-03-28 follow-up — telemetry/debug helper authority moved under canonical runtime entrypoint

- Established canonical loop-level telemetry/debug owner module:
  - `testbot.entrypoints.runtime_turn_telemetry`
- Updated canonical loop owner (`testbot.entrypoints.runtime_loop`) to call
  `emit_runtime_turn_telemetry(...)` instead of inlining telemetry/debug helper logic.
- Kept compatibility behavior stable:
  - runtime telemetry payload shaping and debug payload formatting implementations still delegate to
    `testbot.sat_chatbot_memory_v2` helper functions via dependency injection while retirement is in progress.
- Added anti-regression ownership guard in runtime-mode tests to enforce:
  - canonical runtime loop imports runtime turn telemetry entrypoint;
  - canonical runtime loop does not directly call monolith telemetry helper symbols.

Status impact for retirement inventory:

- Runtime loop telemetry/debug helper authority: moved from implicit monolith-inline coupling to **B migrated (wrapper retained)**.

Done vs Deferred:

- **Done:** canonical loop telemetry/debug assembly ownership now lives under an extracted `entrypoints` owner.
- **Deferred:** commit-persistence helper extraction and broader answer-stage/context-retrieval helper retirement remain
  follow-on work under ISSUE-0022 / ISSUE-0021.

## 2026-03-28 follow-up — runtime loop implementation extraction into canonical owner

- Moved the **actual runtime loop control-flow implementation** into `testbot.entrypoints.runtime_loop.run_chat_loop`.
  - The canonical owner now directly executes loop sequencing responsibilities: obligation polling/completion checks, user-input ingest/stop handling, turn-state initialization, canonical turn-pipeline invocation, loop-level telemetry emission, debug-trace emission, pending-ingestion registry updates, chat-history progression, and commit persistence dispatch.
- Reduced monolith runtime authority:
  - `testbot.sat_chatbot_memory_v2._run_chat_loop` is now a compatibility wrapper that delegates to `testbot.entrypoints.runtime_loop.run_chat_loop`.
  - `testbot.sat_chatbot_memory_v2.run_chat_loop` remains a compatibility export but no longer owns runtime-loop sequencing logic.
- Behavior-preservation basis:
  - The canonical loop implementation intentionally reuses existing stage/telemetry/persistence helpers from `sat_chatbot_memory_v2` (e.g., `_run_canonical_turn_pipeline`, `_process_background_ingestion_completion`, `answer_commit_persistence`) without changing their contract.
  - Focused regression tests cover loop stop/return control behavior at the new owner and verify the monolith wrapper delegates into the canonical runtime-loop owner.

Status impact for retirement inventory:

## 2026-03-28 follow-up — background-ingestion helper authority extraction into canonical entrypoint owner

- Established canonical runtime-owned background-ingestion entrypoint module:
  - `testbot.entrypoints.runtime_background_ingestion`
- Extracted background-ingestion dependency assembly used by runtime loop / turn-pipeline wiring:
  - `poll_pending_ingestion_obligations`
  - `process_background_ingestion_completion`
  - `poll_background_source_ingestion`
  - `start_background_source_ingestion`
  - plus shared dependency contract `RuntimeBackgroundIngestionDependencies`.
- Updated canonical runtime loop ownership path:
  - `testbot.entrypoints.runtime_loop.run_chat_loop` now calls canonical background-ingestion owner directly and wires
    retrieve-stage background start/poll hooks from that owner.
  - canonical loop no longer directly depends on monolith background-ingestion wrapper functions.
- Kept compatibility wrappers in place:
  - `testbot.sat_chatbot_memory_v2` background-ingestion helper wrappers now delegate into
    `testbot.entrypoints.runtime_background_ingestion`.
- Added regression guard for seam ownership:
  - runtime ownership test asserts `runtime_loop.py` imports canonical background-ingestion helper owner and does not call
    monolith `_poll_pending_ingestion_obligations` / `_process_background_ingestion_completion` helpers.

Done vs Deferred:

- **Done:** background-ingestion helper authority on the canonical runtime path moved from monolith wrappers to a canonical
  `entrypoints` owner while preserving compatibility wrappers.
- **Deferred:** telemetry/debug, answer-stage, and context/retrieval hook clusters are still primarily compatibility-wired and
  remain follow-on extraction candidates under ISSUE-0022 ranking.

- `run_chat_loop`: advanced from **B migrated (wrapper retained)** to **A keep temporarily (canonical owner active, compatibility export retained)**.

Done vs Deferred:

- **Done:** canonical runtime-loop owner now contains loop sequencing authority, and monolith delegation in the CLI runtime path is removed.
- **Deferred:** lower-level stage/telemetry helper extraction from `sat_chatbot_memory_v2` remains follow-on work so long as behavior contracts continue to rely on those helper boundaries.
- **Residual monolith authority after this step:** stage helper implementations, telemetry helper details, and compatibility export surface remain in `sat_chatbot_memory_v2`; the loop contract boundary itself now resides in `entrypoints/runtime_loop`.

## 2026-03-28 follow-up — runtime turn-pipeline dependency-assembly extraction into canonical runtime owner

- Established canonical runtime-owned turn-pipeline dependency assembly module:
  - `testbot.entrypoints.runtime_turn_pipeline`
  - exported symbols:
    - `RuntimeTurnPipelineHooks`
    - `run_runtime_turn_pipeline`
- Extracted dependency assembly authority from monolith helper:
  - `testbot.entrypoints.runtime_loop.run_chat_loop` now calls `run_runtime_turn_pipeline(...)`;
  - canonical loop no longer calls `testbot.sat_chatbot_memory_v2._run_canonical_turn_pipeline(...)`.
- Preserved compatibility behavior:
  - `testbot.sat_chatbot_memory_v2._run_canonical_turn_pipeline(...)` now delegates to the canonical helper.
- Added focused anti-regression guard:
  - runtime-mode test verifies `runtime_loop.py` uses canonical helper import and does not contain monolith helper call.
- Residual authority statement (explicit):
  - this step removes direct monolith ownership of the turn-pipeline dependency-assembly seam;
  - but `RuntimeTurnPipelineHooks` remains a large compatibility hook bag wired mostly from
    `testbot.sat_chatbot_memory_v2`, so helper-authority concentration is reduced but still significant.

Residual hook clusters captured for follow-on extraction sequencing:

- background-ingestion hooks;
- telemetry/debug hooks;
- answer-stage hooks;
- context/retrieval hooks.

Done vs Deferred:

- **Done:** runtime turn-pipeline dependency assembly is now canonically owned in `entrypoints`, materially reducing helper-level
  runtime authority concentration in `sat_chatbot_memory_v2` on the canonical loop path.
- **Deferred:** background-ingestion lifecycle helper extraction, telemetry/debug helper extraction, commit-persistence extraction,
  and broader compatibility façade retirement remain follow-on work under ISSUE-0021/ISSUE-0022.

## 2026-03-28 follow-up — commit-persistence extraction + post-telemetry residual authority ranking

- Established canonical runtime-owned commit-persistence module:
  - `testbot.entrypoints.runtime_commit_persistence`
  - exported symbols:
    - `RuntimeCommitPersistenceDependencies`
    - `answer_commit_persistence`
- Rewired canonical runtime loop commit call path:
  - `testbot.entrypoints.runtime_loop.run_chat_loop` now commits via
    `testbot.entrypoints.runtime_commit_persistence.answer_commit_persistence(...)`.
  - runtime-loop source no longer calls monolith `testbot.sat_chatbot_memory_v2.answer_commit_persistence(...)` directly.
- Preserved compatibility behavior:
  - `testbot.sat_chatbot_memory_v2.answer_commit_persistence(...)` is now a compatibility wrapper delegating to the canonical commit owner.
  - background-ingestion continuation path still receives commit persistence via callable injection, now targeting the canonical commit owner from the runtime loop.
- Added anti-regression guard:
  - runtime ownership test now asserts canonical runtime-loop imports the commit-persistence owner and does not directly call
    `_legacy_runtime.answer_commit_persistence(...)`.

Post-telemetry residual authority-density ranking refresh (runtime-loop path):

1. **answer-stage residual helpers** (highest remaining density):
   - still represented by a broad hook surface in `RuntimeTurnPipelineHooks`;
   - still dominated by compatibility-wired dependencies sourced from `sat_chatbot_memory_v2`.
2. **context/retrieval helpers** (second-highest):
   - still turn-critical and invoked every turn through the hook bag;
   - still mostly supplied by monolith-owned helper implementations.
3. **commit-persistence** (now reduced):
   - orchestration ownership moved to canonical `entrypoints` owner;
   - compatibility wrapper retained for façade continuity during retirement window.

Retirement leverage created by this step:

- Simplifies future façade retirement checks by isolating commit persistence behind a canonical owner module.
- Creates a narrower caller-census surface for determining when monolith `answer_commit_persistence` can move to compatibility-only/export-only status.
- Provides a concrete anti-regression assertion that helps prevent runtime-loop drift back to direct monolith commit helper calls.

## 2026-03-28 follow-up — answer-stage helper wiring moved to canonical answer-stage runtime owner

- Established canonical answer-stage turn-service wiring helpers under:
  - `testbot.application.services.answer_stage_runtime.answer_assemble_for_turn_service`
  - `testbot.application.services.answer_stage_runtime.answer_validate_for_turn_service`
  - `testbot.application.services.answer_stage_runtime.detect_capability_offer`
- Updated canonical runtime-loop hook assembly (`testbot.entrypoints.runtime_loop`) to source:
  - `resolve_answer_routing_for_stage`
  - `answer_assemble_for_turn_service`
  - `answer_validate_for_turn_service`
  - `detect_capability_offer`
  from `answer_stage_runtime` directly instead of `sat_chatbot_memory_v2` wrappers.
- Kept compatibility façade behavior stable:
  - `_answer_assemble_for_turn_service`, `_answer_validate_for_turn_service`, and `_detect_capability_offer`
    in `sat_chatbot_memory_v2` now delegate to canonical answer-stage runtime service helpers.
- Added anti-regression tests:
  - runtime-loop ownership guard for answer-stage helper sourcing;
  - compatibility-wrapper delegation assertions for extracted answer-stage helpers.

Status impact for retirement inventory:

- answer-stage helper wiring (`_answer_assemble_for_turn_service`, `_answer_validate_for_turn_service`, `_detect_capability_offer`):
  moved from compatibility-owned authority to **B migrated (wrapper retained)**.

Done vs Deferred:

- **Done:** canonical runtime path no longer sources answer-stage turn-service adapter hooks from monolith wrappers.
- **Deferred:** broader compatibility façade prune and context/retrieval helper extraction remain tracked follow-on work.

## 2026-03-28 follow-up — post-PR-681 pre-merge investigation census refresh

Investigation-only refresh (no additional runtime behavior changes):

- `answer_stage_runtime` coherence check:
  - module remains primarily answer-stage semantic owner;
  - newly extracted turn-service adapters are narrow boundary shims and do not yet justify internal owner split.
- Canonical runtime-path monolith touchpoints after PR-681:
  - answer-stage hook sourcing moved to canonical owner (`answer_stage_runtime`);
  - residual monolith density remains concentrated in context/retrieval and related runtime hook wiring.
- Façade caller census refresh:
  - authoritative runtime path remains migrated to canonical entrypoint owners;
  - remaining `sat_chatbot_memory_v2` / `runtime_legacy_bridge` imports are predominantly compatibility and test surfaces.
- Next anti-regression guard recommendation:
  - add a deterministic allowlist-based ownership test for monolith helper symbols referenced by `entrypoints/runtime_loop.py`
    so any new monolith touchpoint requires explicit review.

Status impact:

- answer-stage helper extraction remains validated as a meaningful density reduction.
- next highest-leverage extraction seam remains context/retrieval helper wiring.
