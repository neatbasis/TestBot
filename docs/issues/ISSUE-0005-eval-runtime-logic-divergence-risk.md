# ISSUE-0005: Eval script logic divergence risk from runtime logic

- **ID:** ISSUE-0005
- **Title:** Eval script logic divergence risk from runtime logic
- **Status:** open
- **Severity:** amber
- **Owner:** Sebastian Mäki (@NeatBasis, Runtime Quality Lead)
- **Created:** 2026-03-04
- **Target Sprint:** Sprint 3
- **Principle Alignment:** deterministic, traceable, invariant-driven

## Problem Statement

Most high-risk divergence has been reduced by reusing runtime parser/rerank functions in `scripts/eval_recall.py`. The remaining gap is the absence of an explicit, automated parity regression check that compares eval ranking outputs against the runtime path on a shared fixture.

## Evidence

- Eval script imports `parse_target_time` from `testbot.time_parse` and rerank/score functions from `testbot.rerank`.
- Eval script documents intentional scope limits under non-goals.
- No dedicated parity test command currently asserts eval-vs-runtime ranking equivalence for the same fixture inputs.

## Impact

- Residual risk that future runtime changes alter ordering/threshold behavior without a parity alarm in eval workflows.

## Acceptance Criteria

1. ✅ Eval script reuses production parse/rerank logic where possible.
2. ✅ Intentional deviations are documented explicitly.
3. Add deterministic parity regression checks that compare eval ordering + intent decisions against runtime outputs across fixture families:
   - ordering
   - top-1 to top-x stability
   - fallback
   - confidence boundary
   - edge-time
   - ambiguous-intent
   - observation-making-processes
4. Parity checks must assert comparable intermediate signals (`scored_candidates`, `near_tie_candidates`, `ambiguity_detected`) so adapter-level drift is visible before final metric drift.
5. Release gate keeps parity check as a blocking check and emits a dedicated divergence hint that points to likely boundary modules.

## Work Plan

- Expand parity pytest coverage with explicit fixture sets for all required families and scenarios.
- Ensure eval adapter path emits the same intermediate ranking signals used by runtime parity assertions.
- Wire the parity command into docs/testing as a deterministic optional/required check.
- Add a release gate failure hint for parity-check failures that names likely divergence modules.

## Verification

- Command: `python scripts/eval_recall.py --cases eval/cases.jsonl --top-k 4 --idk-threshold 0.2 --now 2026-03-10T11:00:00+00:00`
  - Expected: exits `0`; emits stable JSON metrics.
- Command: `pytest tests/test_eval_runtime_parity.py`
  - Expected: exits `0`; confirms ranking, top-k stability, intent parity, ambiguity parity, and scored candidate parity across all fixture families.

## Closure Notes

- 2026-03-04: Partially mitigated by shared imports and documented eval non-goals.
- Residual risk: medium until parity regression is automated and enforced.
