# ISSUE-0014: CLI self-identity turns are stabilized structurally but semantically misrouted before memory retrieval and durable fact promotion

- **ID:** ISSUE-0014
- **Title:** CLI self-identity turns are stabilized structurally but semantically misrouted before memory retrieval and durable fact promotion
- **Status:** open
- **Severity:** red
- **Owner:** platform-qa
- **Created:** 2026-03-08
- **Target Sprint:** Sprint 6
- **Canonical Cross-Reference:** ISSUE-0013 (primary bug-elimination stream), ISSUE-0012 (delivery-plan governance), ISSUE-0015 (quality/governance hardening review)
- **Principle Alignment:** contract-first, invariant-driven, traceable, deterministic, ci-enforced

## Cross-Reference

- Routing anchor: ISSUE-0013 (**blocker** in current execution order; identity-continuity behavioral gate for AC-0013-11).
- Execution-order linkage: ISSUE-0008 -> ISSUE-0011 -> ISSUE-0012 (parallel stream) -> ISSUE-0014 -> ISSUE-0015.
- Delivery/governance companion references: ISSUE-0012 (delivery-plan governance), ISSUE-0015 (quality/governance hardening review).

## Problem Statement

Recent production-style CLI debug logs show the canonical turn pipeline now preserves richer pre-route structure (observation, candidate encoding, stabilization, segment constraints, same-turn exclusion), but the turn is still semantically misinterpreted before retrieval/decisioning can activate memory-grounded behavior. This causes self-identity declarations and immediate self-referential follow-ups to be handled as generic direct-answer knowledge turns instead of memory/context turns.

## Observed Behavior

### Turn 1: `Hi! I'm sebastian`

- Observation and stabilization artifacts are created with durable turn structure (utterance records, stabilized facts, segment/retrieval constraints, same-turn exclusion hygiene).
- Query rewrite inverts user meaning from self-identification into assistant-focused Q&A.
- The turn is then classified as `knowledge_question` and routed to `direct_answer` with `evidence_posture=not_requested`.
- Retrieval and rerank stages are skipped.
- No durable identity confirmation is promoted (`confirmed_user_facts=[]`).
- Answer contract fails and fallback response path is emitted.

### Turn 2: `Who am I?`

- The follow-up is again classified as `knowledge_question`, routed to `direct_answer`, and skips retrieval/rerank.
- Existing continuity signals (including last-user timestamp and prior turn commit trail) do not recover memory/self-reference intent.
- The final response again follows empty-evidence fallback behavior.

## Expected Behavior

### Turn 1 expected (`Hi! I'm sebastian`)

- Rewrite must preserve user meaning and must not convert self-identification into assistant-focused intent.
- Intent resolution should classify this as identity/profile declaration context (not generic `knowledge_question`).
- Decisioning should preserve a memory-usable path so durable user fact candidates can be promoted at commit (`user_name=sebastian` or equivalent normalized fact).

### Turn 2 expected (`Who am I?`)

- Context + intent resolution should treat this as self-referential memory recall dependent on prior committed user facts.
- Retrieval should be requested and evaluated against stabilized/committed continuity artifacts.
- Policy + answer assembly should produce memory-grounded identity recall (or explicit clarification if evidence is genuinely insufficient), not default direct-answer fallback due to skipped retrieval.

## Root-Cause Hypothesis

1. **Rewrite-stage semantic inversion defect**
   - The rewrite transform introduces meaning drift that changes discourse object type (self-identification statement -> assistant-knowledge question).
2. **Intent/context underweighting of stabilized and continuity signals**
   - Decisioning appears to over-trust rewritten text and/or coarse intent defaults while underusing stabilized candidate facts and commit continuity anchors.
3. **Premature direct-answer routing**
   - `direct_answer` branch assignment occurs before memory/self-reference checks are fully resolved, forcing retrieval/rerank skips and starving downstream policy stages of evidence.
4. **Commit promotion gap for identity facts under misroute conditions**
   - Even with stabilization artifacts present, misrouting prevents promotion of `confirmed_user_facts`, so next-turn identity recall cannot succeed deterministically.

## Defect Taxonomy

### Earliest primary defect stage

- **Primary defect (rewrite stage):** self-identification discourse is transformed into assistant-focused Q&A intent, changing discourse object type before intent/routing evaluation.

### Downstream cascade defects

- **Cascade A (intent stage):** intent resolution over-weights rewritten text and under-weights stabilized identity candidates and continuity anchors.
- **Cascade B (routing stage):** misclassified turn is routed to `direct_answer`, forcing retrieval/rerank skip path.
- **Cascade C (commit stage):** identity candidates are not promoted to `confirmed_user_facts` because memory path prerequisites were bypassed.

## Earliest Invalid State

- **First forbidden transformation:** `user self-identity declaration` -> `assistant-knowledge question` at rewrite output for Turn 1 (`Hi! I'm sebastian`).
- Any pipeline state at or after this transformation is considered invalid for identity-continuity handling unless rewrite output is corrected before intent/routing commit points.

## Stage Contract Clauses

1. **Rewrite contract (testable):** For self-identification utterances, rewrite must preserve discourse object type as `user_identity_declaration`; transformed text must not invert speaker/subject perspective.
2. **Intent contract (testable):** If stabilized facts contain identity candidates and/or self-reference cues, intent must resolve to a memory/profile-aware class, never defaulting to generic `knowledge_question` without an explicit override rationale.
3. **Routing contract (testable):** For self-reference recall turns with continuity anchors present, routing must request retrieval evaluation and must not select `direct_answer` as terminal branch prior to memory-path checks.
4. **Commit contract (testable):** When identity candidates are stabilized and no contradiction exists, commit must either promote confirmed identity facts or emit explicit denial reason; silent non-promotion is forbidden.

## Quality-System Gap Analysis

- Existing BDD/pytest coverage validated structural pipeline stabilization and generic routing behavior, but did not pin semantic discourse-type invariance across rewrite -> intent -> routing transitions for identity turns.
- Current gates emphasize aggregate green status and component-level checks; they did not include an end-to-end deterministic scenario asserting identity declaration -> immediate self-recall with behavioral outcome proof.
- Telemetry assertions were present for branch/skip events, but lacked required fields to distinguish semantically valid skips from misroute-induced skips, allowing false confidence from structurally complete traces.

## Required Observability Fields

The following trace keys are mandatory for identity declaration and self-reference recall turns:

1. `rewrite_discourse_type_pre`
2. `rewrite_discourse_type_post`
3. `self_reference_detection_result`
4. `continuity_anchor_present`
5. `retrieval_skip_rationale`
6. `commit_promotion_denial_reason`

Missing any mandatory field in relevant turns is a validation failure for ISSUE-0014 closure evidence.

## Regression History Classification

- **Newly introduced regression:** not yet proven.
- **Pre-existing defect newly observed via improved instrumentation:** currently most plausible, pending blame/timeline confirmation.
- **Acceptance-criteria under-specification contribution:** confirmed; prior ISSUE-0014 wording permitted structural-progress interpretation without requiring behavioral identity-continuity proof.

Closure evidence must explicitly classify the defect into exactly one primary history bucket, with supporting trace/test rationale.

## Invariant Breach Language

This issue represents a runtime breach (or high-risk near-breach) of canonical pipeline invariants and doctrine:

- **Observe-before-infer / Stabilize-before-route:** preserved structurally but not honored semantically when downstream routing ignores stabilized identity signals.
- **Intent derived from enriched state, not raw/transformed text alone:** violated when rewrite-drifted text dominates intent resolution.
- **Retrieval-policy coherence:** violated when self-referential memory turns are labeled non-memory and routed to `direct_answer` with retrieval not requested.
- **Decision-answer alignment:** degraded when known memory-recall posture is effectively converted into generic fallback behavior due to early branch misclassification.

## Evidence

- Session log artifact: [`docs/issues/evidence/production-debug-cli-session-log-2026-03-08-21-23.jsonl`](evidence/production-debug-cli-session-log-2026-03-08-21-23.jsonl)
- Analyst notes mapped to canonical stages and defects (batch 21:23): [`docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md`](evidence/production-debug-cli-session-log-notes-2026-03-08-21-23.md)
- Additional analyst findings (batch 21:52): [`docs/issues/evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md`](evidence/production-debug-cli-session-log-notes-2026-03-08-21-52.md)

Key observed indicators in evidence include:

- rewrite inversion to assistant-focused query text,
- `retrieval_branch_selected=direct_answer`,
- retrieval/rerank skip events,
- empty `confirmed_user_facts`,
- fallback completion despite available stabilization structure.


### Additional findings from evidence batch 21:52

- Confirms that foundation instrumentation improvements are real, but semantically insufficient without downstream decisioning correction.
- Reaffirms rewrite-stage semantic inversion as the earliest high-leverage failure that cascades into retrieval and commit starvation.
- Reaffirms that self-reference follow-up (`Who am I?`) remains misrouted as generic direct-answer instead of memory/context identity recall despite continuity traces.
- Reaffirms that commit receipts exist but fail to promote identity facts into `confirmed_user_facts` under current misroute path.

## Impact

- Self-identity and self-reference flows remain unreliable in production-like CLI runs.
- Canonical pipeline foundation improvements do not convert into user-visible memory-grounded behavior.
- ISSUE-0013 acceptance-criteria closure remains blocked for decisioning + commit semantics tied to identity continuity.
- User trust is degraded when the assistant cannot maintain memory-backed self-identity continuity across adjacent turns.
- Memory-backed identity continuity integrity is at risk: structural trace completeness can mask semantic corruption, creating capability-status misrepresentation risk.

## Acceptance Criteria

1. Add deterministic BDD and pytest coverage for the exact reproduction pair:
   - `Hi! I'm sebastian`
   - `Who am I?`
   asserting rewrite semantic preservation, memory-appropriate intent resolution, retrieval activation, durable fact promotion, and user-visible memory-grounded recall outcome.
2. Rewrite layer must preserve discourse object type for self-identification utterances.
3. Intent/context resolution must prefer stabilized identity facts and continuity anchors over generic knowledge fallback defaults for self-reference follow-ups.
4. Retrieval branch must not default to `direct_answer` for self-referential identity recall turns when continuity artifacts exist.
5. Commit receipts must include confirmed identity facts when stabilization extracted durable identity candidates and no explicit contradiction exists.
6. Canonical gate evidence (`python scripts/all_green_gate.py`) and feature-status reporting must reflect closure progress without over-claiming implemented status.
7. ISSUE-0014 cannot be closed on structural telemetry alone; closure requires behavioral proof (deterministic tests + reproducible CLI evidence) that identity declaration and immediate self-recall are semantically correct end-to-end.
8. ISSUE-0013 linkage: ISSUE-0013 identity-continuity milestones remain non-closable while ISSUE-0014 behavioral proof criteria are unmet, even if structural instrumentation appears complete.

## Work Plan

- Add/extend feature scenarios in `features/memory_recall.feature` and `features/intent_grounding.feature` for identity declaration + recall continuity.
- Add deterministic regression tests covering rewrite invariance, intent routing, retrieval branch selection, and commit receipt promotion fields.
- Tighten decisioning logic so self-reference identity turns cannot bypass retrieval solely via rewrite-drifted phrasing.
- Re-run canonical gates and regenerate status artifacts after behavior is corrected.
- Record closure evidence under ISSUE-0013 with explicit AC traceability.

## Verification

- Command: `python -m behave features/memory_recall.feature features/intent_grounding.feature`
  - Expected: identity declaration + recall continuity scenarios pass.
- Command: `python -m pytest -m "not live_smoke"`
  - Expected: regression tests for rewrite/intent/retrieval/commit continuity pass.
- Command: `python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json`
  - Expected: gate reflects resolved regression without masking unrelated failures.
- Command: `python -m pytest -vv tests/test_pipeline_semantic_contracts.py::test_resolve_turn_intent_matches_canonical_intent_resolution_for_identity_followup`
  - Expected: reproducible CLI trace artifact for semantic-preservation criterion is generated.
- Command: `python -m pytest -vv tests/test_pipeline_semantic_contracts.py::test_policy_authority_is_not_written_before_policy_decide_stage`
  - Expected: reproducible CLI trace artifact for retrieval-activation criterion is generated.
- Command: `python -m pytest -vv tests/test_answer_commit_identity_promotion.py::test_promoted_identity_fact_is_available_as_next_turn_continuity_anchor`
  - Expected: reproducible CLI trace artifact for commit-promotion criterion is generated.
- Command: `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`
  - Expected: governance cross-links validate for ISSUE-0013/0014/0015 dependency chain.
- Command: `python scripts/validate_issues.py --all-issue-files --base-ref origin/main`
  - Expected: canonical issue schema and lifecycle metadata remain valid after dependency updates.

### Closure-proof evidence references (identity continuity dependency)

Deterministic suite evidence is attached and reproducible CLI identity-continuity traces are now attached for each required proof point:

1. **Identity semantic preservation (rewrite/intent contract).**
   - Required trace artifact path: `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md`.
   - Deterministic reproduction steps:
     1. `python -m behave features/memory_recall.feature features/intent_grounding.feature`
     2. `python -m pytest tests/test_pipeline_semantic_contracts.py tests/test_canonical_turn_orchestrator.py tests/test_intent_router.py`
     3. Run CLI reproducer turn pair in a clean local session and attach trace showing rewrite output preserves `user_identity_declaration` semantics for `Hi! I'm sebastian`.
2. **Retrieval activation on self-reference recall (routing/retrieval contract).**
   - Required trace artifact path: `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md`.
   - Deterministic reproduction steps:
     1. Repeat the same deterministic command set above.
     2. In the same CLI repro session, run follow-up turn `Who am I?` and capture stage trace proving retrieval activation (not default `direct_answer` bypass).
3. **Confirmed identity fact promotion at commit (commit contract).**
   - Required trace artifact path: `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md`.
   - Deterministic reproduction steps:
     1. Repeat the same deterministic command set above.
     2. Capture commit-stage receipt trace for the repro session proving confirmed identity fact promotion (`confirmed_user_facts` contains normalized user identity fact) and next-turn recall consumption.

### Evidence-to-acceptance mapping (ISSUE-0014 checklist)

- `docs/issues/evidence/2026-03-09-issue-0014-cli-identity-semantic-preservation-trace.md` -> **AC2, AC3, AC7** (rewrite/intent semantic preservation proof for identity follow-up parity).
- `docs/issues/evidence/2026-03-09-issue-0014-cli-self-reference-retrieval-activation-trace.md` -> **AC3, AC4, AC7** (self-reference turns remain in retrieval-enabled memory branch, not direct-answer bypass).
- `docs/issues/evidence/2026-03-09-issue-0014-cli-confirmed-fact-promotion-trace.md` -> **AC5, AC7** (commit receipt confirmed identity fact promotion and next-turn continuity-anchor consumption).
- `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md` (+ linked logs) -> **AC1, AC6, AC8** (deterministic BDD/pytest/gate evidence and ISSUE-0013 dependency linkage).

Status: **dependency evidence attached; lifecycle still open/red pending governance closure decision** — required CLI trace artifact files are attached and map directly to acceptance criteria, so ISSUE-0013 AC-0013-11 dependency evidence is now satisfiable subject to synchronized governance state updates across ISSUE-0013/0014/0015/RED_TAG.

## Phase 1 Behavioral Exit Evidence (2026-03-09)

- Evidence bundle: [`docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md`](evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md)
- BDD result (**pass**): [`2026-03-09-issue-0014-0013-behave.log`](evidence/2026-03-09-issue-0014-0013-behave.log)
- Focused pytest result (**pass**): [`2026-03-09-issue-0014-0013-focused-pytests.log`](evidence/2026-03-09-issue-0014-0013-focused-pytests.log)
- Canonical all-green gate result (**pass with warning mode**): [`2026-03-09-issue-0014-0013-all-green-gate.log`](evidence/2026-03-09-issue-0014-0013-all-green-gate.log), [`artifacts/all-green-gate-summary.json`](../../artifacts/all-green-gate-summary.json)

Phase 1 status: **behavioral evidence satisfied; governance closure pending**. Targeted deterministic checks pass, canonical gate reports `status=passed` with warning-mode KPI guardrail handling (non-blocking by current gate policy), and all three reproducible CLI identity-continuity closure-proof traces are now attached for identity semantic preservation, retrieval activation on self-reference recall, and confirmed identity fact promotion at commit.

Governance validator rerun (2026-03-09):
- `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main` -> **pass** (base-ref fallback `origin/main` -> `HEAD~1`).
- `python scripts/validate_issues.py --all-issue-files --base-ref origin/main` -> **pass** (`--pr-body-file` not provided; base-ref fallback `origin/main` -> `HEAD~1`).

## Closure Notes

- 2026-03-09: Closure posture remains open by dependency gate; see synchronized red-tag triage note below for current blocker state.

## Red-tag triage note (dependency gate)

- Last reviewed: 2026-03-09
- Next review due: 2026-03-16
- KPI evidence: docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md
- Decision notes: Phase 1 deterministic suites and required CLI closure-proof traces are attached with AC mapping complete; issue remains open/red only for synchronized dependency-gate governance closure interpretation across ISSUE-0013/0014/0015/RED_TAG.

- 2026-03-08: Opened from production-style CLI session evidence showing stabilization progress with persistent semantic routing and fact-promotion defects in identity continuity turns.

## Cross-Functional Session Preparation (Sprint 6)

- Session plan artifact: [`docs/sessions/ISSUE-0014-cross-functional-session-plan.md`](../sessions/ISSUE-0014-cross-functional-session-plan.md)
- Session length: 90-120 minutes
- Scope locked: identity declaration + self-reference recall regression in CLI canonical pipeline.

### Owner Matrix (D1)

| Role | Team | Assigned Owner | Backup |
|---|---|---|---|
| Facilitator | platform-qa | _TBD_ | _TBD_ |
| Scribe | release governance | _TBD_ | _TBD_ |
| Rewrite owner | runtime/pipeline engineering | _TBD_ | _TBD_ |
| Intent/routing owner | runtime/pipeline engineering | _TBD_ | _TBD_ |
| Commit/persistence owner | runtime/pipeline engineering | _TBD_ | _TBD_ |
| Test/BDD owner | test/BDD ownership | _TBD_ | _TBD_ |

### Session Execution Contract (D0-D8)

1. D0 Plan: confirm scope, artifacts, and goals (root cause, containment, corrective actions, verification).
2. D1 Team: finalize role assignments and update the matrix above in-issue.
3. D2 Problem Description: complete 5W2H with exact reproducer:
   - Turn 1: `Hi! I'm sebastian`
   - Turn 2: `Who am I?`
   - Must record observed vs expected for rewrite -> intent -> branch selection -> retrieval/rerank -> commit promotion -> response.
4. D3 Interim Containment: define temporary rewrite + routing guards and pair each with deterministic regression tests.
5. D4 Root Cause Analysis: confirm evidence-led fault tree and causal chain via trace checkpoints.
6. D5 Permanent Corrective Actions: approve owner/file-mapped changes in `src/testbot/`, `features/`, and `tests/`.
7. D6 Implement & Validate: execute required validation gates and produce AC traceability evidence.
8. D7 Prevent Recurrence: add regression/invariant coverage and governance updates if impacted.
9. D8 Closure & Recognition: close only after ISSUE-0014 AC completion + gate evidence; publish lessons learned and Sprint 6 postmortem summary.

- 2026-03-09: Added stage-authority regression evidence to prevent premature policy mutation before `policy.decide` in canonical flow, reducing identity-routing starvation risk caused by early direct-answer authority.
  - Runtime authority update: `intent.resolve` emits retrieval requirement + context rationale only; authoritative `policy_decision`/`decision_object` are written in `policy.decide`.
  - Deterministic regression assertions:
    - `tests/test_pipeline_semantic_contracts.py::test_policy_authority_is_not_written_before_policy_decide_stage`
    - `tests/test_canonical_turn_orchestrator.py::test_orchestrator_stabilizes_before_route_authority_assignment`
  - Deterministic proof commands:
    - `python -m pytest tests/test_pipeline_semantic_contracts.py::test_policy_authority_is_not_written_before_policy_decide_stage`
    - `python -m pytest tests/test_canonical_turn_orchestrator.py::test_orchestrator_stabilizes_before_route_authority_assignment`
    - `python -m pytest tests/test_pipeline_semantic_contracts.py tests/test_canonical_turn_orchestrator.py`

- 2026-03-09: Hardened non-authoritative intent helper isolation to prevent silent routing influence outside canonical orchestration.
  - Runtime guard: `resolve_turn_intent(...)` in `src/testbot/sat_chatbot_memory_v2.py` is now explicitly diagnostic-only and raises when called as authoritative (`diagnostic_only=False`).
  - Explicit labeling: helper invocation emits non-authoritative diagnostic warning metadata (`authority=non_authoritative`).
  - Deterministic regression evidence:
    - `tests/test_intent_router.py::test_resolve_turn_intent_requires_diagnostic_only_mode`
    - `tests/test_pipeline_semantic_contracts.py::test_resolve_turn_intent_matches_canonical_intent_resolution_for_identity_followup`
  - Verification commands:
    - `python -m pytest tests/test_intent_router.py::test_resolve_turn_intent_requires_diagnostic_only_mode`
    - `python -m pytest tests/test_pipeline_semantic_contracts.py::test_resolve_turn_intent_matches_canonical_intent_resolution_for_identity_followup`

- 2026-03-09: Phase 1 deterministic verification set for ISSUE-0014/0013 re-executed and evidence-linked with refreshed outcomes.
  - Pass evidence: `python -m behave features/memory_recall.feature features/intent_grounding.feature` and focused regression suites (`tests/test_pipeline_semantic_contracts.py`, `tests/test_canonical_turn_orchestrator.py`, `tests/test_intent_router.py`).
  - Gate evidence: canonical gate now reports overall `passed` with a KPI guardrail warning (`qa_validate_kpi_guardrails` in optional warning mode), so blocking product/safety/qa checks are green under current policy.
  - Dependency-state language: ISSUE-0014 dependency evidence is satisfied and lifecycle language is synchronized to "evidence satisfied, closure decision pending" across ISSUE-0013/0014/0015/RED_TAG.
  - Evidence artifacts: `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md`, `docs/issues/evidence/2026-03-09-issue-0014-0013-behave.log`, `docs/issues/evidence/2026-03-09-issue-0014-0013-focused-pytests.log`, `docs/issues/evidence/2026-03-09-issue-0014-0013-all-green-gate.log`, `artifacts/all-green-gate-summary.json`.
