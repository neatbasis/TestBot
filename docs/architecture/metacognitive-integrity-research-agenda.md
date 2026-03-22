# Metacognitive Integrity Research Agenda

**Status:** Draft for architecture pivot planning  
**Scope:** TestBot turn pipeline, trace artifacts, self-report behavior, governance gates  
**Related issue anchor:** ISSUE-0014

## 1) Research objective

TestBot should be able to provide useful metacognitive reports while staying explicitly constrained by what the architecture makes knowable. This agenda treats metacognition as a verifiable systems property instead of an unconstrained narrative style.

### North-star question

**How can TestBot produce useful metacognitive reports while remaining explicitly constrained by what its architecture actually makes knowable?**

## 2) Question clusters

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

## 3) Hypotheses

H1. Requiring every mechanism-level self-claim to cite supporting trace fields reduces unsupported explanations.

H2. Explicit separation of `TurnTrace` and `SelfReport` artifacts improves auditability without reducing answer quality.

H3. Epistemic status tagging (`observed` / `derived` / `speculative`) increases reviewer reliability and reduces overclaiming.

H4. Confabulated self-explanations cluster around low-evidence and late-binding policy paths.

H5. Automated metacognitive mismatch detection surfaces architecture drift earlier than narrative audit alone.

## 4) Operational definitions and ontology

Define and freeze these terms before broad experimentation:

- **Self-report claim:** Any statement about why TestBot produced a response, selected an action, assessed confidence, or followed policy.
- **Trace support:** A claim is supported when corresponding fields/events are present in canonical trace artifacts with consistent values and timestamps.
- **Confabulation:** A mechanism-level claim that is not supported by trace and cannot be marked as clearly speculative reconstruction.
- **Epistemic tags:**
  - `observed`: directly emitted by active-turn instrumentation.
  - `derived`: deterministic computation over observed fields.
  - `predicted`: estimated from patterns when direct support is absent.
- **Integrity mismatch:** A detectable inconsistency between `SelfReport` claims and `TurnTrace` evidence.

## 5) Measures (success criteria)

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

## 6) Required artifacts and evidence

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

## 7) Milestone sequence

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

## 8) Proposed initial gate candidates

Start with non-blocking checks, then promote based on sustained evidence:

1. Every mechanism-level self-claim references at least one valid trace field.
2. No `observed` claim may reference non-emitted fields.
3. `speculative` claims must include explicit uncertainty language.
4. Mismatch detector false-negative rate remains below a predefined threshold on gold fixtures.

## 9) Immediate next steps (first implementation slice)

1. Define schemas for `TurnTrace` and `SelfReport` in a docs + fixture pair.
2. Add a deterministic validator that maps claim IDs to trace fields.
3. Create a compact labeled fixture set covering grounded, compatible, and speculative examples.
4. Add a non-blocking CI/readiness check that emits an integrity summary artifact.

This first slice should keep scope minimal while producing measurable signal for whether the metacognitive integrity pivot is working.
