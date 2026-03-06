# ISSUE-0005: Eval script logic divergence risk from runtime logic

- **ID:** ISSUE-0005
- **Title:** Eval script logic divergence risk from runtime logic
- **Status:** closed
- **Severity:** green
- **Owner:** Sebastian Mäki (@NeatBasis, Runtime Quality Lead)
- **Created:** 2026-03-04
- **Target Sprint:** Sprint 3
- **Principle Alignment:** deterministic, traceable, invariant-driven

## Problem Statement

The original concern was potential divergence between eval ranking behavior and runtime ranking behavior.
That gap has now been closed by deterministic parity coverage and by keeping parity checks in the canonical gate.

## Evidence

- Eval script imports `parse_target_time` from `testbot.time_parse` and rerank/score functions from `testbot.rerank`.
- `tests/test_eval_runtime_parity.py` now provides explicit parity checks for ordering, fallback, ambiguity, and intermediate ranking signals.
- `scripts/all_green_gate.py` includes `product_eval_runtime_parity` as a blocking check.

## Impact

Residual risk is now low and limited to future policy/schema changes that intentionally alter expected parity behavior.

## Acceptance Criteria

1. ✅ Eval script reuses production parse/rerank logic where possible.
2. ✅ Intentional deviations are documented explicitly.
3. ✅ Add deterministic parity regression checks that compare eval ordering + intent decisions against runtime outputs across fixture families:
   - ordering
   - top-1 to top-x stability
   - fallback
   - confidence boundary
   - edge-time
   - ambiguous-intent
   - observation-making-processes
4. ✅ Parity checks must assert comparable intermediate signals (`scored_candidates`, `near_tie_candidates`, `ambiguity_detected`) so adapter-level drift is visible before final metric drift.
5. ✅ Release gate keeps parity check as a blocking check and emits a dedicated divergence hint that points to likely boundary modules.

## Work Plan

- Maintain parity pytest coverage with explicit fixture sets for required families and scenarios.
- Keep eval adapter path aligned with runtime intermediate ranking signals.
- Keep parity command and gate wiring current in testing/gate docs.

## Verification

- Command: `python scripts/eval_recall.py --top-k 4`
  - Observed 2026-03-06: exits `0`; deterministic summary emitted.
- Command: `python -m pytest tests/test_eval_runtime_parity.py`
  - Observed 2026-03-06: exits `0`; confirms ranking, top-k stability, intent parity, ambiguity parity, and scored candidate parity across fixture families.
- Command: `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json`
  - Observed 2026-03-06: exits `0`; `product_eval_runtime_parity` check passed.

## Closure Notes

- 2026-03-04: Partially mitigated by shared imports and documented eval non-goals.
- 2026-03-06: Closed after validating parity coverage and canonical gate enforcement in a dependency-complete environment.
- Residual risk: low; revisit if intentional runtime ranking contract changes are introduced.
