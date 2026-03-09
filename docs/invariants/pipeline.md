# Pipeline Semantics Invariants

This registry defines semantic/pipeline invariants for canonical stage transitions, artifact contracts, and projection safety.

## Pipeline invariant ID scheme

Pipeline invariants use the dedicated `PINV-*` namespace to avoid ambiguity with response-policy invariants (`INV-*`).

| Pipeline Invariant ID | Invariant statement | Scope |
|---|---|---|
| PINV-001 | **Canonical stage ordering is fixed**: the runtime pipeline preserves the exact stage order `observe.turn → encode.candidates → stabilize.pre_route → context.resolve → intent.resolve → retrieve.evidence → policy.decide → answer.assemble → answer.validate → answer.render → answer.commit`. | Stage-ordering semantics. |
| PINV-002 | **Artifact preconditions are mandatory at each stage boundary**: each stage executes only when its required upstream artifacts are present and non-empty according to its contract. | Artifact precondition and handoff integrity. |
| PINV-003 | **Anti-projection safeguard**: intent resolution must not project raw utterance directly to interpreted intent (`U → I`) and instead must consume enriched stabilized artifacts (`turn_observation`, `encoded_candidates`, `stabilized_turn_state`). | Intent-resolution safety and projection control. |

## Stage transition contracts

| Stage | Preconditions | Postconditions | Invariant linkage |
|---|---|---|---|
| `observe.turn` | `user_input` is present and non-empty before processing begins. | Observation artifact preserves raw user utterance and turn metadata without interpretation loss. | `PINV-002` (fallback flow is only meaningful for non-empty user turns). |
| `encode.candidates` | `turn_observation` artifact is present. | Candidate encodings preserve multiplicity (speech-act/fact/repair/query candidates) without assigning route authority. | `PINV-002` (fallback and clarification pathways rely on candidate evidence shape). |
| `stabilize.pre_route` | `encoded_candidates` artifact is present. | Stable pre-routing artifacts (utterance card + candidate facts with provenance) are persisted before intent routing. | `PINV-002` (memory insufficiency evaluation depends on stabilized evidence posture). |
| `context.resolve` | `stabilized_turn_state` artifact is present. | Context state includes pending repair/obligation anchors used by downstream intent resolution. | `PINV-002` (clarify/assist behavior depends on context completeness). |
| `intent.resolve` | `turn_observation`, `encoded_candidates`, and `stabilized_turn_state` artifacts are present. | Intent/state classification is derived from enriched artifacts; forbidden early projection `U → I` (raw utterance directly to interpreted intent) is not allowed. | `PINV-002`, `PINV-003` (artifact and anti-projection guards jointly apply). |
| `retrieve.evidence` | `resolved_intent` and stabilized state are present. | Evidence bundle selection is coherent with resolved intent and preserves provenance references. | `PINV-002` (retrieval requires resolved intent and staged artifacts). |
| `policy.decide` | Retrieval result plus stabilized/context artifacts are present. | Decision object class is explicit (`answer_from_memory`, `ask_for_clarification`, repair continuation, etc.) and matches evidence posture. | `PINV-002` (decision classing depends on valid upstream artifacts). |
| `answer.assemble` | Decision object and evidence bundle are present. | Draft answer is bound to explicit evidence/provenance payloads and selected response class. | `PINV-002` (assembly requires decision and evidence artifacts). |
| `answer.validate` | Draft answer and decision metadata are present. | Invariant contract checks are recorded (`invariant_decisions`), including citation and confidence-gate enforcement. | `PINV-002` (validation consumes assembled artifacts and decision metadata). |
| `answer.render` | Validated answer state is present. | User-visible response rendering preserves semantic class selected by policy/validation. | `PINV-001`, `PINV-002` (rendering remains in canonical order with validated input). |
| `answer.commit` | Validated/rendered answer plus stabilized state are present. | Commit receipt records durable next-turn artifacts (assistant utterance memory, provenance, pending repair/obligations). | `PINV-001`, `PINV-002` (commit finalizes canonical order and artifact persistence). |
