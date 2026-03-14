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

- [x] **ISSUE-0017-WP1 (completed 2026-03-14):** Capture deterministic reproduction fixture for pending-lookup CLI path in unit/integration tests.
- [x] **ISSUE-0017-WP2 (completed 2026-03-14, depends on ISSUE-0017-WP1):** Normalize fallback-policy predicates so assist/dont-know pending-lookup behavior is non-conflicting.
- [x] **ISSUE-0017-WP3 (completed 2026-03-14, depends on ISSUE-0017-WP2):** Decouple commit-post checks into concern-specific validators (policy, alignment/provenance, pipeline-stage semantics).
- [x] **ISSUE-0017-WP4 (completed 2026-03-14, depends on ISSUE-0017-WP3):** Sync invariant/directive mirror text to executable policy.
- [ ] **ISSUE-0017-WP5 (target 2026-03-18, depends on ISSUE-0017-WP4 + ISSUE-0018-WP3):** Re-run reopened CLI-path evidence with strict pending-start semantics and capture behavior deltas.
- [ ] **ISSUE-0017-WP6 (target 2026-03-18, depends on ISSUE-0017-WP5):** Execute targeted pytest, issue validators, and canonical gate; attach artifacts and closure recommendation.

## Current State (2026-03-14)

- **Scope:** finalize reopened regression evidence against strict pending-lookup lifecycle semantics.
- **Owner:** runtime-pipeline.
- **Blocker:** pending-start strictness handoff from ISSUE-0018 is required before final replay evidence is conclusive.
- **Next Action:** start ISSUE-0017-WP5 immediately after ISSUE-0018-WP3 merges, then complete ISSUE-0017-WP6.

## Cross-Issue Dependency Map

- **Depends on ISSUE-0018:** ISSUE-0018-WP3 provides strict pending-start semantics required by ISSUE-0017-WP5 replay.
- **Informs ISSUE-0019:** commit-post concern boundaries from ISSUE-0017 reduce policy/engine coupling during ISSUE-0019 dispatcher refactor.
- **Informs ISSUE-0020:** fallback-policy invariants from ISSUE-0017 remain mandatory guardrails when ISSUE-0020 changes ingestion-enable defaults.

## Triage Notes

- **2026-03-14:** **Phase:** in progress. **Immediate next owner action:** execute issue-governance validators and canonical gate against the current branch, then reconcile reopened CLI-path behavior evidence with ISSUE-0018 lifecycle semantics before closure decision. **Target review date:** 2026-03-18.

## Verification

- Implementation delivered in:
  - `ad5d5e3` (`src/testbot/stage_transitions.py` fallback classification normalization)
  - `70115a8` (`src/testbot/stage_transitions.py` concern-specific validator refactor + `tests/test_alignment_transitions.py` coverage)
  - `a90a466` (pending-lookup regression path coverage in `tests/test_runtime_logging_events.py`)
  - `6291fe3` (invariant/directive and issue-governance text sync)
- Initial duplicate-prevention pre-check command executed successfully:
  - `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json` (pass)
- Reopen evidence (operator report, 2026-03-09): with `SOURCE_INGEST_ASYNC_CONTINUATION=1 TESTBOT_DEBUG=1 testbot --mode cli --debug-verbose`, first-turn `What is life?` entered `pending_lookup_background_ingestion` (`answer_mode=assist`, `fallback_action=ANSWER_UNKNOWN`) and produced uncertainty fallback text; issue remains open until the expected pending-lookup UX/policy outcome is explicitly validated and attached to deterministic acceptance evidence.
- Canonical validation commands for this issue remain mandatory before closure (`pytest` targets + issue validators + `all_green_gate`).
- 2026-03-14 governance-validation artifacts (current branch):
  - `artifacts/issue-triage-2026-03-14/validate_issue_links.txt`
  - `artifacts/issue-triage-2026-03-14/validate_issues.txt`
- Next verification artifact expected:
  - `artifacts/issue-0017/2026-03-18/cli-pending-lookup-replay.log`

## Closure Notes

- 2026-03-09: Opened to track invariant-definition and enforcement-boundary ambiguity causing runtime `answer.commit.post` assertion failures on pending-lookup fallback branches.
- Routed under ISSUE-0013 as canonical pipeline bug-elimination anchor with explicit ISSUE-0010 linkage for unknowing fallback contract semantics.
- 2026-03-09: Marked resolved after fallback normalization, commit-post validator separation, deterministic regression coverage, and invariant/doc sync landed.
- 2026-03-09: Reopened after operator CLI verification under `SOURCE_INGEST_ASYNC_CONTINUATION=1` showed unresolved pending-lookup closure evidence gap; do not re-close until canonical validation bundle and explicit expected-outcome evidence are attached.
