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

## Canonical references
For normative contract details, use these documents directly:

- [docs/architecture/canonical-turn-pipeline.md](architecture/canonical-turn-pipeline.md)
- [docs/directives/decision-policy.md](directives/decision-policy.md)
- [docs/invariants/pipeline.md](invariants/pipeline.md)
- [docs/invariants/answer-policy.md](invariants/answer-policy.md)
- [docs/directives/product-principles.md](directives/product-principles.md)

## Usage guidance
Use this page as a navigation and orientation entry point. When implementing or reviewing behavior, consult the canonical references above for binding requirements.
