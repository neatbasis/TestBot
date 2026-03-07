# Canonical Turn Pipeline

## Purpose

Define a turn-processing pipeline that preserves observations before abstraction, prevents premature intent collapse, and ensures that routing, retrieval, answer generation, and post-answer state all operate over a shared canonical representation.

Core doctrine:

> **Write before infer. Infer from enriched state, not raw text.**

Program linkage: [`ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](../issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md) is the project's **primary bug-elimination program** in the current state; contributors should triage canonical pipeline defects and follow-on work against ISSUE-0013 first, with ISSUE-0012 treated as linked delivery planning context in [`ISSUE-0012-canonical-turn-pipeline-delivery-plan.md`](../issues/ISSUE-0012-canonical-turn-pipeline-delivery-plan.md).

## Canonical stage sequence

```text
observe.turn
→ encode.candidates
→ stabilize.pre_route
→ context.resolve
→ intent.resolve
→ retrieve.evidence
→ policy.decide
→ answer.assemble
→ answer.validate
→ answer.render
→ answer.commit
```

## Typed state model (category-theoretic framing)

Treat each stage as a morphism between typed system-state objects:

- `U`: raw utterance
- `O`: observation object
- `C`: candidate encodings
- `S`: stabilized pre-routing state
- `I`: interpreted intent/state
- `E`: retrieved evidence
- `D`: decision object
- `A`: answer candidate
- `V`: validated answer state
- `R`: rendered response
- `S'`: committed next-turn state

Preferred compositional chain:

```text
U → O → C → S → I → E → D → A → V → R → S'
```

Avoid early lossy projection:

```text
U → I
```

Intent labels are quotient-like and should be derived only after structure has been preserved.

## Stage contracts

### 1) `observe.turn`

Input:
- raw utterance
- timestamp
- speaker/channel identifiers
- prior dialogue state and pending repair state

Output:
- `TurnObservation ∈ O`

Invariant:
- No interpretation here may erase raw content.

### 2) `encode.candidates`

Input:
- `TurnObservation`

Output:
- multiplicity-preserving candidate set `C`, including:
  - speech-act candidates
  - fact candidates
  - episodic-event candidates
  - repair/control/query candidates

Invariant:
- Multiple plausible candidates may coexist; none is authoritative yet.

### 3) `stabilize.pre_route`

Input:
- candidate set `C`

Output:
- stable pre-routing state `S` with:
  - utterance memory card
  - fact candidates with provenance
  - dialogue-state candidates
  - durable IDs/references

Invariant:
- Durable extractable facts are persisted before routing authority.

### 4) `context.resolve`

Input:
- stabilized state `S`

Output:
- context-enriched state with:
  - pending repair mode
  - unresolved obligations
  - prior assistant-offer anchors
  - active focus/anaphora anchors

Invariant:
- Assistant offers that imply next-step expectations become explicit state.

### 5) `intent.resolve`

Input:
- context-enriched state

Output:
- interpreted intent/state `I`

Invariant:
- Intent is derived from enriched state, not raw text alone.

### 6) `retrieve.evidence`

Input:
- `(I, S)`

Output:
- evidence set `E` with provenance links:
  - structured facts
  - episodic utterances
  - prior assistant offers
  - reflections/anchors

Invariant:
- Retrieval branch selection is coherent with resolved intent and discourse context.

### 7) `policy.decide`

Input:
- interpreted intent, evidence, confidence, capability and repair state

Output:
- decision object `D` (`answer_from_memory`, `ask_for_clarification`, `continue_repair_*`, etc.)

Invariant:
- Decision class must match planned semantic response class.

### 8) `answer.assemble`

Input:
- `(D, E)`

Output:
- answer candidate `A` with response content + explicit evidence/provenance bindings

Invariant:
- No unbound free-form generation path outside chosen decision class.

### 9) `answer.validate`

Input:
- `A`

Output:
- validated answer state `V`

Checks include:
- grounding and evidence sufficiency
- provenance/citation contract
- decision-answer class alignment
- discourse-state consistency

### 10) `answer.render`

Input:
- `V`

Output:
- user-visible rendered response `R`

Invariant:
- Rendering does not change semantic class.

### 11) `answer.commit`

Input:
- `(S, V, R)`

Output:
- next-turn committed state `S'`

Must persist:
- assistant utterance memory card
- answer provenance
- updated pending repair state
- resolved/remaining obligations
- confirmed user facts

Invariant:
- If a repair offer is rendered, pending repair state is established in `S'`.

## Canonical invariants

1. **Observe-before-infer**  
   Durable observations are encoded before routing may discard alternatives.
2. **Stabilize-before-route**  
   Extractable user facts get memory-ready representations pre-routing.
3. **Repair-offer materialization**  
   Rendered repair offers must produce explicit pending repair state.
4. **Decision-answer alignment**  
   Chosen action, answer class, and rendered response class agree.
5. **Empty evidence is distinct**  
   No-candidate state is not equivalent to zero-scored candidates.
6. **Retrieval-policy coherence**  
   Memory retrieval with valid evidence cannot be relabeled as generic non-memory without explicit justification.

## Recommended intent/state ontology split

Use separate classes at minimum:

- `user_fact_declaration`
- `memory_recall`
- `repair_offer_followup`
- `clarification_response`
- `general_knowledge_question`
- `control`
- `meta_conversation`

Rationale: current coarse quotienting merges distinct discourse objects too early.

## Definition of done (for pipeline adoption)

A pipeline adoption change is complete when all are true:

1. Pre-routing candidate extraction exists for durable facts and speech acts.
2. Pre-route stabilization persists utterance/fact candidates with provenance.
3. Pending repair state is committed after repair-offer responses.
4. Intent resolution consumes enriched state, not raw utterance alone.
5. Retrieval represents empty evidence distinctly from scored-empty candidate sets.
6. Validation enforces retrieval/policy/answer-class alignment.
7. BDD scenarios and deterministic tests in `features/` + `tests/` are updated for stakeholder-visible behavior changes.

## Example traces

### A) Self-identification

User: `Hi! My name is Sebastian.`

- `encode.candidates`: greeting + self-identification + fact candidate `user_name=Sebastian`
- `stabilize.pre_route`: persist utterance and fact candidate with provenance
- `intent.resolve`: `user_fact_declaration`
- `policy.decide`: acknowledge + persist
- `answer.render`: "Nice to meet you, Sebastian."
- `answer.commit`: user-name fact survives for later recall

### B) Memory recall

User: `What's my name?`

- `intent.resolve`: `memory_recall(user_profile.name)`
- `retrieve.evidence`: structured fact `user_name=Sebastian`
- `policy.decide`: `answer_from_memory`
- `answer.render`: "Your name is Sebastian."

### C) Repair continuation

Prior assistant offer: "I can help reconstruct the timeline or suggest where to check next."

User: `What do you need?`

- `context.resolve`: materialize pending repair mode from prior offer
- `intent.resolve`: `repair_continuation(memory_reconstruction_offer)`
- `policy.decide`: request missing reconstruction slots
- `answer.commit`: keep repair mode active for next turn
