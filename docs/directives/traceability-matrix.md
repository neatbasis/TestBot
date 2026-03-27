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
| **Foundation** | `observe.turn` → `encode.candidates` → `stabilize.pre_route` (ISSUE-0013 Foundation checkpoint: “observe/encode/stabilize baseline”, no early lossy `U -> I` path; supersedes ISSUE-0012 Sprint 3 checkpoint) | Stage/state flow: `observe_stage(...)`, `encode_stage(...)`, `stage_rewrite_query(...)`, `PipelineState`, `append_pipeline_snapshot(...)`; transition guards: `validate_observe_turn_pre/post(...)`, `validate_encode_candidates_pre/post(...)`, `validate_stabilize_pre_route_pre/post(...)` in `stage_transitions.py`; durable pre-route persistence: `make_utterance_card(...)`, `store_doc(...)`, `generate_reflection_yaml(...)`. | `BDD-MR-01` cited memory-grounded answer path; `BDD-MR-02` progressive assist fallback path; `BDD-MR-04` pronoun temporal follow-up resolves anchor before routing. | `python scripts/all_green_gate.py`; `python -m behave`; `python -m pytest -m "not live_smoke"`. | `user_utterance_ingest`; `query_rewrite_output`; `pipeline_state_snapshot` (`stage: rewrite`); `stage_transition_validation` (`stage: observe.turn|encode.candidates|stabilize.pre_route`). | Postcondition: raw user turn is durably observed and encoded before intent authority/routing. **PINV-001/PINV-002/PINV-003/PINV-004** linkage: stage order, observe-before-infer, candidate multiplicity, and stabilize-before-route govern foundation-stage authority. |
| **Decisioning** | `context.resolve` → `intent.resolve` → `retrieve.evidence` → `policy.decide` (ISSUE-0013 Decisioning checkpoint: context/intent/retrieve/policy alignment with explicit empty-evidence vs scored-empty handling; incorporates ISSUE-0012 Sprint 4 outcomes) | Context/intent/policy routing: `context_resolution.resolve(...)`, `intent_resolution.resolve(...)`, `policy_decision.decide(...)`; evidence stages: `stage_retrieve(...)`, `stage_rerank(...)`, `parse_target_time(...)`, `rerank_docs_with_time_and_type_outcome(...)`, `has_sufficient_context_confidence(...)`; policy execution: `stage_answer(...)`, `decide_fallback_action(...)`; transition guards: `validate_context_resolve_pre/post(...)`, `validate_intent_resolve_pre/post(...)`, `validate_retrieve_evidence_pre/post(...)`, `validate_policy_decide_pre/post(...)`. | `BDD-MR-01`; `BDD-MR-02`; `BDD-MR-03` equivalent candidates remain ambiguous after tie-break; `BDD-AC-05` ambiguous memory recall uses ask route when capability available; `BDD-AC-06` low-confidence non-memory fallback maps to uncertainty token; `BDD-AC-07` memory recall without confident hit offers assist alternatives. | `python scripts/all_green_gate.py`; `python -m behave`; `python -m pytest -m "not live_smoke"`; `python -m pytest tests/test_eval_runtime_parity.py`. | `retrieval_branch_selected`; `retrieval_candidates`; `time_target_parse`; `intent_classified`; `ambiguity_detected`; `rerank_skipped`; `fallback_action_selected`; `pipeline_state_snapshot` (`stage: retrieve|rerank|answer`); `stage_transition_validation` (`stage: context.resolve|intent.resolve|retrieve.evidence|policy.decide`). | Postcondition: resolved intent, retrieval evidence, ambiguity/confidence, and fallback action are mutually coherent for the selected decision class. **PINV-005/PINV-006/PINV-007/PINV-008/PINV-009** linkage: repair/obligation materialization, resolved-intent authority, typed evidence posture, retrieval-policy coherence, and decision-answer alignment govern decisioning. |
| **Commit / Audit** | `answer.assemble` → `answer.validate` → `answer.render` → `answer.commit` (ISSUE-0013 Commit/Audit checkpoint: assemble/validate/render/commit completion with release-readiness traceability and audit artifacts; fed by ISSUE-0012 Sprint 5 validation) | Answer runtime stages: `answer_assemble(...)`, `answer_validate(...)`, `answer_render(...)`, `answer_commit(...)`; provenance assembly + contract validation: `build_provenance_metadata(...)`, `validate_answer_contract(...)`, `validate_general_knowledge_contract(...)`, `response_contains_claims(...)`, `has_required_memory_citation(...)`; commit/persistence: `answer_commit_persistence(...)` performs assistant `store_doc(...)` + `persist_promoted_context(...)`; audit feed: `append_session_log(...)`, `aggregate_turn_dataset(...)`, `compute_kpis(...)`. | `BDD-MR-01`; `BDD-MR-02`; `BDD-AC-01` rejection of uncited factual response; `BDD-AC-02` disallowed unlabeled general-knowledge output; `BDD-AC-03` allowed labeled general-knowledge output; `BDD-AC-04` non-memory fallback stays knowledge-safe; `BDD-AC-08` low-confidence recall debug emits transparent observation/policy layers. | `python scripts/all_green_gate.py`; `python -m behave`; `python -m pytest -m "not live_smoke"`; `python -m pytest tests/test_eval_runtime_parity.py`. | `final_answer_mode`; `provenance_summary`; `alignment_decision_evaluated`; `promoted_context_persisted`; `debug_turn_trace`; `pipeline_state_snapshot` (`stage: answer`); turn analytics artifacts `logs/turn_analytics.jsonl`, `logs/turn_analytics_summary.json`. | Postcondition: only validated/render-safe answers are committed with citation/provenance and replayable audit telemetry. **PINV-009/PINV-010/PINV-011/PINV-012** linkage: decision/validation alignment, validation-gated rendering, continuity-preserving commit semantics, and artifact-backed claim legitimacy govern commit/audit replayability. |


## DTO boundary crosswalk for canonical stages

This crosswalk complements the canonical stage-group traceability rows above by focusing on boundary-level DTO/state honesty at each canonical stage handoff. It is subordinate to this matrix’s canonical behavior → stage → deterministic-test authority, and it does not replace pipeline narrative authority in `docs/architecture/canonical-turn-pipeline.md`. It is a mapping artifact (traceability surface), not a second canonical owner of DTO boundary semantics. When prose here diverges from the typed contract surface in `src/testbot/domain/canonical_dtos.py` and `src/testbot/logic/stage_artifacts.py`, those code contracts govern runtime behavior and tests.

| Canonical stage | Input DTO / state | Output DTO / state | Required boundary facts | Must preserve | Forbidden boundary violation | Invariant / contract linkage | Runtime guard / evidence | <!-- PINV-000 header linkage marker for stage-conformance tooling -->
| --- | --- | --- | --- | --- | --- | --- | --- |
| `observe.turn` | raw utterance `U` + turn metadata + prior dialogue/repair state | `TurnObservation` (`O`) | Raw content + speaker/channel/timestamp captured; observation object emitted | Raw user wording and source metadata before inference | Interpreting away or rewriting raw user content during observation | `PINV-001/PINV-002` canonical order + observe-before-infer contract | `validate_observe_turn_pre/post(...)`; `stage_transition_validation` (`observe.turn`); `user_utterance_ingest` |
| `encode.candidates` | `TurnObservation` (`O`) | candidate set `C` (multiplicity-preserving encodings) | Candidate multiplicity present; no authoritative single intent yet | Alternative plausible candidates (speech-act/fact/repair/control) | Collapsing candidates into one authoritative intent before stabilization | `PINV-001/PINV-003` canonical order + candidate-multiplicity-before-authority contract | `validate_encode_candidates_pre/post(...)`; `stage_transition_validation` (`encode.candidates`); `query_rewrite_output` |
| `stabilize.pre_route` | candidate set `C` | stabilized pre-routing state `S` with durable refs/IDs | Durable IDs/refs established; extractable facts persisted pre-route | Candidate-linked facts/provenance and pre-route alternatives | Routing/intent authority before durable extractable facts are stabilized | `PINV-001/PINV-004/PINV-012` canonical order + stabilize-before-route durability contract | `validate_stabilize_pre_route_pre/post(...)`; `stage_transition_validation` (`stabilize.pre_route`); `pipeline_state_snapshot` (`rewrite`) |
| `context.resolve` | stabilized state `S` | context-enriched state (repair/obligation/anchor-resolved `S`) | Pending repair, obligations, and discourse anchors explicit in state | Offer/anchor obligations and anaphora focus continuity | Dropping pending repair or assistant-offer anchors before intent resolution | `PINV-001/PINV-005` canonical order + repair/obligation materialization contract | `validate_context_resolve_pre/post(...)`; `stage_transition_validation` (`context.resolve`); `pipeline_state_snapshot` |
| `intent.resolve` | context-enriched state (`S` + context annotations) | interpreted intent/state `I` (`resolved_intent` authoritative; telemetry `intent` aligned) | `resolved_intent` explicit; telemetry intent mirrors resolved intent | Distinction between classifier-only signal and resolved authoritative intent | Allowing telemetry `intent` to diverge from `resolved_intent` | `PINV-001/PINV-006` canonical order + resolved-intent authority/telemetry coherence contract | `validate_intent_resolve_pre/post(...)`; `stage_transition_validation` (`intent.resolve`); `intent_classified` |
| `retrieve.evidence` | tuple `(I, S)` | evidence set `E` with provenance links | Retrieval branch coherent with resolved intent; evidence/provenance bindings explicit (or explicit empty-evidence state) | Branch rationale + provenance links + empty-vs-scored-empty distinction | Retrieving/reranking against intent-discordant branch or erasing empty-evidence semantics | `PINV-001/PINV-007/PINV-008` canonical order + typed evidence posture + retrieval-policy coherence contract | `validate_retrieve_evidence_pre/post(...)`; `retrieval_branch_selected`; `retrieval_candidates`; `time_target_parse`; `stage_transition_validation` (`retrieve.evidence`) |
| `policy.decide` | interpreted intent + `E` + confidence/capability/repair context | decision object `D` | Decision class explicit and executable (`answer_from_memory`, `ask_for_clarification`, etc.) | Decision rationale inputs (intent/evidence/confidence/repair obligations) | Choosing decision class inconsistent with available evidence/intent state | `PINV-001/PINV-008/PINV-009` canonical order + retrieval-policy/decision-answer coherence contract | `validate_policy_decide_pre/post(...)`; `fallback_action_selected`; `alignment_decision_evaluated`; `stage_transition_validation` (`policy.decide`) |
| `answer.assemble` | `(D, E)` | answer candidate `A` | Candidate text bound to selected decision class and evidence/provenance | Provenance bindings and decision-class constraints in assembled answer | Free-form semantic generation path unbound to decision/evidence class | `PINV-001/PINV-009/PINV-012` canonical order + decision-answer alignment + artifact-backed assembly claims contract | `answer_assemble(...)`; `provenance_summary`; `pipeline_state_snapshot` (`answer`) |
| `answer.validate` | answer candidate `A` | validated answer state `V` (pass or explicit degraded fallback eligibility) | Validation outcome explicit; grounding/citation/alignment checks resolved | Validation verdict + failure mode (if any) for downstream render/commit | Passing forward semantic answer text with unresolved validation status | `PINV-001/PINV-009/PINV-010/PINV-012`; canonical validation-gate and artifact-backed claims contract | `answer_validate(...)`; `validate_answer_contract(...)`; `validate_general_knowledge_contract(...)`; `has_required_memory_citation(...)` |
| `answer.render` | validated answer state `V` | rendered response `R` | Render mode explicit (validated normal vs explicit degraded fallback) | Validation outcome semantics and fallback labeling | Rendering unvalidated semantic answer text | `PINV-001/PINV-010/PINV-012` render-after-validate and artifact-backed claim contract | `answer_render(...)`; `final_answer_mode`; `debug_turn_trace` |
| `answer.commit` | `(S, V, R)` | committed next-turn state `S'` | Commit-ready persistence state explicit (provenance, repair state, obligations) | Assistant memory card, answer provenance, pending repair/obligation continuity | Committing failed-validation semantic answer text or dropping rendered repair-state obligations | `PINV-001/PINV-011/PINV-012`; canonical commit continuity + artifact-backed claim contract `(S,V,R) → S'` | `answer_commit(...)`; `answer_commit_persistence(...)`; `promoted_context_persisted`; `pipeline_state_snapshot`; `stage_transition_validation` (`answer.commit`) |

### DTO inventory and landing targets (pivot-aligned)

The crosswalk above is stage-boundary-first. This inventory is DTO-type-first and lists where each canonical DTO belongs under the pivot package-direction model (`domain/` for canonical contracts, `logic/` for orchestration-boundary typed artifact access, and `ports/` DTO signatures for external protocol boundaries). This table traces DTO placement and invariant linkage; it does not establish a competing DTO contract authority.

| DTO / typed state contract | Canonical role in pipeline | Authoritative contract surface today | Where it should land (pivot target) | Notes on boundary usage | Invariant linkage | <!-- PINV-000 header linkage marker for stage-conformance tooling -->
| --- | --- | --- | --- | --- | --- |
| `TurnObservation` | Observed turn object (`O`) after `observe.turn` | `src/testbot/domain/canonical_dtos.py` | `src/testbot/domain/` (canonical stage DTO) | Authoritative post-observe DTO before candidate encoding. | `PINV-001/PINV-002` |
| `CandidateEncodingSet` | Multiplicity-preserving candidate state (`C`) | `src/testbot/domain/canonical_dtos.py` | `src/testbot/domain/` (canonical stage DTO) | Must preserve alternatives pre-stabilization and pre-route authority. | `PINV-001/PINV-003` |
| `PreRouteState` | Stabilized pre-routing state (`S`) | `src/testbot/domain/canonical_dtos.py` | `src/testbot/domain/` (canonical stage DTO) | Durable IDs/provenance established before context/intent routing. | `PINV-001/PINV-004` |
| `ContextResolvedState` | Context-enriched stabilized state (`S` with repair/obligation/anchor resolution) | `src/testbot/domain/canonical_dtos.py` | `src/testbot/domain/` (canonical stage DTO) | Carries pending repair and obligations into intent resolution. | `PINV-001/PINV-005` |
| `IntentResolution` | Interpreted intent/state (`I`) with classifier-vs-resolved intent semantics | `src/testbot/domain/canonical_dtos.py` | `src/testbot/domain/` (canonical stage DTO) | `resolved_intent` remains downstream authority; telemetry mirrors it. | `PINV-001/PINV-006` |
| `EvidenceSet` | Retrieved evidence state (`E`) | `src/testbot/domain/canonical_dtos.py` | `src/testbot/domain/` (canonical stage DTO) | Preserves provenance links and empty-vs-scored-empty distinctions. | `PINV-001/PINV-007/PINV-008` |
| `PolicyDecision` | Decision object (`D`) for action class selection | `src/testbot/domain/canonical_dtos.py` | `src/testbot/domain/` (canonical stage DTO); consume in `src/testbot/policies/` + `src/testbot/logic/answer/` | Policy/validation should consume normalized DTO shape, not provider-native payloads. | `PINV-001/PINV-008/PINV-009` |
| `AnswerCandidate` | Assembled candidate answer (`A`) | `src/testbot/domain/canonical_dtos.py` | `src/testbot/domain/` (canonical stage DTO) | Must retain explicit decision/evidence bindings into validation. | `PINV-001/PINV-009/PINV-012` |
| `ValidationResult` | Validated answer gate state (`V`) | `src/testbot/domain/canonical_dtos.py` | `src/testbot/domain/` (canonical stage DTO) | Governs render eligibility and degraded fallback gating. | `PINV-001/PINV-010/PINV-012` |
| `RenderedResponse` | User-visible rendered artifact (`R`) | `src/testbot/domain/canonical_dtos.py` | `src/testbot/domain/` (canonical stage DTO) | Commit boundary accepts validated render output only. | `PINV-001/PINV-010/PINV-012` |
| `CommittedTurnState` | Next-turn committed state (`S'`) | `src/testbot/domain/canonical_dtos.py` | `src/testbot/domain/` (canonical stage DTO) | Persists assistant memory card, provenance, repair/obligation continuity. | `PINV-001/PINV-011/PINV-012` |
| `PipelineState` | Cross-stage orchestration state carrier | `src/testbot/domain/` + stage/runtime orchestration modules | `src/testbot/domain/` as canonical state authority; orchestration consumption in `src/testbot/application/services/` | Keep as typed state carrier; avoid dict-only stage payload regression. | `PINV-001/PINV-002/PINV-003/PINV-004/PINV-005/PINV-006/PINV-007/PINV-008/PINV-009/PINV-010/PINV-011/PINV-012` |
| `StageArtifacts` typed accessors | Typed read/write surface for boundary-critical stage artifacts | `src/testbot/logic/stage_artifacts.py` | `src/testbot/logic/` (orchestration-boundary typed access) | Boundary-critical artifact keys should be accessed through typed accessors. | `PINV-001/PINV-004/PINV-005/PINV-006/PINV-007/PINV-008/PINV-009/PINV-010/PINV-011/PINV-012` |
| Port-boundary request/response DTOs (e.g., retrieval/memory/source connector contracts) | Adapter-facing protocol I/O contracts | `src/testbot/ports/` protocols + companion DTO contracts | `src/testbot/ports/` (protocol signatures) + `src/testbot/domain/` shared DTO definitions | Must prevent backend/provider-native objects from crossing into logic/policy boundaries. | `PINV-004/PINV-007/PINV-008/PINV-012` |

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

This matrix is a synchronized governance artifact. Any stage boundary, rollout checkpoint, scenario inventory, capability-state change, or DTO-boundary crosswalk contract change must be updated here **in the same change set** as:

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
  - Enforcement mechanism: installer creates CLI entry point bound to `testbot.entrypoints.cli:main`.
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
