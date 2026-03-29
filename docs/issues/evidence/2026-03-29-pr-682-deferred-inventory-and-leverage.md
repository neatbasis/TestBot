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

## 2026-03-29 residual authority decomposition — `stage_rerank` post-#686 refresh

### Post-#686 reality check (runtime-facing seam ownership)

- #686 processed the prior rank-1 target-time slice: `stage_rerank(...)` now delegates target-time parsing/override
  resolution to runtime-owned `resolve_rerank_target_time(...)`.
- #686 did **not** extract scorer invocation policy assembly, confidence/telemetry shaping, or wrapper retirement.
- Therefore the residual map below starts at the next coherent scorer-adjacent slice, not at target-time policy.

### Residual monolith-owned rerank slices after #686

| Rank (leverage-to-scope) | Residual slice | Current responsibility + owner/path | Why this is / is not best next move | Best candidate future owner | Compatibility posture after extraction | Wrapper-removal readiness criterion | Evidence required to close slice |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **Scorer invocation policy assembly** (`adaptive_sigma_fractional`, scorer call contract, exclusion wiring) | `sat_chatbot_memory_v2.stage_rerank(...)` still computes `sigma`, assembles rerank scorer arguments (`top_k`, `near_tie_delta`, `exclude_doc_ids`, `exclude_source_ids`), and invokes `rerank_docs_with_time_and_type_outcome(...)`. | **Best next move:** highest leverage-to-scope ratio now that target-time policy already moved; this is the next bounded propagation point adjacent to runtime seam ownership without changing scorer internals. | Runtime seam owner helper (for example `build_rerank_invocation(...)` in `context_retrieval_runtime`) returning normalized scorer inputs/contract. | Keep scorer implementation compatibility-owned; monolith may call scorer until invocation contract authority fully shifts to runtime seam. | Wrapper is not removable yet; readiness improves only after invocation assembly and confidence projection are both runtime-owned. | Deterministic tests for exclusion-set assembly and `top_k`/`near_tie_delta` defaults, plus seam-level tests proving canonical runtime path sources invocation contract from runtime-owned helper. |
| 2 | **Rerank threshold/profile policy surface** (`rerank_confidence_thresholds()` values and how they are projected into rerank decision payload) | `stage_rerank(...)` currently reads threshold/profile values and writes them into `confidence_decision` fields (for example `top_final_score_min`, `min_margin_to_second`, ambiguity override toggles). | **Not best immediate move alone:** meaningful but tightly coupled to confidence projection shape; extracting this before projection would split one policy surface across owners and reduce clarity. | Runtime-owned projection helper that owns threshold/profile read + payload placement together (or a dedicated runtime-owned threshold profile adapter consumed by projection helper). | Preserve field names and semantics for downstream consumers until schema migration is explicitly planned. | Wrapper posture unchanged until confidence payload projection moves with threshold mapping semantics. | Golden-shape tests asserting exact threshold/profile fields in `confidence_decision`, plus backward-compat checks for debug payload consumers. |
| 3 | **Confidence-decision projection / telemetry shaping** (construction of post-rerank `confidence_decision` payload) | Monolith still projects rerank outcome, temporal bridge fields, objective metadata, and threshold values into one dict payload. | **Medium leverage:** strong anti-backslide value but broader blast radius due many downstream consumers; should follow scorer invocation extraction or be combined with threshold/profile extraction in one bounded PR. | Runtime seam owner projection helper (for example `project_rerank_confidence_decision(...)`) with strict schema-preservation contract. | Keep compatibility delegation active while payload shape remains externally consumed; migration must be schema-first and evidence-backed. | Wrapper not removable until this projection authority is runtime-owned and call sites prove no monolith-only fields remain. | Golden payload snapshot tests + structured debug payload compatibility tests + stage-transition/invariant checks under canonical runtime path. |
| 4 | **Residual wrapper posture** (`_stage_rerank_for_turn_service` forwarding through monolith `stage_rerank`) | Compatibility wrapper remains because substantive rerank authority still exists inside monolith stage helper. | **Not a best-next move:** low leverage now; removing wrapper before slices 1–3 complete would hide residual authority instead of retiring it. | Final owner should be runtime service path only, with monolith wrapper downgraded to deprecated shim then removed. | Require explicit deprecation window and caller census before removal. | Removable only when: (a) canonical runtime path no longer needs monolith rerank authority, and (b) in-repo + compatibility inventories show zero required wrapper consumers. | Caller census, import allowlist contraction, seam tests proving runtime-only path equivalence, and deprecation/removal evidence PR. |

### Ranked next-step candidates (post-#686)

1. **Scorer invocation policy assembly** (best leverage-to-scope ratio).
2. **Confidence projection + threshold/profile co-extraction** (second-best, if kept schema-preserving and bounded).
3. **Wrapper retirement** (last, only after residual rerank authority is already moved).

### Recommended next bounded extraction target

**Recommended next target: Rank 1 — scorer invocation policy assembly.**

- What should move next: invocation contract authority (`sigma`, exclusions, `top_k`, near-tie inputs) behind runtime-facing seam ownership.
- What should not move yet: full confidence payload projection and wrapper retirement in the same PR (deferred deeper extraction to preserve bounded propagation).

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
