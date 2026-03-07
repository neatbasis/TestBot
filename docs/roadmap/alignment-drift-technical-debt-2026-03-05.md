# Alignment Drift and Technical Debt Assessment (2026-03-05)

## Scope

This assessment compares current implementation, tests, and governance behavior against roadmap and issue-tracking artifacts to identify:

1. **Alignment drift** (docs/process no longer reflecting current reality), and
2. **Technical debt** (known gaps that increase delivery or reliability risk).

## Executive summary

Implementation-risk burn-down and canonical pipeline defect-elimination sequencing should be tracked in [`ISSUE-0013`](../issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md), with ISSUE-0012 retained as historical planning context.

- Core runtime quality signals are currently strong: BDD and deterministic pytest suites are passing locally after installing dev dependencies.
- The largest alignment drift is in planning/governance documents that still describe now-resolved states or reference non-existent module/test paths.
- The highest technical debt item is release-gate brittleness in environments without `origin/main` fetch context, which can cause governance checks to fail even when behavior/tests pass.

## Evidence snapshot

- `python scripts/all_green_gate.py` (after `python -m pip install -e .[dev]`) executed BDD and deterministic pytest checks successfully, then failed in governance validation because `origin/main` was not available in local git metadata.
- Roadmap mapping points to `src/testbot/ingestion_pipeline.py` and `tests/test_ingestion_pipeline.py`, but repository implementation uses `src/testbot/source_ingest.py` and `tests/test_source_ingest.py`.
- Current-status roadmap notes claim merge gate is blocked by intent-grounding BDD failures, while current observed run shows those scenarios passing.
- `ISSUE-0005` states parity regression checks are missing, but parity tests exist and are wired into the release gate.

## Alignment drift findings

### D1 — Roadmap-to-code path drift (module/test names)

**Finding**
- Planned implementation map references files not present in the repository (`ingestion_pipeline.py`, `test_ingestion_pipeline.py`, `test_pipeline_state.py`).

**Impact**
- Contributors may spend time searching for deprecated module names.
- Traceability from roadmap priorities to executable evidence is weakened.

**Suggested remediation**
- Update roadmap mapping table to canonical current files:
  - `src/testbot/source_ingest.py`
  - `tests/test_source_ingest.py`
  - existing pipeline-state coverage references if applicable.

### D2 — Current status narrative drift

**Finding**
- Status doc reports intent-grounding BDD failures as current blocker; observed gate run shows intent-grounding scenarios passing.

**Impact**
- Stakeholders may prioritize the wrong blocker and underestimate current progress.

**Suggested remediation**
- Refresh status section with timestamped gate output and move previous blocker note into historical context.

### D3 — Issue ledger drift (open issue no longer matching system state)

**Finding**
- `ISSUE-0005` states missing eval/runtime parity checks, but `tests/test_eval_runtime_parity.py` exists and is part of release gate.

**Impact**
- Open issue inventory overstates unresolved risk and dilutes triage focus.

**Suggested remediation**
- Update `ISSUE-0005` evidence/closure notes and close or re-scope to any remaining parity edge cases only.

## Technical debt findings

### T1 — Governance gate depends on `origin/main` availability

**Finding**
- Release gate fails in environments lacking `origin/main...HEAD` comparison context.

**Impact**
- False-negative gate failures in ephemeral CI/dev environments.
- Added friction for contributors running canonical checks locally.

**Suggested remediation**
- Add fallback behavior in governance validators/release gate:
  - allow configurable base ref,
  - auto-fallback to `HEAD~N`/merge-base when `origin/main` is unavailable,
  - emit explicit actionable hint with override example.

### T2 — Red-tag issue still open for now-mitigated dependency behavior

**Finding**
- `ISSUE-0007` remains open though docs and gate workflow now explicitly require/install dev dependencies prior to behave usage.

**Impact**
- Red-tag board may not distinguish between historical and active critical risks.

**Suggested remediation**
- Re-verify acceptance criteria with current gate workflow; downgrade severity or close if criteria now satisfied.

### T3 — Architecture acceptance checklist not stateful

**Finding**
- Architecture acceptance criteria checkboxes are all unchecked and not tied to a dated verification snapshot.

**Impact**
- Readers cannot infer whether criteria are unmet or simply not maintained.

**Suggested remediation**
- Convert static checklist into dated status table (criterion, status, last verified command/evidence).

## Prioritized remediation plan

1. **P0 (immediate):** fix release-gate base-ref brittleness (T1).
2. **P1:** update roadmap path mappings and status narrative drift (D1, D2).
3. **P1:** reconcile issue tracker drift (`ISSUE-0005`, `ISSUE-0007`) (D3, T2).
4. **P2:** make architecture acceptance criteria evidence-backed and timestamped (T3).

## Suggested ownership

- **Platform QA / tooling:** T1, T2
- **Roadmap/documentation owner:** D1, D2
- **Runtime quality lead:** D3
- **Architecture owner:** T3

## Verification commands used in this assessment

```bash
python -m pip install -e .[dev]
python scripts/all_green_gate.py
rg -n "ingestion_pipeline|test_ingestion_pipeline|reasoning_path" docs src tests
rg --files src/testbot tests | rg 'pipeline_state|source_ingest|ingestion_pipeline'
```
