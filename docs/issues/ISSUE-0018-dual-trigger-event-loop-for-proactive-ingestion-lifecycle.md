# ISSUE-0018: Dual-trigger event loop for proactive ingestion lifecycle (user + system initiated processing)

- **ID:** ISSUE-0018
- **Title:** Dual-trigger event loop for proactive ingestion lifecycle (user + system initiated processing)
- **Status:** open
- **Severity:** amber
- **Owner:** runtime-pipeline
- **Created:** 2026-03-09
- **Target Sprint:** Sprint 8
- **Canonical Cross-Reference:** ISSUE-0017 (latest pending-ingestion lifecycle contract/closure evidence), ISSUE-0019 (channel-agnostic conversation engine dependency for adapter decoupling), ISSUE-0020 (quickstart ingestion-toggle deprecation depends on scheduler semantics), ISSUE-0013 (canonical pipeline bug-elimination program), ISSUE-0012 (delivery-plan context), ISSUE-0010 (unknowing fallback contract)
- **Principle Alignment:** contract-first, invariant-driven, traceable, deterministic, ci-enforced, user-centric

## Problem Statement

The current chat loop is primarily user-driven: completion processing is polled at loop boundaries, then execution blocks on input reads. This can delay system-originated lifecycle actions (for example background-ingestion completion notices) until user input resumes in blocking interfaces.

Stakeholder expectation requires two explicit lifecycle guarantees:

1. first pending-lookup turn always emits explicit start text ("I'm ingesting external sources in the background now…"), and
2. completion notifications/answers are proactively surfaced as soon as completion is observed, without requiring a follow-up user turn.

To satisfy this robustly across interfaces, loop processing must support both **user-initiated events** and **system-initiated events**, including timer/poll events.

## Evidence

- Current runtime loop processes background completion once per loop, then waits for `read_user_utterance()`, which can block proactive completion output in CLI-style interfaces.
- Runtime already has completion linkage + proactive emit semantics once completion is processed (`source_ingest_completion_event_emitted`, `source_ingest_completion_user_message_emitted`, linked continuation answer), indicating loop-triggering rather than completion payload shape is the remaining architecture gap.
- Pending-lookup answer policy still allows both explicit progress and uncertainty fallback text, so "always explicit ingestion start text" is not yet a strict contract.
- Existing deterministic tests validate lifecycle pieces and synthetic event ordering, but do not yet enforce a true dual-trigger scheduler contract with timer/poll events as first-class triggers.

## Impact

- User-facing latency/ambiguity for completion notices in blocking input modes.
- Inconsistent lifecycle UX across interfaces (CLI vs any non-blocking interface).
- Residual acceptance-criterion ambiguity for "always explicit start line" semantics.
- Continued issue churn where behavior appears correct in logs but not timely from the user perspective.

## Acceptance Criteria

1. **Dual-trigger loop contract defined:** runtime loop accepts both user-originated and system-originated events as canonical triggers (including timer/poll events).
2. **First-turn pending start guarantee:** when `pending_lookup_background_ingestion` is active on first turn, the emitted user-facing answer is always `BACKGROUND_INGESTION_PROGRESS_ANSWER`.
3. **Proactive completion guarantee:** when ingestion completion is detected, completion user message + linked grounded answer are emitted without waiting for a new user utterance.
4. **Causal linkage preserved:** completion emissions include linkage fields that match persisted pending request correlation keys.
5. **Deterministic tests added/updated:** runtime tests cover event ordering and timing semantics under blocking and non-blocking input adapters, including timer/poll-trigger processing.
6. **BDD lifecycle scenario expanded:** source-ingestion BDD includes user-triggered start and system-triggered completion/timer polling behavior.
7. **Docs/invariants synced:** architecture + invariant/directive text is updated to reflect strict pending-start and dual-trigger proactive completion semantics.
8. **Validation evidence attached:**
   - `python -m behave features/source_ingestion.feature features/answer_contract.feature`
   - `python -m pytest tests/test_runtime_logging_events.py tests/test_runtime_modes.py tests/test_alignment_transitions.py`
   - `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`
   - `python scripts/validate_issues.py --all-issue-files --base-ref origin/main`
   - `python scripts/all_green_gate.py`

## Work Plan

- [ ] **ISSUE-0018-WP1 (target 2026-03-17):** Publish event envelope + scheduler contract (`user_utterance_received`, `poll_tick`, `background_ingestion_completed`) with explicit engine ownership boundaries.  
  **Depends on:** ISSUE-0019-WP1.
- [ ] **ISSUE-0018-WP2 (target 2026-03-18):** Implement bounded-wait/non-blocking input integration so poll/timer events progress without new user input.  
  **Depends on:** ISSUE-0018-WP1, ISSUE-0019-WP2.
- [ ] **ISSUE-0018-WP3 (target 2026-03-18):** Enforce strict first-turn pending-start answer (`BACKGROUND_INGESTION_PROGRESS_ANSWER`) in all pending lookup flows.  
  **Depends on:** ISSUE-0017-WP4, ISSUE-0018-WP1.
- [ ] **ISSUE-0018-WP4 (target 2026-03-19):** Route completion fast-path through system-triggered loop with idempotent linked completion message + grounded answer emission.  
  **Depends on:** ISSUE-0018-WP2, ISSUE-0018-WP3, ISSUE-0019-WP3.
- [ ] **ISSUE-0018-WP5 (target 2026-03-19):** Expand deterministic tests + BDD for user-triggered start and system-triggered completion under no-input conditions.  
  **Depends on:** ISSUE-0018-WP4.
- [ ] **ISSUE-0018-WP6 (target 2026-03-19):** Complete docs/governance sync across architecture/invariants/directives and linked issue records.  
  **Depends on:** ISSUE-0018-WP5, ISSUE-0019-WP5, ISSUE-0020-WP1.

## Current State (2026-03-14)

- **Scope:** finalize dual-trigger scheduler behavior and strict pending-start guarantee for proactive ingestion lifecycle.
- **Owner:** runtime-pipeline.
- **Blocker:** engine boundary and adapter ownership decision from ISSUE-0019 is still required for scheduler wiring.
- **Next Action:** close ISSUE-0019-WP1/WP2, then execute ISSUE-0018-WP1 and ISSUE-0018-WP2 as the immediate implementation slice.

## Cross-Issue Dependency Map

- **Depends on ISSUE-0019:** ISSUE-0019-WP1/WP2 define engine/adaptor boundaries required by ISSUE-0018-WP1/WP2; ISSUE-0019-WP3 is required by ISSUE-0018-WP4.
- **Unblocks ISSUE-0017:** ISSUE-0018-WP3 is consumed by ISSUE-0017-WP5 for reopened CLI-path replay closure evidence.
- **Unblocks ISSUE-0020:** ISSUE-0018-WP4 lifecycle semantics feed ISSUE-0020-WP1 contract decision and quickstart deprecation language.

## Triage Notes

- **2026-03-14:** **Phase:** blocked. **Immediate next owner action:** finalize ISSUE-0019 conversation-engine ownership boundaries, then implement dual-trigger scheduler wiring and unblock completion fast-path tasks. **Target review date:** 2026-03-19.


## Verification

Planned verification bundle for closure:

```bash
python -m behave features/source_ingestion.feature features/answer_contract.feature
python -m pytest tests/test_runtime_logging_events.py tests/test_runtime_modes.py tests/test_alignment_transitions.py
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
python scripts/validate_issues.py --all-issue-files --base-ref origin/main
python scripts/all_green_gate.py
```

Expected pass signal:
- lifecycle BDD scenarios pass with strict start-message and proactive completion semantics,
- runtime deterministic tests prove dual-trigger + timer/poll behavior,
- governance validators pass,
- canonical all-green gate passes.

Governance-validation artifacts (current branch triage run):
- `artifacts/issue-triage-2026-03-14/validate_issue_links.txt`
- `artifacts/issue-triage-2026-03-14/validate_issues.txt`

Next verification artifact expected for this issue:
- `artifacts/issue-0018/2026-03-19/dual-trigger-event-order-report.md`

## Closure Notes

- 2026-03-09: Opened to capture the architecture-level follow-on from ISSUE-0017 after stakeholder clarification that lifecycle processing must be triggerable by both user and system, with timer/poll events processed through the same loop contract.
- This issue does not replace ISSUE-0017; it extends pending-ingestion lifecycle behavior from policy correctness into scheduler/trigger correctness and proactive timing guarantees.
