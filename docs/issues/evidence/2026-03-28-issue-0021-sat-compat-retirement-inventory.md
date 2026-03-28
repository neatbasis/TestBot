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
