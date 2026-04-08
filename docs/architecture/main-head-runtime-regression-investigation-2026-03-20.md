# Main-head runtime/test regression investigation (2026-03-20)

## Scope
Investigation-only baseline on current main head (no production fixes applied).

## Execution baseline
- Worktree: `/tmp/TestBot-mainhead` (detached clean worktree from repository HEAD).
- Commit SHA: `b7f9cb1ba23aec0368e59f6962375d93b51eb424`.
- Python: `3.11.14` (`/root/.pyenv/versions/3.11.14/bin/python`).
- Platform: `Linux-6.12.47-x86_64-with-glibc2.39`.
- Runtime-affecting assumptions observed:
  - no active virtualenv (`VIRTUAL_ENV=None`),
  - no explicit `PYTHONPATH`,
  - no `TESTBOT_*` env overrides,
  - pytest plugins loaded: `langsmith`, `anyio`.

## Required commands and outcomes
1. `python scripts/architecture_boundary_report.py --pretty --output artifacts/architecture-boundary-report.main-head.json`
   - succeeded; report emitted with 152 edges / 61 violations.
2. `python -m pytest | tee artifacts/pytest-main-head.txt`
   - completed with failures: **46 failed, 751 passed**.
3. `grep "^FAILED " artifacts/pytest-main-head.txt > artifacts/failed-main-head.txt`
   - captured 46 failure identifiers.

## Failure clusters
See detailed cluster file: `artifacts/main-head-failure-clusters.md`.

High-level clusters:
1. Compatibility export regression (`CanonicalTurnOrchestrator` missing from `sat_chatbot_memory_v2`).
2. Dominant retrieval contamination chain in `run_canonical_answer_stage_flow` wrapper causing fallback/action/GK/provenance/time-query drift.
3. `answer.commit` confirmed-fact merge regression.
4. Commit continuity anchor schema drift.
5. DTO compatibility roundtrip drift (`None` vs `{}`).
6. Live degraded-mode contract drift (likely downstream of #2, pending isolation).

## First authoritative breakpoints
See detailed boundary mapping: `artifacts/main-head-first-failure-boundaries.md`.

Most important first break:
- **`retrieve.evidence` in wrapper flow**: seeded store ignores exclusion filters, introducing self-retrieved same-turn artifacts that poison downstream policy/answer stages.

Other first breaks:
- Compatibility API boundary in `sat_chatbot_memory_v2` export surface.
- `answer.commit` merge function semantics.
- `context.resolve` continuity anchor emission semantics.
- DTO adapter boundary in canonical DTO conversion.

## Root cause vs downstream symptoms
See chain analysis: `artifacts/main-head-regression-chain.md`.

Primary root cause candidate (highest leverage):
- Retrieval contamination in compatibility wrapper (`run_canonical_answer_stage_flow` seeded store behavior).

Downstream symptoms linked to this root cause:
- Wrong `fallback_action` / `answer_mode` / GK contract outcomes.
- `answer.commit.post` invariant failures.
- Wrong memory provenance/cited `doc_id`s.
- Time-query path degrading away from expected deterministic time answer.
- Capability/degraded-mode behavior mismatches.

## Regression class determination
See classification file: `artifacts/main-head-regression-classification.md`.

Summary:
- Confirmed product regressions: seeded-store contamination chain; commit confirmed-fact merge.
- Confirmed compatibility regressions: missing compatibility export; DTO roundtrip normalization.
- Unclear/test-drift boundary: continuity anchor additions and residual live-smoke contract mismatches pending post-fix isolation.

## Merge-safety decision for architecture PRs
**Main head is currently NOT merge-safe** for boundary-hardening architecture PRs.

Reason:
- 46 failing tests include contract/invariant/compatibility failures in canonical stage surfaces, including post-commit invariants and compatibility APIs.
- Proceeding with boundary hardening on top of this baseline would compound diagnosis difficulty and risk masking primary regressions.

## Required repair order before boundary-hardening merges
See ordered plan: `artifacts/main-head-repair-order.md`.

Abbreviated order:
1. Fix retrieval contamination in wrapper path.
2. Restore compatibility exports.
3. Fix commit confirmed-fact merge semantics.
4. Resolve continuity anchor contract policy (revert vs codify).
5. Align DTO legacy nullability roundtrip behavior.
6. Re-run full baseline and only then decide merge readiness for architecture PRs.
