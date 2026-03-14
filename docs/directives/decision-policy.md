# Decision Policy

This document is the consolidated decision-path policy reference for directive-governed behavior.

Use this file to define and review decision expectations (for example fallback routing, confidence handling, and escalation paths) that were previously scattered across legacy mapping artifacts.

## Decision-path update requirements

When contributor changes affect decision behavior, update this file in the same change set with:

- the decision trigger/condition,
- the expected decision outcome,
- links to enforcement points (runtime logic, tests, and traceability rows), and
- any stakeholder-visible behavior impact.

## Relationship to other authoritative docs

- Terminology and naming policy live in `docs/terminology.md`.
- Cross-artifact traceability and test linkage live in `docs/directives/traceability-matrix.md`.
- Invariant registries remain canonical in `docs/invariants/answer-policy.md` and `docs/invariants/pipeline.md`.

Keep these references aligned whenever decision rules change.
