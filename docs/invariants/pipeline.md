# Pipeline Semantics Invariants

This registry defines semantic/pipeline invariants for canonical stage transitions, artifact contracts, and projection safety.

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
