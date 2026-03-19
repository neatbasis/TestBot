# Plan Execution Checklist (from `plan.md` unresolved obligations)

This checklist captures unresolved delivery obligations grouped by Workstream A–H, with scoped-progress markers aligned to the current plan narrative.

## Workstream A — Canonical types and stage interfaces
- [ ] Define canonical staged DTO/state contracts (`PipelineState`, stage DTOs, invariants, and stage interfaces) in `src/testbot/domain/` + `src/testbot/logic/`; **owner module(s):** `src/testbot/domain/*`, `src/testbot/logic/*`; **required evidence (test/script/doc):** deterministic DTO/invariant unit tests + architecture contract doc update; **done signal:** typed stage contracts are the single source of truth and tests verify all required state distinctions.
- [x] DTO status: [x] `CandidateEncodingSet`, [x] `PreRouteState`, [x] `ContextResolvedState`, [x] `EvidenceSet`, [x] `PolicyDecision`, [x] `ValidationResult`, [x] `RenderedResponse`, [x] `TurnObservation`, [x] `IntentResolution`, [x] `AnswerCandidate`, [x] `CommittedTurnState`.
- [x] Typed replacement coverage for prior dict blobs/keys:
  - `pending_repair_state` now uses typed `PendingRepairState` contracts at assembly/render/commit boundaries.
  - policy/retrieval `reasoning` distinctions are explicit (`empty_evidence` vs `scored_empty`) and covered by deterministic unit tests.
  - stage artifact map access now uses typed accessors (`StageArtifacts`) for boundary-critical keys (e.g., `turn_id`, `retrieval_requirement`, `pending_ingestion_request_id`).

## Workstream B — Thin orchestration path
- [ ] Replace monolithic turn flow with explicit canonical sequence orchestration (`observe → encode → stabilize → context → intent → retrieve → decide → assemble → validate → render → commit`); **owner module(s):** `src/testbot/application/turn_service.py`, `src/testbot/entrypoints/*`; **required evidence (test/script/doc):** service tests over fake ports + sequence coverage in BDD; **done signal:** no supported runtime path bypasses the canonical stage chain.

## Workstream C — Stabilization and discourse state
- [ ] Implement pre-route stabilization and explicit unresolved-obligation discourse model (`PendingClarification`, `PendingRepair`, anchors, candidate/confirmed fact split); **owner module(s):** `src/testbot/logic/stabilization/*`, `src/testbot/domain/discourse*`, `src/testbot/domain/memory*`; **required evidence (test/script/doc):** unit tests for preservation/ID/provenance semantics + BDD scenarios for clarification/repair follow-up; **done signal:** candidate interpretations are preserved pre-route and discourse obligations survive turn boundaries deterministically.

## Workstream D — Intent resolution and retrieval contracts
- [ ] Implement two-layer intent model (classified vs resolved intent with precedence/facet validation) plus normalized retrieval contracts and explicit empty-state semantics; **owner module(s):** `src/testbot/logic/intent/*`, `src/testbot/ports/retrieval*`, `src/testbot/domain/evidence*`; **required evidence (test/script/doc):** precedence/facet legality tests + retrieval contract tests for all empty/sufficient states; **done signal:** downstream stages consume only resolved intent + normalized evidence DTOs with provider-neutral semantics.

## Workstream E — Decision/validation/commit chain
- [ ] Enforce typed `PolicyDecision` → `answer.assemble` → `answer.validate` gate → degraded fallback/commit transition semantics; **owner module(s):** `src/testbot/policies/*`, `src/testbot/logic/answer/*`, `src/testbot/application/commit*`; **required evidence (test/script/doc):** validation reason-code tests + commit transition tests + BDD degraded-fallback behavior; **done signal:** unvalidated semantic answers cannot render/commit, and commit writes canonical next-turn state only.

## Workstream F — Ports and adapters
- [ ] Introduce/normalize `MemoryRepository`, `VectorStore`, `LanguageModel`, `SourceConnector` interfaces and adapter implementations without provider-shape leakage; **owner module(s):** `src/testbot/ports/*`, `src/testbot/adapters/*`; **required evidence (test/script/doc):** port contract test suite + adapter conformance tests; **done signal:** logic/policy layers compile/run against protocol DTOs only (no backend-native types crossing boundaries).

## Workstream G — Boundary enforcement
- [ ] Add enforceable dependency/script boundary controls (import-linter, public API declarations, typed package enforcement, deep-import prohibitions); **owner module(s):** repository config + `scripts/*` + package `__init__` surfaces; **required evidence (test/script/doc):** automated boundary checks in canonical gate + failing fixture tests for forbidden imports; **done signal:** CI blocks merges on boundary violations and scripts use declared public surfaces only.

## Workstream H — Executable evidence and governance
- [ ] Produce auditable readiness/governance artifacts (schema-versioned gate outputs, check/rule IDs, traceability links, retention/version policy, standards crosswalk evidence); **owner module(s):** `scripts/all_green_gate.py`, `docs/`, `artifacts/` schemas; **required evidence (test/script/doc):** gate artifact schema validation + issue/traceability validators + governance doc updates; **done signal:** `all_green_gate` emits machine-validated evidence artifacts that map controls to owners, checks, and blocking status.

## Do-not-claim-yet
- [~] **Architecture-as-document only:** do not mark A/B complete until typed contracts and canonical orchestration are executable and covered by deterministic tests (not prose-only architecture alignment).
- [~] **Validation as advisory:** do not mark E complete until failed validation provably prevents semantic render+commit and only degraded fallback artifacts are allowed through.
- [~] **Adapter leakage risk:** do not mark D/F complete until provider-native objects are absent from logic/policy interfaces and contract tests enforce DTO-only boundaries.
- [~] **Boundary controls pending:** do not mark G complete until automated dependency/script boundary checks run inside the canonical readiness gate and are merge-blocking.
- [~] **Governance intent without evidence:** do not mark H complete until schema-validated gate artifacts include check IDs, rule IDs, traceability metadata, and retention/version semantics.
