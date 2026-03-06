# ISSUE-0005: Time-aware memory ranking parity remains partial across recall gate

- **ID:** ISSUE-0005
- **Title:** Time-aware memory ranking parity remains partial across recall gate
- **Status:** closed
- **Severity:** amber
- **Owner:** Sebastian Mäki (@NeatBasis, Runtime Quality Lead)
- **Created:** 2026-03-04
- **Target Sprint:** Sprint 3
- **Principle Alignment:** deterministic, traceable, invariant-driven, ci-enforced

## Problem Statement

`time_aware_memory_ranking` is still declared `partial` in `docs/qa/feature-status.yaml`, but the previously closed issue focused on generic eval/runtime divergence rather than explicit capability-level readiness for `product_eval_recall_topk4` and `qa_pytest_not_live_smoke`. The issue is rescoped and reopened so capability-level gaps remain traceable until both gate checks and deterministic time-aware ranking expectations are satisfied.

## Evidence

- Capability contract `time_aware_memory_ranking` is currently `partial`.
- The feature status report should surface at least one open issue for this capability while it remains partial.
- Existing tests (`tests/test_rerank.py`, `tests/test_time_reasoning.py`, `tests/test_eval_recall.py`) provide baseline coverage but not yet complete closure evidence tied to gate-level thresholds.

## Impact

- Ranking drift can reappear at temporal boundaries (near ties, ambiguous target-time extraction).
- Eval recall confidence can be overstated if parity checks pass on narrow fixtures but miss time-aware edge classes.
- Product decisions using reranked context may degrade grounded answer quality.

## Acceptance Criteria

1. `python scripts/eval_recall.py --top-k 4` completes with deterministic output and meets the agreed minimum recall threshold for the maintained fixture set used by `product_eval_recall_topk4`.
2. `python -m pytest -m "not live_smoke"` passes with no failures in `tests/test_rerank.py`, `tests/test_time_reasoning.py`, and `tests/test_eval_recall.py`.
3. `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json` reports `product_eval_recall_topk4` and `qa_pytest_not_live_smoke` as `passed`.
4. `docs/qa/feature-status.yaml` is updated to `implemented` for `time_aware_memory_ranking` only after criteria 1-3 are met.

## Work Plan

- Expand time-aware fixture families for boundary dates and ambiguous temporal language.
- Add deterministic assertions for top-k ordering stability and fallback behavior under ambiguous time signals.
- Keep capability/issue linkage explicit in `docs/qa/feature-status.yaml` and regenerate status artifacts on each milestone.

## Verification

- Command: `python scripts/eval_recall.py --top-k 4`
  - Expected: deterministic summary emitted and threshold satisfied.
- Command: `python -m pytest -m "not live_smoke"`
  - Expected: passes including all time-aware ranking suites.
- Command: `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json`
  - Expected: both capability gate checks pass.

## Closure Notes

- 2026-03-04: Issue originally opened for generic eval/runtime divergence concern.
- 2026-03-06: Rescoped/reopened to track explicit `time_aware_memory_ranking` readiness and gate-tied closure criteria.

- 2026-03-06: Closed after ISSUE-0005 scope completion; `product_eval_recall_topk4` and `qa_pytest_not_live_smoke` verified passing with expanded temporal fixtures and deterministic near-tie ordering hardening.
