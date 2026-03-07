# Next 4 Sprints Roadmap: Grounded Knowing

## Scope and intent

This roadmap operationalizes the top-5 grounded-knowing priorities over four sprints. Each sprint includes explicit goals, measurable exits, and rollback criteria so delivery remains deterministic, testable, and reversible.

## Canonical stage bundle mapping (ISSUE-0013 implementation-risk alignment)

The roadmap priorities map to canonical turn pipeline stage bundles and implementation-risk burn-down sequencing in
`docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md` (with ISSUE-0012 retained as historical planning context) as follows.

| Sprint milestone | Canonical stage bundle | Primary roadmap priorities | ISSUE-0013 implementation-risk burn-down link |
| --- | --- | --- | --- |
| **Sprint 3** | **observe / encode / stabilize** | `P1`, `P2` foundations required before route authority and ranking policy hardening | Foundation checkpoint sequencing, defect intake, and evidence links are recorded in ISSUE-0013 Work Plan + Closure Notes. |
| **Sprint 4** | **context / intent / retrieve / decide** | `P2`, `P3` policy/ranking convergence and intent-grounded decisioning | Decisioning checkpoint sequencing and cross-issue dependency routing are tracked in ISSUE-0013. |
| **Sprint 5** | **assemble / validate / render / commit** | `P4`, `P5` answer contract completion, replay hardening, and post-turn traceability | Commit/audit checkpoint sequencing and release-readiness risk burn-down are tracked in ISSUE-0013. |

### Governance checkpoint rule for Sprint 3-5 milestones

For each canonical stage bundle milestone above, maintain a mandatory code-review checkpoint before merge that explicitly records:

- preserved canonical stage ordering,
- invariant conformance against `docs/invariants.md`, and
- deterministic evidence from BDD + pytest + canonical gate commands defined in `docs/testing.md`.

## Priority stack (ordered)

1. **P1: Source connector interface + ingestion pipeline**
2. **P2: Evidence normalization/ranking for mixed sources**
3. **P3: Knowing/unknowing decision policy with confidence calibration**
4. **P4: Citation UX + provenance explainability output format**
5. **P5: Feedback loop using follow-up signals and offline eval replay**

### Priority ID convention

Use `P1`-`P5` as stable **capability-family IDs** across roadmap and QA artifacts:

- `P1` = source connector interface + ingestion pipeline
- `P2` = evidence normalization/ranking for mixed sources
- `P3` = knowing/unknowing decision policy with confidence calibration
- `P4` = citation UX + provenance explainability output format
- `P5` = feedback loop using follow-up signals and offline eval replay

If a roadmap item is renamed for readability, keep the `P#` bound to the same capability family so status references in `docs/qa/feature-status.yaml` remain semantically stable over time.

---

## Sprint 1 — Foundation: connectors + ingestion contract (P1)

### Goals
- Define a stable source connector interface for heterogeneous memory/evidence sources.
- Implement deterministic ingestion pipeline stages (fetch → normalize envelope → persist candidate records).
- Add ingestion observability signals needed by downstream ranking and policy layers.

### Measurable exits
- At least one connector implementation can ingest a fixture-backed source end-to-end with deterministic outputs.
- Ingestion emits structured records containing required fields (`source_id`, `doc_id`, `ts`, `content`, `metadata`).
- Stage-specific deterministic evidence is attached for ingestion-stage behavior and failure modes: `python -m behave`, `python -m pytest -m "not live_smoke"`, and `python scripts/all_green_gate.py` all pass for this scope (per `docs/testing.md`).

### Mandatory code-review checkpoint (ISSUE-0013 sequencing consistency)
- Architecture + runtime review confirms connector/ingestion delivery does not create an early lossy path that would violate canonical stage ordering before Sprint 3 stage-bundle work.
- Review record includes links to deterministic evidence artifacts (BDD, pytest, canonical gate summary).

### Rollback criteria
- If connector abstraction causes regression in existing retrieval flow, feature-flag new ingestion path off and revert to current pipeline defaults.
- If ingestion schema instability breaks ranking tests, freeze schema to previous known-good envelope and defer non-essential fields.
- Any rollback must preserve canonical stage order and retain invariant enforcement checks; do not accept rollback paths that bypass required stage transitions even when feature flags are disabled.

---

## Sprint 2 — Mixed-source evidence ranking (P2)

### Goals
- Normalize evidence from connector outputs into a single ranking-ready representation.
- Extend rerank objective to support mixed sources while preserving deterministic ordering guarantees.
- Add traceable per-component score attribution (semantic, temporal, source/type priors).

### Measurable exits
- Ranking pipeline accepts mixed-source candidate sets without schema conversion errors.
- Deterministic tests show stable ordering/top-1 selection across fixed fixtures for mixed-source cases.
- Stage-specific deterministic evidence is attached for mixed-source normalization/ranking behavior: `python -m behave`, `python -m pytest -m "not live_smoke"`, `python -m pytest tests/test_eval_runtime_parity.py`, and `python scripts/all_green_gate.py` pass (per `docs/testing.md`).

### Mandatory code-review checkpoint (ISSUE-0013 sequencing consistency)
- Policy + retrieval reviewers verify ranking updates remain compatible with upcoming Sprint 4 `context/intent/retrieve/decide` stage sequencing.
- Review notes explicitly capture deterministic evidence and stage-order invariant checks.

### Rollback criteria
- If mixed-source ranking reduces baseline recall/precision beyond accepted threshold, disable mixed-source weighting and use existing single-source scoring path.
- If attribution output is inconsistent run-to-run, remove non-deterministic components before merge.
- Rollback must preserve canonical stage ordering and invariant enforcement, including deterministic checks that prove no out-of-order retrieval/decision path is introduced.

---

## Sprint 3 — Observe/encode/stabilize baseline delivery (P1, P2 foundations)

### Goals
- Land observe/encode/stabilize baseline updates required before route/decision authority.
- Ensure durable fact extraction and speech-act candidate stabilization are deterministic and traceable.
- Prepare policy/citation layers by enforcing observe-before-infer and stabilize-before-route semantics.

### Measurable exits
- BDD scenarios demonstrate observe-before-infer and stabilize-before-route behavior with deterministic fixtures.
- Deterministic pytest coverage confirms stage outputs are stable and no lossy projection bypasses stabilize.
- Canonical gate evidence is green: `python -m behave`, `python -m pytest -m "not live_smoke"`, and `python scripts/all_green_gate.py` pass for this sprint scope (per `docs/testing.md`).
- Milestone trace links to ISSUE-0013 sequencing checkpoints for decisioning + deterministic validation evidence.

### Mandatory code-review checkpoint (ISSUE-0013 decisioning sequencing)
- Architecture + runtime review confirms no early lossy `U -> I` projection path is reintroduced.
- Reviewer sign-off includes stage-order and invariant checklist references plus deterministic evidence links.

### Rollback criteria
- If baseline stabilization introduces regressions, revert the affected change set while preserving canonical stage order (`observe -> encode -> stabilize`) and invariant enforcement.
- Do not approve rollback variants that skip required stage transitions, even behind temporary toggles.

---

## Sprint 4 — Context/intent/retrieve/decide alignment (P2, P3)

### Goals
- Deliver context resolution + intent resolution hardening and retrieval/policy coherence updates.
- Ensure decision classes align with resolved intent and evidence posture (including empty-evidence vs scored-empty distinctions).
- Keep knowing/unknowing decisioning calibrated to deterministic retrieval evidence.

### Measurable exits
- BDD scenarios validate context/intent/retrieve/decide behavior and deterministic know/unknown outcomes.
- Deterministic pytest suites (including parity checks) confirm retrieval-policy alignment and stable decision routing.
- Canonical gate evidence is green: `python -m behave`, `python -m pytest -m "not live_smoke"`, `python -m pytest tests/test_eval_runtime_parity.py`, and `python scripts/all_green_gate.py` pass (per `docs/testing.md`).
- Milestone trace links to ISSUE-0013 sequencing checkpoints for cross-issue dependency routing + deterministic validation evidence.

### Mandatory code-review checkpoint (ISSUE-0013 sequencing checkpoint)
- Policy/retrieval review signs off on decision-answer alignment and explicit handling of empty-evidence vs scored-empty states.
- Review notes include explicit cross-issue dependency traceability to ISSUE-0013 sequencing records (with historical linkage back to ISSUE-0012 when needed).

### Rollback criteria
- If alignment changes regress behavior, revert to the prior policy/retrieval package only if canonical stage order (`context -> intent -> retrieve -> decide`) and invariants remain enforced.
- Feature toggles may be used temporarily, but must not permit out-of-order stage execution or bypass invariant checks.

---

## Sprint 5 — Assemble/validate/render/commit completion (P4, P5)

### Goals
- Complete answer assembly, validation, rendering, and commit sequencing for stakeholder-visible responses.
- Finalize citation/provenance contract materialization into committed turn state.
- Harden feedback/replay visibility and release-readiness reporting for post-turn audits.

### Measurable exits
- BDD scenarios pass for answer contract, provenance output, and fallback behavior at final response stages.
- Deterministic pytest coverage verifies committed-state traceability and replay-sensitive correctness.
- Canonical gate evidence is green: `python -m behave`, `python -m pytest -m "not live_smoke"`, `python -m pytest tests/test_eval_runtime_parity.py`, and `python scripts/all_green_gate.py` pass (per `docs/testing.md`).
- Milestone trace links to ISSUE-0013 sequencing checkpoints for commit/audit risk burn-down + deterministic validation evidence.

### Mandatory code-review checkpoint (ISSUE-0013 sequencing checkpoint)
- Release-readiness review confirms pipeline invariants, traceability artifacts, and deterministic gate evidence before capability status changes.
- Review explicitly records that canonical stage order is preserved through `assemble -> validate -> render -> commit`.

### Rollback criteria
- If final response/commit sequencing regresses, rollback must retain canonical stage order and invariant enforcement for all pre-commit stages.
- Do not ship rollback paths that preserve feature toggles but break stage ordering, provenance traceability, or deterministic validation guarantees.

---

## Priority-to-implementation mapping

_Last verified: 2026-03-06_

| Priority | Implementation files (likely `src/testbot/*`) | BDD scenarios (`features/*`) | Deterministic tests (`tests/*`) |
| --- | --- | --- | --- |
| **P1** Source connector interface + ingestion pipeline | `src/testbot/source_connectors.py`, `src/testbot/source_ingest.py`, `src/testbot/pipeline_state.py`, `src/testbot/config.py` | `features/source_ingestion.feature`, `features/capabilities.feature` | `tests/test_source_connectors.py`, `tests/test_source_ingest.py`, `tests/test_source_fusion.py` |
| **P2** Evidence normalization/ranking for mixed sources | `src/testbot/rerank.py`, `src/testbot/vector_store.py`, `src/testbot/eval_fixtures.py` | `features/memory_recall.feature`, `features/intent_grounding.feature` | `tests/test_rerank.py`, `tests/test_vector_store.py`, `tests/test_eval_runtime_parity.py` |
| **P3** Knowing/unknowing decision policy with confidence calibration | `src/testbot/intent_router.py`, `src/testbot/promotion_policy.py`, `src/testbot/reflection_policy.py` | `features/answer_contract.feature`, `features/intent_grounding.feature` | `tests/test_intent_router.py`, `tests/test_promotion_policy.py`, `tests/test_reflection_policy.py` |
| **P4** Citation UX + provenance explainability output format | `src/testbot/sat_chatbot_memory_v2.py`, `src/testbot/history_packer.py`, `src/testbot/memory_cards.py` | `features/answer_contract.feature`, `features/memory_recall.feature` | `tests/test_history_packer.py`, `tests/test_runtime_logging_events.py`, `tests/test_capabilities_help.py` |
| **P5** Feedback loop using follow-up signals and offline eval replay | `src/testbot/stage_transitions.py`, `src/testbot/time_reasoning.py`, `src/testbot/eval_fixtures.py` | `features/time_awareness.feature`, `features/memory_recall.feature` | `tests/test_time_reasoning.py`, `tests/test_eval_recall.py`, `tests/test_eval_runtime_parity.py` |

---

## Definition of Done (tied to `docs/testing.md` commands)

| DoD checkpoint | Required command | Evidence expectation |
| --- | --- | --- |
| BDD acceptance scenarios pass for changed behavior | `python -m behave` | No failed/undefined steps for affected features. |
| Deterministic unit/component checks pass | `python -m pytest -m "not live_smoke"` | Exit code `0`; no network-bound flakes. |
| Eval/runtime parity remains aligned after roadmap changes | `python -m pytest tests/test_eval_runtime_parity.py` | Ordering/top-1/fallback parity preserved. |
| Authoritative merge/readiness gate is green | `python scripts/all_green_gate.py` | Full deterministic merge/readiness gate passes in required order. |
