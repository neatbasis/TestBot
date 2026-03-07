# ISSUE-0012: Canonical turn pipeline delivery plan requires staged implementation and mandatory code review checkpoints

- **ID:** ISSUE-0012
- **Title:** Canonical turn pipeline delivery plan requires staged implementation and mandatory code review checkpoints
- **Status:** open
- **Severity:** amber
- **Owner:** platform-qa
- **Created:** 2026-03-07
- **Target Sprint:** Sprint 3-5
- **Principle Alignment:** contract-first, invariant-driven, traceable, deterministic, ci-enforced

## Problem Statement

The canonical turn pipeline contract in `docs/architecture/canonical-turn-pipeline.md` defines required stages and invariants, but execution is not yet tracked as a single sprinted delivery plan with explicit feature slices and mandatory code review checkpoints. Without this governance layer, related capability work can land out of order and leave cross-stage invariants only partially enforced.

## Evidence

- `docs/architecture/canonical-turn-pipeline.md` specifies an 11-stage sequence (`observe.turn` through `answer.commit`) and explicit adoption definition-of-done criteria.
- `docs/qa/feature-status.yaml` tracks current high-level capabilities, but does not yet include dedicated planned capability entries for canonical turn pipeline stage adoption.
- Existing open capability issues (`ISSUE-0008`, `ISSUE-0009`, `ISSUE-0010`, `ISSUE-0011`) capture partial deltas but are not currently sequenced under a single canonical pipeline sprint plan.

## Impact

- Stage-ordering and invariant dependencies can drift when fixes are applied in isolation.
- Reviewers lack one canonical issue that states which sprint delivers each pipeline feature family.
- Readiness reporting remains harder to interpret because partial capability issues are not explicitly attached to a pipeline adoption program.

## Acceptance Criteria

1. `docs/qa/feature-status.yaml` includes planned capability entries for canonical turn pipeline feature slices, each linked to ISSUE-0012 keywords and roadmap priorities.
2. Relevant open issues in `docs/issues/` that impact canonical turn semantics explicitly reference ISSUE-0012 in `Work Plan` or `Closure Notes` as a dependency/coordinator.
3. ISSUE-0012 `Work Plan` defines sprint-by-sprint delivery slices and names mandatory code review checkpoints for each sprint.
4. ISSUE-0012 verification section names deterministic commands used to validate contract alignment and report freshness.

## Work Plan

### Sprint 3 — Observe/encode/stabilize baseline

- Land pre-route extraction and stabilization updates needed to preserve durable facts and speech-act candidates before route authority.
- Update/extend deterministic tests and BDD scenarios for observe-before-infer and stabilize-before-route behavior.
- **Code review checkpoint:** architecture+runtime review confirms no early lossy `U -> I` projection path is reintroduced.

### Sprint 4 — Context/intent/retrieve/policy alignment

- Deliver context-resolve + intent-resolve hardening and retrieval-policy coherence updates.
- Ensure decision classes match resolved intent and evidence posture.
- **Code review checkpoint:** policy/retrieval review signs off on decision-answer alignment and explicit handling for empty-evidence vs scored-empty states.

### Sprint 5 — Assemble/validate/render/commit completion

- Complete answer assembly/validation/render/commit sequencing, including repair-offer materialization into committed state.
- Finalize runtime logging and analytics visibility needed for post-turn audits.
- **Code review checkpoint:** release-readiness review confirms pipeline invariants, traceability artifacts, and gate evidence align before capability status moves from planned/partial to implemented.

## Verification

- Command: `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json`
  - Expected: report includes canonical turn pipeline capability entries and links to ISSUE-0012.
- Command: `python scripts/validate_issue_links.py --all-issue-files --base-ref HEAD`
  - Expected: exits `0` and issue references remain valid.
- Command: `python scripts/validate_issues.py --all-issue-files --base-ref HEAD`
  - Expected: exits `0` with canonical issue schema intact after updates.

## Closure Notes

- 2026-03-07: Opened to establish a cross-issue sprint plan and mandatory review checkpoints for canonical turn pipeline adoption.
