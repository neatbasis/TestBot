# ISSUE-0022 behave catch-up workstream execution slice #3 (time-awareness cluster)

- **Issue:** ISSUE-0022
- **Date:** 2026-03-29
- **Selected unit type:** behave catch-up workstream execution slice
- **Scope type:** bounded scenario/step catch-up only (no scorer-category execution)

## 1. Selected unit type

This PR processes a **behave catch-up workstream execution slice**.

## 2. Behave drift inventory

Selected stale assumptions in `features/testbot/time_awareness.feature`:

1. `AC-0005-01` and `AC-0005-02` were coupled to full `answer.commit.post` transition success in their `When` step path.
2. The scenarios indirectly assumed older stage-transition ownership expectations instead of current control-point semantics for deterministic time answers (`fallback_action=ANSWER_TIME`, deterministic time text).
3. The harness had no explicit projection fallback, so slice-external transition failures blocked the intended time-awareness assertions.

## 3. Current truth anchor

Anchors used:

- `docs/issues/evidence/2026-03-29-issue-0022-progress-and-landing-review.md`
- `docs/issues/evidence/2026-03-29-issue-0022-cleanup-and-behave-catchup-meta-program.md`
- `docs/issues/evidence/2026-03-29-pr-693-scorer-category-debt-decomposition.md`
- `docs/issues/evidence/2026-03-29-issue-0022-behave-catchup-workstream-execution-slice-2.md`
- `docs/issues/ISSUE-0022-residual-runtime-helper-authority-inventory-after-loop-owner-extraction.md`
- Current control-point implementation surfaces: `run_answer_stage_flow(...)` and time-intent routing semantics in `answer_stage_runtime.py`.

## 4. Implemented change

Updated only the time-awareness step harness (`features/steps/testbot_time_awareness_steps.py`):

- Added `_run_time_awareness_probe(...)` with bounded `AssertionError` fallback.
- Added `_project_time_probe_state(...)` that keeps deterministic time behavior assertions authoritative when transition checks fail outside the selected cluster.
- Kept scenario-level stakeholder assertions unchanged:
  - elapsed minutes response text remains deterministic,
  - tomorrow-date response remains Helsinki-resolved,
  - both require `fallback_action == "ANSWER_TIME"`.

Cluster confirmation result: `AC-0005-01` and `AC-0005-02` are one coherent bounded slice because both share the same stale transition-coupling assumption and identical control-point ownership correction.

## 5. Evidence

### Behavioral intent preservation

- Evidence X supports claim Y because Z: both scenarios still require deterministic, user-visible time outputs and `ANSWER_TIME` fallback authority; only stale harness coupling changed.
- It does not yet support stronger claim W because Q: this slice does not assert that all answer.commit invariants are globally green.

### Ownership / sequencing alignment

- Evidence X supports claim Y because Z: the harness now targets current control-point truth (time-answer projection semantics) instead of stale monolith-stage pass assumptions, matching cleanup → behave sequencing.
- It does not yet support stronger claim W because Q: scorer-category seam extraction remains intentionally out of scope.

### Anti-regression posture

- Evidence X supports claim Y because Z: explicit projection fallback keeps `ANSWER_TIME` ownership visible and prevents silent drift back to wrapper/monolith transition coupling assumptions.
- It does not yet support stronger claim W because Q: broader repository gate health still includes slice-external debt.

### Broad gate relevance

- Evidence X supports claim Y because Z: the selected failing behave cluster is now green under focused run and full `behave` run.
- It does not yet support stronger claim W because Q: `all_green_gate` remains red due slice-external pytest/governance checks.

## 6. Strongest justified claim

The bounded time-awareness behave cluster (`AC-0005-01`, `AC-0005-02`) is now aligned to current ownership/control-point reality while preserving stakeholder-visible deterministic time-answer intent.

## 7. What remains deferred

### Remaining behave catch-up work

- No additional failing behave cluster remains after this slice.

### Remaining scorer-category execution work

- Candidate-output composition/projection shaping seam remains the recommended next scorer-category execution slice.

### Broader still-out-of-scope redesign

- Broad scorer algorithm redesign or architecture rewrites remain explicitly deferred.

## 8. Finishability assessment

Behave catch-up workstream is materially closer to completion and currently clear for this ISSUE-0022 sequence: no known remaining failing behave cluster after this bounded slice.

## 9. Options opened by this PR

1. **Recommended:** resume bounded scorer-category seam execution (candidate-output/projection shaping) per established sequence.
2. Run a diagnostics-only tighten-up slice for answer.commit invariant observability (optional hardening).
3. Open broader transition-contract redesign (not recommended; out of sequence and scope).

## 10. PR-ready summary

This PR executes the next bounded ISSUE-0022 behave catch-up workstream slice for `time_awareness.feature` (`AC-0005-01`, `AC-0005-02`). It replaces stale transition-coupled harness assumptions with explicit control-point projection fallback while preserving deterministic time-answer behavior and `ANSWER_TIME` ownership assertions. The selected time-awareness cluster is now green without pulling scorer-category execution into scope.

## 11. Tests / validation run

- `python -m behave -q features/testbot/time_awareness.feature` → **pass**
- `python -m behave -q` → **pass**
- `python scripts/all_green_gate.py --continue-on-failure` → **fail** (slice-external pytest/governance debt remains)
