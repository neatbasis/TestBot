# ISSUE-0017: Invariant boundary ambiguity permits answer-commit regressions under pending-lookup fallback paths

- **ID:** ISSUE-0017
- **Title:** Invariant boundary ambiguity permits answer-commit regressions under pending-lookup fallback paths
- **Status:** open
- **Severity:** amber
- **Owner:** runtime-pipeline
- **Created:** 2026-03-09
- **Target Sprint:** Sprint 8
- **Canonical Cross-Reference:** ISSUE-0013 (primary bug-elimination stream), ISSUE-0012 (delivery-plan context), ISSUE-0010 (unknowing fallback contract)
- **Principle Alignment:** contract-first, invariant-driven, traceable, deterministic, ci-enforced

## Problem Statement

A reproducible CLI runtime path fails with:

`AssertionError: Stage transition validation failed at answer.commit.post: inv_003_general_knowledge_contract_enforced`

The failure occurs in a pending-lookup branch where runtime behavior and commit-post invariant enforcement disagree on which fallback answers are policy-safe. Current enforcement centralizes multiple concerns (response-policy checks, alignment shape checks, provenance checks, and stage-transition checks) in `validate_answer_commit_post`, making mismatch diagnosis and policy evolution brittle.

This indicates an invariant-definition gap: response-policy constraints are not sufficiently unambiguous at edge-case boundaries, and enforcement layering does not cleanly separate concerns.

## Evidence

- Repro trace provided from `testbot --mode cli --debug-verbose` with first-turn query `What is ontology?` crashing in `answer.commit.post` on `inv_003_general_knowledge_contract_enforced`.
- `src/testbot/stage_transitions.py` currently allows broad assist/clarify fallback in `_follows_approved_fallback_path(...)` while `_is_gk_contract_safe_fallback(...)` is narrower for pending lookup under `assist`, creating policy inconsistency at commit-post.
- `validate_answer_commit_post(...)` aggregates policy checks (`inv_001`, `inv_002`, `inv_003`), alignment checks, provenance checks, and stage-semantics references in one boundary validator, increasing coupling and reducing diagnostic clarity.
- Existing tests in `tests/test_runtime_logging_events.py` include flows that monkeypatch `_validate_and_log_transition` off, which can mask runtime commit-post contract failures.
- Duplicate-prevention pre-check completed via:
  - `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json`
  - Result: no existing open issue explicitly isolates this invariant-boundary/concern-separation failure mode; ISSUE-0013 remains canonical stream anchor and this issue is filed as a focused sub-problem.

## Impact

- User-visible CLI crash on simple non-memory question paths when pending-lookup + fallback interactions hit invariant mismatch.
- Reduced confidence that invariant contracts are executable policy, not just static documentation.
- Higher regression risk because test harnesses can pass while runtime assertion guards fail.
- Slower triage due to mixed-failure surface (policy vs transition vs alignment/provenance all co-located).

## Acceptance Criteria

1. Define and document a single canonical rule for pending-lookup fallback semantics across `dont-know` and `assist` answer modes, including which final-answer forms are valid when GK contract is invalid.
2. Refactor commit-post enforcement so response-policy checks and stage-transition semantics are independently traceable (clear failure names and ownership), without weakening existing safety/citation/unknowing guarantees.
3. Add deterministic tests that execute the real transition validator path (no monkeypatch bypass) for the reported CLI regression branch.
4. Update invariant documentation (`docs/invariants/*` and mirrored directive surface where applicable) so prose constraints match executable checks.
5. Run and pass:
   - `python -m pytest tests/test_alignment_transitions.py tests/test_runtime_logging_events.py`
   - `python scripts/validate_issue_links.py --all-issue-files --base-ref HEAD~1`
   - `python scripts/validate_issues.py --all-issue-files --base-ref HEAD~1`
   - `python scripts/all_green_gate.py`

## Work Plan

- [ ] Capture minimal deterministic reproduction fixture for the pending-lookup CLI path in unit/integration tests.
- [ ] Normalize fallback-policy predicate definitions so assist/dont-know pending-lookup behavior is unambiguous and non-conflicting.
- [ ] Decouple commit-post checks into concern-specific groups (policy, alignment/provenance integrity, pipeline-stage semantics) while preserving existing contracts.
- [ ] Sync invariant docs and directive mirror text to match executable policy.
- [ ] Validate with targeted pytest + governance validators + canonical all-green gate.

## Verification

- Pending implementation.
- Initial duplicate-prevention pre-check command executed successfully:
  - `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json` (pass)

## Closure Notes

- 2026-03-09: Opened to track invariant-definition and enforcement-boundary ambiguity causing runtime `answer.commit.post` assertion failures on pending-lookup fallback branches.
- Routed under ISSUE-0013 as canonical pipeline bug-elimination anchor with explicit ISSUE-0010 linkage for unknowing fallback contract semantics.
