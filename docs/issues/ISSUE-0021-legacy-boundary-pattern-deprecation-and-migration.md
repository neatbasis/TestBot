# ISSUE-0021: Legacy boundary-pattern deprecation and migration

- **ID:** ISSUE-0021
- **Title:** Legacy boundary-pattern deprecation and migration
- **Status:** open
- **Issue State:** governed_execution
- **Severity:** amber
- **Owner:** runtime-pipeline
- **Created:** 2026-03-15
- **Target Sprint:** Sprint 5-6
- **Canonical Cross-Reference:** ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md
- **Principle Alignment:** contract-first, invariant-driven, deterministic, ci-enforced, traceable

## Problem Statement

Recent architecture-boundary enforcement and canonical pipeline stage-contract tests define a stricter implementation direction than legacy runtime patterns currently reflect. The repository now needs an explicit deprecation/migration issue that tracks what is no longer acceptable for new work and how existing legacy surfaces will be retired without breaking behavior.

## Evidence

- `docs/architecture-boundaries.md` now declares boundary rules enforced by `tests/architecture/test_import_boundaries.py` and explicitly marks prohibited patterns as deprecated.
- New deterministic tests under `tests/pipeline/` codify canonical stage contracts and decision-matrix behavior around `intent.resolve`, `retrieve.evidence`, `policy.decide`, `answer.validate`, `answer.commit`, and metrics contracts.
- The canonical program issue `ISSUE-0013` remains open/blocked pending evidence; this deprecation issue scopes migration debt made explicit by the new boundary checks.
- Retirement-readiness inventory and migration plan for `sat_chatbot_memory_v2` compatibility exports captured in `docs/issues/evidence/2026-03-28-issue-0021-sat-compat-retirement-inventory.md` (export-by-export bucket classification + caller census).

## Impact

- Without explicit migration ownership, legacy coupling patterns can persist and continue to produce architecture drift.
- Contributors lack a single issue anchor for deprecation lifecycle (announce -> freeze -> migrate -> remove).
- Documentation can appear directionally strict while runtime retains contradictory legacy shortcuts.

## Acceptance Criteria

- [ ] Deprecated patterns are explicitly listed in docs and linked to this issue from canonical program metadata.
- [ ] Legacy call sites violating the boundary direction are inventoried with file-level references and target-removal milestones.
- [ ] New feature work is prevented from introducing deprecated patterns by deterministic tests (boundary checks + canonical stage suites).
- [ ] Migration completion criteria and removal date/status are recorded for each deprecated pattern class.
- [ ] Closure evidence includes passing canonical gate output (`python scripts/all_green_gate.py`) and synchronized issue statuses.

## Work Plan

1. ✅ Completed (2026-03-28): inventory remaining legacy call sites/patterns for `sat_chatbot_memory_v2` compatibility exports and classify migration/removal disposition in the linked evidence note.
2. ✅ Completed (2026-03-28): freeze loop-owner extraction contract in evidence and open follow-on ISSUE-0022 for residual helper-level runtime authority ranking/extraction sequencing.
3. Pending: add migration subtasks under this issue grouped by pattern class (import coupling, stage-order duplication, raw-to-render shortcuts).
4. Pending: remove or isolate legacy paths behind canonical orchestrator boundaries with deterministic regression tests.
5. Pending: update linked documentation (`docs/architecture.md`, `docs/testing.md`, `docs/issues/ISSUE-0013...`) as milestones are completed.
6. Pending: close only when migration inventory is empty and canonical gate evidence is green.

## Verification

```bash
python -m pytest tests/architecture/test_import_boundaries.py
python -m pytest tests/pipeline/test_intent_resolution.py tests/pipeline/test_retrieve_evidence.py tests/pipeline/test_policy_decide_matrix.py tests/pipeline/test_answer_validation.py tests/pipeline/test_answer_commit.py tests/pipeline/test_metrics_contract.py
python scripts/all_green_gate.py
```

## Closure Notes

Pending. Follow-on residual authority inventory and seam-ranking work is tracked in `docs/issues/ISSUE-0022-residual-runtime-helper-authority-inventory-after-loop-owner-extraction.md`.
