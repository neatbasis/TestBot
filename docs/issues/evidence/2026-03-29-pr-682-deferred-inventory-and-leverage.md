# PR #682 post-merge deferred inventory and leverage note

- **Date:** 2026-03-29
- **Related Issue:** ISSUE-0022
- **Related PR:** [#682](https://github.com/neatbasis/TestBot/pull/682)
- **Scope:** post-merge inventory for deferred surfaces and leverage now available after runtime-facing context/retrieval seam extraction.
- **Planning posture:** current best synthesis of intended ownership direction; provisional target model subject to refinement as semantic boundaries are clarified.

## What PR #682 bought

PR #682 moved runtime-facing context/retrieval hook wiring to a canonical runtime-owned service and rewired
`entrypoints/runtime_loop.py` to source seam hooks from that owner. This raised confidence that the canonical
runtime loop now owns the hook-binding surface for this seam, while preserving behavior via compatibility
wrappers.

Owned surfaces captured by the change:

- identity-recall forced-retrieval helper wiring;
- retrieval input/document conversion adapters;
- turn-service retrieve/rerank adapter wiring;
- runtime loop hook-binding control point for the seam.

## Deferred inventory with dual-view planning (near-term + ideal future state)

| Deferred item | Current deferred state | Leverage available now | Best next narrow delta | Ideal future state | Blocking uncertainty | Evidence required for completion |
| --- | --- | --- | --- | --- | --- | --- |
| Retrieval policy-core | Runtime-facing retrieve adapter path is canonicalized, but retrieval policy-core remains monolith-owned. | Canonical runtime hook control point exists; compatibility delegation and anti-backslide posture already established. | Extract the smallest coherent retrieval policy-core authority behind the canonical seam. | Retrieval policy-core is canonically owned outside `sat_chatbot_memory_v2`; runtime adapters no longer inject monolith retrieval policy logic for canonical flow. | Which retrieval decision sub-slice can move first without broad policy coupling churn. | Runtime-loop ownership assertions + canonical retrieval-policy tests + reduced monolith allowlist entries showing no canonical-path retrieval policy ownership. |
| Rerank / temporal policy-core | Rerank adapter path is canonicalized, but rerank/temporal policy-core remains legacy-owned. | Same seam family as retrieval with the same runtime control-point leverage. | Move the smallest rerank policy authority slice that does not require full temporal redesign. | Canonical rerank/temporal policy decisions for canonical runtime path are owned outside monolith with explicit bounded adapters. | Exact seam split between rerank scoring policy and temporal bridge helpers. | Canonical rerank owner tests, runtime hook assertions, and explicit monolith touchpoint contraction for rerank semantics. |
| `resolve_context` semantic ownership | Runtime sourcing is canonicalized, but full semantic ownership may not yet be in final stable owner boundary. | Context-resolution call surface is now visible and testable through canonical hook owner. | Run ownership audit separating call-surface ownership from semantic ownership and relocate residual semantics if needed. | `resolve_context` has one justified semantic owner; runtime service depends on that owner intentionally (not pseudo-ownership forwarding ambiguity). | Whether residual downstream assumptions still imply hidden legacy semantic authority. | Ownership audit artifact + targeted semantic tests + dependency assertions proving intentional owner boundary. |
| Monolith retirement / wrapper downgrade | Monolith runtime authority is reduced but still present; compatibility wrappers remain. | Wrapper delegation is explicit and tested; allowlist already narrowed. | Define per-wrapper expiry/removal criteria and shrink allowlist in lockstep with each seam extraction. | `sat_chatbot_memory_v2` no longer owns canonical runtime behavior for extracted seams; wrappers are removed or reduced to clearly temporary stubs. | External/non-repo callers for some compatibility wrappers may still exist. | Compatibility inventory refresh, allowlist shrink diffs, deprecation/expiry markers, and wrapper-removal PR evidence when thresholds are met. |
| Broader suite failures outside seam | Pre-existing broader readiness failures remain and were not introduced by #682. | Seam extractions can proceed with narrow evidence so long as failures are kept categorically separate. | Keep separation unless a specific failing suite item becomes a direct blocker for seam extraction. | Seam extraction evidence and broader readiness debt are independently tracked; blockers are explicit rather than ambient. | Which failing scenarios, if any, directly block next seam extraction proof. | Gate reports showing explicit failure attribution and issue links for broader-suite remediation outside seam PR scope. |

## Ideal future state synthesis

Deferred items are not a queue of leftovers; they converge toward a runtime re-ownership end-state where:

- runtime-facing context/retrieval authority is fully owned by canonical runtime-aligned modules;
- deeper retrieval and rerank semantics are no longer monolith-owned for canonical execution paths;
- context-resolution semantic ownership is explicit and stable;
- compatibility wrappers have tracked expiry and are retired rather than normalized;
- residual monolith authority is unnecessary for canonical runtime execution.

This is the **idealized planning end-state** for convergence, not a requirement to complete all moves in one PR.

## Best next deltas (ordered by leverage)

1. **Retrieval policy-core first**: the next narrow delta is retrieval policy-core extraction because the runtime seam
   control point, compatibility delegation path, and anti-backslide scaffolding already exist.
2. **Rerank/temporal policy-core second**: the next narrow delta is adjacent rerank authority extraction because it
   shares seam mechanics and control-point leverage with retrieval.
3. **Wrapper retirement criteria tightening**: the next narrow delta is explicit expiry/removal criteria because
   wrappers are useful now but become camouflage if unbounded.
4. **Pattern templating**: the next narrow delta is codifying this extraction method as a repeatable checklist because
   it keeps future increments bounded while preserving end-state convergence.

## Strongest summary

- **Deferred now:** retrieval policy-core; rerank/temporal policy-core; full `resolve_context` semantic ownership audit;
  wrapper retirement completion; broader non-seam readiness debt.
- **Leverage now:** one canonical runtime hook control point; anti-backslide assertions; behavior-preserving staged
  extraction path; clearer extraction claim language.
- **Directional target:** incremental deltas continue, but each move must also reduce monolith semantic ownership and
  increase proof that canonical runtime execution no longer depends on monolith authority for extracted seams.

## 2026-03-29 execution update — bounded retrieval policy-core slice processed

- Processed deferred row: **Retrieval policy-core**.
- Bounded delta: extracted retrieval filter normalization + store-query branching (`search_memory_records` vs
  `similarity_search_with_score`) into canonical runtime-owned
  `testbot.application.services.context_retrieval_runtime`.
- Remaining deferred within the same row: retrieval candidate mixing/ranking semantics and broader retrieval policy
  decisions still remain compatibility-owned in `sat_chatbot_memory_v2` pending additional bounded extractions.

## 2026-03-29 execution update — bounded rerank/temporal policy-core slice processed

- Processed deferred row: **Rerank / temporal policy-core**.
- Bounded delta: extracted temporal anaphora-bridge construction and temporal-window filtering authority from
  `sat_chatbot_memory_v2.stage_rerank` into canonical runtime-owned
  `testbot.application.services.context_retrieval_runtime`
  (`resolve_temporal_anaphora_bridge`, `filter_documents_for_temporal_window`), with monolith stage-rerank now
  delegating through the canonical seam owner.
- Remaining deferred within the same row: rerank scoring objective/threshold policy, time-target parsing policy,
  and broader temporal decision semantics still remain compatibility-owned in `sat_chatbot_memory_v2` pending
  deeper bounded extractions.

## 2026-03-29 residual authority decomposition — `stage_rerank` after #685

### Residual monolith-owned slices inside `sat_chatbot_memory_v2.stage_rerank`

| Rank (leverage → scope) | Residual slice | Current owner/path | Why leverage is high now | Bounded extraction candidate | Wrapper-removal criterion | Required evidence to close slice |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **Target override + target parsing resolution policy** (`parse_target_time`, anchor override application, fallback when override parse fails) | Monolith `stage_rerank` still owns target construction before calling rerank scorer. | Temporal bridge/window is already runtime-owned, so target resolution is now the smallest adjacent decision seam with low blast radius and high control-point reuse. | Add a runtime-owned `resolve_rerank_target_time(...)` helper that consumes utterance + bridge + now and returns target + telemetry fields. | Remove monolith-side target override branch when runtime helper is the only canonical caller for target derivation in runtime loop path. | Unit tests for target precedence (bridge override > parsed utterance > now baseline), invalid override fallback behavior, and runtime-loop hook-path assertion that canonical flow no longer relies on monolith target-resolution branch. |
| 2 | **Rerank scoring invocation policy assembly** (`adaptive_sigma_fractional`, scorer call arguments, top_k/near_tie/exclusion wiring) | Monolith assembles scorer invocation contract in `stage_rerank`. | After target-resolution extraction, scorer invocation assembly becomes isolated and testable without moving scorer implementation itself. | Add runtime-owned `build_rerank_invocation(...)` (or equivalent) that returns normalized scorer inputs; keep scorer function unchanged. | Monolith wrapper can drop scorer-parameter assembly once canonical seam owner computes the invocation contract and monolith only forwards to scorer or receives already-scored outcome. | Deterministic tests on exclusion-set construction and top_k/near_tie defaults, plus seam tests proving canonical runtime path sources invocation parameters from runtime owner. |
| 3 | **Confidence-decision projection / telemetry shaping** (construction of `confidence_decision` payload fields from rerank outcome + temporal fields) | Monolith formats confidence payload and writes policy-shaping fields. | Medium leverage: valuable anti-backslide signal, but coupled to policy vocabulary and downstream expectations. | Extract runtime-owned `project_rerank_confidence_decision(...)` while preserving field schema exactly. | Remove monolith payload-construction block only when schema conformance and debug-payload consumers validate against runtime-owned projection path. | Golden-shape tests for confidence payload keys/values, compatibility tests for structured debug payload consumers, and invariant/post-stage transition checks passing under canonical path. |
| 4 | **Residual wrapper posture** (`_stage_rerank_for_turn_service` forwarding `stage_rerank_fn=stage_rerank`) | Compatibility wrapper remains in monolith module. | Lowest immediate leverage until slices 1–3 move, because wrapper still fronts legitimate residual authority. | Convert wrapper to thin deprecated shim after residual slices migrate; eventually remove. | Remove wrapper only when no in-repo call sites require monolith export and compatibility inventory shows no external blocker (or expiry accepted). | Caller census showing zero canonical-path dependencies, allowlist contraction diff, and deprecation/removal PR with green targeted seam tests. |

### Recommended next bounded extraction target

**Next target: Rank 1 — target override + target parsing resolution policy.**

This is the highest leverage-to-scope step because it sits directly adjacent to the already-extracted temporal bridge/window helpers, uses the same runtime-facing seam ownership boundary, and avoids entangling scorer internals or confidence schema concerns.

### Explicit bounded claim posture for that next step

- **What it should prove:** canonical runtime path no longer sources target-resolution authority from monolith `stage_rerank`.
- **What it should not claim yet:** full rerank policy-core extraction or wrapper retirement.
- **Compatibility delegation posture to keep:** monolith may still host scorer invocation and confidence projection until their dedicated bounded steps.

## 2026-03-29 execution update — bounded rerank target-time resolution slice processed

- Processed deferred row: **Rank 1 rerank residual — target override + target parsing resolution policy**.
- Bounded delta: extracted `resolve_rerank_target_time(...)` into canonical runtime-owned
  `testbot.application.services.context_retrieval_runtime`, and rewired `sat_chatbot_memory_v2.stage_rerank(...)`
  to delegate target-time resolution through the runtime-facing seam owner.
- Behavior-preservation evidence added:
  - explicit target override precedence when bridge override parses cleanly;
  - invalid override fallback to parsed utterance target-time;
  - compatibility wrapper proof that monolith `stage_rerank(...)` now calls runtime-owned target-time resolver.
- Remaining deferred rerank slices are unchanged: scorer invocation policy assembly, confidence-decision projection,
  and residual wrapper retirement.
