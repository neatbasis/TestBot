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
- intent contract fields (state + telemetry):
  - `classified_intent`: classifier-only result from utterance/pattern signals.
  - `resolved_intent`: authoritative context-enriched intent used by downstream stages.
  - `intent` (telemetry alias): MUST mirror `resolved_intent` and never diverge.

Invariant:
- Intent is derived from enriched state, not raw text alone.
- Downstream logging/routing MUST read intent fields from one post-resolution `PipelineState` instance.

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


## Intent taxonomy contract

This section defines the deterministic contract for top-level intent classification and typed facet composition used by `intent.resolve`.

### 1) Allowed intent classes

Canonical top-level classes are constrained to:

- `knowledge_question`
- `meta_conversation`
- `capabilities_help`
- `memory_recall`
- `time_query`
- `control`

Any other class label is invalid for canonical routing.

### 2) Allowed facet combinations

Facets are secondary typed signals (`temporal`, `memory`, `capability`, `control`) and must satisfy:

| Intent class | Allowed facet contract |
| --- | --- |
| `control` | `control=true`; `temporal=false`, `memory=false`, `capability=false` |
| `time_query` | `temporal=true`; `control=false`; `memory` optional; `capability` optional |
| `memory_recall` | `memory=true`; `control=false`; `temporal` optional; `capability` optional |
| `capabilities_help` | `capability=true`; `control=false`; `temporal=false`; `memory=false` |
| `meta_conversation` | `control=false`; `temporal=false`; `memory=false`; `capability` optional |
| `knowledge_question` | `control=false`; `temporal` optional; `memory` optional; `capability` optional |

Invalid combinations are rejected as taxonomy violations (deterministic error reasons should be emitted by validation).

### 3) Precedence rules for overlaps

When an utterance activates multiple cues, overlap resolution order is:

1. `control`
2. `time_query`
3. `memory_recall`
4. `capabilities_help`
5. `meta_conversation`
6. `knowledge_question` (default/fallback)

Operationally for the overlap classes requested by stakeholders:

- `control` supersedes `capabilities_help`, `meta_conversation`, and `knowledge_question`.
- `capabilities_help` supersedes `meta_conversation` and `knowledge_question` when capability-action phrasing is explicit.
- `meta_conversation` supersedes `knowledge_question` for chat/process reflection prompts.
- `knowledge_question` remains the deterministic fallback when no higher-precedence class matches.

## Example traces

The following trace classes are intended to be **mutually exclusive and commonly exhaustive** for canonical turn handling at `intent.resolve` time.

Classification precedence (top to bottom) defines exclusivity:

1. `control`
2. `repair_offer_followup`
3. `clarification_response`
4. `memory_recall`
5. `user_fact_declaration`
6. `general_knowledge_question`
7. `meta_conversation`

If multiple candidate labels are present, choose the highest-precedence class and carry lower-precedence alternatives as non-authoritative candidates in stabilized state.

### A) `user_fact_declaration` (self-identification)

User: `Hi! My name is Sebastian.`

- `encode.candidates`: greeting + self-identification + fact candidate `user_name=Sebastian`
- `stabilize.pre_route`: persist utterance and fact candidate with provenance
- `intent.resolve`: `user_fact_declaration`
- `policy.decide`: acknowledge + persist
- `answer.render`: "Nice to meet you, Sebastian."
- `answer.commit`: user-name fact survives for later recall

### B) `memory_recall`

User: `What's my name?`

- `intent.resolve`: `memory_recall(user_profile.name)`
- `retrieve.evidence`: structured fact `user_name=Sebastian`
- `policy.decide`: `answer_from_memory`
- `answer.render`: "Your name is Sebastian."

### C) `repair_offer_followup`

Prior assistant offer: "I can help reconstruct the timeline or suggest where to check next."

User: `What do you need?`

- `context.resolve`: materialize pending repair mode from prior offer
- `intent.resolve`: `repair_offer_followup(memory_reconstruction_offer)`
- `policy.decide`: request missing reconstruction slots
- `answer.commit`: keep repair mode active for next turn

### D) `clarification_response`

Prior assistant clarification: "Did you mean your legal name or display name?"

User: `Display name.`

- `context.resolve`: detect unresolved clarification obligation
- `intent.resolve`: `clarification_response(display_name)`
- `retrieve.evidence`: gather only clarification-relevant candidates/anchors
- `policy.decide`: continue suspended parent task with resolved slot

### E) `general_knowledge_question`

User: `What is the capital of France?`

- `intent.resolve`: `general_knowledge_question`
- `retrieve.evidence`: source connector or curated knowledge evidence
- `policy.decide`: answer when evidence sufficiency passes, otherwise safe fallback
- `answer.validate`: ensure provenance/citation contract for knowing mode

### F) `control`

User: `/reset session`

- `encode.candidates`: detect command/control candidate
- `intent.resolve`: `control(reset_session)`
- `policy.decide`: perform control action; suppress unrelated retrieval
- `answer.commit`: persist updated session/control state

### G) `meta_conversation`

User: `How do you decide whether you're sure about an answer?`

- `intent.resolve`: `meta_conversation`
- `retrieve.evidence`: pull policy/provenance explanation anchors (not user-memory recall)
- `policy.decide`: explain contract-level behavior without fabricating unseen state
- `answer.render`: concise explanation plus uncertainty boundary when needed

Together, traces A-G partition the canonical intent/state ontology and provide a baseline exhaustive test surface for AC-0013-10 deterministic behavior validation.
