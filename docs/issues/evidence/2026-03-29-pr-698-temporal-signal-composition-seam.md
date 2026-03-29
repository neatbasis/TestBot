# 2026-03-29 PR #698 — scorer category slice: temporal signal composition seam hardening

Issue: `ISSUE-0022`

## Selected unit type

- Processed unit type: **category-debt execution slice** (not a deferred row).

## Adjacent-state map

Already runtime-owned / runtime-facing (post-#697):
- scorer execution invocation/result contract (`execute_rerank_scorer_contract`, `ScorerExecutionRequest`);
- scorer result interpretation / compatibility shaping (`interpret_rerank_scorer_result`);
- scorer input normalization / config materialization (`normalize_scorer_execution_request`, `materialize_rerank_scorer_config`);
- sigma control-point ownership (`resolve_rerank_sigma_seconds`).

Still scorer-internal before this slice:
- gaussian temporal weighting implementation;
- timestamp-quality attribution (`valid` / `missing` / `invalid`);
- temporal signal composition consumed by `rerank_objective_score_components(...)`.

Still broader deferred scorer-category debt:
- final-score component composition beyond this temporal seam;
- broader scorer algorithm/objective/fusion redesign.

## Bounded authority move

- Added explicit scorer-internal seam type `TemporalSignalComposition` plus owner function
  `compute_temporal_signal_composition(...)` in `src/testbot/rerank.py`.
- Routed both `time_weight(...)` and `rerank_objective_score_components(...)` through that seam.
- Kept coefficients and objective semantics unchanged (same gaussian math, timestamp-quality states, and final-score formula).

## Why this is the smallest coherent slice

- Evidence X supports claim Y because Z: the pre-change scorer path computed gaussian weight and timestamp quality inside
  `rerank_objective_score_components(...)`, so extracting temporal composition there creates one seam without reopening runtime boundaries.
- It does not yet support stronger claim W because Q: this slice does not decompose non-temporal objective composition or lane fusion,
  so broader scorer redesign remains deferred.

## Evidence

Grounded behavior:
- deterministic tests assert seam output for valid and invalid timestamps;
- equivalence test asserts `rerank_objective_score_components(...)` temporal fields still equal seam output.

Compatibility posture:
- scorer component keys (`temporal_gaussian_weight`, `time_decay_freshness`, `temporal_blend`, `timestamp_quality`) remain unchanged.

Ownership / anti-backslide posture:
- both public temporal consumers (`time_weight`, `rerank_objective_score_components`) now consume a single scorer-internal seam,
  reducing re-entanglement risk.

Runtime control-point evidence:
- none of the runtime-owned scorer contract helpers changed; the seam is scorer-internal only.

## Remaining scorer-category debt after this slice

Processed seam (explicit handoff contract):
- scorer-internal temporal signal composition seam only:
  - `TemporalSignalComposition`
  - `compute_temporal_signal_composition(...)`
  - bounded propagation to `time_weight(...)` and `rerank_objective_score_components(...)`.

Remaining scorer-category debt (explicit):
- final-score component composition internals beyond this temporal seam;
- broader scorer objective/fusion internals redesign.

Recommended next slice:
- bounded final-score component composition seam hardening inside scorer internals (type/lane/temporal component assembly), preserving objective semantics.

Lower-priority slices:
- scorer-internal objective/fusion decomposition and optional nomenclature cleanup.

Still out-of-scope broad redesign:
- broad scorer objective reformulation, coefficient redesign, and global fusion strategy redesign.

## Strongest bounded claim

- **Processed unit type:** category-debt execution slice.
- **Processed slice:** scorer-internal temporal signal composition seam hardening (gaussian weighting + timestamp-quality attribution contract).
- **Still deferred:** scorer-category debt beyond this seam (final-score component composition and broader internals redesign).
