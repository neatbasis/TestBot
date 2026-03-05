# Grounded Knowing Status + Next 5 Priorities (Current Snapshot)

## Why this exists

This document answers four operational questions in one place:

1. Where are we right now?
2. Do we have good tests to prove it?
3. What are the next five highest-value features for knowing/unknowing behavior?
4. What should we do when a PR (for example #78) misses one required merge check?

---

## Current status (as of this snapshot)

### What is working

- Core behavior contracts are in place for:
  - citation-required factual responses,
  - progressive fallback behavior, and
  - deterministic time-aware routing.
- Deterministic merge gate orchestration exists via `scripts/release_gate.py`.
- In-repo issue governance and deterministic issue-link validation are implemented.

### What is not yet green

- Full `python scripts/release_gate.py` is currently blocked at the BDD layer (`python -m behave`) due to failures in `features/intent_grounding.feature` scenarios.
- Because the gate is fail-closed, downstream required checks do not run after the first failure.

### Risk interpretation

- **Knowing-mode risk:** intent-grounding failures can produce incorrect or unstable basis/provenance behavior.
- **Unknowing-mode risk:** policy assertions failing in intent-grounding paths indicate fallback decision quality is not yet reliable enough for merge.

---

## Test confidence map (what tells us where we are)

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
   - Governance/traceability merge-safety signal.

Interpretation rule:

- If #1 fails, treat knowing/unknowing behavior as **not merge-ready**, even if some unit tests pass.

---

## Next 5 highest-value features (priority order)

### P1 — Intent-grounding reliability hardening (merge-unblocker)

- Goal: make all intent-grounding scenarios deterministic and green.
- Value: immediately restores trust in knowing/unknowing selection logic.
- Exit: all `features/intent_grounding.feature` scenarios pass in `python -m behave`.

### P2 — Confidence calibration for knowing vs unknowing decisions

- Goal: tighten threshold policy to reduce false-knowing and ambiguous unknown responses.
- Value: improves user trust by preventing overconfident unsupported answers.
- Exit: fixture-driven threshold tests plus parity checks stay green.

### P3 — Searchable external fact connectors (with trust tiers)

- Goal: add source connectors so conversation can ground to searchable facts beyond chat memory.
- Value: unlocks broader “knowing mode” utility while preserving provenance.
- Exit: deterministic connector fixture tests + source-backed BDD scenarios pass.

### P4 — Provenance explainability payload standardization

- Goal: consistently expose `doc_id`, `ts`, `source_id`, and basis/provenance fields in all knowing outputs.
- Value: makes grounded answers auditable and debuggable.
- Exit: answer-contract and runtime logging tests confirm complete provenance payloads.

### P5 — Feedback/replay loop for policy drift detection

- Goal: capture correction/clarification signals and replay them offline to detect ranking/policy regressions.
- Value: protects quality over time as features expand.
- Exit: replay workflow produces comparable before/after metrics in deterministic runs.

---

## PR miss policy (example: PR #78 missed one required merge check)

When one required check is missed, do **not merge**. Use this recovery sequence:

1. Re-run full deterministic gate:
   - `python -m pip install -e .[dev]`
   - `python scripts/release_gate.py`
2. If gate fails at `behave`, fix failing scenarios first (especially intent-grounding).
3. Re-run full gate until all required checks are green.
4. Ensure PR body includes `Issue: ISSUE-XXXX` and verification evidence.
5. Ensure non-trivial commit messages include `ISSUE-XXXX` to satisfy `validate_issue_links.py`.

Definition of done for the missed-check PR:

- all required release-gate checks pass,
- issue-link validation passes,
- issue status/docs updated with closure notes and residual risk.
