# Reflective Milestone Roadmap: 10 Capability-Increment Sprints

## Scope and governance

This roadmap defines one sprint per capability increment, in this order:

1. intent routing
2. fallback matrix
3. provenance model
4. history packer
5. BDD transcript coverage
6. alignment extension
7. observability
8. stakeholder matrix
9. hardening
10. release gate

Each sprint must ship in one or more PRs that:

- reference the sprint ID in the PR title or body (`Sprint: RM10-S0X`), and
- pass the deterministic merge checks before merge:
  1. `behave`
  2. `pytest -m "not live_smoke"`
  3. `pytest tests/test_eval_runtime_parity.py`
  4. `python scripts/validate_issue_links.py --all-issue-files --base-ref origin/main`

---

## RM10-S01 — Intent Routing

### Deliverables (code/docs/tests)
- **Code:** deterministic intent classifier/routing updates for explicit intent buckets.
- **Docs:** routing decision table (utterance pattern -> route) and failure handling notes.
- **Tests:** unit tests for route selection and BDD scenarios for user-visible intent outcomes.

### Measurable exit criteria
- >= 95% pass rate on curated intent fixture set.
- 0 ambiguous-route regressions on existing intent tests.
- Route reason is logged for every classified utterance in deterministic test mode.

### Non-goals
- No semantic rerank redesign.
- No model-provider migration.
- No live environment tuning.

### Rollback criteria
- Roll back if fallback rate increases by >10% on fixed eval fixtures.
- Roll back if any existing intent BDD scenario fails after merge.

---

## RM10-S02 — Fallback Matrix

### Deliverables (code/docs/tests)
- **Code:** explicit fallback matrix mapping failure classes to exact fallback behavior.
- **Docs:** matrix specification and examples for confidence, citation, and empty-answer paths.
- **Tests:** deterministic checks for each matrix branch, including exact-string fallback assertions.

### Measurable exit criteria
- 100% branch coverage of fallback matrix conditions.
- Exact fallback string compliance in all low-confidence and invalid-contract paths.
- No uncategorized fallback events in deterministic logs.

### Non-goals
- No UX copy experimentation beyond canonical fallback text.
- No probabilistic fallback selection.

### Rollback criteria
- Roll back if any path emits non-canonical fallback text where canonical text is required.
- Roll back if matrix branch tests become non-deterministic/flaky.

---

## RM10-S03 — Provenance Model

### Deliverables (code/docs/tests)
- **Code:** structured provenance payload (`doc_id`, `ts`, source segment metadata) attached to answer pipeline.
- **Docs:** provenance schema and citation requirements.
- **Tests:** contract tests enforcing provenance fields for factual responses.

### Measurable exit criteria
- 100% of factual answers in deterministic fixtures include required provenance fields.
- Provenance schema validator passes on all fixture outputs.
- Citation-contract regression tests remain green.

### Non-goals
- No external knowledge graph integration.
- No long-term archival store redesign.

### Rollback criteria
- Roll back if required provenance keys are missing in deterministic transcript outputs.
- Roll back if citation contract is weakened or bypassed.

---

## RM10-S04 — History Packer

### Deliverables (code/docs/tests)
- **Code:** deterministic history packing policy for context-window budgeting.
- **Docs:** packing heuristics and truncation policy with examples.
- **Tests:** fixture-driven tests for stable packing order, token budgeting, and truncation behavior.

### Measurable exit criteria
- Stable packed-history output for identical input transcripts across repeated runs.
- >= 90% retention of high-priority turns under fixed token budget benchmark.
- No token-budget overflow in deterministic packing tests.

### Non-goals
- No summarization model experimentation.
- No adaptive policy based on live telemetry.

### Rollback criteria
- Roll back if packing becomes order-unstable for identical inputs.
- Roll back if high-priority recall drops below agreed benchmark threshold.

---

## RM10-S05 — BDD Transcript Coverage

### Deliverables (code/docs/tests)
- **Code:** glue/step updates needed to exercise transcript-centric workflows.
- **Docs:** coverage map from transcript behaviors to feature scenarios.
- **Tests:** new `.feature` scenarios and step assertions for transcript replay and expected outcomes.

### Measurable exit criteria
- Every critical transcript path has at least one passing BDD scenario.
- BDD suite runs with 0 undefined steps.
- Coverage map shows no unowned critical transcript behavior.

### Non-goals
- No replacement of existing unit/component suites.
- No load/performance benchmarking.

### Rollback criteria
- Roll back if critical transcript paths are untested after change.
- Roll back if BDD execution introduces persistent flaky scenarios.

---

## RM10-S06 — Alignment Extension

### Deliverables (code/docs/tests)
- **Code:** alignment-policy extension hooks wired into stage transitions/response validation.
- **Docs:** updated alignment objective and decision boundaries.
- **Tests:** deterministic tests for alignment transitions, policy edge cases, and invariant preservation.

### Measurable exit criteria
- Alignment transition tests pass for all defined stage boundaries.
- No invariant violations in deterministic policy checks.
- Policy decisions are explainable via deterministic reason codes.

### Non-goals
- No broad rewrite of base prompting strategy.
- No changes to unrelated governance directives.

### Rollback criteria
- Roll back if alignment transitions regress on previously passing fixtures.
- Roll back if invariants fail or reason codes are missing.

---

## RM10-S07 — Observability

### Deliverables (code/docs/tests)
- **Code:** structured events for routing, fallback, provenance, and alignment decisions.
- **Docs:** event schema, sampling policy (if any), and operator runbook updates.
- **Tests:** log-schema validation and deterministic event-presence tests.

### Measurable exit criteria
- Required event types emitted in all deterministic happy/fallback paths.
- Log schema validation passes on current and backward-compat fixture sets.
- Event payload includes correlation/session IDs for end-to-end traceability.

### Non-goals
- No external dashboard procurement/integration as part of this sprint.
- No always-on live alerting rollout.

### Rollback criteria
- Roll back if event schema breaks compatibility for required consumers.
- Roll back if required decision events are missing in deterministic runs.

---

## RM10-S08 — Stakeholder Matrix

### Deliverables (code/docs/tests)
- **Code:** minimal enforcement hooks for stakeholder obligation checks where implemented in runtime/test tooling.
- **Docs:** stakeholder matrix linking obligations -> invariants -> deterministic evidence.
- **Tests:** checks proving every mandatory obligation has at least one executable deterministic verifier.

### Measurable exit criteria
- 100% of mandatory stakeholder obligations mapped to deterministic checks.
- No orphan obligation rows (missing owner/evidence/check command).
- Governance validation passes with updated matrix artifacts.

### Non-goals
- No organizational RACI redesign outside repository scope.
- No policy additions lacking executable verification.

### Rollback criteria
- Roll back if any mandatory obligation is left without deterministic evidence.
- Roll back if matrix/documentation drifts from executable checks.

---

## RM10-S09 — Hardening

### Deliverables (code/docs/tests)
- **Code:** defensive handling for known edge cases, deterministic failure isolation, and stability fixes.
- **Docs:** hardening checklist and known-risk register updates.
- **Tests:** regression tests for previously observed failures and boundary-condition cases.

### Measurable exit criteria
- Previously reproduced critical bugs have deterministic regression tests and pass.
- No increase in deterministic test flake rate.
- Error paths return contract-compliant behavior.

### Non-goals
- No new product-scope features.
- No speculative optimization without a measured defect/risk target.

### Rollback criteria
- Roll back if hardening changes introduce new critical regressions.
- Roll back if contract-compliant failure behavior is broken.

---

## RM10-S10 — Release Gate

### Deliverables (code/docs/tests)
- **Code:** release-gate script/config wiring deterministic checks into a single merge/release readiness entrypoint.
- **Docs:** release checklist and sign-off protocol tied to deterministic evidence.
- **Tests:** CI/local validation that gate fails closed on missing checks and passes only when all required checks are green.

### Measurable exit criteria
- Single release-gate command executes required deterministic checks end-to-end.
- Gate fails on any missing/failed required check.
- Gate output includes machine-readable status summary per check.

### Non-goals
- No deployment orchestration overhaul.
- No production rollout automation beyond deterministic readiness gating.

### Rollback criteria
- Roll back if gate can pass while required checks are skipped.
- Roll back if gate results are non-reproducible between local and CI deterministic environments.
