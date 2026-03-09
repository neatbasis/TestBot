# Traceability Matrix (Canonical Turn Pipeline)

This matrix aligns runtime traceability to the canonical stage boundaries in `docs/architecture/canonical-turn-pipeline.md` and the ISSUE-0013 canonical-turn-pipeline program checkpoints, with ISSUE-0012 retained as superseded historical rollout context that feeds into ISSUE-0013 sequencing.

| Canonical stage group | Canonical stage boundaries + ISSUE-0013 program checkpoint (ISSUE-0012 historical feed) | Runtime enforcement identifiers (`src/testbot/`) | BDD scenarios (`features/*.feature`) | Deterministic checks (`docs/testing.md`) | Emitted log evidence keys | Canonical stage postconditions + invariant linkage |
|---|---|---|---|---|---|---|
| **Foundation** | `observe.turn` → `encode.candidates` → `stabilize.pre_route` (ISSUE-0013 Foundation checkpoint: “observe/encode/stabilize baseline”, no early lossy `U -> I` path; supersedes ISSUE-0012 Sprint 3 checkpoint) | Stage/state flow: `observe_stage(...)`, `encode_stage(...)`, `stage_rewrite_query(...)`, `PipelineState`, `append_pipeline_snapshot(...)`; transition guards: `validate_observe_pre/post(...)`, `validate_encode_pre/post(...)` in `stage_transitions.py`; durable pre-route persistence: `make_utterance_card(...)`, `store_doc(...)`, `generate_reflection_yaml(...)`. | `BDD-MR-01` cited memory-grounded answer path; `BDD-MR-02` progressive assist fallback path; `BDD-MR-04` pronoun temporal follow-up resolves anchor before routing. | `python scripts/all_green_gate.py`; `python -m behave`; `python -m pytest -m "not live_smoke"`. | `user_utterance_ingest`; `query_rewrite_output`; `pipeline_state_snapshot` (`stage: rewrite`); `stage_transition_validation` (`stage: observe|encode`). | Postcondition: raw user turn is durably observed and encoded before intent authority/routing. **PINV-001/PINV-002** linkage: canonical stage order and stage-boundary artifacts must remain non-lossy before routing decisions. |
| **Decisioning** | `context.resolve` → `intent.resolve` → `retrieve.evidence` → `policy.decide` (ISSUE-0013 Decisioning checkpoint: context/intent/retrieve/policy alignment with explicit empty-evidence vs scored-empty handling; incorporates ISSUE-0012 Sprint 4 outcomes) | Context/intent/policy routing: `context_resolution.resolve(...)`, `intent_resolution.resolve(...)`, `policy_decision.decide(...)`; evidence stages: `stage_retrieve(...)`, `stage_rerank(...)`, `parse_target_time(...)`, `rerank_docs_with_time_and_type_outcome(...)`, `has_sufficient_context_confidence(...)`; policy execution: `stage_answer(...)`, `decide_fallback_action(...)`; transition guards: `validate_retrieve_pre/post(...)`, `validate_rerank_pre/post(...)`. | `BDD-MR-01`; `BDD-MR-02`; `BDD-MR-03` equivalent candidates remain ambiguous after tie-break; `BDD-AC-05` ambiguous memory recall uses ask route when capability available; `BDD-AC-06` low-confidence non-memory fallback maps to uncertainty token; `BDD-AC-07` memory recall without confident hit offers assist alternatives. | `python scripts/all_green_gate.py`; `python -m behave`; `python -m pytest -m "not live_smoke"`; `python -m pytest tests/test_eval_runtime_parity.py`. | `retrieval_branch_selected`; `retrieval_candidates`; `time_target_parse`; `intent_classified`; `ambiguity_detected`; `rerank_skipped`; `fallback_action_selected`; `pipeline_state_snapshot` (`stage: retrieve|rerank|answer`); `stage_transition_validation` (`stage: retrieve|rerank|answer`). | Postcondition: resolved intent, retrieval evidence, ambiguity/confidence, and fallback action are mutually coherent for the selected decision class. **PINV-002/PINV-003** linkage: decisioning must consume stabilized artifacts and preserve anti-projection safeguards across context/intent/retrieval transitions. |
| **Commit / Audit** | `answer.assemble` → `answer.validate` → `answer.render` → `answer.commit` (ISSUE-0013 Commit/Audit checkpoint: assemble/validate/render/commit completion with release-readiness traceability and audit artifacts; fed by ISSUE-0012 Sprint 5 validation) | Answer runtime stages: `answer_assemble(...)`, `answer_validate(...)`, `answer_render(...)`, `answer_commit(...)`; provenance assembly + contract validation: `build_provenance_metadata(...)`, `validate_answer_contract(...)`, `validate_general_knowledge_contract(...)`, `response_contains_claims(...)`, `has_required_memory_citation(...)`; commit/persistence: `answer_commit_persistence(...)` performs assistant `store_doc(...)` + `persist_promoted_context(...)`; audit feed: `append_session_log(...)`, `aggregate_turn_dataset(...)`, `compute_kpis(...)`. | `BDD-MR-01`; `BDD-MR-02`; `BDD-AC-01` rejection of uncited factual response; `BDD-AC-02` disallowed unlabeled general-knowledge output; `BDD-AC-03` allowed labeled general-knowledge output; `BDD-AC-04` non-memory fallback stays knowledge-safe; `BDD-AC-08` low-confidence recall debug emits transparent observation/policy layers. | `python scripts/all_green_gate.py`; `python -m behave`; `python -m pytest -m "not live_smoke"`; `python -m pytest tests/test_eval_runtime_parity.py`. | `final_answer_mode`; `provenance_summary`; `alignment_decision_evaluated`; `promoted_context_persisted`; `debug_turn_trace`; `pipeline_state_snapshot` (`stage: answer`); turn analytics artifacts `logs/turn_analytics.jsonl`, `logs/turn_analytics_summary.json`. | Postcondition: only validated/render-safe answers are committed with citation/provenance and replayable audit telemetry. **PINV-001/PINV-002** linkage: commit/audit semantics preserve canonical stage completion and durable artifact persistence for replayability. |


## Scenario-level tagging convention for BDD traceability

All executable BDD scenarios in `features/*.feature` must include explicit scenario-level traceability tags placed immediately above each `Scenario` or `Scenario Outline` declaration.

- Required tags per scenario:
  - `@ISSUE-xxxx` where `xxxx` is a zero-padded 4-digit issue ID.
  - `@AC-xxxx-yy` where `xxxx` matches the issue ID and `yy` is a zero-padded 2-digit acceptance-criteria/scenario index for that feature slice.
- Existing governance/behavior tags (for example `@Rule:*`, `@Role:*`, `@Priority:*`, `@fast`) must be preserved and may co-exist on the same or adjacent tag lines.
- If a scenario uses multiple rule tags, keep those tags intact and add traceability tags without removing or renaming `@Rule:*` tags.
- `features/memory_recall.feature` is the canonical pattern reference for ISSUE/AC scenario tagging granularity.

Validation intent:

- Missing `@ISSUE-*` and/or `@AC-*` tags are treated as traceability gaps for reporting and governance readiness.
- Reporting utilities may surface these as warnings and unmapped-scenario entries.

## BDD scenario ID mapping used in this matrix

- `BDD-MR-01` → `Scenario: cited memory-grounded answer path` (`features/memory_recall.feature`)
- `BDD-MR-02` → `Scenario: progressive assist fallback path` (`features/memory_recall.feature`)
- `BDD-MR-03` → `Scenario: equivalent candidates remain ambiguous after tie-break` (`features/memory_recall.feature`)
- `BDD-MR-04` → `Scenario: pronoun temporal follow-up resolves anchor before routing` (`features/memory_recall.feature`)
- `BDD-AC-01` → `Scenario: rejection of uncited factual response from eval pattern` (`features/answer_contract.feature`)
- `BDD-AC-02` → `Scenario: disallowed unlabeled general-knowledge factual output` (`features/answer_contract.feature`)
- `BDD-AC-03` → `Scenario: allowed labeled general-knowledge output when confidence gate passes` (`features/answer_contract.feature`)
- `BDD-AC-04` → `Scenario: non-memory general-knowledge fallback stays knowledge-safe` (`features/answer_contract.feature`)
- `BDD-AC-05` → `Scenario: ambiguous memory recall uses ask route when ask capability is available` (`features/answer_contract.feature`)
- `BDD-AC-06` → `Scenario: low-confidence non-memory fallback maps to uncertainty token` (`features/answer_contract.feature`)
- `BDD-AC-07` → `Scenario: memory recall without confident hit offers assist alternatives` (`features/answer_contract.feature`)
- `BDD-AC-08` → `Scenario: low-confidence recall debug emits transparent observation and policy layers` (`features/answer_contract.feature`)

## Maintenance note

This matrix is a synchronized governance artifact. Any stage boundary, rollout checkpoint, scenario inventory, or capability-state change must be updated here **in the same change set** as:

1. `docs/architecture/canonical-turn-pipeline.md`
2. `docs/qa/feature-status.yaml`

Do not merge canonical pipeline changes when these three artifacts disagree.

## Invariant ontology status

- **Canonical ontology split:** response-policy invariants are canonical in `docs/invariants/answer-policy.md`; pipeline semantics are canonical in `docs/invariants/pipeline.md`.
- **Enforcement:** `python scripts/validate_pipeline_stage_conformance.py` rejects stage-semantic rows that omit `PINV-*` linkage or rely only on response-policy `INV-*` IDs.
