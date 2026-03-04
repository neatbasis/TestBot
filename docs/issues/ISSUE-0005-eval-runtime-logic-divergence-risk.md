# ISSUE-0005: Eval script logic divergence risk from runtime logic

- **ID:** ISSUE-0005
- **Title:** Eval script logic divergence risk from runtime logic
- **Status:** open
- **Severity:** amber
- **Owner:** unassigned
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
3. Add one deterministic parity regression check that compares eval ordering against runtime ordering for at least one shared fixture case.

## Work Plan

- Add a parity check script or pytest that invokes both paths over a fixed fixture.
- Wire the parity command into docs/testing as a deterministic optional/required check.

## Verification

- Command: `python scripts/eval_recall.py --cases eval/cases.jsonl --top-k 4 --idk-threshold 0.2 --now 2026-03-10T11:00:00+00:00`
  - Expected: exits `0`; emits stable JSON metrics.
- Command: `pytest -k parity` (planned)
  - Expected: exits `0`; confirms ranking parity between eval and runtime adapters on fixed fixture.

## Closure Notes

- 2026-03-04: Partially mitigated by shared imports and documented eval non-goals.
- Residual risk: medium until parity regression is automated and enforced.
