# Invariant Registry

This registry defines contract-level invariants for answer behavior. Each invariant has a stable ID and traceability links to implementation and verification coverage.

`docs/invariants.md` is the canonical source of truth; directive mirrors (for example `docs/directives/invariants.md`) must remain synchronized with this contract.

Program linkage: [`ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md) is the project's **primary bug-elimination program** in the current state; contributors should triage canonical pipeline defects and follow-on work against ISSUE-0013 first, with ISSUE-0012 treated as linked delivery planning context in [`ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`](issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md).

## Canonical mirror source (exact sync block)

The block between the markers below is the **single source section** for the invariant table and scenario map. `docs/directives/invariants.md` must mirror this block exactly via `python scripts/sync_invariants_mirror.py`.

<!-- BEGIN_SYNCED_INVARIANTS_TABLE_AND_SCENARIO_MAP -->

## Invariants

| Invariant ID | Invariant statement | Runtime enforcement (code location) | Test/BDD coverage |
|---|---|---|---|
| INV-001 | **Citation-required factual responses**: Any response containing factual claims must include at least one memory citation with both `doc_id` and `ts`; otherwise the response is contract-invalid. | `response_contains_claims`, `raw_claim_like_text_detected`, `has_required_memory_citation`, and `validate_answer_contract` in `src/testbot/sat_chatbot_memory_v2.py`; answer contract language in `ANSWER_PROMPT` in the same module. | BDD: `Scenario: rejection of uncited factual response from eval pattern` in `features/answer_contract.feature` via step validator mirror in `features/steps/answer_contract_steps.py`. BDD: cited-answer path `Scenario: cited memory-grounded answer path` in `features/memory_recall.feature` via citation assertions in `features/steps/memory_steps.py`. |
| INV-002 | **Progressive fallback for insufficient memory**: If memory is empty/low-confidence, assistant must ask one targeted clarifier or offer at least two capability-based alternatives; if memory is partial/ambiguous, assistant must provide a brief user-facing summary plus one bridging clarifier; direct memory fallback phrase usage is not used for standard insufficiency paths. | Fallback policy routing in `decide_fallback_action(...)` in `src/testbot/reflection_policy.py`; progressive clarify/assist branches (`build_partial_memory_clarifier`, `ASSIST_ALTERNATIVES_ANSWER`) and uncertainty fallback handling in `stage_answer(...)` in `src/testbot/sat_chatbot_memory_v2.py`. | BDD: `Scenario: progressive assist fallback path` and `Scenario: equivalent candidates remain ambiguous after tie-break` in `features/memory_recall.feature`, validated via mode/shape assertions in `features/steps/memory_steps.py`. |
| INV-003 | **General-knowledge responses require explicit marker + confidence gate**: non-memory factual answers must include `General definition (not from your memory):` and pass confidence/support thresholds; otherwise runtime must degrade to a knowledge-safe uncertainty response. | `has_general_knowledge_marker`, `passes_general_knowledge_confidence_gate`, `validate_general_knowledge_contract`, and enforcement/degrade logic in `stage_answer(...)` in `src/testbot/sat_chatbot_memory_v2.py`. | BDD: `Scenario: disallowed unlabeled general-knowledge factual output`, `Scenario: allowed labeled general-knowledge output when confidence gate passes`, and `Scenario: non-memory general-knowledge fallback stays knowledge-safe` in `features/answer_contract.feature` via `features/steps/answer_contract_steps.py`. |

## Scenario ID map

- `BDD-AC-01`: `features/answer_contract.feature` → `Scenario: rejection of uncited factual response from eval pattern`
- `BDD-MR-01`: `features/memory_recall.feature` → `Scenario: cited memory-grounded answer path`
- `BDD-MR-02`: `features/memory_recall.feature` → `Scenario: progressive assist fallback path`
- `BDD-AC-02`: `features/answer_contract.feature` → `Scenario: disallowed unlabeled general-knowledge factual output`
- `BDD-AC-03`: `features/answer_contract.feature` → `Scenario: allowed labeled general-knowledge output when confidence gate passes`
- `BDD-AC-04`: `features/answer_contract.feature` → `Scenario: non-memory general-knowledge fallback stays knowledge-safe`

<!-- END_SYNCED_INVARIANTS_TABLE_AND_SCENARIO_MAP -->

## Stage transition contracts

| Stage | Preconditions | Postconditions | Invariant linkage |
|---|---|---|---|
| `observe.turn` | `user_input` is present and non-empty before processing begins. | Observation artifact preserves raw user utterance and turn metadata without interpretation loss. | `INV-002` (fallback flow is only meaningful for non-empty user turns). |
| `encode.candidates` | `turn_observation` artifact is present. | Candidate encodings preserve multiplicity (speech-act/fact/repair/query candidates) without assigning route authority. | `INV-002` (fallback and clarification pathways rely on candidate evidence shape). |
| `stabilize.pre_route` | `encoded_candidates` artifact is present. | Stable pre-routing artifacts (utterance card + candidate facts with provenance) are persisted before intent routing. | `INV-002` (memory insufficiency evaluation depends on stabilized evidence posture). |
| `context.resolve` | `stabilized_turn_state` artifact is present. | Context state includes pending repair/obligation anchors used by downstream intent resolution. | `INV-002` (clarify/assist behavior depends on context completeness). |
| `intent.resolve` | `turn_observation`, `encoded_candidates`, and `stabilized_turn_state` artifacts are present. | Intent/state classification is derived from enriched artifacts; forbidden early projection `U → I` (raw utterance directly to interpreted intent) is not allowed. | `INV-002` (fallback classing and ambiguity routing require enriched-state intent resolution). |
| `retrieve.evidence` | `resolved_intent` and stabilized state are present. | Evidence bundle selection is coherent with resolved intent and preserves provenance references. | `INV-001`, `INV-002` (citation and insufficiency paths depend on retrieval posture). |
| `policy.decide` | Retrieval result plus stabilized/context artifacts are present. | Decision object class is explicit (`answer_from_memory`, `ask_for_clarification`, repair continuation, etc.) and matches evidence posture. | `INV-002`, `INV-003` (fallback and general-knowledge branch gating depend on decision class). |
| `answer.assemble` | Decision object and evidence bundle are present. | Draft answer is bound to explicit evidence/provenance payloads and selected response class. | `INV-001`, `INV-003`. |
| `answer.validate` | Draft answer and decision metadata are present. | Invariant contract checks are recorded (`invariant_decisions`), including citation and confidence-gate enforcement. | `INV-001`, `INV-002`, `INV-003`. |
| `answer.render` | Validated answer state is present. | User-visible response rendering preserves semantic class selected by policy/validation. | `INV-002`, `INV-003`. |
| `answer.commit` | Validated/rendered answer plus stabilized state are present. | Commit receipt records durable next-turn artifacts (assistant utterance memory, provenance, pending repair/obligations). | `INV-001`, `INV-002`, `INV-003`. |
