# ISSUE-0010: Unknowing safe fallback remains partial for explicit uncertainty contract completeness

- **ID:** ISSUE-0010
- **Title:** Unknowing safe fallback remains partial for explicit uncertainty contract completeness
- **Status:** open
- **Severity:** amber
- **Owner:** platform-qa
- **Created:** 2026-03-06
- **Target Sprint:** Sprint 2
- **Principle Alignment:** contract-first, user-centric, deterministic, traceable

## Cross-Reference

- Primary implementation/bug-elimination program: ISSUE-0013
- Normalized pending-lookup fallback semantics authority: ISSUE-0017 (`pending_lookup_background_ingestion` keeps non-clarify handling by mapping to answer mode `assist` with pending-lookup-safe final answers).
- This issue remains planning/history/context unless otherwise specified.

## Problem Statement

The `unknowing_safe_fallback` capability is still marked `partial`. ISSUE-0010 is the primary traceability record for this capability and tracks the remaining measurable deltas tied to its gate checks (`product_behave`, `safety_reflection_and_runtime_logging_pytests`), while preserving explicit cross-capability linkage with ISSUE-0009 in generated status reporting.

## Evidence

- `docs/qa/feature-status.yaml` marks `unknowing_safe_fallback` as `partial`.
- `docs/qa/feature-status-report.md` and `artifacts/feature-status-summary.json` list ISSUE-0009 and ISSUE-0010 as relevant open issues for this partial capability while `product_behave` remains failed for the capability's evidence profile.
- Contract behavior spans both BDD intent scenarios and deterministic reflection-policy/runtime-logging tests.

## Impact

- Incorrectly confident responses may leak into turns that should be explicit-uncertainty fallbacks.
- Safety posture can degrade if fallback messaging/action routing drifts from tested expectations.
- Stakeholders use ISSUE-0010 as the accountable primary mitigation tracker while ISSUE-0009 linkage remains visible for shared closure dependencies.

## Acceptance Criteria

1. `python -m behave features/testbot/answer_contract.feature features/testbot/intent_grounding.feature` passes for uncertainty/fallback scenarios.
2. `python -m pytest tests/test_reflection_policy.py tests/test_runtime_logging_events.py` passes.
3. `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json` reports `product_behave` and `safety_reflection_and_runtime_logging_pytests` as `passed`.
4. `docs/qa/feature-status.yaml` is updated to `implemented` for `unknowing_safe_fallback` only after criteria 1-3 are met.

### Residual blockers (post-PR #325 verification, 2026-03-09)

- AC-0010-R1: Canonical gate evidence currently does not expose `safety_reflection_and_runtime_logging_pytests` check ID in `artifacts/all-green-gate-summary.json`; acceptance criterion 3 cannot be fully satisfied until expected check naming/output is restored or this issue's gate contract is explicitly migrated to current canonical check names with validation updates.
- AC-0010-R2: `docs/qa/feature-status.yaml` still declares `unknowing_safe_fallback` as `partial`, so criterion 4 remains intentionally unmet pending AC-0010-R1 resolution.


## Enforcement mapping (implementation anchors)

| Acceptance criterion | Runtime/Policy enforcement points |
| --- | --- |
| AC #1 (`behave` answer+intent features) | `src/testbot/reflection_policy.py::decide_fallback_action` and `fallback_reason` enforce deterministic unknowing route selection and reason codes; `src/testbot/answer_render.py` and `src/testbot/answer_validate.py` keep render/validation boundaries explicit. |
| AC #2 (`pytest` reflection policy + runtime logging) | `src/testbot/reflection_policy.py` fallback matrix + reason strings plus `src/testbot/policy_decision.py` clarify-vs-labeled-general-knowledge decisioning for low-confidence and scored-empty paths, with normalized pending-lookup fallback semantics from ISSUE-0017 (`pending_lookup_background_ingestion` remains non-clarify and policy-safe). |
| AC #3 (all-green gate check IDs passed) | Canonical gate evidence from `scripts/all_green_gate.py`; policy/validation execution points remain `reflection_policy`, `policy_decision`, and answer validate/render boundaries. |
| AC #4 (status move to implemented) | `docs/qa/feature-status.yaml` capability status lifecycle, regenerated into markdown/JSON status artifacts. |

## Work Plan

- [x] Capture production-debug evidence trace and map symptoms to ISSUE-0009/ISSUE-0010 acceptance criteria (`docs/issues/evidence/production-debug-cli-trace-2026-03-07.md`).
- [x] **Remaining delta: confident memory-recall recovery** — complete memory confidence recovery updates so upstream product behave no longer fails from memory ambiguity edge cases that cascade into fallback posture.
- [x] **Remaining delta: citation-context format** — ensure uncertainty/fallback outputs keep explicit provenance and basis formatting aligned with contract text across intent-grounding and runtime logging checks.
- [x] **Remaining delta: debug reason accuracy** — reconcile debug/trace reason strings so low-confidence and unknown branches report accurate reasons for fallback decisions.
- [x] Regenerate report/status artifacts with existing scripts only after acceptance criteria 1-3 are fully implemented and validated as passing (`artifacts/all-green-gate-summary.json`, `logs/turn_analytics_summary.json`).

### Remaining delta stage map

| Remaining delta item | Canonical stage | Why this stage is authoritative |
| --- | --- | --- |
| confident memory-recall recovery | `policy.decide` | Upstream confidence recovery and ambiguity handling determine whether unknowing fallback is entered for memory-recall turns. |
| citation-context format | `answer.render` | Uncertainty and provenance/basis wording is a rendered-output contract that must stay deterministic across channels. |
| debug reason accuracy | `answer.validate` | Low-confidence vs unknown-branch reason strings should be validated against policy outcomes before render/commit. |

- Track fallback-contract completion as a dependency of ISSUE-0012 Sprint 4/5 review checkpoints for decision-answer alignment and commit-state consistency.

- [x] Linked uncertainty/reason-code hardening: empty-evidence vs scored-empty distinctions now carry explicit reason codes through policy decisioning, and answer validation rejects rendered-class conflicts before fallback rendering/commit.

## Verification

- Command: `python -m behave features/testbot/answer_contract.feature features/testbot/intent_grounding.feature`
  - Observed (2026-03-09): exit `0` (pass).
- Command: `python -m pytest tests/test_reflection_policy.py tests/test_runtime_logging_events.py`
  - Observed (2026-03-09): exit `0` (pass).
- Command: `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json`
  - Observed (2026-03-09): overall gate `failed` because `qa_validate_markdown_paths` failed; `product_behave` is `passed` in the generated summary.
- Command: `python - <<'PY' ...` (JSON probe of `artifacts/all-green-gate-summary.json` for `product_behave` and `safety_reflection_and_runtime_logging_pytests` check IDs)
  - Observed (2026-03-09): `product_behave=passed`; `safety_reflection_and_runtime_logging_pytests` is missing from the summary, so AC #3 is not fully satisfiable with current canonical gate output.

## Closure Notes

- 2026-03-06: Opened to establish explicit, measurable governance linkage for partial unknowing safe fallback capability.

- 2026-03-09: Completed remaining deltas for memory-recall recovery, citation-context formatting, and debug fallback reason accuracy; reran deterministic verification and refreshed readiness artifacts.

- 2026-03-09 (PR #325 verification refresh): Acceptance criteria 1-2 are currently satisfied by deterministic behave/pytest runs, but acceptance criterion 3 remains unmet because required check ID evidence is absent from current canonical gate summary output and the latest run also fails `qa_validate_markdown_paths`; status remains open with explicit residual blockers (AC-0010-R1, AC-0010-R2).
