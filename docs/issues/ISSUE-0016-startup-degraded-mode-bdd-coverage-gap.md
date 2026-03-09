# ISSUE-0016: Startup degraded-mode user messaging lacks explicit BDD coverage

- **ID:** ISSUE-0016
- **Title:** Startup degraded-mode user messaging lacks explicit BDD coverage
- **Status:** open
- **Severity:** amber
- **Owner:** platform-qa
- **Created:** 2026-03-09
- **Target Sprint:** Sprint 7
- **Canonical Cross-Reference:** ISSUE-0013 (primary bug-elimination stream), ISSUE-0012 (delivery-plan context)
- **Principle Alignment:** contract-first, traceable, deterministic, user-centric

## Problem Statement

Mission/vision principle **P4 (avoid dependency-promoting defaults)** requires user-visible degraded-mode behavior to be both deterministic and explicitly verifiable. While pytest coverage exists for startup/runtime degradation behavior, there is no dedicated BDD scenario in `features/*.feature` that asserts startup degraded-mode messaging semantics as stakeholder-visible behavior.

This leaves a behavior-contract gap between policy language and executable acceptance criteria.

## Evidence

- Principle/source policy: `docs/directives/product-principles.md` (P4).
- Existing behavior specs: `features/capabilities.feature` (capability-help behavior) with no startup degraded-status scenario family.
- Existing deterministic tests for degradation/startup behavior:
  - `tests/test_runtime_modes.py`
  - `tests/test_startup_status.py`
  - `tests/test_capabilities_runtime_status.py`
- Governance alignment map recording the uncovered gap:
  - `docs/governance/mission-vision-alignment.md`

## Impact

- Stakeholder-visible startup degraded-mode commitments are partially enforced (pytest-only), reducing contract readability at the BDD layer.
- Policy/behavior drift risk increases when startup messaging evolves without scenario-level acceptance criteria.
- Regression diagnosis is slower because behavior intent is less explicit than feature-level scenarios.

## Acceptance Criteria

1. Add explicit startup degraded-mode messaging scenarios in `features/*.feature` (new or existing feature file) that assert user-visible degraded-mode semantics.
2. Add aligned deterministic tests in `tests/` for any new scenario branches.
3. Apply minimal code updates in `src/testbot/` only if needed to satisfy scenario/test contracts.
4. Update related docs (including governance/directive traceability surfaces) so no contradictions remain between policy and executable behavior.
5. Run and pass:
   - `python -m behave`
   - `python -m pytest -m "not live_smoke"`
   - `python scripts/all_green_gate.py`

## Work Plan

- [ ] Draft startup degraded-mode stakeholder-visible scenarios first in `features/`.
- [ ] Add/adjust step definitions under `features/steps/` as needed.
- [ ] Add/adjust deterministic pytest coverage in `tests/`.
- [ ] Make minimal runtime changes in `src/testbot/sat_chatbot_memory_v2.py` only if scenario/test gaps require it.
- [ ] Update `docs/governance/mission-vision-alignment.md` and any affected directive/testing docs to keep traceability synchronized.
- [ ] Validate via behave, pytest (non-live-smoke), and canonical all-green gate.

## Verification

- Command: `python -m behave`
  - Expected: exits `0` with startup degraded-mode scenarios included.
- Command: `python -m pytest -m "not live_smoke"`
  - Expected: exits `0`.
- Command: `python scripts/all_green_gate.py`
  - Expected: canonical gate exits `0`.

## Closure Notes

- 2026-03-09: Opened from mission/vision alignment audit to close P4 executable contract gap with BDD-first coverage.
