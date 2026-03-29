# ISSUE-0022: Residual runtime helper authority inventory after loop-owner extraction

- **ID:** ISSUE-0022
- **Title:** Residual runtime helper authority inventory after loop-owner extraction
- **Status:** open
- **Issue State:** governed_execution
- **Severity:** amber
- **Owner:** runtime-pipeline
- **Created:** 2026-03-28
- **Target Sprint:** Sprint 6
- **Canonical Cross-Reference:** ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md, ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md
- **Principle Alignment:** contract-first, invariant-driven, deterministic, traceable, ci-enforced

## Problem Statement

`testbot.entrypoints.runtime_loop.run_chat_loop` is now the canonical loop sequencing owner, but helper-level runtime authority remains concentrated behind compatibility delegation in `testbot.sat_chatbot_memory_v2`. Without a residual-authority inventory and explicit ranking, follow-up extraction can regress into utility-motion instead of authority retirement.

## Evidence

- Runtime-loop seam extraction evidence was recorded under ISSUE-0021 with `entrypoints/runtime_loop.py` declared as loop-owner and `runtime_legacy_bridge` narrowed to compatibility-facing delegation.
- Current loop owner still depends on compatibility delegation into helper-level monolith behavior (`sat_chatbot_memory_v2`) for pipeline invocation, telemetry/debug emission, pending-ingestion update handling, commit persistence dispatch, and runtime turn-bridge surfaces.
- Focused runtime-loop regression coverage currently protects short-circuit and delegation behavior but does not yet enforce a residual-helper authority ranking contract.

## Impact

- Residual authority ambiguity can re-introduce split ownership across runtime loop and compatibility monolith layers.
- Future extraction PRs may optimize line movement while leaving policy authority concentrated in legacy helpers.
- Reviewers lose a deterministic rubric for choosing the next seam by ownership impact.

## Acceptance Criteria

- [ ] Residual helper-level runtime authorities reachable from `entrypoints/runtime_loop` are enumerated with file-level symbol references and responsibility statements.
- [ ] The inventory includes authority-density ranking with explicit justification for top seam selection.
- [ ] A successor implementation issue is opened (or this issue is updated) for exactly one highest-leverage seam extraction.
- [ ] A deterministic anti-regression guard is added (test or validator assertion) that prevents monolith re-ownership of loop sequencing.
- [ ] Closure evidence includes governance validator success and canonical gate status (including explicit treatment of unrelated pre-existing failures when present).

## Work Plan

1. Build a residual-authority table for helper clusters currently delegated from `entrypoints/runtime_loop`.
2. Rank helper clusters by authority density (policy ownership concentration, cross-cutting blast radius, and ambiguity reduction potential).
3. Select one top-ranked helper cluster and define the narrow extraction boundary for the next PR.
4. Add an anti-regression contract asserting loop sequencing remains owned by `entrypoints/runtime_loop`.
5. Execute targeted extraction PR with focused tests and update ISSUE-0021/ISSUE-0013 cross-links.

## Verification

```bash
python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
python scripts/validate_issues.py --all-issue-files --base-ref origin/main
python scripts/all_green_gate.py
```

## Closure Notes

This issue remains open; the update below records the completed narrow extraction increment and explicit deferrals.

## 2026-03-28 update — turn-pipeline dependency-assembly seam extraction (narrow)

- Extracted canonical runtime-owned dependency-assembly helper:
  - `testbot.entrypoints.runtime_turn_pipeline.run_runtime_turn_pipeline`
  - hook contract: `RuntimeTurnPipelineHooks`
- Rewired canonical loop owner:
  - `testbot.entrypoints.runtime_loop.run_chat_loop` now invokes `run_runtime_turn_pipeline(...)` and no longer calls
    `testbot.sat_chatbot_memory_v2._run_canonical_turn_pipeline(...)`.
- Compatibility kept:
  - `testbot.sat_chatbot_memory_v2._run_canonical_turn_pipeline(...)` now delegates to
    `testbot.entrypoints.runtime_turn_pipeline.run_runtime_turn_pipeline(...)`.
- Added focused anti-regression guard:
  - runtime-mode test asserts `runtime_loop.py` imports canonical runtime turn-pipeline helper and does not call monolith
    `_run_canonical_turn_pipeline(...)`.
- Residual authority shape (explicit):
  - this extraction removes direct monolith ownership of the turn-pipeline assembly seam;
  - however `RuntimeTurnPipelineHooks` still carries a large compatibility hook bag wired primarily from
    `testbot.sat_chatbot_memory_v2`, so helper-authority density remains concentrated behind that compatibility surface.

Residual hook clusters for next-step prioritization:

- background-ingestion hooks (`poll/start/process` continuation surfaces);
- telemetry/debug hooks (session-log and structured debug payload surfaces);
- answer-stage hooks (assemble/validate + decision projection helpers);
- context/retrieval hooks (context resolve + retrieve/rerank + conversion helpers).

Done vs Deferred:

- **Done:** runtime turn-pipeline dependency assembly is now canonically owned under `entrypoints` and loop wiring no longer
  depends on monolith turn-pipeline helper calls.
- **Deferred:** background-ingestion lifecycle helpers, telemetry/debug helper extraction, and commit-persistence extraction remain
  explicitly out of scope for this narrow step.

## 2026-03-28 update — background-ingestion helper cluster extraction (narrow)

- Extracted canonical runtime-owned background-ingestion dependency-assembly helper:
  - `testbot.entrypoints.runtime_background_ingestion`
  - dependency contract: `RuntimeBackgroundIngestionDependencies`
- Rewired canonical runtime loop owner:
  - `testbot.entrypoints.runtime_loop.run_chat_loop` now calls canonical background-ingestion helpers for:
    - pending obligation polling
    - completion processing continuation
    - turn-pipeline retrieval-stage start/poll hook wiring
  - canonical loop no longer directly calls background-ingestion helper wrappers from `testbot.sat_chatbot_memory_v2`.
- Compatibility kept:
  - `testbot.sat_chatbot_memory_v2` background-ingestion wrappers now delegate to
    `testbot.entrypoints.runtime_background_ingestion`.
- Added focused anti-regression guard:
  - runtime-mode ownership test now asserts `runtime_loop.py` imports the canonical background-ingestion entrypoint and
    does not call monolith background-ingestion wrappers.

Done vs Deferred:

- **Done:** background-ingestion helper authority used by canonical loop + turn-pipeline hook wiring is now canonically
  assembled under `entrypoints/runtime_background_ingestion.py`.
- **Deferred:** telemetry/debug hooks, answer-stage hooks, and context/retrieval hooks remain compatibility-wired through
  `sat_chatbot_memory_v2` and are explicitly out of scope for this narrow extraction.

## 2026-03-28 update — telemetry/debug helper cluster extraction (narrow)

- Extracted canonical runtime-owned turn telemetry/debug helper:
  - `testbot.entrypoints.runtime_turn_telemetry`
  - dependency contract: `RuntimeTurnTelemetryDependencies`
- Rewired canonical runtime loop owner:
  - `testbot.entrypoints.runtime_loop.run_chat_loop` now delegates loop-level telemetry/debug emission to
    `emit_runtime_turn_telemetry(...)`.
  - canonical loop no longer inlines fallback/provenance/alignment telemetry payload assembly and debug-trace emission
    logic.
- Compatibility kept:
  - telemetry payload formatting + debug payload generation implementations still come from compatibility helpers in
    `testbot.sat_chatbot_memory_v2` via dependency injection.
- Added focused anti-regression guard:
  - runtime-mode ownership test now asserts `runtime_loop.py` imports canonical runtime turn-telemetry helper and does
    not directly call monolith telemetry/debug helper functions.

Done vs Deferred:

- **Done:** loop-level telemetry/debug helper authority is canonically assembled under
  `entrypoints/runtime_turn_telemetry.py`, reducing in-loop helper authority concentration.
- **Deferred:** commit-persistence helper extraction and answer-stage/context-retrieval helper extraction remain
  compatibility-wired through `sat_chatbot_memory_v2` and are intentionally out of scope for this narrow step.

## 2026-03-28 update — answer-stage residual helper wiring extraction (narrow)

- Extracted canonical answer-stage turn-service adapters into canonical owner module:
  - `testbot.application.services.answer_stage_runtime.answer_assemble_for_turn_service`
  - `testbot.application.services.answer_stage_runtime.answer_validate_for_turn_service`
  - `testbot.application.services.answer_stage_runtime.detect_capability_offer`
- Rewired canonical runtime loop owner:
  - `testbot.entrypoints.runtime_loop.run_chat_loop` now wires answer-stage hooks in
    `RuntimeTurnPipelineHooks` from `answer_stage_runtime` directly for:
    - answer routing for stage
    - answer assemble adapter
    - answer validate adapter
    - capability-offer detection
  - canonical loop no longer sources those answer-stage helper hooks from
    `testbot.sat_chatbot_memory_v2`.
- Compatibility kept:
  - `testbot.sat_chatbot_memory_v2` wrappers
    `_answer_assemble_for_turn_service`, `_answer_validate_for_turn_service`, and
    `_detect_capability_offer` now delegate to canonical
    `answer_stage_runtime` helpers.
- Added focused anti-regression coverage:
  - runtime-mode ownership guard asserts runtime loop imports canonical answer-stage service owner and does not reference monolith answer-stage helper symbols;
  - compatibility wrapper tests assert monolith wrappers delegate to
    canonical answer-stage runtime helpers.

Done vs Deferred:

- **Done:** answer-stage hook authority on the canonical runtime path is now sourced from
  `application/services/answer_stage_runtime.py` rather than monolith helper wrappers.
- **Deferred:** context/retrieval hook extraction and remaining legacy helper pruning are out of scope for this narrow seam.

## 2026-03-28 pre-merge investigation update — post-PR-681 ownership shape and next seam selection

Post-681 investigation summary (narrow, no additional runtime behavior changes):

- `answer_stage_runtime` coherence after answer-stage extraction:
  - **semantic owner surface remains coherent** (`answer_assemble`, `answer_validate`, answer-mode/routing/format helpers);
  - newly added turn-service adapters (`answer_assemble_for_turn_service`, `answer_validate_for_turn_service`) and
    `detect_capability_offer` are currently small boundary helpers directly tied to answer-stage contract assembly;
  - extraction did not introduce a broad new “misc glue” bucket; defer any internal split until additional non-answer-stage
    adapters accumulate.
- residual monolith touchpoints on canonical runtime path after PR-681:
  - answer-stage helper hooks are now sourced from `answer_stage_runtime` in `runtime_loop` hook assembly;
  - highest remaining monolith density in `runtime_loop` hook/dependency wiring is now context/retrieval and related
    conversion/policy-prep helpers (`resolve_context`, retrieve/rerank adapters, decision projection helpers, conversion utilities).
- next residual-cluster ranking refresh:
  1. context/retrieval helper wiring (highest remaining authority density on canonical path)
  2. loop state/obligation helper details still wired through compatibility helpers
  3. smaller residual conversion/helper touchpoints
- recommended smallest next anti-regression guard:
  - add an ownership inventory assertion for `runtime_loop` that enumerates the currently allowed monolith helper symbols and
    fails on additions (explicit allowlist guard prevents “silent” hook-bag backsliding).
- guard implementation status:
  - **implemented in tests** via a deterministic allowlist assertion for `_legacy_runtime.<symbol>` touchpoints in
    `tests/test_runtime_modes.py`; future extractions should shrink the allowlist deliberately.

Done vs Deferred (investigation pass):

- **Done:** post-681 residual authority ranking and canonical-path touchpoint inventory were refreshed for next-step selection.
- **Deferred:** implementing context/retrieval extraction and allowlist guard hardening is intentionally left to the next narrow PR.

## 2026-03-29 update — context/retrieval helper wiring seam extraction (narrow)

Seam inventory (before → after):

- Context/retrieval helper hooks still sourced from monolith in canonical runtime-loop wiring:
  - `_should_force_memory_retrieval_for_identity_recall`
  - `resolve_context`
  - `_stage_retrieve_for_turn_service`
  - `_stage_rerank_for_turn_service`
  - `_document_from_retrieval_input`
- New canonical owner for this seam:
  - `testbot.application.services.context_retrieval_runtime`
  - authoritative hook functions now sourced in `entrypoints/runtime_loop.py` from that module.
- Compatibility posture:
  - corresponding monolith helpers now remain as thin wrappers delegating to canonical context/retrieval runtime helpers.
  - follow-up completion in this PR head also wraps monolith `resolve_context` as an explicit compatibility shim into the
    canonical context/retrieval runtime owner (instead of a direct domain import alias), so the seam boundary is explicit at
    the compatibility surface.

Ask-boundary contract posture:

- This seam extraction did not add new Ask-internal coupling.
- Runtime-loop hook rewiring remains constrained to canonical runtime/service surfaces and does not introduce dependency on
  demo-only or non-canonical Ask internals.

Anti-backslide hardening:

- Runtime ownership assertions now require `runtime_loop.py` to import canonical
  `context_retrieval_runtime` and disallow monolith-owned context/retrieval helper symbol usage in loop wiring.
- Monolith-touchpoint allowlist was intentionally narrowed for this seam (removed legacy helper symbols replaced by the
  canonical owner).
- Added focused compatibility wrapper tests to ensure monolith wrappers delegate to canonical context/retrieval runtime
  helpers rather than owning logic inline.
- Added explicit residual-seam ownership assertions for runtime loop wiring:
  - remaining legacy touchpoints for this seam are constrained to `stage_retrieve` / `stage_rerank` policy-core call sites only;
  - legacy `resolve_context`, forced-retrieval helper, turn-service adapter wrappers, and retrieval conversion wrappers are
    asserted as non-runtime-loop dependencies.
- Added direct canonical-owner tests for `context_retrieval_runtime` to verify seam-owned behavior and adapter conversion logic
  independent of monolith wrappers.

Done vs Deferred:

- **Done:** context/retrieval hook wiring authority on the canonical runtime path moved to
  `application/services/context_retrieval_runtime.py`; runtime-loop monolith touchpoints narrowed.
  This is a runtime-facing seam/control-point extraction (wiring authority), not full retrieval/rerank policy-core semantic extraction.
- **Deferred (explicit residual seam elements):**
  - monolith `stage_retrieve(...)` policy/core retrieval implementation;
  - monolith `stage_rerank(...)` policy/core rerank + temporal-bridge implementation;
  - supporting rerank-temporal helper internals coupled to that policy core.
  These remain intentionally deferred because this increment is scoped to runtime wiring/adapters and compatibility-surface
  ownership, not retrieval/rerank policy-core redesign.

## 2026-03-29 post-merge inventory addendum — PR #682 deferred scope + leverage

A structured post-merge inventory note for PR #682 has been added to preserve explicit deferred surfaces and
next-step leverage framing:

- `docs/issues/evidence/2026-03-29-pr-682-deferred-inventory-and-leverage.md`

This addendum intentionally does not broaden implementation scope; it consolidates planning evidence for the
next highest-leverage extraction steps (retrieval policy-core first, rerank/temporal policy-core next) while
adding explicit ideal-future-state synthesis so deferred items are tracked as a convergent re-ownership program
rather than a queue of leftovers.
