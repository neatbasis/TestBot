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

Recommended next bounded slice:
- threshold-profile ownership tightening as a dedicated runtime contract object with explicit anti-backslide coverage.

Lower-priority scorer internals slices:
- scorer objective component decomposition and detailed algorithmic reshaping.

Still out-of-scope broad redesign:
- complete scorer algorithm redesign and broad objective/fusion reformulation.
