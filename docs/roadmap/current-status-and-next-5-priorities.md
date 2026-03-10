# Grounded Knowing Status + Next 5 Priorities (Current Snapshot)

## Why this exists

Implementation-risk burn-down for canonical pipeline milestones is tracked under [`ISSUE-0013`](../issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md); treat ISSUE-0012 references in roadmap material as historical delivery-planning context only.

This document answers four operational questions in one place:

1. Where are we right now?
2. Do we have good tests to prove it?
3. What are the next five highest-value features for knowing/unknowing behavior?
4. What should we do when a PR (for example #78) misses one required merge check?

---

## Current status

Evidence timestamp reference (artifact freshness):

- `artifacts/feature-status-summary.json` → `generated_at_utc`: `2026-03-10T20:06:56Z`
- `docs/qa/feature-status-report.md` reports the same generation moment (`Generated at (UTC): 2026-03-10T20:06:56Z`), so capability counts below are tied to that artifact run.
- `artifacts/all-green-gate-summary.json` is the gate execution artifact used for gate status and failed-check assertions below (`snapshot_utc`: `2026-03-10T20:32:23Z`).

Source-of-truth refresh discipline (use this order on each update):

- Contract: `docs/qa/feature-status.yaml`
- Generated report (canonical status view): `docs/qa/feature-status-report.md`
- Generated JSON summary: `artifacts/feature-status-summary.json`

From the latest generated status artifacts:

- Capability summary line (`docs/qa/feature-status-report.md`): **Implemented: 0 | Partial: 9 | Missing: 0**.
- Gate status (`artifacts/all-green-gate-summary.json` → top-level `status`): **failed**.
- Current failing and warning-mode checks/signals in the same gate artifact (snapshot `2026-03-10T20:32:23Z`):
  - Failing checks: `product_behave`, `qa_pytest_not_live_smoke`, `qa_validate_invariant_sync`.
  - Warning-mode check: `qa_validate_kpi_guardrails` returned `warning` (non-zero exit code tracked as a warning by the gate runner).
  - First failing command by stage:
    - `product`: `/root/.pyenv/versions/3.11.14/bin/python -m behave`
    - `qa`: `/root/.pyenv/versions/3.11.14/bin/python -m pytest -m 'not live_smoke'`

### What is working

- `product_eval_recall_topk4`, safety validators, governance validators, markdown-path validation, and turn analytics aggregation are passing in the gate artifact.
- Time-aware memory retrieval/reranking and canonical merge-gate/governance capabilities remain tracked as **implemented** in the feature status report.
- Governance validators (`qa_validate_issue_links`, `qa_validate_issues`) and markdown path validation (`qa_validate_markdown_paths`) are passing in the current gate artifact run.

### Current blockers (active)

- Canonical gate evidence is currently **failed** due to `product_behave`, `qa_pytest_not_live_smoke`, and `qa_validate_invariant_sync`; treat behavior as not merge-ready until these checks are green in a newer artifact run.
- KPI guardrail validation remains in explicit **warning mode** (`qa_validate_kpi_guardrails`), so guardrail threshold violations are active quality signals alongside failing checks.
- All canonical pipeline capability slices remain **partial** in the latest status report and should still be treated as delivery blockers for full readiness:
  - `foundation` slice: **Canonical turn pipeline foundation (observe/encode/stabilize)** is partial.
  - `decisioning` slice: **Canonical turn pipeline decisioning (context/intent/retrieve/policy)** is partial.
  - `commit and auditability` slice: **Canonical turn pipeline commit and auditability (assemble/validate/render/commit)** is partial.

### Historical blockers (resolved in prior runs; retained for context only)

The following are historical notes from prior runs. They are separate from current blockers above and do not imply that the current failing checks are resolved:

- Missing `behave` in environment (resolved by installing dev dependencies and re-running gate).
- `product_eval_recall_topk4` import failure (`ModuleNotFoundError: No module named 'testbot'`) resolved in validated environment.
- `qa_validate_issue_links` base-ref failure for `origin/main` resolved via canonical fallback behavior (`HEAD~1` per policy order `origin/main` → `HEAD~1` → `HEAD`).

### Risk interpretation

- **Knowing-mode risk:** high immediate execution risk (active behavior and deterministic-test failures) plus capability-completeness risk and KPI warning-mode guardrail risk.
- **Unknowing-mode risk:** behavior remains partially complete per feature contract and is currently not merge-ready due to active gate failures.

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

Pipeline adoption focus for this priority set:

- **Foundation** is advanced primarily by P1 and P2.
- **Decisioning** is advanced primarily by P2 and P3.
- **Commit and auditability** is advanced primarily by P4 and P5.
- Until all three slices are no longer reported as partial in `docs/qa/feature-status-report.md`, treat these priorities as merge-readiness blockers, not optional improvements.

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
