# Grounded Knowing Status + Next 5 Priorities (Current Snapshot)

## Why this exists

This document answers four operational questions in one place:

1. Where are we right now?
2. Do we have good tests to prove it?
3. What are the next five highest-value features for knowing/unknowing behavior?
4. What should we do when a PR (for example #78) misses one required merge check?

---

## Current status

Evidence timestamp reference (artifact freshness):

- `artifacts/feature-status-summary.json` → `generated_at_utc`: `2026-03-07T01:26:56Z`
- `docs/qa/feature-status-report.md` reports the same generation moment (`Generated at (UTC): 2026-03-07T01:26:56Z`), so capability counts below are tied to that artifact run.
- `artifacts/all-green-gate-summary.json` is the gate execution artifact used for gate status and failed-check assertions below.

Canonical machine-readable/source-of-truth status now lives in:

- Contract: `docs/qa/feature-status.yaml`
- Generated report (canonical status view): `docs/qa/feature-status-report.md`
- Generated JSON summary: `artifacts/feature-status-summary.json`

From the latest generated status artifacts:

- Capability summary line (`docs/qa/feature-status-report.md`): **Implemented: 2 | Partial: 4 | Missing: 0**.
- Gate status (`artifacts/all-green-gate-summary.json` → top-level `status`): **failed**.
- Failed checks in the same gate artifact:
  - `product_behave`
  - `safety_behave_answer_contract_and_memory`

### What is working

- Most deterministic pytest layers in the gate artifact are passing (including non-live smoke and eval/runtime parity checks).
- Time-aware memory retrieval/reranking and canonical merge-gate/governance capabilities remain tracked as **implemented** in the feature status report.
- Governance validators (`qa_validate_issue_links`, `qa_validate_issues`) are passing in the current gate artifact run.

### Current blockers (active)

- Canonical gate evidence is currently **failed** due to `product_behave` and `safety_behave_answer_contract_and_memory`; treat behavior as not merge-ready until these checks are green in a newer artifact run.
- Feature status output includes a staleness warning that gate evidence may be older than some source inputs; refresh gate artifacts before making final merge-readiness calls.

### Historical blockers (resolved in prior runs)

The following are historical notes from prior runs. They are separate from current blockers above and do not imply that the current failing checks are resolved:

- Missing `behave` in environment (resolved by installing dev dependencies and re-running gate).
- `product_eval_recall_topk4` import failure (`ModuleNotFoundError: No module named 'testbot'`) resolved in validated environment.
- `qa_validate_issue_links` base-ref failure for `origin/main` resolved via canonical fallback behavior (`HEAD~1` per policy order `origin/main` → `HEAD~1` → `HEAD`).

### Risk interpretation

- **Knowing-mode risk:** primarily capability-completeness risk (several features still intentionally tracked as partial), not immediate gate-execution risk.
- **Unknowing-mode risk:** behavior remains only partially complete per feature contract, and current executable gate evidence is not yet green (failed checks are still present).

---

## Test confidence map (what tells us where we are)

For current capability-level status, use the generated feature status report as the canonical view:

- `python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json`

Use this exact order for deterministic confidence:

1. `python -m behave`
   - Primary behavior contract signal for knowing/unknowing outputs.
2. `python -m pytest tests/test_vector_store.py tests/test_source_fusion.py tests/test_log_schema_validation.py`
   - Fast source/provenance and logging schema signal.
3. `python -m pytest -m "not live_smoke"`
   - Broad deterministic component signal.
4. `python -m pytest tests/test_eval_runtime_parity.py`
   - Eval/runtime alignment signal for ordering/top-1/fallback parity.
5. `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`
   - Governance/traceability merge-safety signal under canonical base-ref policy (`origin/main` default with fallback to `HEAD~1`, then `HEAD` when unavailable).

Interpretation rule:

- If #1 fails, treat knowing/unknowing behavior as **not merge-ready**, even if some unit tests pass.

---

## Next 5 highest-value capability families (priority order)

Priority IDs in this document follow the canonical convention in `docs/roadmap/next-4-sprints-grounded-knowing.md#priority-id-convention`.

### P1 — Source connector interface + ingestion pipeline

- Goal: harden connector abstractions and ingestion flow so source evidence is fetched, normalized, and persisted deterministically.
- Value: unlocks reliable grounding inputs for all downstream knowing decisions.
- Exit: `features/source_ingestion.feature` plus connector/ingestion pytest coverage stay green with deterministic fixture-backed outputs.

### P2 — Evidence normalization/ranking for mixed sources

- Goal: normalize and rank evidence consistently across memory and external source candidates.
- Value: improves grounded-answer quality by stabilizing mixed-source ordering and top-hit selection.
- Exit: reranking and parity checks remain deterministic for mixed-source fixtures.

### P3 — Knowing/unknowing decision policy with confidence calibration

- Goal: tighten intent/policy thresholds to reduce false-knowing behavior while preserving explicit safe fallback behavior.
- Value: improves trust by making know-vs-unknown decisions reproducible and conservative under uncertainty.
- Exit: intent-grounding and reflection-policy scenarios/tests pass with deterministic confidence-band expectations.

### P4 — Citation UX + provenance explainability output format

- Goal: consistently expose `doc_id`, `ts`, `source_id`, and basis/provenance fields in all knowing outputs.
- Value: makes grounded answers auditable and debuggable.
- Exit: answer-contract and runtime logging tests confirm complete provenance payloads.

### P5 — Feedback loop using follow-up signals and offline eval replay

- Goal: capture correction/clarification signals and replay them offline to detect ranking/policy regressions.
- Value: protects quality over time as features expand.
- Exit: replay workflow produces comparable before/after metrics in deterministic runs.

---

## PR miss policy (example: PR #78 missed one required merge check)

When one required check is missed, do **not merge**. Use this recovery sequence:

1. Re-run full deterministic gate:
   - `python -m pip install -e .[dev]`
   - `python scripts/all_green_gate.py`
2. If gate fails at `behave`, fix failing scenarios first (especially intent-grounding).
3. Re-run full gate until all required checks are green.
4. Ensure PR body includes `Issue: ISSUE-XXXX` and verification evidence.
5. Ensure non-trivial commit messages include `ISSUE-XXXX` to satisfy `validate_issue_links.py`.

Definition of done for the missed-check PR:

- all required all-green-gate checks pass,
- issue-link validation passes,
- issue status/docs updated with closure notes and residual risk.
