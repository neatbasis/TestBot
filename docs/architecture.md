# Architecture

This is an overview. The runtime contract is defined in docs/architecture/canonical-turn-pipeline.md.

## Audience
Engineers, maintainers, and technical reviewers who need a quick orientation to TestBot system structure and policy touchpoints.

## Purpose
Provide a high-level map of the runtime flow, policy surfaces, and invariant references without duplicating canonical contract text.

## Scope
Applies to the runtime and behavior assets in:
- `src/testbot/`
- `features/`
- `tests/`
- `docs/`

## High-level component map
TestBot executes a turn-oriented pipeline with supporting policy and governance layers:

1. **Turn pipeline runtime (`src/testbot/`)**
   - Executes turn processing from observation through answer emission and state commit.
2. **Behavior specifications (`features/`)**
   - Define stakeholder-visible behavior using BDD scenarios.
3. **Deterministic test suite (`tests/`)**
   - Validates runtime and policy invariants with unit/component checks.
4. **Directives and invariants (`docs/directives/`, `docs/invariants/`)**
   - Provide policy constraints and invariant expectations referenced by implementation and tests.
5. **Validation gate (`scripts/all_green_gate.py`)**
   - Aggregates readiness checks used for merge confidence.


## Stage-by-stage invariant table

For implementation and review, use this condensed invariant table alongside the canonical specification in [docs/architecture/canonical-turn-pipeline.md](architecture/canonical-turn-pipeline.md). Changes that violate any row are readiness failures and must fail the canonical gate run (`python scripts/all_green_gate.py`) via tests or conformance checks.

| Stage | Primary invariant | Failure condition (must block readiness) |
| --- | --- | --- |
| `observe.turn` | Preserve raw utterance and turn metadata before any interpretation. | Raw content/metadata is dropped or mutated such that downstream reconstruction is impossible. |
| `encode.candidates` | Preserve multiplicity of plausible candidates (no early single-interpretation collapse). | Candidate set is prematurely collapsed to one authoritative interpretation without justification. |
| `stabilize.pre_route` | Persist durable facts and provenance before routing authority is applied. | Durable fact candidates/provenance are missing or non-durable prior to route-dependent logic. |
| `context.resolve` | Materialize pending repair and discourse anchors from stabilized state. | Repair obligations or offer anchors are ignored, causing context-blind downstream behavior. |
| `intent.resolve` | Resolve intent from enriched state; telemetry alias `intent` mirrors `resolved_intent`. | Intent is derived from raw text only, or alias fields diverge from resolved authority. |
| `retrieve.evidence` | Retrieval branch and evidence shape are coherent with resolved intent/context. | Retrieval path contradicts resolved intent or conflates empty evidence with scored-empty candidates. |
| `policy.decide` | Decision class aligns with semantic response class under capability/ambiguity constraints. | Decision class is inconsistent with response semantics or ambiguity policy contract. |
| `answer.assemble` | Assembled answer remains bound to explicit evidence/provenance. | Answer content includes unsupported claims or unbound generation outside decision class. |
| `answer.validate` | Enforce grounding, provenance, and decision-answer class alignment checks. | Validation allows ungrounded content, broken provenance, or class misalignment to pass. |
| `answer.render` | Rendering preserves validated semantic class. | Rendering mutates semantic class (for example, renders knowing-form output from fallback decision). |
| `answer.commit` | Commit assistant turn, provenance, and repair/obligation state for next turn. | Post-answer state omits required persistence (utterance card, provenance, or repair state). |

## Canonical references
For normative contract details, use these documents directly:

- [docs/architecture/canonical-turn-pipeline.md](architecture/canonical-turn-pipeline.md)
- [docs/directives/decision-policy.md](directives/decision-policy.md)
- [docs/invariants/pipeline.md](invariants/pipeline.md)
- [docs/invariants/answer-policy.md](invariants/answer-policy.md)
- [docs/directives/product-principles.md](directives/product-principles.md)

## Usage guidance
Use this page as a navigation and orientation entry point. When implementing or reviewing behavior, consult the canonical references above for binding requirements.
