# ISSUE-0019: Channel-agnostic conversation engine with shared cross-channel history

- **ID:** ISSUE-0019
- **Title:** Channel-agnostic conversation engine with shared cross-channel history
- **Status:** open
- **Issue State:** governed_execution
- **Severity:** amber
- **Owner:** runtime-pipeline
- **Created:** 2026-03-09
- **Target Sprint:** Sprint 8
- **Canonical Cross-Reference:** ISSUE-0018 (dual-trigger proactive lifecycle scheduler that depends on this engine boundary), ISSUE-0020 (quickstart ingestion-toggle deprecation depends on unified orchestration contract), ISSUE-0017 (pending-ingestion lifecycle contract), ISSUE-0013 (canonical pipeline bug-elimination program), ISSUE-0012 (delivery-plan context)
- **Principle Alignment:** contract-first, invariant-driven, traceable, deterministic, user-centric, interface-neutral

## Problem Statement

Current runtime orchestration still couples core turn processing to channel-local loop behavior and in-memory adapter state:

- CLI and satellite adapters both call a shared loop, but loop progress depends on `read_user_utterance()` and channel IO timing.
- `chat_history` is instantiated as an adapter-local deque and passed around runtime paths, rather than managed as a channel-agnostic conversation state object keyed by conversation identity.

Stakeholder expectation is that CLI should behave like any channel transport and should not block system-originated lifecycle notifications (for example ingestion completion), while message history should not be tied to any specific channel adapter.

## Evidence

- Runtime enters a user-input loop and blocks on `read_user_utterance()` after each completion poll.
- `chat_history` is initialized as `deque(maxlen=10)` in startup and passed to mode-specific runners.
- Completion lifecycle semantics are already implemented with correlation IDs and linked completion events/answers, indicating orchestration/event-dispatch ownership is the remaining gap for interface-neutral behavior.
- ISSUE-0018 captures dual-trigger scheduling expectations but does not fully define the shared conversation-history model and channel decoupling contract.

## Impact

- Blocking adapters can delay user-visible system-originated notifications.
- Conversation continuity risks divergence if channel-specific runtime state becomes authoritative.
- Cross-interface behavior parity is harder to guarantee and test.
- Future multi-interface concurrency (CLI + satellite + additional transports) remains fragile without a canonical channel-neutral conversation state model.

## Acceptance Criteria

1. **Conversation engine boundary:** Introduce a channel-agnostic conversation engine that owns event handling and turn progression; channel adapters are reduced to transport-only inbound/outbound wrappers.
2. **Shared conversation history contract:** Replace channel-local history ownership with a canonical conversation history/state model keyed by conversation identity; retain channel as metadata only.
3. **Interface-neutral lifecycle delivery:** Pending-ingestion completion notifications and linked grounded answers are dispatched through the engine regardless of adapter read-loop blocking behavior.
4. **Backward-compatible telemetry:** Existing lifecycle events and correlation payload fields remain backward compatible (`ingestion_request_id`, `linked_pending_ingestion_request_id`, completion user-message/answer events).
5. **Deterministic tests added/updated:**
   - blocking-adapter scenario proves system-originated completion dispatch without requiring new user input,
   - shared-history scenario proves continuity across channel handoff in one conversation,
   - regression tests preserve current pending-ingestion causal linkage invariants.
6. **BDD coverage expanded:** Add/expand source-ingestion and continuity scenarios to reflect channel-agnostic dispatch + shared history behavior.
7. **Docs/invariants sync:** Update architecture and any relevant directive/invariant surfaces so runtime behavior and governance text remain aligned.
8. **Validation evidence attached:**
   - `python -m behave`
   - `python -m pytest -m "not live_smoke"`
   - `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`
   - `python scripts/validate_issues.py --all-issue-files --base-ref origin/main`
   - `python scripts/all_green_gate.py`

## Work Plan

- [ ] **ISSUE-0019-WP1 (target 2026-03-17):** Finalize engine boundary RFC defining event ownership, adapter responsibilities, and canonical dispatch API.
- [ ] **ISSUE-0019-WP2 (target 2026-03-18):** Refactor CLI/satellite adapters into transport-only wrappers that push/pull engine events without owning progression.
  **Depends on:** ISSUE-0019-WP1.
- [ ] **ISSUE-0019-WP3 (target 2026-03-18):** Introduce shared conversation history store keyed by conversation ID (channel retained as metadata) and migrate existing runtime paths.
  **Depends on:** ISSUE-0019-WP1.
- [ ] **ISSUE-0019-WP4 (target 2026-03-19):** Route pending-ingestion completion dispatch through engine to remove adapter-blocking delivery dependency.
  **Depends on:** ISSUE-0018-WP2, ISSUE-0019-WP2, ISSUE-0019-WP3.
- [ ] **ISSUE-0019-WP5 (target 2026-03-19):** Add deterministic tests + BDD for channel handoff continuity and system-originated completion delivery.
  **Depends on:** ISSUE-0019-WP4.
- [ ] **ISSUE-0019-WP6 (target 2026-03-20):** Sync architecture/invariant/directive docs and cross-issue links with finalized engine model.
  **Depends on:** ISSUE-0019-WP5, ISSUE-0018-WP6, ISSUE-0020-WP3.

## Current State (2026-03-14)

- **Scope:** establish channel-agnostic engine ownership and shared-history authority to unlock scheduler and ingestion-contract workstreams.
- **Owner:** runtime-pipeline.
- **Blocker:** no approved RFC yet for event-dispatch ownership between engine and adapters.
- **Next Action:** complete ISSUE-0019-WP1 RFC sign-off and start adapter refactor (ISSUE-0019-WP2) immediately afterward.

## Cross-Issue Dependency Map

- **Unblocks ISSUE-0018:** ISSUE-0019-WP1/WP2/WP3 are prerequisites for ISSUE-0018-WP1/WP2/WP4 dual-trigger scheduler wiring.
- **Unblocks ISSUE-0020:** ISSUE-0019-WP3 shared-history/engine contract constrains ISSUE-0020 default-ingestion enablement behavior and docs wording.
- **Depends on ISSUE-0018:** ISSUE-0019-WP4 consumes ISSUE-0018-WP2 bounded-poll semantics to guarantee non-user-triggered completion dispatch timing.

## Triage Notes

- **2026-03-14:** **Phase:** in progress. **Immediate next owner action:** complete engine boundary RFC/implementation slice for adapter decoupling and shared-history ownership, then hand interface contract updates to ISSUE-0018 and ISSUE-0020 owners. **Target review date:** 2026-03-20.


## Verification

Planned closure bundle:

```bash
python -m behave
python -m pytest -m "not live_smoke"
python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
python scripts/validate_issues.py --all-issue-files --base-ref origin/main
python scripts/all_green_gate.py
```

Expected pass signal:
- channel-agnostic dispatch behavior is deterministic,
- shared conversation history is authoritative across adapters,
- lifecycle linkage and telemetry invariants remain stable,
- canonical gate is green in same change window.

Governance-validation artifacts (current branch triage run):
- `artifacts/issue-triage-2026-03-14/validate_issue_links.txt`
- `artifacts/issue-triage-2026-03-14/validate_issues.txt`

Next verification artifact expected for this issue:
- `artifacts/issue-0019/2026-03-20/channel-handoff-history-parity.json`

## Closure Notes

- 2026-03-09: Opened from stakeholder request to operationalize interface-neutral orchestration and channel-independent message history, complementing (not replacing) ISSUE-0018 scheduler semantics.
