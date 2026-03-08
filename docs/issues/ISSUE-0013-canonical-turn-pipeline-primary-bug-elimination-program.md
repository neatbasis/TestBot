# ISSUE-0013: Implement canonical turn pipeline as the primary bug-elimination program

- **ID:** ISSUE-0013
- **Title:** Implement canonical turn pipeline as the primary bug-elimination program
- **Status:** open
- **Severity:** amber
- **Owner:** platform-qa
- **Created:** 2026-03-07
- **Target Sprint:** Sprint 3-5
- **Canonical Cross-Reference:** `ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`
- **Principle Alignment:** contract-first, invariant-driven, traceable, deterministic, ci-enforced, ontology-aware

## Problem Statement

The repository documents a canonical 11-stage turn pipeline and the doctrine "write before infer; infer from enriched state, not raw text," but major runtime paths still rely on legacy monolithic surfaces and raw-utterance-first routing. This architecture/implementation gap is now the highest-leverage defect source. The system must make typed stabilized turn state the primary routing and retrieval authority and remove early lossy `U -> I` behavior from the main loop.

## Evidence

- `docs/architecture/canonical-turn-pipeline.md` defines the canonical sequence: `observe.turn -> encode.candidates -> stabilize.pre_route -> context.resolve -> intent.resolve -> retrieve.evidence -> policy.decide -> answer.assemble -> answer.validate -> answer.render -> answer.commit` and forbids early lossy `U -> I` projection.
- `docs/qa/feature-status.yaml` still reports canonical-turn capability slices as planned while related legacy capability areas remain partial.
- `docs/issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md` establishes staged delivery governance, but runtime implementation remains incomplete.
- Runtime traceability still points to monolithic surfaces (for example `src/testbot/sat_chatbot_memory_v2.py` and `src/testbot/intent_router.py`) as core policy and routing execution points.
- External research alignment supports typed memory and segmented retrieval over flat turn/session units (SeCom, Semantic XPath, D-SMART, ENGRAM, Amory).

## Impact

- Recurring bugs persist from early intent routing on raw utterances and flattened evidence mixing.
- Same-turn memory self-contamination can produce false confidence and echo retrieval.
- Repair continuity, user-fact recall, and temporal consistency remain fragile due to missing typed boundaries and weak commit semantics.
- Feature readiness cannot move canonical capability slices out of partial states with confidence until deterministic runtime evidence closes the remaining behavioral gaps.

## Acceptance Criteria

1. Main turn runtime enforces canonical stage ordering and removes direct raw-utterance-first routing (`U -> I`) from the primary loop.
2. Typed artifacts exist and are used at stage boundaries for:
   - `TurnObservation`, `SpeechActCandidate`, `FactCandidate`, `RepairCandidate`, `DialogueStateCandidate`, `StabilizedTurnState`, `ResolvedContext`, `ResolvedIntent`, `EvidenceBundle`, `DecisionObject`, `AnswerCandidate`, `ValidatedAnswer`, `CommittedTurnState`.
3. `stabilize.pre_route` becomes the first durable semantic boundary and persists utterance card, candidate facts with provenance, candidate dialogue state, and durable references before route authority.
4. Retrieval keeps evidence classes distinct in `EvidenceBundle` (structured facts, episodic utterances, repair anchors/offers, reflections/hypotheses, source evidence) and does not flatten to a single undifferentiated top-k before policy.
5. Same-turn retrieval hygiene is enforced by construction:
   - `same_turn_exclusion_doc_ids` is populated during stabilization,
   - standard answer-evidence retrieval excludes same-turn artifacts,
   - only explicitly permitted same-turn access classes (for example observation-state and repair anchors) are allowed.
6. Durable memory strata are implemented and persisted:
   - episodic,
   - semantic,
   - procedural/dialogue-state.
7. Segment-level memory construction and retrieval are introduced with minimum segment types: contiguous topic, repair, task, self-profile, temporal episode; segment IDs and membership edges are persisted.
8. `policy.decide` is explicitly typed and separated from `answer.assemble`; answer assembly consumes only the `DecisionObject` + `EvidenceBundle` contract and disallows free-form decision drift.
9. `answer.commit` persists continuity-critical state (including pending repair state, obligations, and confirmed facts promotion path).
10. Deterministic behavior scenarios pass for:
    - observe-before-infer,
    - stabilize-before-route,
    - same-turn retrieval exclusion,
    - self-identification persistence (for example `user_name=Sebastian`),
    - repair-offer continuation (`What do you need?` after assistant repair offer),
    - empty-evidence distinct from scored-empty,
    - semantic-memory recall winning over raw utterance recall when both exist.
11. `docs/qa/feature-status.yaml` canonical pipeline capability slices are advanced from `planned` to implemented maturity states that reflect delivered behavior.

## Work Plan

### Foundation slice (Sprint 3)

- Implement typed `observe.turn`, `encode.candidates`, and `stabilize.pre_route` modules and contracts.
- Add candidate taxonomy: speech-act, fact, episodic-event, repair/control/query.
- Persist first durable pre-route artifacts and IDs.
- Enforce same-turn exclusion list wiring and deny-by-default same-turn evidence for answer retrieval.
- Start monolith reduction by moving semantic logic out of `src/testbot/sat_chatbot_memory_v2.py` into stage modules; keep orchestrator responsibilities only.
- Add deterministic tests and BDD scenarios for observe-before-infer, stabilize-before-route, self-identification, and same-turn contamination prevention.

### Decisioning slice (Sprint 4)

- Implement `context.resolve`, `intent.resolve`, `retrieve.evidence`, and `policy.decide` over stabilized typed state.
- Introduce typed `EvidenceBundle` with class-separated evidence channels.
- Introduce typed `DecisionObject` classes (`answer_from_memory`, `answer_from_source_evidence`, `ask_for_clarification`, `continue_repair_reconstruction`, `continue_repair_disambiguation`, `answer_general_knowledge_labeled`, `decline_unsafe`).
- Encode explicit empty-evidence vs scored-empty distinction in retrieval and policy outputs.
- Add unit/integration tests for context resolution, decision typing, and evidence-class separation.

### Commit and audit slice (Sprint 5)

- Implement `answer.assemble`, `answer.validate`, `answer.render`, and `answer.commit` as explicit modules consuming typed contracts.
- Persist repair continuity and obligation state in committed turn artifacts.
- Implement episodic/semantic/procedural persistence and segment graph edges for retrieval.
- Add contradiction/consistency checks (NLI-style or deterministic contradiction fixtures) for identity, preferences, pending repair state, and temporal recall.
- Complete feature-status and traceability updates to reflect delivered capability.

### Module and schema targets

- Add/expand modules:
  - `src/testbot/turn_observation.py`
  - `src/testbot/candidate_encoding.py`
  - `src/testbot/stabilization.py`
  - `src/testbot/context_resolution.py`
  - `src/testbot/intent_resolution.py`
  - `src/testbot/evidence_retrieval.py`
  - `src/testbot/policy_decision.py`
  - `src/testbot/answer_assembly.py`
  - `src/testbot/answer_validation.py`
  - `src/testbot/answer_rendering.py`
  - `src/testbot/answer_commit.py`
- Add stage/state fields at minimum: `turn_id`, `same_turn_exclusion_doc_ids`, `candidate_facts`, `candidate_speech_acts`, `candidate_dialogue_state`, `active_segments`, `resolved_context`, `resolved_intent_class`, `evidence_bundle`, `decision_class`, `decision_reason`, `answer_bindings`, `pending_repair_state`, `resolved_obligations`, `remaining_obligations`, `confirmed_user_facts`.

## Verification

- Command: `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json`
  - Expected: canonical pipeline capability slices reflect ISSUE-0013-linked delivery states and no longer remain planned after implementation milestones are met.
- Command: `python scripts/validate_issue_links.py --all-issue-files --base-ref HEAD`
  - Expected: issue cross-links and IDs validate successfully.
- Command: `python scripts/validate_issues.py --all-issue-files --base-ref HEAD`
  - Expected: ISSUE-0013 file passes canonical issue schema checks.
- Command: `python scripts/all_green_gate.py`
  - Expected: deterministic merge/readiness gate passes with canonical pipeline tests included.

## Closure Notes

- 2026-03-07: Opened as the primary bug-elimination program to align runtime behavior with the canonical turn pipeline contract and eliminate raw-utterance-first routing as the dominant defect source.
- 2026-03-07: Cross-system traceability note — ISSUE-0013 is the implementation and bug-elimination counterpart to `ISSUE-0012-canonical-turn-pipeline-delivery-plan.md` (delivery planning/governance anchor).
- Closure requires evidence that canonical pipeline foundation, decisioning, and commit/audit slices are implemented in runtime, test coverage is deterministic and passing, and feature status moved beyond planned states.

- 2026-03-07: Foundation slice evidence recorded — owner modules now reference canonical stage implementations (`turn_observation`, `candidate_encoding`, `stabilization`) and capability status remains `partial` in `docs/qa/feature-status.yaml` pending closure-criteria runtime proof.
- 2026-03-07: Decisioning slice evidence recorded — owner modules now reference canonical decisioning implementations (`context_resolution`, `intent_resolution`, `evidence_retrieval`, `policy_decision`) and capability status remains `partial` in `docs/qa/feature-status.yaml` pending closure-criteria runtime proof.
- 2026-03-07: Commit/audit slice evidence recorded — owner modules now reference canonical commit-path implementations (`answer_assembly`, `answer_validation`, `answer_rendering`, `answer_commit`) and capability status remains `partial` in `docs/qa/feature-status.yaml` pending closure-criteria runtime proof.
- 2026-03-07: Dependent issue deltas linked for merge-readiness traceability (governance/reporting recalibration) — ISSUE-0008 (intent grounding), ISSUE-0009 (knowing-mode provenance), ISSUE-0010 (unknowing fallback), and ISSUE-0011 (turn analytics input coverage) remain explicitly linked as downstream defect tracks under this primary program while ISSUE-0012 remains the delivery-plan governance counterpart.

- 2026-03-07: Governance evidence distinction recorded — merge-readiness evidence should use blocking gate semantics (`python scripts/all_green_gate.py --json-output ...`), while `--continue-on-failure` outputs are advisory and must be labeled as such in reporting.

- 2026-03-08: Progress audit of the latest 10 commits recorded staged delivery evidence and governance recalibration markers:
  - foundation module split landed (`b3d4337`, merged via `aeacea5`)
  - decisioning module contracts landed (`f2dc7d7`, behavior alignment follow-up `4605987`)
  - commit/audit module contracts landed (`25cdf6b`)
  - reporting/governance recalibration landed (`605fad9`, merged via `9820354`)
- 2026-03-08: Next-step execution plan refreshed from commit audit evidence:
  1. Close deterministic self-identification and durable fact-ingestion gaps in canonical examples (`features/memory_recall.feature`, `tests/test_eval_runtime_parity.py`, canonical orchestrator flow).
  2. Tighten decision-object routing so known facts avoid `ANSWER_GENERAL_KNOWLEDGE` fallback when grounded evidence exists (`src/testbot/policy_decision.py`, `src/testbot/answer_policy.py`, `src/testbot/reflection_policy.py`).
  3. Add commit/audit proof tests that committed-turn artifacts are persisted and re-used on subsequent turns (`tests/test_runtime_logging_events.py`, `tests/test_turn_analytics_aggregator.py`, canonical pipeline integration tests).
  4. Keep governance evidence explicit: blocking gate artifact for merge-readiness and separate advisory artifact labeling for KPI guardrail warnings.
