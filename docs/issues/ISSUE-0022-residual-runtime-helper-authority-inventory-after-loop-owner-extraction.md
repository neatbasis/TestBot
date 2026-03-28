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
