# Commit-by-commit progression/regression audit — 2026-03-19

## Scope and method

Date window audited: **2026-03-19 (local repo commit dates)**.

Method:
1. Enumerate all **non-merge** commits on 2026-03-19 in chronological order.
2. Read commit subjects + touched files.
3. Cross-check high-impact symbols and docs against current `HEAD` code (`turn_service`, canonical aliases, DTO carry, unresolved obligations, package script entrypoint).
4. Flag **progression**, **regression risk**, and **documentation alignment drift**.

Commands used:
- `git log --since='2026-03-19 00:00' --no-merges --reverse --pretty=format:'%H|%ad|%s'`
- `for c in ...; git show --name-only ...`
- `rg -n "CANONICAL_STAGE_SEQUENCE|run_answer_stage_flow|..." ...`
- `wc -l src/testbot/sat_chatbot_memory_v2.py`
- `rg -n "[project.scripts]|testbot = \"testbot.entrypoints.sat_cli:main\"" pyproject.toml`

Evidence confidence policy used in this audit:
- **High confidence:** major code-moving commits with symbol-level verification at `HEAD`.
- **Medium confidence:** commit classification based on message + touched-file scope.
- **Low confidence:** avoid definitive behavior claims unless symbol/runtime evidence is directly observed.

---

## Chronological ledger (non-merge commits)

### 1) `19364f42` — docs: add ISSUE-0013 system structure audit report
- **Classification:** Progression (documentation baseline).
- **Net effect:** Establishes structural diagnosis and extraction narrative.
- **Risk introduced:** Early audit assertions later required correction as code evolved (expected for a first-pass audit).

### 2) `134f7463` — docs: amend ISSUE-0013 system structure audit with authority census
- **Classification:** Progression (better structural evidence).
- **Net effect:** Adds authority census and concrete risk framing.

### 3) `af8f5404` — ISSUE-0009: restructure changelog entry template
- **Classification:** Mixed (process progression + potential documentation overhead).
- **Progression:** Changelog entries become more structured and migration-aware.
- **Regression risk:** Higher doc-maintenance burden can create stale status statements if updates lag behind code.

### 4) `996efff7` — ISSUE-0001: freeze `sat_chatbot_memory_v2` export contract
- **Classification:** Strong progression.
- **Code progression:** Explicit public surface via `__all__` and contract stabilization.
- **Test progression:** Broad test import updates reduce accidental private-symbol dependence.
- **Documentation progression:** Audit/changelog synced to frozen API surface.

### 5) `ce2e6cc9` — ISSUE-0013: type high-frequency pipeline artifact fields
- **Classification:** Progression.
- **Code progression:** Typed accessor/field coverage improved for critical artifact paths.
- **Risk reduced:** Less dict-key drift in hot paths.

### 6) `0e1e96c2` — docs: clarify deprecated answer-stage alias in architecture audit
- **Classification:** Progression (doc correction).
- **Net effect:** Clarifies alias/deprecation behavior to reduce parallel-runner ambiguity.

### 7) `7791bd32` — docs: refresh pivot status and reprioritize next tasks
- **Classification:** Progression (planning hygiene).

### 8) `fff6b05d` — ISSUE-0013: extract canonical turn pipeline into application turn service
- **Classification:** Major progression.
- **Code progression:** Canonical orchestration ownership moved into app service layer.
- **Architecture progression:** Monolith begins delegating rather than directly owning stage choreography.

### 9) `989e63b6` — ISSUE-0013-B: decouple `pipeline_state` snapshot clock from `memory_cards`
- **Classification:** Progression.
- **Code progression:** Domain contract purity improved (time source decoupling).

### 10) `4b9929ab` — ISSUE-0013: scoped progress for stabilization/retrieval split
- **Classification:** Progression.
- **Code progression:** Separation between pure logic seams and adapter-facing persistence/mapping improved.

### 11) `9d63797f` — docs(pivot): scoped answer-commit seam progress
- **Classification:** Progression.
- **Code progression:** Commit seam extraction (`AnswerCommitService` and staged input building) becomes explicit.
- **Doc posture:** Correctly marked as partial/non-final.

### 12) `51450639` — ISSUE-0013: add typed port contracts + adapter contract tests
- **Classification:** Major progression.
- **Code progression:** Formal protocols for ports plus contract-test coverage.
- **Test progression:** Integration contract suite helps prevent adapter-shape leakage.

### 13) `58c6c666` — Add plan for executing `docs/pivot.md`
- **Classification:** Progression (coordination artifact).

### 14) `8a59e507` — ISSUE-0001: add plan execution checklist
- **Classification:** Progression (execution tracking scaffold).

### 15) `b6ea2fa3` — ISSUE-0013: add canonical stage DTO wrappers and adapters
- **Classification:** Major progression.
- **Code progression:** Domain DTO layer expanded and test-covered.

### 16) `8de37e1c` — ISSUE-0013: extract alignment scoring to logic module with shim
- **Classification:** Major progression.
- **Code progression:** Alignment logic moved to `logic/` with deprecation shim for compatibility.
- **Risk managed:** Backward compatibility maintained while ownership migrates.

### 17) `883c4c2d` — ISSUE-0001: extract turn pipeline stages into explicit callables
- **Classification:** Progression.
- **Code progression:** Stage wiring readability/testability improves (explicit callable handlers).

### 18) `57247bea` — ISSUE-0013: remove seeded parallel runner + canonical delegation
- **Classification:** Major progression.
- **Code progression:** Parallel seeded path retired; canonical authority centralized.
- **Regression avoided:** Reduces dual-path execution divergence risk.

### 19) `cdfbfdff` — ISSUE-0013: update plan status layer + changelog evidence risk
- **Classification:** Mixed.
- **Progression:** Explicitly acknowledges “intent vs evidence” governance risk.
- **Regression observed later:** Plan status lines became stale after subsequent code moves (see drift section).

### 20) `645cbb0a` — ISSUE-0013: complete typed stage contracts + boundary accessors
- **Classification:** Major progression.
- **Code progression:** Broader typed contract adoption across answer pipeline modules.
- **Docs progression:** canonical-turn-pipeline docs and checklist advanced.

### 21) `ca9d775f` — ISSUE-0013: unify canonical stage routing + remove seeded answer orchestration
- **Classification:** Major progression.
- **Code progression:** Tightens single-path canonical execution.

### 22) `88dbc562` — ISSUE-0008: add typed anchors + enforce candidate/confirmed fact separation
- **Classification:** Major progression.
- **Code progression:** Discourse/intent-grounding model improved with typed anchors and fact-state separation.
- **Behavior progression:** BDD scenarios updated to protect stakeholder-visible semantics.

### 23) `5012548a` — docs: sync architecture docs with extraction progress
- **Classification:** Progression.
- **Net effect:** Attempted doc realignment with current code.

### 24) `600d3bc5` — docs: changelog note for architecture doc sync
- **Classification:** Progression (traceability).

### 25) `3e9424bc` — ISSUE-0013: extract canonical entrypoint + sequence ownership
- **Classification:** Major progression.
- **Code progression:** Explicit sequence constant and entrypoint/service ownership relocation.
- **Architecture progression:** Further monolith authority reduction with compatibility delegation retained.

### 26) `720edeb8` — ISSUE-0021: move deprecated alias removal target to 2026-04-01
- **Classification:** Mixed.
- **Progression:** Stabilizes migration timeline and avoids premature breakage.
- **Potential regression risk:** Extends life of deprecated surfaces, prolonging alias drift risk.

### 27) `24730228` — ISSUE-0013: ratchet stage payloads toward typed DTO wrappers
- **Classification:** Major progression.
- **Code progression:** Wider DTO normalization across context/retrieval/policy/validation/pipeline state.

### 28) `36c83c11` — ISSUE-0013: finalize unresolved obligation DTO carry + intent/evidence normalization
- **Classification:** Major progression.
- **Code progression:** `UnresolvedObligation` and intent/evidence normalization integrated through pipeline.
- **Behavior progression:** Intent-grounding feature/tests updated for continuity guarantees.

---

## Progression pattern across the day

1. **Morning:** architecture diagnosis and governance scaffolding landed first.
2. **Midday:** extraction seams and service decomposition accelerated (`turn_service`, stabilization/retrieval split, commit seam, typed ports).
3. **Late day:** canonical execution authority converged (parallel seeded path removed, sequence ownership explicit, entrypoint extraction).
4. **End of day:** DTO carry finalized (`UnresolvedObligation`, intent/evidence normalization) with BDD/test updates.

Overall trajectory: **high structural progression with partial (not complete) runtime ambiguity reduction**.

### Confidence-graded veracity check (post-review correction)

The strongest claims are now explicitly graded:

- **High-confidence confirmed progression:** `51450639`, `ca9d775f`, `3e9424bc` (typed ports/contracts, canonical stage routing consolidation, explicit sequence + entrypoint extraction).
- **Medium-confidence ledger classifications:** remaining commits in the 28-entry list are classified from commit message + touched-file evidence; they should not be read as equally deep symbol-level verification.
- **Operational non-closure evidence at `HEAD` (historical audit snapshot, later updates may differ):**
  - package script boot mapping at audit time: `testbot = "testbot.sat_chatbot_memory_v2:main"` in `pyproject.toml`;
  - `sat_chatbot_memory_v2.py` remains large (`3806` lines at audit time).

This means the day shows substantial progress, but not architectural closure.

---

## Regressions and regression risks identified

## A) Confirmed regressions
No direct runtime-behavior regressions were found from commit metadata + current contract signals; the direction was consistently toward single-path canonical execution and stronger typing.

## B) Active regression risks (not yet failures)
1. **Deprecated alias half-life risk** (`run_answer_stage_flow`, alignment shim): removal date pushed to 2026-04-01, so stale imports can persist if enforcement weakens.
2. **Residual dict-heavy payload risk:** despite DTO progress, docs still correctly note remaining `dict[str, object]` heavy contracts in policy/validation/artifacts.
3. **Monolith residual authority risk:** entrypoint/service extraction is meaningful, but `sat_chatbot_memory_v2.py` still remains a high-authority compatibility surface.
4. **Entrypoint centralization not yet complete:** packaging still executes monolith `main`, so extracted entrypoint modules are not yet the sole operational boot surface.

---

## Documentation ↔ code alignment drift (current `HEAD`)

### Drift 1: Workstream B owner path is stale in checklist
- **Doc text:** points at `src/testbot/application/turn_service.py`.
- **Code reality:** canonical service is `src/testbot/application/services/turn_service.py`.
- **Impact:** contributor navigation friction + incorrect ownership breadcrumb.

### Drift 2: `plan.md` Workstream B status is stale
- **Doc text (status dated 2026-03-19):** says orchestration still wires lambdas capturing `stage_runtime`.
- **Code reality:** handler receiver `_TurnPipelineStageHandlers` and explicit sequence constant are in place.
- **Impact:** understates achieved refactor state; can trigger redundant work.

### Drift 3: `plan.md` Workstream C status is stale
- **Doc text (status dated 2026-03-19):** says `UnresolvedObligation` does not yet exist as typed object.
- **Code reality:** `UnresolvedObligation` exists in `src/testbot/domain/canonical_dtos.py` and is exported/consumed.
- **Impact:** falsely marks completed DTO milestone as missing.

### Drift 4: System-structure audit has internal temporal tension
- **Doc text (earlier sections):** frames `evaluate_alignment_decision()` as co-located collapse logic.
- **Code reality + later doc update:** alignment logic is extracted to `src/testbot/logic/alignment.py`; monolith symbol is compatibility shim.
- **Impact:** mixed narrative in one audit document can confuse extraction priority decisions.

---

## Recommended corrective actions

1. **Patch `docs/architecture/plan-execution-checklist.md` owner path for Workstream B** to `src/testbot/application/services/turn_service.py`.
2. **Patch `plan.md` Workstream status snapshots** so dated status lines reflect post-`3e9424bc` and post-`36c83c11` reality.
3. **Normalize audit language around alignment ownership** to clearly separate “historical collapse point” vs “current shim state”.
4. **Keep deprecated-alias import enforcement strict** through 2026-04-01 to avoid late-stage regression.

---

## Bottom line

On 2026-03-19, commits show a clear **progression arc** from architecture diagnosis → extraction seams → canonical-path consolidation → typed discourse/intent normalization.

Corrected interpretation: the repo now shows **high real progression, moderate remaining structural centralization, and clear documentation lag**.

Documentation drift is real and actionable, but it is **not** the only primary remaining issue: monolith authority is reduced yet still materially present in runtime boot and behavior ownership.
