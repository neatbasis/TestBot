# PR #693 scorer-category debt decomposition (ISSUE-0022)

- **Date:** 2026-03-29
- **Selected unit type:** category debt decomposition (not a deferred row)
- **Anchor:** staged rerank wrapper-retirement rows are complete; scorer-category redesign/internals remain deferred category debt.
- **Scope posture:** decision-grade decomposition + bounded next-slice recommendation only; no broad scorer redesign.

## Why the unit type is category debt decomposition now

The wrapper-retirement row program is complete, so there is no remaining row-sized rerank wrapper action to execute. The remaining work is scorer-category debt with multiple ownership surfaces, which requires subcategory decomposition and slice selection before execution.

- Evidence X supports claim Y because Z: `ISSUE-0022` evidence declares wrapper-row completion and names scorer-category debt as the residual scope, so the next useful unit is category decomposition rather than another row execution.
- It does not yet support stronger claim W because Q: wrapper-row completion alone does not identify the smallest safe scorer slice; decomposition is still required.

## Current scorer-category authority map (post-#692)

### Runtime/control-point relationship

1. `stage_rerank(...)` in `sat_chatbot_memory_v2.py` is still the execution choke point that invokes scorer behavior (`rerank_docs_with_time_and_type_outcome(...)`) and computes runtime inputs (`adaptive_sigma_fractional(...)`).
2. `context_retrieval_runtime.py` now owns rerank decision-policy assembly and confidence projection adapters (`assemble_rerank_decision_policy(...)`, `project_rerank_confidence_decision(...)`) and is the canonical runtime seam owner.
3. `rerank.py` remains the scorer implementation owner (objective config loading, lane fusion, scoring computation, ambiguity detection, context-confidence evaluation).

### Compatibility posture

- Runtime seam ownership is explicit for boundary helpers.
- Scorer execution semantics remain implementation-owned in `rerank.py`, with monolith stage orchestration still coupling invocation to scorer internals.
- This is category debt (ownership decomposition incomplete), not row debt (wrapper mechanics already retired).

### Candidate decomposition boundaries discovered from code

| Subcategory | Current responsibility | Current owner/path | Slice type |
| --- | --- | --- | --- |
| Scorer execution contract at runtime seam | Inputs passed to scorer (target, sigma, exclusions, top_k, near_tie_delta) and scorer call sequencing in stage flow | `src/testbot/sat_chatbot_memory_v2.py` (`stage_rerank`) | Contract/boundary slice |
| Scorer input normalization/config materialization | Objective + thresholds + lane-fusion config loading, cache, parse/validation fallback behavior | `src/testbot/rerank.py` (`load_rerank_objective_config`, parse helpers) | Contract/boundary slice |
| Scorer output/result contract | `RerankOutcome`/`scored_candidates`/near-tie payload shape and runtime assumptions of those fields | `src/testbot/rerank.py` + consumers in `context_retrieval_runtime.py` | Contract/boundary slice |
| Score computation internals | Temporal/type/lane math, ranking keys, lane fusion algorithm, ambiguity detection internals | `src/testbot/rerank.py` | Implementation/internals slice |
| Post-execution compatibility shaping | Conversion to `CandidateHit`, confidence payload projection fields, telemetry field placement | `src/testbot/sat_chatbot_memory_v2.py` + `context_retrieval_runtime.py` | Contract/boundary slice |
| Residual temporal/scoring coupling | `adaptive_sigma_fractional(...)` computed in stage execution, tightly coupled to scorer invocation timing | `src/testbot/sat_chatbot_memory_v2.py` + `src/testbot/rerank.py` | Contract/boundary slice |

## Ideal future state for scorer ownership

### Canonical runtime path ownership

Canonical runtime path should own **explicit scorer boundary contracts** and should not own score semantics internals:

- Own: scorer invocation contract DTO/policy (inputs and deterministic defaults), scorer result contract adapter, and compatibility-preserving projection contract for downstream pipeline state.
- Do not own: objective math, lane-fusion algorithm internals, timestamp Gaussian details, ambiguity tie-break internals.

### Explicit scorer contract/boundary surfaces

1. **Invocation contract surface**: stable typed scorer input contract consumed by runtime stage orchestration.
2. **Result contract surface**: stable typed scorer output contract consumed by projection/policy stages.
3. **Compatibility projection contract**: explicit mapping from scorer outputs to current pipeline telemetry/state fields.

### What can remain implementation-owned longer

- Objective coefficient math and lane-fusion internals in `rerank.py`.
- Detailed tie-break/ambiguity algorithm internals in `rerank.py`.
- Internal config parsing implementation details, as long as boundary contract and behavior are stable.

### How category debt completion differs from row completion

- Row completion retires one bounded execution mechanic (already done for wrapper retirement).
- Category debt completion requires explicit ownership model closure across multiple scorer subcategories, potentially over several bounded slices.

## Decomposition with leverage-to-scope ranking

| Rank | Subcategory | Why this is / is not the best next move | Best candidate future owner | Compatibility posture after extraction | Evidence needed for clean extraction | Slice type |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **Scorer execution contract at runtime seam** | Best leverage-to-scope: smallest boundary that reduces monolith choke-point authority without changing scorer math. | `context_retrieval_runtime` (new scorer invocation/result boundary helpers or DTOs) | Keep existing payload fields; preserve `stage_rerank` behavior through contract delegation. | Runtime-path equivalence tests proving contract-mediated scorer call; anti-backslide assertion that stage no longer authors raw scorer call arguments inline. | Contract/boundary |
| 2 | **Scorer output/result contract normalization** | High leverage but broader consumer surface than rank 1; safer after invocation contract is explicit. | `context_retrieval_runtime` + typed result adapter near scorer seam | Preserve `confidence_decision` field shape and downstream expectations. | Golden-shape tests for `RerankOutcome`-derived payload mapping + stage-transition compatibility checks. | Contract/boundary |
| 3 | **Residual temporal/scoring coupling (`sigma` ownership)** | Useful, but easiest and safest once invocation contract exists; otherwise duplicates movement. | Runtime seam scorer policy helper | Keep `adaptive_sigma_fractional` behavior identical while relocating owner. | Deterministic tests for `sigma` computation parity and control-point ownership assertion. | Contract/boundary |
| 4 | **Post-execution compatibility shaping rationalization** | Valuable for cleanup; not smallest first slice because current projection contract just moved and is stable. | `context_retrieval_runtime` | Maintain exact key compatibility in `confidence_decision` until explicit schema migration. | Telemetry compatibility snapshots and downstream consumer checks. | Contract/boundary |
| 5 | **Scorer input normalization/config materialization** | Medium leverage but higher blast radius (config loader + cache + fallback semantics). Better after boundaries are explicit. | `rerank.py` internal owner behind explicit config contract | Keep env/config-path and default-fallback semantics unchanged. | Config parse/fallback regression suite + objective metadata stability checks. | Contract/boundary |
| 6 | **Score computation internals (objective/ambiguity/lane fusion redesign)** | Not a good next bounded move; broad redesign risk and crosses many invariants. | `rerank.py` (internals owner) | Out of scope for next bounded slice. | Full algorithmic regression program (not suitable for next small slice). | Implementation/internals |

## Recommended next bounded scorer slice

### Recommendation

**Recommended next slice: Rank 1 — scorer execution contract boundary extraction at the runtime seam.**

This slice should extract the scorer invocation/result boundary from `stage_rerank(...)` into an explicit runtime-owned scorer execution contract helper while preserving existing scorer internals and payload compatibility.

### Why preferred over nearby alternatives

- Compared with output-contract normalization: invocation boundary is smaller and upstream, so it unlocks cleaner subsequent output-contract work.
- Compared with sigma-only movement: a full invocation contract captures sigma plus other scorer inputs in one coherent boundary.
- Compared with internals redesign: dramatically lower blast radius and stronger leverage-to-scope ratio.

### Evidence required in the next execution PR

1. Deterministic runtime equivalence proving unchanged rerank outputs/hits and unchanged confidence payload under the new invocation contract boundary.
2. Control-point assertion proving canonical runtime path sources scorer execution contract from runtime-owned helper.
3. Anti-backslide guard proving `stage_rerank(...)` no longer assembles raw scorer invocation arguments inline for canonical path.
4. Explicit out-of-scope declaration that scorer internals (objective math/fusion/tie-break semantics) remain unchanged.

## Strongest justified claim from this decomposition PR

The strongest bounded claim is: scorer-category debt is now decomposed into concrete contract and internals subcategories with a ranked leverage-to-scope ordering, and the smallest recommended next execution slice is a runtime-owned scorer execution contract boundary extraction.

- Evidence X supports claim Y because Z: direct code inspection identifies current owners and remaining couplings across `sat_chatbot_memory_v2`, `context_retrieval_runtime`, and `rerank`, enabling ranked bounded-slice selection.
- It does not yet support stronger claim W because Q: this decomposition does not itself execute scorer boundary extraction or scorer internals redesign.

## Remaining deferred scorer-category debt after this PR

### Recommended next slice

- Scorer execution contract/boundary extraction at runtime seam (rank 1).

### Lower-priority slices

- Scorer output/result contract normalization.
- Residual temporal/scoring coupling ownership (`sigma` policy ownership).
- Post-execution compatibility shaping rationalization.
- Scorer input normalization/config materialization contract hardening.

### Still out-of-scope broad redesign

- Objective function redesign.
- Lane-fusion redesign.
- Ambiguity/tie-break semantic redesign.

## Inventory update for ISSUE-0022 handoff

- Category decomposed: scorer-category debt.
- Ranked options: six scorer subcategories ranked by leverage-to-scope.
- Recommended bounded next slice: scorer execution contract/boundary extraction.
- Explicit out-of-scope remains: broad scorer internals redesign.

## PR-ready summary

This PR decomposes the remaining scorer-category debt (post-wrapper-retirement) into explicit contract-boundary and implementation-internals subcategories, ranks them by leverage-to-scope ratio, and recommends one bounded next execution slice: runtime-owned scorer execution contract extraction. This makes later scorer moves easier by turning broad “scorer redesign” debt into a small contract-first sequence with concrete evidence requirements and preserved compatibility posture.

## Merge-note explicit status lines

- **Rows remaining:** none for the rerank wrapper-retirement row program.
- **Category debt remaining:** scorer-category debt.
- **Recommended next unit:** scorer execution contract/boundary slice (not broad scorer internals redesign).

## 2026-03-29 execution update — scorer execution invocation/result contract slice processed

- Processed unit type: **category-debt execution slice** (not a deferred row).
- **Processed in #694:** scorer execution invocation/result contract boundary.
- Processed slice: runtime-owned scorer execution invocation/result contract for canonical rerank path.
- Bounded change:
  - Added `ScorerExecutionRequest`, `ScorerExecutionResult`, and
    `execute_rerank_scorer_contract(...)` in
    `context_retrieval_runtime`.
  - Rewired `stage_rerank(...)` to call the runtime-owned scorer execution contract helper instead
    of invoking scorer internals inline.
- Compatibility posture: scorer internals (`rerank.py` objective/ambiguity/lane semantics) remain unchanged;
  only execution boundary ownership moved.
- **Category debt remaining:** scorer internals / broader scorer-category redesign.
- **Recommended next unit:** smallest scorer-internals slice, unless owners determine the #694 execution-boundary
  move materially changes remaining boundaries, in which case run a scorer-category decomposition refresh first.

## 2026-03-29 execution update — scorer result-interpretation internals slice processed

- Decision on #694 conditional: remaining scorer-category boundaries remain materially stable; no decomposition refresh required.
- Processed unit type: **category-debt execution slice** (not a decomposition refresh).
- Selected scorer-internals slice: **scorer output/result interpretation compatibility shaping**.
- Bounded change:
  - Added runtime-owned `ScorerInterpretationResult` and
    `interpret_rerank_scorer_result(...)` in `context_retrieval_runtime`.
  - Rewired `stage_rerank(...)` to consume scorer interpretation outputs (`hits`, `has_context`)
    through the runtime-owned scorer result interpretation helper.
- Runtime control-point evidence posture:
  - Canonical path still executes through runtime-owned scorer contract boundary from #694.
  - Canonical path now also consumes scorer-result interpretation through runtime-owned helper,
    reducing stage-local scorer-assumption handling.
- Compatibility posture:
  - Scorer internals in `rerank.py` remain unchanged.
  - Confidence payload shape and reranked-hit output shape remain unchanged.
- **Category debt remaining:** broader scorer internals / redesign debt remains.
- **Recommended next unit:** smallest scorer internals slice around scorer input normalization or temporal/scoring coupling ownership.

### Post-#695 handoff (explicit next-decision surface)

- **Processed unit type:** category-debt execution slice.
- **Processed slice in #695:** scorer result interpretation / compatibility shaping behind runtime seam.
- **Remaining scorer-category debt (explicit):**
  1. scorer input normalization/config materialization contract hardening;
  2. residual temporal/scoring coupling ownership (`sigma` ownership posture);
  3. broader scorer internals redesign (objective/fusion/ambiguity semantics), still intentionally out of scope.
- **Recommended next smallest scorer-internals slice:** scorer input normalization/config materialization
  contract hardening, because it is adjacent to the newly explicit execution + interpretation seam and can be
  moved without reopening objective semantics.

### Post-#696 handoff (explicit next-decision surface)

- **Processed unit type:** category-debt execution slice.
- **Processed slice in #696:** scorer input normalization/config materialization contract hardening behind runtime seam.
- **Bounded authority movement recorded:**
  - runtime seam now materializes scorer objective config through `materialize_rerank_scorer_config(...)`;
  - runtime seam now owns scorer request normalization through `normalize_scorer_execution_request(...)`;
  - scorer execution contract now carries explicit `scorer_config` materialized at runtime control-point.
- **`sigma` ownership posture in this slice:** left separate on purpose; `sigma` computation remains in stage policy flow
  (`adaptive_sigma_fractional(...)` in `stage_rerank`) so temporal-coupling ownership can be handled as its own bounded
  scorer-category slice.
- **Decomposition stability after #696:** scorer-category decomposition remains decision-grade and stable; no targeted
  decomposition refresh is required before executing the next bounded `sigma` ownership slice.
- **Remaining scorer-category debt (explicit):**
  1. residual temporal/scoring coupling ownership (`sigma` ownership posture);
  2. broader scorer internals redesign (objective/fusion/ambiguity semantics), still intentionally out of scope.
- **Recommended next smallest scorer-category slice:** residual temporal/scoring coupling ownership (`sigma`) behind the
  same runtime seam, now that scorer config materialization is explicit and runtime-owned.
