# ISSUE-0011: Turn analytics aggregation silently drops non-analytics session events without operator coverage diagnostics

- **ID:** ISSUE-0011
- **Title:** Turn analytics aggregation silently drops non-analytics session events without operator coverage diagnostics
- **Status:** open
- **Severity:** amber
- **Owner:** platform-qa
- **Created:** 2026-03-06
- **Target Sprint:** Sprint 2
- **Principle Alignment:** contract-first, traceable, deterministic, user-centric

## Cross-Reference

- Primary implementation/bug-elimination program: ISSUE-0013
- This issue remains planning/history/context unless otherwise specified.

## Problem Statement

`scripts/aggregate_turn_analytics.py` currently accepts a session log input, but turn construction only starts on `user_utterance_ingest` and enrichment only uses a narrow event vocabulary (`intent_classified`, `fallback_action_selected`, `provenance_summary`). High-volume runtime/process events (for example `pipeline_state_snapshot` and `stage_transition_validation`) are effectively ignored for turn assembly without explicit input-coverage diagnostics.

## Evidence

- Reproduction against `logs/session.jsonl` with 53 rows produced `turn_count: 2`, matching only the 2 `user_utterance_ingest` events.
- Event distribution sample from the same input shows most rows are runtime/process events (e.g., 24 `pipeline_state_snapshot`, 16 `stage_transition_validation`) that do not participate in turn construction.
- The script output reports `invalid_rows: 0` and `skipped_rows: 0`, which can be interpreted as full row utilization even when most input rows are semantically out-of-scope for turn aggregation.

## Impact

- Operators can misread KPI output as if all session rows were represented in the turn dataset.
- Coverage ambiguity reduces trust in reported metrics (`grounded_answer_precision`, `false_knowing_rate`, and related KPIs).
- Debugging ingestion/telemetry mismatches is slower because event-level drop-off is not surfaced in the summary contract.

## Acceptance Criteria

1. `scripts/aggregate_turn_analytics.py` summary output includes explicit coverage diagnostics:
   - `input_rows_total`
   - `recognized_analytics_rows`
   - `ignored_non_analytics_rows`
   - `turn_start_events`
2. Summary output includes either `event_counts` or `ignored_event_counts` so ignored event classes are observable.
3. When ignored rows exceed a documented threshold (or when `turn_start_events == 0` with non-empty input), the script emits a clear warning in CLI output and serialized summary metadata.
4. `docs/testing.md` (or a more specific analytics contract doc) documents expected input semantics for `aggregate_turn_analytics.py`, including what events are required to form turns.
5. Deterministic tests are added/updated under `tests/` to assert coverage diagnostics and warning behavior for mixed-event session logs.

## Work Plan

- Update aggregation pipeline bookkeeping to track total rows, recognized analytics rows, ignored rows, and turn starters.
- Extend summary schema and output writer to serialize coverage diagnostics and ignored-event breakdowns.
- Add warning policy for low-coverage or no-turn-detected inputs with explicit thresholds.
- Add focused unit tests for mixed-event logs and malformed/non-turn-heavy inputs.
- Document the input contract and operator interpretation guidance in testing/analytics docs.

- Land analytics coverage diagnostics in alignment with ISSUE-0012 Sprint 5 auditability checkpoint to preserve post-turn observability requirements.

## Verification

- Command: `python scripts/aggregate_turn_analytics.py --input logs/session.jsonl`
  - Expected: summary includes coverage diagnostics and ignored-event visibility.
- Command: `python -m pytest tests/test_aggregate_turn_analytics.py`
  - Expected: exits `0` with assertions covering diagnostics and warning cases.
- Command: `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json`
  - Expected: relevant analytics tests pass and no regressions are introduced in the canonical gate.

## Closure Notes

- 2026-03-06: Opened from operator-observed mismatch between total session rows and turn analytics output, to make input coverage explicit and reduce semantic confusion.
