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

- [Not Started] **Event model + scheduler:** introduce a minimal event envelope and dispatcher for loop processing (`user_utterance_received`, `background_ingestion_completed`, `poll_tick`) while keeping a single canonical pipeline authority for answer generation.
- [Blocked] **Input/poll integration:** add non-blocking read adapter or bounded wait strategy so periodic poll/timer events are processed even when no user input arrives; blocked by ISSUE-0019 engine boundary decision on adapter contracts.
- [Not Started] **Pending-start strictness:** harden validation/answer policy path so first pending-lookup response is always explicit ingestion-progress text and cannot be replaced by a GK fallback degrade path.
- [Blocked] **Completion fast-path:** route completion events through system-triggered loop path and emit linked user message + linked grounded answer immediately with idempotency guarantees; blocked by ISSUE-0019 shared dispatcher ownership.
- [Not Started] **Tests + BDD:** expand lifecycle scenarios for user-triggered start and system-triggered completion/timer polling and add deterministic ordering/no-input completion tests with correlation IDs.
- [In Progress] **Governance/docs sync:** update `docs/architecture.md`, relevant invariant/directive mirrors, and explicit issue linkage text across ISSUE-0019 and ISSUE-0020 as scheduler dependencies are clarified.

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

## Closure Notes

- 2026-03-09: Opened to capture the architecture-level follow-on from ISSUE-0017 after stakeholder clarification that lifecycle processing must be triggerable by both user and system, with timer/poll events processed through the same loop contract.
- This issue does not replace ISSUE-0017; it extends pending-ingestion lifecycle behavior from policy correctness into scheduler/trigger correctness and proactive timing guarantees.
