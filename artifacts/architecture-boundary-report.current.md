# TestBot Architecture Boundary Remediation Report

Generated: 2026-03-19 UTC (second-pass, remediation-focused)

Baseline commit analyzed: `7c3aef136ffd01f4c51a505082419a9873480e29` on branch `work`.

Evidence inputs:
- `artifacts/architecture-boundary-report.current.json`
- `scripts/architecture_boundary_report.py`
- `docs/qa/architecture-boundaries.json`
- Runtime code under `src/testbot/**`
- Architecture docs under `docs/architecture/**`

## 1. Executive judgment

Architecture drift is **mixed**, but the dominant source is **migration incompleteness in/around `sat_chatbot_memory_v2` plus boundary config/public-surface under-modeling**, not just arbitrary bad code.

Current state split:
- **True code-level boundary leaks exist** (notably adapter coupling in `memory_cards`, `promotion_policy`, `stabilization`, and `turn_service`/runtime wrappers via `vector_store`).
- **Many private-surface violations are config/public API shaping gaps**: application service imports are semantically expected for orchestration, but target areas expose too little public surface.
- **`sat_chatbot_memory_v2` is mixed-authority, not a pure shell**: it still owns runtime wiring/loops and compatibility exports while delegating canonical stage execution to application services.

## 2. Violation triage table

Legend for “actual problem type”:
- **A** = Must fix in code now
- **B** = Introduce/inject a port
- **C** = Widen approved public package surface
- **D** = Transitional compatibility edge; document + time-box
- **E** = Likely false positive/rule-config mismatch

| importer | imported module | current classification | actual problem type | recommended action | severity | confidence |
|---|---|---|---|---|---|---|
|testbot.answer_assembly|testbot.policy_decision|forbidden_dependency_direction|E|Reclassify boundary area/public-surface rule to match intended architecture.|low|medium|
|testbot.application.services.canonical_turn_runtime|testbot.clock|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.canonical_turn_runtime|testbot.evidence_retrieval|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.canonical_turn_runtime|testbot.memory_cards|private_surface_import|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.application.services.canonical_turn_runtime|testbot.reflection_policy|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.canonical_turn_runtime|testbot.vector_store|forbidden_dependency_direction|B|Introduce or inject a port; move adapter dependency to adapter/composition root.|high|medium|
|testbot.application.services.turn_service|testbot.answer_assembly|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.answer_commit|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.answer_rendering|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.answer_validation|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.candidate_encoding|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.clock|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.evidence_retrieval|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.intent_resolution|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.intent_router|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.memory_strata|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.policy_decision|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.reflection_policy|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.retrieval_routing|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.stabilization|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.stage_transitions|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.turn_observation|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.application.services.turn_service|testbot.vector_store|forbidden_dependency_direction|B|Introduce or inject a port; move adapter dependency to adapter/composition root.|high|medium|
|testbot.context_resolution|testbot.intent_router|forbidden_dependency_direction|E|Reclassify boundary area/public-surface rule to match intended architecture.|low|medium|
|testbot.domain.canonical_dtos|testbot.intent_router|forbidden_dependency_direction|A|Refactor module ownership/import now to remove cross-layer leak.|high|high|
|testbot.domain.canonical_dtos|testbot.policy_decision|forbidden_dependency_direction|A|Refactor module ownership/import now to remove cross-layer leak.|high|high|
|testbot.entrypoints.sat_cli|testbot.clock|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.entrypoints.sat_cli|testbot.vector_store|forbidden_dependency_direction|E|Reclassify boundary area/public-surface rule to match intended architecture.|low|medium|
|testbot.entrypoints.sat_runtime_modes|testbot.clock|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.entrypoints.sat_runtime_modes|testbot.vector_store|forbidden_dependency_direction|E|Reclassify boundary area/public-surface rule to match intended architecture.|low|medium|
|testbot.intent_resolution|testbot.intent_router|forbidden_dependency_direction|E|Reclassify boundary area/public-surface rule to match intended architecture.|low|medium|
|testbot.memory_cards|testbot.ports|forbidden_dependency_direction|A|Refactor module ownership/import now to remove cross-layer leak.|high|high|
|testbot.memory_cards|testbot.vector_store|forbidden_dependency_direction|A|Refactor module ownership/import now to remove cross-layer leak.|high|high|
|testbot.observability.session_log|testbot.memory_cards|private_surface_import|A|Refactor module ownership/import now to remove cross-layer leak.|high|high|
|testbot.policy_decision|testbot.evidence_retrieval|private_surface_import|C|Add/adjust deliberate public facade/re-export; update importer to use public path.|medium|high|
|testbot.promotion_policy|testbot.memory_cards|private_surface_import|A|Refactor module ownership/import now to remove cross-layer leak.|high|high|
|testbot.promotion_policy|testbot.vector_store|forbidden_dependency_direction|A|Refactor module ownership/import now to remove cross-layer leak.|high|high|
|testbot.sat_chatbot_memory_v2|testbot.candidate_encoding|private_surface_import|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.clock|private_surface_import|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.config|forbidden_dependency_direction|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.context_resolution|private_surface_import|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.evidence_retrieval|private_surface_import|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.history_packer|private_surface_import|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.intent_resolution|private_surface_import|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.intent_router|forbidden_dependency_direction|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.logic.alignment|forbidden_dependency_direction|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.logic.decision_helpers|forbidden_dependency_direction|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.memory_cards|private_surface_import|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.memory_strata|private_surface_import|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.policy_decision|forbidden_dependency_direction|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.promotion_policy|forbidden_dependency_direction|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.reflection_policy|forbidden_dependency_direction|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.reject_taxonomy|forbidden_dependency_direction|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.rerank|forbidden_dependency_direction|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.retrieval_routing|forbidden_dependency_direction|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.source_connectors|forbidden_dependency_direction|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.source_ingest|forbidden_dependency_direction|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.stabilization|private_surface_import|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.stage_transitions|forbidden_dependency_direction|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.time_parse|private_surface_import|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.time_reasoning|private_surface_import|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.turn_observation|private_surface_import|D|Keep as transitional compatibility edge; document owner + sunset criteria.|medium|medium|
|testbot.sat_chatbot_memory_v2|testbot.vector_store|forbidden_dependency_direction|B|Introduce or inject a port; move adapter dependency to adapter/composition root.|high|medium|
|testbot.stabilization|testbot.vector_store|forbidden_dependency_direction|B|Introduce or inject a port; move adapter dependency to adapter/composition root.|high|medium|
|testbot.stage_transitions|testbot.memory_cards|private_surface_import|A|Refactor module ownership/import now to remove cross-layer leak.|high|high|

## 3. Top offender deep dives

### 3.1 `sat_chatbot_memory_v2`

**Current authority**: mixed authority.
- It is not just a dead wrapper: it still defines runtime loop and compatibility APIs (`run_chat_loop`, `run_source_ingestion`, `build_capability_snapshot`, `run_canonical_answer_stage_flow`) and composes `TurnPipelineDependencies` before delegating pipeline execution.  
- It does delegate canonical pipeline execution to application services (`run_canonical_turn_pipeline` via `canonical_turn_runtime`).

**Truly inappropriate imports**
- Adapter coupling from an entrypoint/compat module: `vector_store`, `source_connectors`, `source_ingest`, `rerank`, `config`.
- Logic-layer direct dependencies (`logic.alignment`, `logic.decision_helpers`) remain concentrated here and keep this file as behavioral owner.

**Missing public API shaping signals**
- Several domain imports are semantically “pipeline contracts” that should come from a deliberate facade, not from many concrete modules.

**What should move next**
1. Move ingestion orchestration and connector wiring behind an application service/port seam.
2. Move compatibility-facing function exports to a dedicated `entrypoints.compat` facade.
3. Keep temporary exception until `sat_cli` and runtime modes no longer require monolith-owned wiring functions.

### 3.2 `application.services.turn_service`

**Current authority**: canonical stage-order orchestrator; this is the right place for pipeline choreography.

**Truly inappropriate imports**
- Direct `vector_store.MemoryStore` type dependency in application service is an adapter leakage (port needed).

**Missing public API shaping signals**
- Most private-surface violations are orchestration dependencies that are semantically valid for this service (answer/context/intent/evidence/stage transition contracts), but blocked by too-narrow `domain` and `logic` public surfaces.

**What should move next**
1. Replace `MemoryStore` typing with a port/protocol type.
2. Introduce domain and logic facades for stage contracts imported here.

### 3.3 `application.services.canonical_turn_runtime`

**Current authority**: wrapper shim around `run_canonical_turn_pipeline_service` plus compatibility re-export (`store_doc`).

**Truly inappropriate imports**
- `vector_store` in application wrapper remains adapter coupling.

**Missing public API shaping signals**
- `clock`, `evidence_retrieval`, and `reflection_policy` imports are likely valid orchestration-level contracts but not exposed by configured public surface.

**Transitional indicators**
- Importing and re-exporting `store_doc` from `memory_cards` is compatibility behavior, not stable architecture.

**What should move next**
- Keep wrapper thin and remove compatibility re-exports once callers are migrated.

### 3.4 `domain.canonical_dtos`

**Current authority**: DTO adapters bridging canonical domain wrappers to legacy classes.

**Truly inappropriate imports**
- Direct dependency on `intent_router.IntentType` and `policy_decision.Decision*` from `domain` violates directionality semantically.

**Interpretation**
- This is not merely a private/public-surface mismatch; the domain package is importing logic-owned types.

**What should move next**
- Extract shared enum/type contracts to domain-owned module (or duplicate canonical DTO-native enums) and have logic consume domain types.

## 4. Public surface corrections

These are recommended **deliberate** facades/re-exports (C-bucket fixes), not broad allow-all openings.

1. **Expose canonical domain contracts for application orchestration**
   - Expose from: `testbot.domain` package facade (`src/testbot/domain/__init__.py`) and/or `testbot.domain.pipeline_contracts`.
   - Modules/contracts to expose: `clock`, `candidate_encoding`, `turn_observation`, `stabilization`, `intent_resolution`, `evidence_retrieval`, `answer_assembly`, `answer_validation`, `answer_rendering`, `answer_commit`, `memory_strata`.
   - Imports that become valid: most `turn_service` + `canonical_turn_runtime` current private-surface domain imports.

2. **Expose logic policy/query contracts used by application orchestration**
   - Expose from: `testbot.logic` facade.
   - Contracts to expose: `IntentType`/facet APIs, `decide_retrieval_routing`, policy decision types, stage transition validators, capability policy types.
   - Imports that become valid: `turn_service` imports of `intent_router`, `retrieval_routing`, `policy_decision`, `reflection_policy`, `stage_transitions`.

3. **Expose a stable time provider utility for cross-cutting modules**
   - Expose from: `testbot.domain.time` or `testbot.clock` via domain facade.
   - Replace current `memory_cards.utc_now_iso` call sites in observability/stage transition modules.

4. **Compatibility facade for monolith exports**
   - New package: `testbot.entrypoints.compat` (or similar).
   - Re-export only transitional APIs currently imported from `sat_chatbot_memory_v2`.

## 5. Code fixes that should happen before config changes

1. **Split storage writes from domain helper modules (A/B)**
   - Files: `src/testbot/memory_cards.py`, `src/testbot/stabilization.py`, `src/testbot/promotion_policy.py`, new port module under `src/testbot/ports/`.
   - Change type: ownership/import-path change; behavior should remain equivalent.
   - Tests: stabilization/promotion unit tests + retrieval/store contract tests.

2. **Remove observability and transition dependency on `memory_cards.utc_now_iso` (A)**
   - Files: `src/testbot/observability/session_log.py`, `src/testbot/stage_transitions.py`.
   - Change type: import/source-of-time change only.
   - Tests: observability + transition validation tests.

3. **Decouple `domain.canonical_dtos` from logic-owned types (A)**
   - Files: `src/testbot/domain/canonical_dtos.py`, likely new domain enums/contracts module, plus logic consumer updates.
   - Change type: ownership and type source; no intended behavior change.
   - Tests: DTO round-trip and pipeline integration tests where `PolicyDecision`/`IntentType` are serialized.

4. **Replace direct `vector_store` application dependency with port interface (B)**
   - Files: `src/testbot/application/services/turn_service.py`, `src/testbot/application/services/canonical_turn_runtime.py`, `src/testbot/sat_chatbot_memory_v2.py`, `src/testbot/ports/*`, adapter implementation in `src/testbot/vector_store.py`.
   - Change type: ownership/import-path mostly; behavior should stay same.

## 6. Config changes that are justified

1. **Public surface widening for domain/logic (targeted, not wildcard)**
   - Update `docs/qa/architecture-boundaries.json` `public_surface` for `domain` and `logic` with explicit facade modules.
   - Do **after** creating facades so config matches real API, not intent-only docs.

2. **Entrypoint-to-adapter direction for composition root**
   - Allow `entrypoints -> adapters` for explicit composition modules (`testbot.entrypoints.sat_cli`, `testbot.entrypoints.sat_runtime_modes`) **or** define a dedicated composition area.
   - This is justified because these modules are currently composition roots and package script entrypoint is `testbot.entrypoints.sat_cli:main`.

3. **Reclassify select stage modules now treated as domain but behaving as logic/application**
   - Candidate modules for re-area assignment: `intent_resolution`, `context_resolution`, `answer_assembly`.
   - This should follow a short ownership review; confidence medium.

## 7. Migration debt to time-box

1. **`sat_chatbot_memory_v2` compatibility bridge cluster**
   - Scope: 25 D-class edges (excluding `vector_store` which is B).
   - Owner: runtime-pipeline (consistent with `ISSUE-0013` temporary exception ownership).
   - Removal criteria:
     - `sat_cli` + `sat_runtime_modes` no longer import monolith-owned runtime helpers.
     - Monolith no longer composes turn dependencies or ingestion runtime directly.
   - Target condition: monolith reduced to compatibility re-export module with no new behavior.
   - Expiry realism: current 2026-12-31 exception date is likely too late for high-risk edges; recommend staged checkpoints by end of Q2 2026.

2. **`canonical_turn_runtime` `store_doc` shim**
   - Owner: runtime-pipeline.
   - Removal criteria: all callers import stable port/application location for store operation; no `__all__` compatibility export needed.
   - Suggested sunset: with next port-injection milestone.

3. **Legacy public API alias debt in monolith surface**
   - Owner: architecture + runtime maintainers.
   - Removal condition: import-boundary checks enforce zero new non-compatibility callers.

## 8. Recommended next 3 implementation tasks

1. **Task 1 — Introduce storage writer port and remove application/logic/domain direct `vector_store` imports**
   - Why first: highest architectural risk and unblocks multiple B/A findings.
   - Files likely: `turn_service.py`, `canonical_turn_runtime.py`, `sat_chatbot_memory_v2.py`, `stabilization.py`, `memory_cards.py`, `promotion_policy.py`, `ports/*`, `vector_store.py`.
   - Behavior impact: should be none (wiring change).
   - Tests: targeted unit + contract tests + architecture boundary report.
   - Config timing: **after** code path stabilized.

2. **Task 2 — Create explicit domain/logic facades and migrate `turn_service` imports to those public paths**
   - Why second: resolves largest private-surface cluster without broad allowlisting.
   - Files likely: `src/testbot/domain/__init__.py` (or new facade module), `src/testbot/logic/__init__.py` (or facade), `turn_service.py`, `canonical_turn_runtime.py`, `docs/qa/architecture-boundaries.json`.
   - Behavior impact: none expected.
   - Tests: architecture boundary script + import-boundary pytest + smoke unit tests.
   - Config timing: facade first, config second.

3. **Task 3 — Reduce `sat_chatbot_memory_v2` to compatibility-only surface with bounded shim list**
   - Why third: large blast radius; depends on Tasks 1-2.
   - Files likely: `sat_chatbot_memory_v2.py`, `entrypoints/sat_cli.py`, `entrypoints/sat_runtime_modes.py`, optional `entrypoints/compat.py`, boundary config + docs.
   - Behavior impact: intended no external behavior change; ownership move only.
   - Tests: runtime mode tests, pipeline parity checks, architecture boundary report, compatibility import tests.
   - Config timing: add/remove D exceptions **as code migrates**, not in advance.

---

## Private-surface and forbidden-direction adjudication notes

### Private-surface clusters

- **Semantically wrong imports**: `observability.session_log -> memory_cards` (time helper coupling), persistence calls inside logic/domain helpers (`promotion_policy`, `memory_cards`).
- **Missing deliberate public façade**: majority of `turn_service` and `canonical_turn_runtime` imports into domain/logic modules.
- **Exact public paths to introduce**: `testbot.domain.pipeline_contracts.*`, `testbot.logic.pipeline_policies.*` (names illustrative but should be explicit, stable packages).

### Forbidden-direction clusters

- **Importer in wrong layer**: `domain.canonical_dtos` depending on logic types (true direction bug).
- **Imported code in wrong layer (or split needed)**: intent and policy type ownership currently mixed with logic behavior; split type contracts into domain-owned modules.
- **Config assignment likely wrong**: entrypoint composition modules importing adapter wiring (`vector_store`) and stage modules presently assigned to `domain` though behaving as logic/application.

### Monolith extraction judgment (`sat_chatbot_memory_v2`)

Assessment: **mixed authority**.

Concrete evidence:
- Still constructs `TurnPipelineDependencies` and calls `run_canonical_turn_pipeline` wrapper.
- Still owns runtime helper exports used by current entrypoint modules (`parse_args`, `read_runtime_env`, `build_capability_snapshot`, `run_chat_loop`, `run_source_ingestion`, `sat_say`).
- `main` is now a delegator to `entrypoints.sat_cli:main`, which confirms extraction progress but not completion.

So this module is **not authoritative for stage sequencing anymore**, but **still authoritative for significant runtime behavior and compatibility API surface**.
