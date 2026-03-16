# ISSUE-0009: Knowing grounded answers remain partial due to provenance/recall gate debt

- **ID:** ISSUE-0009
- **Title:** Knowing grounded answers remain partial due to provenance/recall gate debt
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

The `knowing_grounded_answers` capability remains `partial`. ISSUE-0009 is the primary traceability record for this capability and tracks the remaining measurable deltas against `product_behave`, `safety_behave_answer_contract_and_memory`, and `qa_eval_fixtures_and_runtime_parity`, while preserving explicit cross-capability linkage with ISSUE-0010 in generated status reporting.

## Evidence

- `docs/qa/feature-status.yaml` marks `knowing_grounded_answers` as `partial`.
- `docs/qa/feature-status-report.md` and `artifacts/feature-status-summary.json` list ISSUE-0009 and ISSUE-0010 as relevant open issues for this partial capability and still report failing checks (`product_behave`, `safety_behave_answer_contract_and_memory`).
- Capability acceptance tests span contract behavior, memory recall, runtime logging, and eval/runtime parity; closure requires cross-check consistency.

## Impact

- Knowing-mode outputs may regress in provenance transparency or memory-grounding quality without immediate governance visibility.
- Remaining failing gate checks keep this capability in partial state and continue to block readiness signals for knowing-mode quality.
- Stakeholder confidence in grounded answers can drift from actual runtime behavior.
- QA report consumers rely on ISSUE-0009 as the accountable primary tracker and on explicit ISSUE-0010 linkage for closure sequencing and delta burn-down.

## Acceptance Criteria

1. `python -m behave features/testbot/answer_contract.feature features/testbot/memory_recall.feature` passes.
2. `python -m pytest tests/test_runtime_logging_events.py tests/test_eval_runtime_parity.py` passes.
3. `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json` reports `product_behave`, `safety_behave_answer_contract_and_memory`, and `qa_eval_fixtures_and_runtime_parity` as `passed`.
4. `docs/qa/feature-status.yaml` is updated to `implemented` for `knowing_grounded_answers` only after criteria 1-3 are met.

### Residual blockers (post-PR #325 verification, 2026-03-09)

- AC-0009-R1: Canonical gate evidence currently does not expose `safety_behave_answer_contract_and_memory` and `qa_eval_fixtures_and_runtime_parity` check IDs in `artifacts/all-green-gate-summary.json`; acceptance criterion 3 cannot be satisfied until those expected checks are restored or this issue's gate contract is explicitly migrated to the current canonical check names with validator coverage.
- AC-0009-R2: `docs/qa/feature-status.yaml` still declares `knowing_grounded_answers` as `partial`, so criterion 4 remains intentionally unmet pending AC-0009-R1 resolution.


## Enforcement mapping (implementation anchors)

| Acceptance criterion | Runtime/Policy enforcement points |
| --- | --- |
| AC #1 (`behave` answer+memory features) | `src/testbot/answer_validate.py` (compat alias) -> `validate_answer_assembly_boundary`; `src/testbot/answer_render.py` (compat alias) -> `render_answer`; `src/testbot/policy_decision.py::decide_from_evidence` for memory-grounded vs clarify branching. |
| AC #2 (`pytest` runtime logging + eval parity) | `src/testbot/policy_decision.py::decide` + `decide_from_evidence` for scored/empty posture determinism, exercised by eval/runtime parity and runtime logging assertions. |
| AC #3 (all-green gate check IDs passed) | Gate check evidence consumed by `scripts/all_green_gate.py`; behavioral proofs are enforced in `policy_decision` + answer validation/render boundaries above. |
| AC #4 (status move to implemented) | `docs/qa/feature-status.yaml` capability status lifecycle, regenerated into `docs/qa/feature-status-report.md` and `artifacts/feature-status-summary.json`. |

## Work Plan

- [x] Capture production-debug evidence trace and map symptoms to ISSUE-0009/ISSUE-0010 acceptance criteria (`docs/issues/evidence/production-debug-cli-trace-2026-03-07.md`).
- [x] **Remaining delta: confident memory-recall recovery** — fix equivalent-candidate ambiguity/tie-break flow so `features/testbot/memory_recall.feature:22` passes consistently.
- [x] **Remaining delta: citation-context format** — align memory-hit citation/provenance formatting with deterministic contract expectations across BDD and pytest parity checks.
- [x] **Remaining delta: debug reason accuracy** — ensure debug/trace reason values reflect true confidence/ambiguity branch decisions for memory-recall turns.
- [x] Regenerate report/status artifacts with existing scripts only after acceptance criteria 1-3 are fully implemented and validated as passing (`artifacts/all-green-gate-summary.json`, `logs/turn_analytics_summary.json`).

### Remaining delta stage map

| Remaining delta item | Canonical stage | Why this stage is authoritative |
| --- | --- | --- |
| confident memory-recall recovery | `policy.decide` | Tie-break and ambiguity routing are decision-time controls that determine whether memory recall proceeds, clarifies, or falls back. |
| citation-context format | `answer.render` | Citation/provenance string shape is a rendered-output contract and must be deterministic in user-facing response text. |
| debug reason accuracy | `answer.validate` | Branch reason strings should be validated against confidence and ambiguity outcomes before final rendering/commit. |

- Sequence memory/provenance deltas against ISSUE-0012 Sprint 3 and Sprint 5 checkpoints so pre-route stabilization and answer validation changes are reviewed together.

- [x] Linked provenance/reason-code hardening: evidence channels remain class-separated into policy decisioning and answer assembly/validation now reject decision-vs-rendered class conflicts to protect knowing-mode provenance contracts.

## Verification

- Command: `python -m behave features/testbot/answer_contract.feature features/testbot/memory_recall.feature`
  - Observed (2026-03-09): exit `0` (pass).
- Command: `python -m pytest tests/test_runtime_logging_events.py tests/test_eval_runtime_parity.py`
  - Observed (2026-03-09): exit `0` (pass).
- Command: `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json`
  - Observed (2026-03-09): overall gate `failed` because `qa_validate_markdown_paths` failed; however `product_behave` is `passed` in the generated summary.
- Command: `python - <<'PY' ...` (JSON probe of `artifacts/all-green-gate-summary.json` for `product_behave`, `safety_behave_answer_contract_and_memory`, and `qa_eval_fixtures_and_runtime_parity` check IDs)
  - Observed (2026-03-09): `product_behave=passed`; `safety_behave_answer_contract_and_memory` and `qa_eval_fixtures_and_runtime_parity` are missing from the summary, so AC #3 is not fully satisfiable with current canonical gate output.

## Closure Notes

- 2026-03-06: Opened to provide capability-specific governance traceability for partial knowing-mode grounded answers.

- 2026-03-09: Completed remaining deltas for memory-recall recovery, citation-context formatting, and debug fallback reason accuracy; reran deterministic verification and refreshed readiness artifacts.

- 2026-03-09 (PR #325 verification refresh): Acceptance criteria 1-2 are currently satisfied by deterministic behave/pytest runs, but acceptance criterion 3 remains unmet because required check IDs are absent from current canonical gate summary output and the latest run also fails `qa_validate_markdown_paths`; status remains open with explicit residual blockers (AC-0009-R1, AC-0009-R2).
