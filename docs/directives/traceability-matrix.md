# Traceability Matrix (Canonical Turn Pipeline)

This document is the **sole canonical source** for behavior → stage → deterministic-test traceability in TestBot. No other document is canonical for this mapping; any quick-reference, source-map, or triage material must resolve back to this matrix.

This matrix aligns runtime traceability to the canonical stage boundaries in `docs/architecture/canonical-turn-pipeline.md` and the ISSUE-0013 canonical-turn-pipeline program checkpoints, with ISSUE-0012 retained as superseded historical rollout context that feeds into ISSUE-0013 sequencing.

## Quick Reference (Fast Triage)

This section is the quick-reference triage map for jumping from BDD behavior to runtime anchors and deterministic tests.

How to triage quickly:

1. Locate the failing scenario title in `features/*.feature`.
2. Search for the runtime anchor in `src/testbot/` (example: `rg "def stage_answer\(" src/testbot`).
3. Run listed deterministic tests first, then run the canonical gate (`python scripts/all_green_gate.py`).

| Feature + scenario(s) | Runtime modules + search anchors (`src/testbot/`) | Validating tests (`tests/`) |
| --- | --- | --- |
| `features/testbot/answer_contract.feature`<br>- rejection of uncited factual response from eval pattern<br>- disallowed unlabeled general-knowledge factual output<br>- allowed labeled general-knowledge output when confidence gate passes<br>- non-memory general-knowledge fallback stays knowledge-safe | `sat_chatbot_memory_v2.py` anchors:<br>- `def validate_answer_contract(`<br>- `def validate_general_knowledge_contract(`<br>- `def passes_general_knowledge_confidence_gate(`<br>- `def stage_answer(`<br>- `def has_required_memory_citation(` | `tests/test_answer_contract.py` anchors:<br>- `def test_non_memory_general_knowledge_contract_failure_degrades_to_knowledge_safe_response(`<br>- `def test_memory_recall_confident_contract_failure_uses_deterministic_recovery_hit(`<br>- `def test_response_contains_claims_matches_extracted_claim_artifacts_for_factual_text(`<br>BDD glue: `features/steps/testbot_answer_contract_steps.py` |
| `features/testbot/memory_recall.feature`<br>- cited memory-grounded answer path<br>- progressive assist fallback path<br>- equivalent candidates remain ambiguous after tie-break | `sat_chatbot_memory_v2.py` anchors:<br>- `def stage_retrieve(`<br>- `def stage_rerank(`<br>- `def stage_answer(`<br>- `def build_partial_memory_clarifier(`<br>- `def build_provenance_metadata(`<br>`rerank.py` anchors:<br>- `def rerank_docs_with_time_and_type(`<br>- `def confidence_decision(` | `tests/test_eval_runtime_parity.py` anchors:<br>- `def test_eval_runtime_parity_fixture_families(`<br>- `def test_eval_runtime_parity_near_tie_fixture_case(`<br>`tests/test_runtime_logging_events.py` anchors:<br>- `def test_stage_answer_memory_recall_confident_hit_recovers_from_contract_failure(`<br>BDD glue: `features/steps/testbot_memory_steps.py` |
| `features/testbot/intent_grounding.feature`<br>- knowledge/meta/relevance/source confidence scenarios<br>- follow-up continuity scenario<br>- retrieval branch logging scenarios<br>- ambiguous routing precedence scenarios<br>- non-knowledge social/control routing scenarios | `sat_chatbot_memory_v2.py` anchors:<br>- `def resolve_turn_intent(`<br>- `def _select_retrieval_branch(`<br>- `def _uses_memory_retrieval(`<br>- `def stage_answer(`<br>- `def _is_short_affirmation(`<br>`intent_router.py` anchors:<br>- `class IntentType`<br>- `def classify_intent(` | `tests/test_intent_router.py` anchors:<br>- `def test_resolve_turn_intent_affirmation_inherits_prior_clarification_intent(`<br>- `def test_classify_intent_control_takes_precedence(`<br>- `def test_classify_intent_capabilities_help_satellite_overrides_meta_phrase(`<br>- `def test_classify_intent_social_greeting_routes_non_knowledge(`<br>`tests/test_runtime_logging_events.py` anchors:<br>- `def test_select_retrieval_branch_routes_definitional_knowledge_question_to_memory_retrieval(`<br>- `def test_chat_loop_conversational_prompt_skips_knowledge_retrieval_path(`<br>BDD glue: `features/steps/testbot_intent_grounding_steps.py` |
| `features/testbot/capabilities.feature`<br>- HA unavailable + CLI fallback capability summary<br>- HA available + satellite enabled capability summary<br>- direct satellite-action requests in CLI mode return alternatives | `sat_chatbot_memory_v2.py` anchors:<br>- `def _build_runtime_capability_status(`<br>- `def build_capability_snapshot(`<br>- `def stage_answer(`<br>- `def _is_capabilities_help_request(` | `tests/test_capabilities_help.py` anchors:<br>- `def test_stage_answer_capabilities_help_reflects_ha_unavailable_cli_fallback(`<br>- `def test_stage_answer_capabilities_help_reflects_ha_satellite_available(`<br>- `def test_stage_answer_satellite_action_request_cli_returns_capability_structured_alternatives(`<br>`tests/test_capabilities_runtime_status.py` anchors:<br>- `def test_shared_snapshot_keeps_cli_fallback_truth_consistent(`<br>BDD glue: `features/steps/testbot_capabilities_steps.py` |
| `features/testbot/source_ingestion.feature`<br>- source-backed knowing answer includes evidence attribution<br>- low-trust source evidence triggers fallback | `source_ingest.py` anchors:<br>- `class SourceIngestor`<br>- `def ingest(`<br>`source_connectors.py` anchors:<br>- `class SourceItem`<br>- `class LocalMarkdownSourceConnector`<br>- `class WikipediaSummarySourceConnector`<br>- `class ArxivSourceConnector`<br>`sat_chatbot_memory_v2.py` anchors:<br>- `def _run_source_ingestion(`<br>- `def collect_used_source_evidence_refs(`<br>- `def build_provenance_metadata(` | `tests/test_source_ingest.py` anchors:<br>- `def test_source_ingestor_stores_memory_and_evidence_with_provenance(`<br>- `def test_source_ingestor_wikipedia_connector_integration(`<br>- `def test_source_ingestor_arxiv_connector_integration(`<br>`tests/test_source_fusion.py` anchors:<br>- `def test_build_provenance_metadata_includes_source_evidence_attribution(`<br>- `def test_build_provenance_metadata_omits_source_keys_when_no_source_refs_used(`<br>BDD glue: `features/steps/testbot_source_ingestion_steps.py` |

| Canonical stage group | Canonical stage boundaries + ISSUE-0013 program checkpoint (ISSUE-0012 historical feed) | Runtime enforcement identifiers (`src/testbot/`) | BDD scenarios (`features/*.feature`) | Deterministic checks (`docs/testing.md`) | Emitted log evidence keys | Canonical stage postconditions + invariant linkage |
|---|---|---|---|---|---|---|
| **Foundation** | `observe.turn` → `encode.candidates` → `stabilize.pre_route` (ISSUE-0013 Foundation checkpoint: “observe/encode/stabilize baseline”, no early lossy `U -> I` path; supersedes ISSUE-0012 Sprint 3 checkpoint) | Stage/state flow: `observe_stage(...)`, `encode_stage(...)`, `stage_rewrite_query(...)`, `PipelineState`, `append_pipeline_snapshot(...)`; transition guards: `validate_observe_turn_pre/post(...)`, `validate_encode_candidates_pre/post(...)`, `validate_stabilize_pre_route_pre/post(...)` in `stage_transitions.py`; durable pre-route persistence: `make_utterance_card(...)`, `store_doc(...)`, `generate_reflection_yaml(...)`. | `BDD-MR-01` cited memory-grounded answer path; `BDD-MR-02` progressive assist fallback path; `BDD-MR-04` pronoun temporal follow-up resolves anchor before routing. | `python scripts/all_green_gate.py`; `python -m behave`; `python -m pytest -m "not live_smoke"`. | `user_utterance_ingest`; `query_rewrite_output`; `pipeline_state_snapshot` (`stage: rewrite`); `stage_transition_validation` (`stage: observe.turn|encode.candidates|stabilize.pre_route`). | Postcondition: raw user turn is durably observed and encoded before intent authority/routing. **PINV-001/PINV-002** linkage: canonical stage order and stage-boundary artifacts must remain non-lossy before routing decisions. |
| **Decisioning** | `context.resolve` → `intent.resolve` → `retrieve.evidence` → `policy.decide` (ISSUE-0013 Decisioning checkpoint: context/intent/retrieve/policy alignment with explicit empty-evidence vs scored-empty handling; incorporates ISSUE-0012 Sprint 4 outcomes) | Context/intent/policy routing: `context_resolution.resolve(...)`, `intent_resolution.resolve(...)`, `policy_decision.decide(...)`; evidence stages: `stage_retrieve(...)`, `stage_rerank(...)`, `parse_target_time(...)`, `rerank_docs_with_time_and_type_outcome(...)`, `has_sufficient_context_confidence(...)`; policy execution: `stage_answer(...)`, `decide_fallback_action(...)`; transition guards: `validate_context_resolve_pre/post(...)`, `validate_intent_resolve_pre/post(...)`, `validate_retrieve_evidence_pre/post(...)`, `validate_policy_decide_pre/post(...)`. | `BDD-MR-01`; `BDD-MR-02`; `BDD-MR-03` equivalent candidates remain ambiguous after tie-break; `BDD-AC-05` ambiguous memory recall uses ask route when capability available; `BDD-AC-06` low-confidence non-memory fallback maps to uncertainty token; `BDD-AC-07` memory recall without confident hit offers assist alternatives. | `python scripts/all_green_gate.py`; `python -m behave`; `python -m pytest -m "not live_smoke"`; `python -m pytest tests/test_eval_runtime_parity.py`. | `retrieval_branch_selected`; `retrieval_candidates`; `time_target_parse`; `intent_classified`; `ambiguity_detected`; `rerank_skipped`; `fallback_action_selected`; `pipeline_state_snapshot` (`stage: retrieve|rerank|answer`); `stage_transition_validation` (`stage: context.resolve|intent.resolve|retrieve.evidence|policy.decide`). | Postcondition: resolved intent, retrieval evidence, ambiguity/confidence, and fallback action are mutually coherent for the selected decision class. **PINV-002/PINV-003** linkage: decisioning must consume stabilized artifacts and preserve anti-projection safeguards across context/intent/retrieval transitions. |
| **Commit / Audit** | `answer.assemble` → `answer.validate` → `answer.render` → `answer.commit` (ISSUE-0013 Commit/Audit checkpoint: assemble/validate/render/commit completion with release-readiness traceability and audit artifacts; fed by ISSUE-0012 Sprint 5 validation) | Answer runtime stages: `answer_assemble(...)`, `answer_validate(...)`, `answer_render(...)`, `answer_commit(...)`; provenance assembly + contract validation: `build_provenance_metadata(...)`, `validate_answer_contract(...)`, `validate_general_knowledge_contract(...)`, `response_contains_claims(...)`, `has_required_memory_citation(...)`; commit/persistence: `answer_commit_persistence(...)` performs assistant `store_doc(...)` + `persist_promoted_context(...)`; audit feed: `append_session_log(...)`, `aggregate_turn_dataset(...)`, `compute_kpis(...)`. | `BDD-MR-01`; `BDD-MR-02`; `BDD-AC-01` rejection of uncited factual response; `BDD-AC-02` disallowed unlabeled general-knowledge output; `BDD-AC-03` allowed labeled general-knowledge output; `BDD-AC-04` non-memory fallback stays knowledge-safe; `BDD-AC-08` low-confidence recall debug emits transparent observation/policy layers. | `python scripts/all_green_gate.py`; `python -m behave`; `python -m pytest -m "not live_smoke"`; `python -m pytest tests/test_eval_runtime_parity.py`. | `final_answer_mode`; `provenance_summary`; `alignment_decision_evaluated`; `promoted_context_persisted`; `debug_turn_trace`; `pipeline_state_snapshot` (`stage: answer`); turn analytics artifacts `logs/turn_analytics.jsonl`, `logs/turn_analytics_summary.json`. | Postcondition: only validated/render-safe answers are committed with citation/provenance and replayable audit telemetry. **PINV-001/PINV-002** linkage: commit/audit semantics preserve canonical stage completion and durable artifact persistence for replayability. |


## Scenario-level tagging convention for BDD traceability

All executable BDD scenarios in `features/*.feature` must include explicit scenario-level traceability tags placed immediately above each `Scenario` or `Scenario Outline` declaration.

- Required tags per scenario:
  - `@ISSUE-xxxx` where `xxxx` is a zero-padded 4-digit issue ID.
  - `@AC-xxxx-yy` where `xxxx` matches the issue ID and `yy` is a zero-padded 2-digit acceptance-criteria/scenario index for that feature slice.
- Existing governance/behavior tags (for example `@Rule:*`, `@Role:*`, `@Priority:*`, `@fast`) must be preserved and may co-exist on the same or adjacent tag lines.
- If a scenario uses multiple rule tags, keep those tags intact and add traceability tags without removing or renaming `@Rule:*` tags.
- `features/testbot/memory_recall.feature` is the canonical pattern reference for ISSUE/AC scenario tagging granularity.

Validation intent:

- Missing `@ISSUE-*` and/or `@AC-*` tags are treated as traceability gaps for reporting and governance readiness.
- Reporting utilities may surface these as warnings and unmapped-scenario entries.

## BDD scenario ID mapping used in this matrix

- `BDD-MR-01` → `Scenario: cited memory-grounded answer path` (`features/testbot/memory_recall.feature`)
- `BDD-MR-02` → `Scenario: progressive assist fallback path` (`features/testbot/memory_recall.feature`)
- `BDD-MR-03` → `Scenario: equivalent candidates remain ambiguous after tie-break` (`features/testbot/memory_recall.feature`)
- `BDD-MR-04` → `Scenario: pronoun temporal follow-up resolves anchor before routing` (`features/testbot/memory_recall.feature`)
- `BDD-AC-01` → `Scenario: rejection of uncited factual response from eval pattern` (`features/testbot/answer_contract.feature`)
- `BDD-AC-02` → `Scenario: disallowed unlabeled general-knowledge factual output` (`features/testbot/answer_contract.feature`)
- `BDD-AC-03` → `Scenario: allowed labeled general-knowledge output when confidence gate passes` (`features/testbot/answer_contract.feature`)
- `BDD-AC-04` → `Scenario: non-memory general-knowledge fallback stays knowledge-safe` (`features/testbot/answer_contract.feature`)
- `BDD-AC-05` → `Scenario: ambiguous memory recall uses ask route when ask capability is available` (`features/testbot/answer_contract.feature`)
- `BDD-AC-06` → `Scenario: low-confidence non-memory fallback maps to uncertainty token` (`features/testbot/answer_contract.feature`)
- `BDD-AC-07` → `Scenario: memory recall without confident hit offers assist alternatives` (`features/testbot/answer_contract.feature`)
- `BDD-AC-08` → `Scenario: low-confidence recall debug emits transparent observation and policy layers` (`features/testbot/answer_contract.feature`)

## Maintenance note

This matrix is a synchronized governance artifact. Any stage boundary, rollout checkpoint, scenario inventory, or capability-state change must be updated here **in the same change set** as:

1. `docs/architecture/canonical-turn-pipeline.md`
2. `docs/qa/feature-status.yaml`

Do not merge canonical pipeline changes when these three artifacts disagree.

## Invariant ontology status

- **Canonical ontology split:** response-policy invariants are canonical in `docs/invariants/answer-policy.md`; pipeline semantics are canonical in `docs/invariants/pipeline.md`.
- **Enforcement:** `python scripts/validate_pipeline_stage_conformance.py` rejects stage-semantic rows that omit `PINV-*` linkage or rely only on response-policy `INV-*` IDs.

## Appendix A — Enforcement and Provenance Source Mapping

This appendix captures enforcement/provenance mapping formerly maintained as a separate source-map document.

Program anchor: [`../issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](../issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md).

Documentation naming note: when updating directive or architecture docs, follow the terminology policy in [docs/terminology.md](../terminology.md), including the rule to preserve real system identifiers verbatim.

### A.1 Runtime-enforced directives (`src/testbot/sat_chatbot_memory_v2.py` guardrails, logging, fallback)

- Answer must be memory-grounded and use only provided context + recent chat.
  - Source location: `ANSWER_PROMPT` system instructions in `src/testbot/sat_chatbot_memory_v2.py`.
  - Enforcement mechanism: prompt-level runtime instruction passed to the model on every response generation.
  - Confidence level: **Advisory** (LLM-followed instruction, not a static type/runtime assert by itself).
- Memory-insufficient turns use progressive fallback (bridging clarifier, assist alternatives, or explicit uncertainty) instead of direct memory fallback.
  - Source location: `ANSWER_PROMPT` guidance + `decide_fallback_action(...)` + deterministic branches in `stage_answer(...)` (`build_partial_memory_clarifier`, `ASSIST_ALTERNATIVES_ANSWER`, `NON_KNOWLEDGE_UNCERTAINTY_ANSWER`).
  - Enforcement mechanism: deterministic answer-stage routing applies policy-selected progressive fallback behavior when confidence/contract checks fail.
  - Confidence level: **Enforced**.
- Factual answers must include citation fields (`doc_id` and `ts`).
  - Source location: `validate_answer_contract()`, `response_contains_claims()`, `has_required_memory_citation()`.
  - Enforcement mechanism: regex-based post-generation contract check; non-compliant outputs are replaced with fallback.
  - Confidence level: **Enforced**.
- Session observability for ingest/retrieval/answer decisions.
  - Source location: `append_session_log()` and call sites (`user_utterance_ingest`, `query_rewrite_output`, `retrieval_candidates`, `time_target_parse`, `final_answer_mode`).
  - Enforcement mechanism: deterministic JSONL logging at key pipeline stages during runtime loop.
  - Confidence level: **Enforced** (when loop runs and log path writable).
- Temporal retrieval behavior should track parsed target time and adaptive sigma.
  - Source location: `parse_target_time(...)`, `adaptive_sigma_fractional(...)`, and rerank call wiring.
  - Enforcement mechanism: runtime rerank pipeline computes target/sigma and uses them in ranking; logged for auditability.
  - Confidence level: **Enforced**.

### A.2 Documentation directives (`README.md` v0 contract, testing policy, BDD requirement)

- v0 scope: small, reliable memory loop for rapid iteration.
  - Source location: project description text in `README.md` (`reliable v0 loop`, intentionally small).
  - Enforcement mechanism: human-facing scope contract for contributors/reviewers.
  - Confidence level: **Advisory**.
- BDD-first policy for stakeholder-visible behavior.
  - Source location: `README.md` section `## BDD-first policy`.
  - Enforcement mechanism: process expectation that features begin as `.feature` scenarios before implementation.
  - Confidence level: **Advisory** (policy-level; enforced socially/review-wise unless CI gates added).
- Testing policy references deterministic checks + behavior contracts.
  - Source location: `README.md` links to `docs/testing.md` and role guidance.
  - Enforcement mechanism: documentation-driven workflow directing contributors to required testing approach.
  - Confidence level: **Advisory**.

### A.3 Tooling directives (`pyproject.toml` dependencies and dev testing stack)

- Runtime dependency baseline for the chatbot stack.
  - Source location: `[project].dependencies` in `pyproject.toml`.
  - Enforcement mechanism: packaging/install resolution enforces required libs for runtime execution.
  - Confidence level: **Enforced** (at install/runtime import boundaries).
- Dev testing/lint/type-check stack (`behave`, `pytest`, `ruff`, `mypy`).
  - Source location: `[project.optional-dependencies].dev` in `pyproject.toml`.
  - Enforcement mechanism: optional dev extra declares expected local/CI tooling.
  - Confidence level: **Advisory** (unless CI/scripts explicitly require all tools).
- Entry point contract for launching the bot (`testbot` script).
  - Source location: `[project.scripts]` in `pyproject.toml`.
  - Enforcement mechanism: installer creates CLI entry point bound to `testbot.entrypoints.sat_cli:main`.
  - Confidence level: **Enforced** (packaging-level).

### A.4 Eval directives (`scripts/eval_recall.py`, `eval/cases.jsonl`)

- Offline evaluation computes retrieval/ranking metrics (`hit_at_k`, rank, IDK decisions).
  - Source location: `evaluate(...)` in `scripts/eval_recall.py`.
  - Enforcement mechanism: deterministic scoring pipeline over fixed candidate sets.
  - Confidence level: **Enforced** (within eval script execution).
- Temporal interpretation heuristic for utterances (`last night`, `earlier this week`, duration phrases).
  - Source location: `parse_target_time(...)` in `scripts/eval_recall.py`.
  - Enforcement mechanism: rule-based parsing used directly by eval ranking flow.
  - Confidence level: **Enforced** (inside eval).
- IDK decision thresholding for weak top score.
  - Source location: `--idk-threshold` arg and `top_score < idk_threshold` check in `scripts/eval_recall.py`.
  - Enforcement mechanism: deterministic decision counter for “don’t know from memory” behavior in eval metrics.
  - Confidence level: **Enforced** (inside eval).
- Canonical evaluation fixtures define expected memory target behavior.
  - Source location: `eval/cases.jsonl` records with `expected_intent`, `expected_doc_id`, and candidate sets.
  - Enforcement mechanism: data contract consumed by eval script to benchmark ranking/IDK outcomes.
  - Confidence level: **Enforced** for eval runs; **advisory** for production runtime unless mirrored by tests/CI.
