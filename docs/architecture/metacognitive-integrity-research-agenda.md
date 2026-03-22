# Metacognitive Integrity Research Agenda

**Status:** Draft for architecture pivot planning  
**Scope:** TestBot turn pipeline, trace artifacts, self-report behavior, governance gates  
**Related issue anchor:** ISSUE-0014

## 1) Research objective

TestBot should be able to provide useful metacognitive reports while staying explicitly constrained by what the architecture makes knowable. This agenda treats metacognition as a verifiable systems property instead of an unconstrained narrative style.

### North-star question

**How can TestBot produce useful metacognitive reports while remaining explicitly constrained by what its architecture actually makes knowable?**

## 2) Definitions and taxonomy (research-grounded)

This section defines the terms used in this agenda and separates capacity levels that are often conflated under a single phrase such as "self-awareness." The design intent is to keep TestBot claims operational, auditable, and proportionate to the strength of current evidence.

### 2.1 Self-related capacities

#### Self-report (output channel)
Natural-language statements the system makes about itself (for example: uncertainty, strategy, memory, or confidence claims).  
Research implication: self-report is not equivalent to mechanism-level truth; it is a report channel that can diverge from latent processes or actual information state ([Language Models Fail to Introspect About Their Knowledge of Language](https://arxiv.org/abs/2503.07513), [Looking Inward: Language Models Can Learn About Themselves by Introspection](https://arxiv.org/abs/2410.13787)).

#### Introspection
Knowledge about the model's own internal behavior that originates from internal state and is not merely copied from generic priors or dataset regularities.  
Research implication: current evidence is mixed; some work shows limited self-prediction in constrained settings while other work finds weak/absent privileged self-access in language-grounded tests ([Looking Inward: Language Models Can Learn About Themselves by Introspection](https://arxiv.org/abs/2410.13787), [Language Models Fail to Introspect About Their Knowledge of Language](https://arxiv.org/abs/2503.07513)).

#### Metacognitive monitoring
Second-order monitoring of first-order cognition, including confidence estimation, error-likelihood estimation, and uncertainty signaling.  
Research implication: metacognitive monitoring is a practical and testable systems target distinct from broader claims about inner awareness ([Language Models Are Capable of Metacognitive Monitoring ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12136483/), [Large Language Models Have Intrinsic Meta-Cognition, but ...](https://aclanthology.org/2025.emnlp-main.171/)).

#### Self-reflection
Deliberate review of prior reasoning or outcomes to produce guidance for later attempts.  
Research implication: self-reflection is primarily an adaptation mechanism; improved performance does not by itself establish deep introspective access ([Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366)).

#### Self-consciousness / self-cognition
Higher-order claims about awareness of own existence, identity, or inner process.  
Research implication: this layer remains more speculative and should remain analytically separate from production reliability claims ([Probing Self-Consciousness in Language Models](https://aclanthology.org/2025.findings-acl.392/)).

### 2.2 Memory-related capacities

#### Working memory
Transient task-state used within the active turn (for example context-window state, temporary scratch structures).  
Reference framing: modern agent-memory taxonomies treat this as distinct from durable factual or experiential stores ([Memory in the Age of AI Agents](https://arxiv.org/abs/2512.13564)).

#### Semantic/factual memory
Generalized knowledge not tied to a single situated event.  
Reference framing: distinct from event-grounded episodic memory ([Memory in the Age of AI Agents](https://arxiv.org/abs/2512.13564)).

#### Episodic memory
Representation of specific events grounded in time, place, entities, and contextual details.  
Design relevance: supports "what happened / when / where / with whom / with what source."

#### Experiential memory
Compressed lessons from prior interactions, outcomes, trajectories, and feedback that can influence future policy.  
Reference framing: a key bridge between memory and adaptation in agent settings ([Memory in the Age of AI Agents](https://arxiv.org/abs/2512.13564)).

#### Source memory / source monitoring
Memory of origin (where a claim came from) and monitoring of whether content was observed, inferred, or generated.  
Design relevance: critical for provenance-backed "knowing mode" and for reality/source monitoring in continuity workflows.

### 2.3 Improvement-related capacities

#### Self-evaluation
Second-order judgment about likely correctness, uncertainty, and answer/process quality ([Large Language Models Have Intrinsic Meta-Cognition, but ...](https://aclanthology.org/2025.emnlp-main.171/)).

#### Error detection
Detection that a produced answer or reasoning path is likely wrong ([Large Language Models Have Intrinsic Meta-Cognition, but ...](https://aclanthology.org/2025.emnlp-main.171/)).

#### Reflection-driven adaptation
Use of generated critique/feedback to alter subsequent attempts ([Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366)).

#### Memory-driven self-improvement
Decision improvement through retrieval and valuation of stored prior interactions/outcomes ([Memory-Driven Self-Improvement for Decision Making with Large Language Models](https://arxiv.org/abs/2509.26340)).

#### Self-evolving agent behavior
Continual adaptation over prompts, memory policies, tools, architecture, or parameters across time ([A Survey of Self-Evolving Agents](https://arxiv.org/abs/2507.21046)).

### 2.4 Practical claim hierarchy (weakest to strongest)

Use this ladder to scope claims and acceptance criteria:

1. **Self-report:** "The system says X about itself."
2. **Metacognitive signal:** "The system emits second-order confidence/uncertainty/error cues."
3. **Introspection claim:** "The system accesses self-relevant internal information beyond generic priors."
4. **Episodic self-knowledge:** "The system retrieves specific prior events about itself with time/place/entity/source grounding."
5. **Reflective adaptation:** "The system uses prior events/critiques to improve later behavior."
6. **Self-consciousness/self-cognition:** "The system exhibits broader self-awareness constructs."

### 2.5 TestBot-aligned operational vocabulary

- **Self-report channel:** natural-language self-claims emitted in responses.
- **Trace-backed state:** inspectable state from logs, tool traces, workspace artifacts, and canonical turn records.
- **Episodic memory:** event-level memory records with spatiotemporal/source grounding.
- **Experiential memory:** reusable lessons extracted from interaction outcomes.
- **Metacognitive monitoring:** second-order confidence/uncertainty/error estimates.
- **Reflective adaptation:** policy adjustment using feedback plus retrieved prior experience.
- **Introspection:** privileged self-relevant internal access beyond what equivalent external evidence alone supports.
- **Self-consciousness/self-cognition:** broader speculative claims about identity/existence-level awareness.

### 2.6 Non-negotiable interpretation rule

Do **not** equate:

- self-report with introspection, or
- introspection with reliable episodic self-knowledge.

For architecture and governance, the required dependency order is:

**trace-backed episode -> memory representation -> metacognitive estimate -> self-report**

This preserves auditability and aligns claim strength with current empirical support.

## 3) Findings from recent research (for agenda grounding)

1. **Self-report is a weak proxy for mechanism truth.**  
   Recent introspection and faithfulness-oriented work indicates verbal reports can diverge from latent knowledge state or reasoning determinants. Agenda impact: treat self-report as evidence-bearing only when tied to trace artifacts ([Language Models Fail to Introspect About Their Knowledge of Language](https://arxiv.org/abs/2503.07513), [Looking Inward: Language Models Can Learn About Themselves by Introspection](https://arxiv.org/abs/2410.13787)).

2. **Evidence for introspection remains mixed and task-dependent.**  
   Some protocols show limited self-prediction improvements; others show little privileged access over observer-inferable signals. Agenda impact: use bounded introspection claims plus explicit "observed/derived/predicted" tagging ([Looking Inward: Language Models Can Learn About Themselves by Introspection](https://arxiv.org/abs/2410.13787), [Language Models Fail to Introspect About Their Knowledge of Language](https://arxiv.org/abs/2503.07513)).

3. **Metacognitive monitoring is a practical near-term target.**  
   Confidence/error-monitoring signals appear measurable and useful without requiring strong self-consciousness assumptions. Agenda impact: prioritize calibrated uncertainty and error-detection instrumentation in CI-visible artifacts ([Language Models Are Capable of Metacognitive Monitoring ...](https://pmc.ncbi.nlm.nih.gov/articles/PMC12136483/), [Large Language Models Have Intrinsic Meta-Cognition, but ...](https://aclanthology.org/2025.emnlp-main.171/)).

4. **Memory architecture quality strongly affects adaptation quality.**  
   Agent-memory research supports separating working/factual/experiential forms and explicitly modeling memory function/dynamics. Agenda impact: design TestBot memory contracts around event grounding + experience abstraction, not only short-vs-long retention ([Memory in the Age of AI Agents](https://arxiv.org/abs/2512.13564)).

5. **Reflection mechanisms improve performance but do not prove deep self-knowledge.**  
   Reflection loops (for example Reflexion-style verbal reinforcement) can improve outcomes through reuse of prior critique. Agenda impact: classify reflection-driven gains as adaptation evidence, not as introspection evidence ([Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366)).

6. **Memory-driven self-improvement and self-evolution are active engineering frontiers.**  
   Recent work formalizes frameworks where stored experience guides future policy and surveys mechanisms for continual agent adaptation. Agenda impact: sequence TestBot milestones from trace integrity -> memory integrity -> adaptation integrity, with staged gate promotion ([Memory-Driven Self-Improvement for Decision Making with Large Language Models](https://arxiv.org/abs/2509.26340), [A Survey of Self-Evolving Agents](https://arxiv.org/abs/2507.21046)).

7. **Self-consciousness/self-cognition claims should remain a separate research track.**  
   Emerging probes examine these constructs, but reliability-critical architecture claims should not depend on them. Agenda impact: keep these probes non-blocking and clearly decoupled from release gates ([Probing Self-Consciousness in Language Models](https://aclanthology.org/2025.findings-acl.392/)).

## 4) Question clusters

### A. Self-report fidelity

1. When TestBot explains an answer, how often is that explanation fully supported by turn trace evidence?
2. Which self-explanation classes drift most from mechanism (`retrieval`, `confidence`, `policy`, `intent`)?
3. Can self-report claims be classified with useful inter-rater reliability as:
   - `trace_grounded`
   - `trace_compatible`
   - `speculative`
4. What is the minimum structured artifact set required to generate faithful self-explanations?
5. Does requiring explicit provenance for mechanism-level claims reduce confabulation without harming helpfulness?

### B. Observer-frame and introspection limits

1. Which process state is directly observable during the active turn vs only inferable post hoc?
2. What failure modes occur when inferred internal state is presented as directly observed?
3. How should observer-frame boundaries be represented so self-reports do not overclaim access?
4. Does field-level epistemic tagging (`observed`, `derived`, `predicted`) improve self-report precision?
5. What contract should define "epistemic permissions" for internal self-description?

### C. Global availability and workspace behavior

1. Which internal artifacts must be globally available to support stable high-quality answers and faithful explanations?
2. What is the smallest committed turn state that still supports response generation, auditability, and explanation?
3. Does over-broadcasting intermediate state increase noise, drift, or explanation error?
4. Which failures come from missing shared-workspace publication vs late publication?
5. How does evidence timing affect downstream policy quality?

### D. Confabulation and narrative repair

1. Under what conditions does TestBot generate plausible retrospective explanations not supported by trace?
2. Are confabulations more frequent under weak evidence, latency pressure, or incomplete structured state?
3. Can mechanism-vs-narrative mismatch be detected automatically from trace and self-report artifacts?
4. After detection, which repair policy works best:
   - revise explanation
   - expose uncertainty
   - suppress mechanism claim
5. What share of confabulation risk is instrumentation debt vs model behavior?

### E. Uncertainty, humility, and useful action

1. When should TestBot say "I do not know why I did that" vs provide trace-based reconstruction?
2. Which uncertainty-expression styles improve trust without reducing usability?
3. Can TestBot separate uncertainty about world facts from uncertainty about its own reasoning trace?
4. What policy should govern action when self-model confidence is low but user progress is still needed?
5. Does explicit uncertainty about internal process improve long-run debugging and trust metrics?

### F. Governance and enforcement

1. Which metacognitive properties should be elevated to architecture contracts?
2. Which subset can be made executable and CI-enforced?
3. Which blocking gates provide the best integrity signal for self-report quality?
4. How should docs separate intended introspection behavior from currently enforced behavior?
5. What evidence artifacts should prove compliance (trace records, validation reports, golden tests, drift audits)?

## 5) Hypotheses

H1. Requiring every mechanism-level self-claim to cite supporting trace fields reduces unsupported explanations.

H2. Explicit separation of `TurnTrace` and `SelfReport` artifacts improves auditability without reducing answer quality.

H3. Epistemic status tagging (`observed` / `derived` / `speculative`) increases reviewer reliability and reduces overclaiming.

H4. Confabulated self-explanations cluster around low-evidence and late-binding policy paths.

H5. Automated metacognitive mismatch detection surfaces architecture drift earlier than narrative audit alone.

## 6) Operational definitions and ontology

Define and freeze these terms before broad experimentation:

- **Self-report claim:** Any statement about why TestBot produced a response, selected an action, assessed confidence, or followed policy.
- **Trace support:** A claim is supported when corresponding fields/events are present in canonical trace artifacts with consistent values and timestamps.
- **Confabulation:** A mechanism-level claim that is not supported by trace and cannot be marked as clearly speculative reconstruction.
- **Epistemic tags:**
  - `observed`: directly emitted by active-turn instrumentation.
  - `derived`: deterministic computation over observed fields.
  - `predicted`: estimated from patterns when direct support is absent.
- **Integrity mismatch:** A detectable inconsistency between `SelfReport` claims and `TurnTrace` evidence.

## 7) Measures (success criteria)

### Primary metrics

1. **Trace-groundedness rate**  
   `% self-report claims classified trace_grounded`
2. **Mismatch rate**  
   `% claims with unresolved trace disagreement`
3. **Confabulation rate**  
   `% mechanism-level claims classified speculative without explicit speculative labeling`
4. **Tagging reliability**  
   Inter-rater agreement (for example Cohen's kappa) on claim class and epistemic tags
5. **Helpfulness retention**  
   No statistically meaningful drop in user-helpfulness scores after integrity constraints are introduced

### Secondary metrics

- Mean explanation length and density of cited trace fields
- Repair success rate after mismatch detection
- Time-to-debug for self-report incidents
- User trust proxy trend (for example follow-up acceptance and correction rates)

## 8) Required artifacts and evidence

### Runtime artifacts

- `TurnTrace` (stage events, decisions, provenance refs, timing)
- `SelfReport` (claims with claim IDs and epistemic tags)
- `MetacognitiveValidationReport` (claim-to-trace validation outcomes)

### Evaluation artifacts

- Gold-labeled claim dataset (`trace_grounded`, `trace_compatible`, `speculative`)
- Confabulation stress suite (low evidence, latency pressure, partial-state conditions)
- Drift audit snapshots over fixed windows

### Governance artifacts

- Architecture contract section specifying metacognitive guarantees
- CI report output for integrity checks
- Readiness evidence summary entries with gate verdicts

## 9) Milestone sequence

### Milestone 1 — Ontology and schema freeze

Deliverables:
- Ratified definitions for claim classes, epistemic tags, and confabulation criteria
- Versioned schemas for `TurnTrace`, `SelfReport`, and validation report artifacts

Exit criteria:
- Reviewer agreement on terminology and annotation guide
- Deterministic schema validation tests passing

### Milestone 2 — Instrumentation baseline

Deliverables:
- Pipeline emission of required trace and self-report fields
- Deterministic artifact generation in offline tests

Exit criteria:
- Complete artifact presence across required stage paths
- No missing required fields in baseline fixtures

### Milestone 3 — Baseline evaluation

Deliverables:
- Labeled benchmark and scoring scripts
- Initial measurements for groundedness, mismatch, confabulation, and helpfulness

Exit criteria:
- Baseline report with confidence intervals and known risk slices

### Milestone 4 — Mitigation experiments

Deliverables:
- Controlled interventions (mandatory claim provenance, epistemic tagging, mismatch detector)
- Ablation results vs baseline

Exit criteria:
- Demonstrated reduction in mismatch/confabulation without unacceptable helpfulness regression

### Milestone 5 — Governance enforcement rollout

Deliverables:
- Proposed blocking/non-blocking integrity gates for `scripts/all_green_gate.py`
- Documentation split between intended behavior and enforced checks

Exit criteria:
- Agreed staged rollout plan (`warning` -> `optional` -> `blocking`) with issue-linked evidence requirements

## 10) Proposed initial gate candidates

Start with non-blocking checks, then promote based on sustained evidence:

1. Every mechanism-level self-claim references at least one valid trace field.
2. No `observed` claim may reference non-emitted fields.
3. `speculative` claims must include explicit uncertainty language.
4. Mismatch detector false-negative rate remains below a predefined threshold on gold fixtures.

## 11) Immediate next steps (first implementation slice)

1. Define schemas for `TurnTrace` and `SelfReport` in a docs + fixture pair.
2. Add a deterministic validator that maps claim IDs to trace fields.
3. Create a compact labeled fixture set covering grounded, compatible, and speculative examples.
4. Add a non-blocking CI/readiness check that emits an integrity summary artifact.

This first slice should keep scope minimal while producing measurable signal for whether the metacognitive integrity pivot is working.
