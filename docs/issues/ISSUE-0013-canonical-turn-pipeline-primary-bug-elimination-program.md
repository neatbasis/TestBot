# ISSUE-0013: Implement canonical turn pipeline as the primary bug-elimination program

- **ID:** ISSUE-0013
- **Title:** Implement canonical turn pipeline as the primary bug-elimination program
- **Status:** open
- **Severity:** amber
- **Owner:** platform-qa
- **Created:** 2026-03-07
- **Target Sprint:** Sprint 3-5
- **Canonical Cross-Reference:** `ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`
- **Cross-Reference Pointers:** ISSUE-0014 (active red identity-continuity regression), ISSUE-0015 (active red quality/governance hardening review)
- **Principle Alignment:** contract-first, invariant-driven, traceable, deterministic, ci-enforced, ontology-aware

## Problem Statement

The repository documents a canonical 11-stage turn pipeline and the doctrine "write before infer; infer from enriched state, not raw text," but major runtime paths still rely on legacy monolithic surfaces and raw-utterance-first routing. This architecture/implementation gap is now the highest-leverage defect source. The system must make typed stabilized turn state the primary routing and retrieval authority and remove early lossy `U -> I` behavior from the main loop.

## Current execution order

Dependent open-issue routing is sequenced through ISSUE-0013 using the following order/state terminology:

1. **ISSUE-0008 — blocker (upstream quality gate):** intent-grounding confidence must remain deterministic to prevent early-route drift from re-entering the canonical turn path.
2. **ISSUE-0011 — blocker (observability gate):** analytics input-coverage diagnostics must remain trustworthy so canonical-pipeline behavior changes are auditable.
3. **ISSUE-0012 — parallel stream (delivery-plan governance):** staged implementation and checkpoint governance run in parallel while execution remains routed through ISSUE-0013.
4. **ISSUE-0014 — blocker (identity-continuity behavioral gate):** AC-0013-11 cannot close until Phase 1 behavioral criteria and reproducible CLI traces are satisfied.
5. **ISSUE-0015 — dependent (governance close-order gate):** ISSUE-0015 remains open/red until blockers above are evidence-satisfied and lifecycle closure sequencing is completed.

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

Status legend: `[ ] pending`, `[~] partial`, `[x] complete`.

Dependency labels (machine-auditable ordered chain):
- `DEP-0008-BLOCKER` -> `DEP-0011-BLOCKER` -> `DEP-0012-PARALLEL` -> `DEP-0014-BLOCKER` -> `DEP-0015-DEPENDENT`

- [~] [AC-0013-01] Main turn runtime enforces canonical stage ordering and removes direct raw-utterance-first routing (`U -> I`) from the primary loop.
  - dependency-labels: `DEP-0008-BLOCKER`, `DEP-0011-BLOCKER`, `DEP-0012-PARALLEL`
  - code-paths: `src/testbot/canonical_turn_orchestrator.py`, `src/testbot/sat_chatbot_memory_v2.py`, `src/testbot/intent_router.py`
  - behavior-specs: `features/intent_grounding.feature`, `features/memory_recall.feature`
  - deterministic-tests: `tests/test_canonical_turn_orchestrator.py`, `tests/test_pipeline_semantic_contracts.py`, `tests/test_intent_router.py`
  - verification:
    ```bash
    python -m pytest tests/test_canonical_turn_orchestrator.py tests/test_pipeline_semantic_contracts.py tests/test_intent_router.py
    # expected pass signal: all selected tests PASS; no anti-projection/stage-order failures
    ```

- [~] [AC-0013-02] Typed artifacts exist and are used at stage boundaries for `TurnObservation`, `SpeechActCandidate`, `FactCandidate`, `RepairCandidate`, `DialogueStateCandidate`, `StabilizedTurnState`, `ResolvedContext`, `ResolvedIntent`, `EvidenceBundle`, `DecisionObject`, `AnswerCandidate`, `ValidatedAnswer`, and `CommittedTurnState`.
  - dependency-labels: `DEP-0008-BLOCKER`, `DEP-0011-BLOCKER`, `DEP-0012-PARALLEL`
  - code-paths: `src/testbot/pipeline_state.py`, `src/testbot/stage_transitions.py`, `src/testbot/stabilization.py`, `src/testbot/evidence_retrieval.py`
  - behavior-specs: `features/intent_grounding.feature`
  - deterministic-tests: `tests/test_canonical_turn_pipeline_contract_ac_0013_02.py`, `tests/test_pipeline_state_artifacts.py`, `tests/test_pipeline_semantic_contracts.py`
  - verification:
    ```bash
    python -m pytest tests/test_canonical_turn_pipeline_contract_ac_0013_02.py tests/test_pipeline_state_artifacts.py tests/test_pipeline_semantic_contracts.py
    # expected pass signal: artifact-contract tests PASS with typed boundary assertions satisfied
    ```

- [~] [AC-0013-03] `stabilize.pre_route` becomes the first durable semantic boundary and persists utterance card, candidate facts with provenance, candidate dialogue state, and durable references before route authority.
  - dependency-labels: `DEP-0008-BLOCKER`, `DEP-0011-BLOCKER`, `DEP-0012-PARALLEL`
  - code-paths: `src/testbot/stabilization.py`, `src/testbot/sat_chatbot_memory_v2.py`, `src/testbot/runtime_logging.py`
  - behavior-specs: `features/memory_recall.feature`
  - deterministic-tests: `tests/test_runtime_logging_events.py`, `tests/test_pipeline_state_artifacts.py`
  - verification:
    ```bash
    python -m pytest tests/test_runtime_logging_events.py -k "stabilize or pre_route or durable"
    # expected pass signal: stabilize/pre-route durable artifact assertions PASS
    ```

- [~] [AC-0013-04] Retrieval keeps evidence classes distinct in `EvidenceBundle` (structured facts, episodic utterances, repair anchors/offers, reflections/hypotheses, source evidence) and does not flatten to a single undifferentiated top-k before policy.
  - dependency-labels: `DEP-0008-BLOCKER`, `DEP-0011-BLOCKER`, `DEP-0012-PARALLEL`
  - code-paths: `src/testbot/evidence_retrieval.py`, `src/testbot/policy_decision.py`
  - behavior-specs: `features/memory_recall.feature`
  - deterministic-tests: `tests/test_evidence_retrieval_mapping.py`, `tests/test_decisioning_stages.py`
  - verification:
    ```bash
    python -m pytest tests/test_evidence_retrieval_mapping.py tests/test_decisioning_stages.py
    # expected pass signal: evidence-bundle class mapping and policy-consumption tests PASS
    ```

- [~] [AC-0013-05] Same-turn retrieval hygiene is enforced by construction: `same_turn_exclusion_doc_ids` is populated during stabilization, standard answer-evidence retrieval excludes same-turn artifacts, and only explicitly permitted same-turn access classes (for example observation-state and repair anchors) are allowed.
  - dependency-labels: `DEP-0008-BLOCKER`, `DEP-0011-BLOCKER`, `DEP-0012-PARALLEL`
  - code-paths: `src/testbot/stabilization.py`, `src/testbot/evidence_retrieval.py`, `src/testbot/vector_store.py`
  - behavior-specs: `features/memory_recall.feature`
  - deterministic-tests: `tests/test_evidence_retrieval_mapping.py`, `tests/test_runtime_logging_events.py`, `tests/test_vector_store.py`
  - verification:
    ```bash
    python -m pytest tests/test_evidence_retrieval_mapping.py tests/test_runtime_logging_events.py -k "same_turn"
    # expected pass signal: same-turn exclusion assertions PASS with explicit allowlist behavior
    ```

- [~] [AC-0013-06] Durable memory strata are implemented and persisted for episodic, semantic, and procedural/dialogue-state memory.
  - dependency-labels: `DEP-0011-BLOCKER`, `DEP-0012-PARALLEL`
  - code-paths: `src/testbot/memory_strata.py`, `src/testbot/sat_chatbot_memory_v2.py`, `src/testbot/answer_commit.py`
  - behavior-specs: `features/memory_recall.feature`
  - deterministic-tests: `tests/test_memory_segments_and_strata.py`, `tests/test_answer_commit_identity_promotion.py`
  - verification:
    ```bash
    python -m pytest tests/test_memory_segments_and_strata.py tests/test_answer_commit_identity_promotion.py
    # expected pass signal: strata persistence + promotion-path tests PASS
    ```

- [~] [AC-0013-07] Segment-level memory construction and retrieval are introduced with minimum segment types (contiguous topic, repair, task, self-profile, temporal episode), and segment IDs and membership edges are persisted.
  - dependency-labels: `DEP-0011-BLOCKER`, `DEP-0012-PARALLEL`
  - code-paths: `src/testbot/memory_strata.py`, `src/testbot/vector_store.py`, `src/testbot/context_resolution.py`
  - behavior-specs: `features/memory_recall.feature`
  - deterministic-tests: `tests/test_memory_segments_and_strata.py`, `tests/test_vector_store.py`
  - verification:
    ```bash
    python -m pytest tests/test_memory_segments_and_strata.py tests/test_vector_store.py -k "segment"
    # expected pass signal: segment membership/edge persistence tests PASS
    ```

- [~] [AC-0013-08] `policy.decide` is explicitly typed and separated from `answer.assemble`; answer assembly consumes only the `DecisionObject` + `EvidenceBundle` contract and disallows free-form decision drift.
  - dependency-labels: `DEP-0008-BLOCKER`, `DEP-0011-BLOCKER`, `DEP-0012-PARALLEL`
  - code-paths: `src/testbot/policy_decision.py`, `src/testbot/answer_assembly.py`, `src/testbot/sat_chatbot_memory_v2.py`
  - behavior-specs: `features/answer_contract.feature`, `features/intent_grounding.feature`
  - deterministic-tests: `tests/test_decisioning_stages.py`, `tests/test_answer_contract.py`, `tests/test_pipeline_semantic_contracts.py`
  - verification:
    ```bash
    python -m pytest tests/test_decisioning_stages.py tests/test_answer_contract.py tests/test_pipeline_semantic_contracts.py
    # expected pass signal: typed decision boundary assertions PASS
    ```

- [~] [AC-0013-09] `answer.commit` persists continuity-critical state, including pending repair state, obligations, and confirmed facts promotion path.
  - dependency-labels: `DEP-0011-BLOCKER`, `DEP-0012-PARALLEL`, `DEP-0014-BLOCKER`
  - code-paths: `src/testbot/answer_commit.py`, `src/testbot/context_resolution.py`, `src/testbot/evidence_retrieval.py`
  - behavior-specs: `features/memory_recall.feature`
  - deterministic-tests: `tests/test_runtime_logging_events.py`, `tests/test_turn_analytics_aggregator.py`, `tests/test_answer_commit_identity_promotion.py`
  - verification:
    ```bash
    python -m pytest tests/test_runtime_logging_events.py tests/test_turn_analytics_aggregator.py tests/test_answer_commit_identity_promotion.py
    # expected pass signal: commit continuity + next-turn consumption tests PASS
    ```

- [~] [AC-0013-10] Deterministic behavior scenarios pass for observe-before-infer, stabilize-before-route, same-turn retrieval exclusion, self-identification persistence (for example `user_name=Sebastian`), repair-offer continuation (`What do you need?` after assistant repair offer), empty-evidence distinct from scored-empty, and semantic-memory recall winning over raw utterance recall when both exist.
  - dependency-labels: `DEP-0008-BLOCKER`, `DEP-0011-BLOCKER`, `DEP-0012-PARALLEL`, `DEP-0014-BLOCKER`
  - code-paths: `src/testbot/canonical_turn_orchestrator.py`, `src/testbot/stabilization.py`, `src/testbot/evidence_retrieval.py`, `src/testbot/policy_decision.py`
  - behavior-specs: `features/intent_grounding.feature`, `features/memory_recall.feature`, `features/answer_contract.feature`
  - deterministic-tests: `tests/test_runtime_logging_events.py`, `tests/test_evidence_retrieval_mapping.py`, `tests/test_intent_router.py`, `tests/test_promotion_policy.py`
  - verification:
    ```bash
    python -m behave features/intent_grounding.feature features/memory_recall.feature features/answer_contract.feature
    python -m pytest tests/test_runtime_logging_events.py tests/test_evidence_retrieval_mapping.py tests/test_intent_router.py tests/test_promotion_policy.py
    # expected pass signal: behave scenarios PASS; deterministic pytest suites PASS
    ```

- [~] [AC-0013-11] ISSUE-0013 identity-continuity closure is explicitly dependent on ISSUE-0014 Phase 1 behavioral evidence and cannot be treated as satisfied by structural instrumentation progress alone.
  - dependency-labels: `DEP-0014-BLOCKER`, `DEP-0015-DEPENDENT`
  - code-paths: `src/testbot/intent_resolution.py`, `src/testbot/stage_rewrite_query.py`, `src/testbot/answer_commit.py`, `src/testbot/context_resolution.py`
  - behavior-specs: `features/memory_recall.feature`, `features/intent_grounding.feature`
  - deterministic-tests: `tests/test_intent_router.py`, `tests/test_promotion_policy.py`, `tests/test_answer_commit_identity_promotion.py`
  - verification:
    ```bash
    python -m pytest tests/test_intent_router.py tests/test_promotion_policy.py tests/test_answer_commit_identity_promotion.py
    python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main
    python scripts/validate_issues.py --all-issue-files --base-ref origin/main
    # expected pass signal: dependency tests PASS and issue validators report zero errors
    ```
  - required dependency evidence (ISSUE-0014): identity declaration semantic preservation, retrieval activation on self-reference recall, and confirmed identity fact promotion at commit.
  - dependency cross-links: [ISSUE-0014 Defect Taxonomy](ISSUE-0014-cli-self-identity-semantic-routing-regression.md#defect-taxonomy), [ISSUE-0014 Stage Contract Clauses](ISSUE-0014-cli-self-identity-semantic-routing-regression.md#stage-contract-clauses), [ISSUE-0014 Required Observability Fields](ISSUE-0014-cli-self-identity-semantic-routing-regression.md#required-observability-fields)
  - closure rule: structural telemetry/stage instrumentation updates are insufficient for ISSUE-0013 closure unless the linked behavioral criteria are passing in deterministic tests and reproducible CLI evidence.
  - exit condition EC-0013-11-A: ISSUE-0014 marks its Phase 1 behavioral criteria as satisfied with linked deterministic test evidence and reproducible CLI traces.
  - exit condition EC-0013-11-B: the deterministic validation set required by ISSUE-0014 Phase 1 runs clean in the current branch (no identity-continuity regressions).
  - exit condition EC-0013-11-C: ISSUE-0015 dependency gate is updated from open to satisfied, confirming closure-governance alignment across ISSUE-0013/0014/0015.
  - 2026-03-09 evidence update:
    - EC-0013-11-A: **in_progress (partial behavioral evidence)** (targeted ISSUE-0014 Phase 1 suites and CLI closure-proof traces are attached, but deterministic dependency closure remains blocked by failing canonical all-green gate evidence).
    - EC-0013-11-B: **unsatisfied (deterministic gate incomplete)** (evidence bundle records canonical all-green gate failure on `product_behave`; refreshed passing gate artifact is required).
    - EC-0013-11-C: **in_progress (governance synchronization)** (ISSUE-0015 dependency gate tracks missing evidence actions and cross-artifact lifecycle language is synchronized to blocked/open dependency posture).
    - linked evidence: `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md`, `docs/issues/evidence/2026-03-09-issue-0014-0013-behave.log`, `docs/issues/evidence/2026-03-09-issue-0014-0013-focused-pytests.log`, `docs/issues/evidence/2026-03-09-issue-0014-0013-all-green-gate.log`, `artifacts/all-green-gate-summary.json`.
    - missing-evidence checklist:
      - [ ] **Owner: runtime-pipeline** — resolve `product_behave` failures in canonical gate evidence. **Due: 2026-03-16**.
      - [ ] **Owner: platform-qa** — rerun canonical all-green gate and attach passing artifacts. **Due: 2026-03-16**.
      - [ ] **Owner: release-governance** — promote lifecycle language to evidence-satisfied only after refreshed passing gate evidence is attached across ISSUE-0013/0014/0015/RED_TAG. **Due: 2026-03-17**.

- [~] [AC-0013-12] `docs/qa/feature-status.yaml` canonical pipeline capability slices are advanced from `planned` to implemented maturity states that reflect delivered behavior.
  - dependency-labels: `DEP-0012-PARALLEL`, `DEP-0014-BLOCKER`, `DEP-0015-DEPENDENT`
  - code-paths: `src/testbot/capabilities_runtime_status.py`, `src/testbot/canonical_turn_orchestrator.py`
  - behavior-specs: `features/capabilities.feature`
  - deterministic-tests: `tests/test_capabilities_runtime_status.py`, `tests/test_report_feature_status.py`, `tests/test_all_green_gate.py`
  - verification:
    ```bash
    python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json
    python -m pytest tests/test_capabilities_runtime_status.py tests/test_report_feature_status.py tests/test_all_green_gate.py
    # expected pass signal: report artifact generation succeeds and status/gate tests PASS
    ```

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
- Command: `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`
  - Result (2026-03-09): **pass** with documented base-ref fallback `origin/main` -> `HEAD~1`.
- Command: `python scripts/validate_issues.py --all-issue-files --base-ref origin/main`
  - Result (2026-03-09): **pass** (`--pr-body-file` not provided; base-ref fallback `origin/main` -> `HEAD~1`).

## Closure Notes

- 2026-03-09: Closure posture remains open by dependency gate; see synchronized red-tag triage note below for current blocker state.

- 2026-03-09: Governance-linked status artifacts regenerated after dependency-order synchronization.
  - `artifacts/all-green-gate-summary.json` regenerated via `python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json` (pass with warning-mode KPI guardrail policy).
  - `docs/qa/feature-status-report.md` and `artifacts/feature-status-summary.json` regenerated at `2026-03-09T04:33:08Z` via `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json`.
  - Verification note: regenerated report no longer shows gate-summary staleness warning and remains aligned to partial canonical pipeline slice states.

## Red-tag triage note (dependency gate)

- Last reviewed: 2026-03-09
- Next review due: 2026-03-16
- KPI evidence: docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md
- Decision notes: Deterministic behave/pytest bundle and required CLI identity-continuity closure traces are attached, but AC-0013-11 dependency remains unresolved because the referenced canonical all-green gate artifact is failing (`product_behave`).

- 2026-03-07: Opened as the primary bug-elimination program to align runtime behavior with the canonical turn pipeline contract and eliminate raw-utterance-first routing as the dominant defect source.
- 2026-03-07: Cross-system traceability note — ISSUE-0013 is the implementation and bug-elimination counterpart to `ISSUE-0012-canonical-turn-pipeline-delivery-plan.md` (delivery planning/governance anchor).
- 2026-03-08: Closure dependency update — identity continuity/routing/memory-recall acceptance remains blocked pending ISSUE-0014 Phase 1 behavioral proof across taxonomy, stage-contract, and observability sections: [Defect Taxonomy](ISSUE-0014-cli-self-identity-semantic-routing-regression.md#defect-taxonomy), [Stage Contract Clauses](ISSUE-0014-cli-self-identity-semantic-routing-regression.md#stage-contract-clauses), and [Required Observability Fields](ISSUE-0014-cli-self-identity-semantic-routing-regression.md#required-observability-fields).
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

- 2026-03-08: Deterministic proof for foundation next-step focus recorded — canonical stage tests now cover self-identification extraction and stabilization ordering (`tests/test_canonical_turn_orchestrator.py`), with scenario alignment in answer-contract behavior specs (`features/answer_contract.feature`). `docs/qa/feature-status.yaml` foundation capability advanced to `implemented` and evidence refs extended with `a725984` for traceable promotion.
- 2026-03-08: Deterministic decisioning proof expanded — evidence bundle class mapping plus decision-object authority routing are exercised in deterministic runtime and contract tests (`tests/test_evidence_retrieval_mapping.py`, `tests/test_runtime_logging_events.py`, `features/answer_contract.feature`). However, runtime trace evidence still shows unresolved note-taking and memory-write misrouting in canonical flows, so `docs/qa/feature-status.yaml` decisioning capability remains `partial` pending behavioral closure; evidence refs are extended with `76a88be` and `ee1727d` for traceability.
- 2026-03-08: Commit/audit continuity closure evidence recorded — deterministic tests now prove committed-turn artifacts persist and are re-used on subsequent turns with explicit retrieval continuity anchors. Runtime log coverage: `test_chat_loop_logs_commit_stage_record_with_durable_commit_state` and `test_chat_loop_two_turn_commit_continuity_is_consumed_by_context_and_retrieval` in `tests/test_runtime_logging_events.py`; analytics normalization/aggregation continuity coverage: `test_aggregate_turn_dataset_multi_turn_commit_continuity_fields_preserved` in `tests/test_turn_analytics_aggregator.py`. `docs/qa/feature-status.yaml` commit/audit capability advances to `implemented` with next-step wording updated from gap-closure to regression monitoring.
- 2026-03-08: Fresh readiness artifacts regenerated with canonical scripts for ISSUE-0013 governance traceability:
  - `artifacts/all-green-gate-summary.json` generated at `2026-03-08T15:15:32Z` via `python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json`.
  - `docs/qa/feature-status-report.md` generated at `2026-03-08T15:15:35Z` and `artifacts/feature-status-summary.json` generated at `2026-03-08T15:15:35Z` via `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json`.
  - Metadata check confirmed no staleness warnings: feature-status summary `warnings` is empty and report header/footer input metadata aligns with `docs/qa/feature-status.yaml` and open ISSUE-0013-linked issue records.


- 2026-03-08: Decision-path closure evidence appended for note-taking and memory-write utterances in canonical routing:
  - Deterministic intent routing now classifies explicit note-taking/memory-write commands as non-knowledge meta conversation (`src/testbot/intent_router.py`, `tests/test_intent_router.py`).
  - Deterministic canonical contract probes now assert resolved intent, retrieval branch, decision-object class, fallback action, and final answer mode for both utterance classes (`features/intent_grounding.feature`, `features/steps/intent_grounding_steps.py`, `tests/test_runtime_logging_events.py`).
  - Stage-answer authority regression coverage confirms decision-object mapping remains authoritative and avoids silent `ANSWER_GENERAL_KNOWLEDGE` fallback when grounded memory evidence is present (`tests/test_runtime_logging_events.py`).

- 2026-03-08: Canonical reporting artifacts regenerated after commit/audit status refresh:
  - `artifacts/all-green-gate-summary.json` generated at `2026-03-08T15:48:11Z` via `python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json` (gate passed with KPI guardrail warning mode active).
  - `docs/qa/feature-status-report.md` and `artifacts/feature-status-summary.json` generated at `2026-03-08T15:48:15Z` via `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json`.


- 2026-03-08: Segment-aware strata persistence evidence added for criteria 6/7/10 traceability:
  - Runtime persistence now stamps explicit memory strata (`episodic`, `semantic`, `procedural_dialogue_state`) and segment metadata (`segment_type`, `segment_id`, `segment_membership_edge_refs`) during stabilization and commit persistence paths (`src/testbot/stabilization.py`, `src/testbot/sat_chatbot_memory_v2.py`, `src/testbot/memory_strata.py`).
  - Retrieval path now accepts and enforces segment constraints for canonical recall (`src/testbot/sat_chatbot_memory_v2.py`, `src/testbot/vector_store.py`).
  - Evidence bundling now preserves segment-aware fields and applies strata precedence so semantic memory wins over same-segment episodic utterance recall (`src/testbot/evidence_retrieval.py`).
  - Deterministic proof coverage added for segment continuity, segment-constrained retrieval, and semantic-over-episodic precedence (`tests/test_memory_segments_and_strata.py`, `tests/test_evidence_retrieval_mapping.py`, `features/memory_recall.feature`, `features/steps/memory_steps.py`).

- 2026-03-08: Historical progress note retained for traceability: foundation/decisioning/commit slices were assessed as materially advanced at that time, but lifecycle interpretation is superseded by the active dependency gate; ISSUE-0013 remains open until AC-0013-11 exit conditions are fully satisfied.

- 2026-03-08: Status artifacts were regenerated during an earlier closure attempt (`python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json`); this claim is now superseded by reopened ISSUE-0013 evidence and reverted partial canonical slice status.

- 2026-03-08: Reopened after external CLI validation contradicted closure assumptions. Production-style debug transcripts show canonical criteria regressions still present: (a) self-identification utterance `Hi! I'm Sebastian` classified as `knowledge_question` and routed to `ANSWER_GENERAL_KNOWLEDGE` with `ANSWER_CONTRACT_GROUNDING_FAIL`; (b) memory follow-up `The memory today` resolved to `knowledge_question`/`direct_answer` instead of stable memory-recall continuity; (c) temporal query `How log ago did I ask you something?` remained in knowledge fallback path with empty retrieval and no committed-turn continuity recall; (d) even with non-empty retrieval context (`What is ontology?`) policy emitted `ANSWER_FROM_MEMORY` decision class while contract rejected with `GK_CONTRACT_MARKER_FAIL`, ending in assist fallback text.
- 2026-03-08: Canonical feature-status slices for foundation, decisioning, and commit/audit were reset to `partial` in `docs/qa/feature-status.yaml` and reporting artifacts were regenerated to remove over-claimed implemented effective status for ISSUE-0013-linked slices.



- 2026-03-08: Regression-hardening pass added explicit acceptance traceability for `AC-0013-01`, `AC-0013-03`, `AC-0013-05`, and `AC-0013-10` across canonical routing entrypoints and deterministic behavior coverage (`src/testbot/canonical_turn_orchestrator.py`, `src/testbot/sat_chatbot_memory_v2.py`, `src/testbot/stabilization.py`, `features/memory_recall.feature`, `tests/test_canonical_turn_orchestrator.py`, `tests/test_runtime_logging_events.py`).


- 2026-03-08: AC-0013-09 continuity proof set expanded and locked with deterministic two-turn + repair-followup coverage.
  - AC-0013-09 proof (commit persistence contract): `src/testbot/answer_commit.py`; runtime commit audit log assertions in `tests/test_runtime_logging_events.py::test_chat_loop_logs_commit_stage_record_with_durable_commit_state`.
  - AC-0013-09 proof (next-turn continuity consumption): `src/testbot/context_resolution.py`, `src/testbot/evidence_retrieval.py`; deterministic assertion in `tests/test_runtime_logging_events.py::test_resolve_context_consumes_commit_receipt_continuity_deterministically`.
  - AC-0013-09 proof (two-turn continuity + audit payload completeness): `tests/test_runtime_logging_events.py::test_chat_loop_two_turn_commit_continuity_is_consumed_by_context_and_retrieval`, `tests/test_turn_analytics_aggregator.py::test_aggregate_turn_dataset_multi_turn_commit_continuity_fields_preserved`, and `tests/test_turn_analytics_aggregator.py::test_normalize_and_validate_rows_preserves_commit_audit_payload_completeness`.

- 2026-03-08: Dependency exit-conditions language clarified for ISSUE-0015 alignment.
  - ISSUE-0013 remains open until AC-0013-11 exit conditions EC-0013-11-A/B/C are all satisfied.
  - ISSUE-0015 remains open/red while the AC-0013-11 dependency gate is unresolved; ISSUE-0013 closure claims must explicitly cite matching ISSUE-0014 behavioral evidence.

- 2026-03-08: AC-0013-12 evidence regenerated from current gate/report inputs without over-claiming implementation closure.
  - AC-0013-12 proof (canonical gate evidence): `artifacts/all-green-gate-summary.json` regenerated via `python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json` and now records current failing `product_behave` checks.
  - AC-0013-12 proof (status report + JSON summary): `docs/qa/feature-status-report.md` and `artifacts/feature-status-summary.json` regenerated via `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json` and continue to classify canonical pipeline slices as `partial`.

- 2026-03-09: Governance parity review against architecture-drift findings confirms the primary orchestration drifts remain open and should continue to route through ISSUE-0013.
  - Confirmed still-open drift: routing authority remains split because `intent.resolve` computes/stores `policy_decision` and emits `retrieval_branch_selected` before `retrieve.evidence`, while `policy.decide` still recomputes policy after rerank in canonical runtime flow (`src/testbot/sat_chatbot_memory_v2.py`).
  - Confirmed still-open drift: canonical `answer.assemble` still invokes `stage_answer(...)`, which performs assemble/validate/render/commit semantics before explicit `answer.validate`, `answer.render`, and `answer.commit` stages (`src/testbot/sat_chatbot_memory_v2.py`).
  - Confirmed still-open drift: canonical `answer.validate` currently enforces `validate_answer_assembly_boundary(...)` while heavier answer-policy validation remains coupled to earlier stage-answer path (`src/testbot/sat_chatbot_memory_v2.py`).
  - Confirmed still-open drift: `resolve_turn_intent(...)` remains an offline mini-pipeline (`store=None`) outside full canonical commit-continuity semantics and should be treated as diagnostic unless parity requirements are formalized (`src/testbot/sat_chatbot_memory_v2.py`).
  - Marked partially outdated prior finding: stage-transition invariant-reference migration is now in progress and no longer accurately described as wholly unresolved, because transition validators emit `PINV-*` with explicit legacy `INV-*` mapping bridge (`src/testbot/stage_transitions.py`).

- 2026-03-09: Stage-authority contract tightened so `intent.resolve` no longer writes authoritative policy/decision objects; retrieval gating is now an intent-derived retrieval requirement artifact and policy authority is deferred to `policy.decide`.
  - Runtime proof surface: `src/testbot/sat_chatbot_memory_v2.py` (`intent.resolve`, `retrieve.evidence`, `policy.decide`).
  - Deterministic regression proof: `tests/test_pipeline_semantic_contracts.py::test_policy_authority_is_not_written_before_policy_decide_stage` and `tests/test_canonical_turn_orchestrator.py::test_orchestrator_stabilizes_before_route_authority_assignment`.
  - Deterministic proof commands:
    - `python -m pytest tests/test_pipeline_semantic_contracts.py::test_policy_authority_is_not_written_before_policy_decide_stage`
    - `python -m pytest tests/test_canonical_turn_orchestrator.py::test_orchestrator_stabilizes_before_route_authority_assignment`
    - `python -m pytest tests/test_pipeline_semantic_contracts.py tests/test_canonical_turn_orchestrator.py`

- 2026-03-09: AC-0013-11 dependency evidence refreshed with explicit pass/fail linkage for ISSUE-0014 Phase 1 behavioral exits.
  - Deterministic targeted suites pass: BDD (`python -m behave features/memory_recall.feature features/intent_grounding.feature`) and focused regression pytests (`tests/test_pipeline_semantic_contracts.py`, `tests/test_canonical_turn_orchestrator.py`, `tests/test_intent_router.py`).
  - Canonical readiness gate now reports `status=passed` with warning-mode KPI guardrail violations: `python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json` (non-blocking warning on `qa_validate_kpi_guardrails`).
  - Governance validators rerun and passing: `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main` and `python scripts/validate_issues.py --all-issue-files --base-ref origin/main` (both with documented `origin/main` -> `HEAD~1` fallback behavior).
  - Governance outcome: AC-0013-11 remains open (`[~]`) for governance close-order sequencing only; synchronized dependency language and reproducible closure-proof CLI traces are complete for identity semantic preservation, retrieval activation on self-reference recall, and confirmed identity fact promotion at commit.
  - Evidence links: `docs/issues/evidence/2026-03-09-issue-0014-0013-phase1-deterministic-verification.md`, `docs/issues/evidence/2026-03-09-issue-0014-0013-behave.log`, `docs/issues/evidence/2026-03-09-issue-0014-0013-focused-pytests.log`, `docs/issues/evidence/2026-03-09-issue-0014-0013-all-green-gate.log`, `artifacts/all-green-gate-summary.json`.
