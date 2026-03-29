# 2026-03-29 PR #700 scorer category-debt execution slice: lane/type prior determination seam

## Processed unit type

- Category-debt execution slice (not a deferred-row decomposition update).

## Processed bounded scorer-internal seam

- Added explicit scorer-internal prior determination seam:
  - `PriorComponentComposition`
  - `compute_prior_component_composition(...)`
- `compute_objective_component_composition(...)` now consumes prior composition output and only assembles final score from:
  - semantic score input
  - temporal blend input
  - prior composition output (`inferred_lane`, `type_prior`, `lane_prior`)

## Unchanged semantics (bounded propagation)

- Final-score formula remains unchanged: `type_prior * lane_prior * semantic_score * temporal_blend`.
- Coefficients and objective semantics remain unchanged.
- Temporal seam and final-score component seam remain in place; this slice hardens the upstream prior/input-selection layer.

## Remaining scorer-category debt after this slice

- Recommended next bounded scorer-internal slice:
  - scorer candidate-output composition/projection shaping before confidence gate and lane fusion (`rerank_docs_with_time_and_type_outcome(...)`).
- Lower-priority scorer internals:
  - tie/ambiguity projection shaping and threshold attribution pathways remain co-located.
- Out-of-scope broad redesign:
  - objective semantics redesign, coefficient redesign, full scorer algorithm redesign.

## Post-#700 handoff (explicit)

- Processed seam (this PR): scorer-internal **lane/type prior determination** (`inferred_lane`, `type_prior`, `lane_prior`) as a named seam consumed by objective component composition.
- Remaining scorer-category debt (still entangled):
  - scorer candidate-output composition/projection shaping in `rerank_docs_with_time_and_type_outcome(...)` (threshold fields, provenance-citation factor, and scored-candidate payload assembly remain co-located);
  - tie/ambiguity projection shaping (`near_tie_candidates`, unresolved ambiguity flags) remains in the same scorer path.
- Recommended next bounded scorer-internal seam:
  - extract scorer candidate-output composition/projection as one explicit seam upstream of confidence gating and downstream of final-score assembly.

## Validation posture for this bounded slice

- Focused scorer validation passed:
  - `python -m pytest tests/test_rerank.py`
- Broader readiness-gate failures observed outside this slice are treated as pre-existing and unrelated to the
  scorer-internal lane/type prior determination seam extraction.
