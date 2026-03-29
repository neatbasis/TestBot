# 2026-03-29 PR #697 — scorer category slice: residual temporal/scoring coupling (`sigma`) ownership posture

Issue: `ISSUE-0022`

## Slice type

- Category-debt execution slice (bounded), not deferred-row decomposition.

## Adjacent-state map at execution time

Already runtime-owned/runtime-facing boundary-owned:
- scorer execution invocation/result contract boundary (`execute_rerank_scorer_contract`, `ScorerExecutionRequest`);
- scorer result interpretation / compatibility shaping (`interpret_rerank_scorer_result`);
- scorer input normalization / config materialization contract (`normalize_scorer_execution_request`, `materialize_rerank_scorer_config`).

Still stage/scorer-category owned:
- sigma materialization control-point in `stage_rerank(...)` via inline `adaptive_sigma_fractional(...)` call (pre-change);
- temporal/scoring policy internals inside scorer algorithm behavior.

Still deferred broader debt:
- scorer algorithm/internals redesign and broader temporal semantics redesign.

## Bounded ownership move in this PR

- Introduce runtime-owned helper `resolve_rerank_sigma_seconds(...)` in `context_retrieval_runtime`.
- Route canonical `stage_rerank(...)` sigma sourcing through that runtime helper before decision policy assembly.
- Keep scorer math and downstream scorer internals unchanged.

## Why this is the smallest coherent sigma move

- It relocates sigma materialization authority to the same runtime owner that already controls adjacent scorer contract surfaces.
- It does not change scorer objective math, scoring internals, or compatibility behavior.
- It establishes an anti-backslide control point for future bounded propagation.

## Evidence summary

- Runtime helper deterministic tests cover sigma-policy delegation and default parity to adaptive policy behavior.
- Compatibility wrapper tests assert canonical stage path now consumes runtime sigma control point before invocation policy assembly.
- Existing scorer execution/interpretation boundaries remain unchanged and continue to be runtime-owner mediated.

## Remaining scorer-category debt after this slice

Processed explicitly in this slice:
- `sigma` ownership posture is now runtime control-point owned (`resolve_rerank_sigma_seconds(...)`) and threaded through the
  existing scorer decision/invocation contract without changing scorer math.

Remaining explicit debt (adjacent and broader):
- scorer internals still own temporal/objective implementation details (for example temporal gaussian weighting, timestamp quality,
  and final-score component composition inside `rerank_objective_score_components(...)`);
- broader scorer algorithm/internals redesign remains out of scope.

Recommended next smallest scorer-internals slice:
- scorer-internal **temporal signal composition seam**: extract and harden a narrow scorer-internal contract around
  temporal gaussian weighting + timestamp-quality attribution (without changing coefficients/objective semantics), so runtime
  contract ownership stays stable while scorer-internal responsibilities become more explicit and test-isolated.

Lower-priority scorer internals slices:
- scorer objective component decomposition and detailed algorithmic reshaping.

Still out-of-scope broad redesign:
- complete scorer algorithm redesign and broad objective/fusion reformulation.
