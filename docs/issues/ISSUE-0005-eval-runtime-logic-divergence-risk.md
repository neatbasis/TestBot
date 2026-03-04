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

Offline eval logic duplicates parts of parsing/scoring behavior, creating a risk that evaluation outcomes diverge from runtime behavior.

## Evidence

- `scripts/eval_recall.py` contains its own parse/score functions.
- Runtime uses `src/testbot/time_parse.py` and `src/testbot/rerank.py`.

## Impact

- Misleading quality metrics.
- Hidden regressions between eval and production path.

## Acceptance Criteria

1. Eval script reuses production parse/rerank logic where possible.
2. Any intentional deviations are documented explicitly.
3. One regression check validates eval/runtime ranking parity on shared fixture.

## Work Plan

- Refactor eval script imports.
- Add parity check using fixture case.
- Update docs.

## Verification

- Compare ranking output before/after refactor on fixed test cases.

## Closure Notes

- _Pending refactor._

