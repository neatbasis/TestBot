# TestBot Reorganization Pivot: **Executed Module Census** + Target Package Map

## Why this document changed

This revision moves from "plan about planning" to a **completed first census pass** on current `src/testbot` modules.

- The census template is still included.
- Scores are now applied to real components.
- Dependency-direction findings are now explicit (`dep_direction_ok=yes/no`).
- Migration order is now driven by scored findings, not generic architecture advice.

---

## 0) Census method used for this pass (2026-03-18)

The first pass used static evidence already available in-repo:

1. Internal import graph across `src/testbot/*.py` (fan-in/fan-out).
2. External import surface (e.g., `elasticsearch`, `langchain_core`, `ha_ask`, filesystem).
3. Test/reference surface by counting module mentions in `tests/**/*.py` and `features/steps/**/*.py`.

Scoring rubric (applied below):

- **Coupling risk (1–3)**: how much infra/orchestration is mixed into module responsibility.
- **Blast radius (1–3)**: fan-in + usage footprint.
- **Test cost (1–3)**: deterministic difficulty (network/filesystem/runtime coupling).

`priority_score = coupling + blast_radius + test_cost`.

Priority bands:

- **P0:** 8–9 (extract first)
- **P1:** 7 (extract next)
- **P2:** 5–6 (follow-on)
- **P3:** <=4 (leave until later)

---

## 1) Census template (kept as reusable scaffold)

| Field | What to capture | Allowed values / guidance |
| --- | --- | --- |
| `component` | File/module path being assessed | Example: `src/testbot/answer_policy.py` |
| `current_role` | One-sentence current responsibility | Keep to one sentence |
| `target_module` | Intended logical module | `domain`, `logic`, `application`, `ports`, `adapters`, `entrypoints`, `observability`, `policies`, `governance_tooling` |
| `depends_on` | What this component may depend on | Use module names only; avoid implementation details |
| `dep_direction_ok` | Is dependency direction acceptable? | `yes` / `no` |
| `external_systems` | External services touched directly | `none`, `ollama`, `elasticsearch`, `home_assistant`, `filesystem`, etc. |
| `test_tier` | Primary expected test tier | `unit`, `service`, `integration`, `smoke`, `bdd` |
| `boundary_risk` | Most important architecture risk | e.g., `infra leakage`, `policy+adapter coupling`, `orchestration bloat` |
| `current_test_locations` | Existing deterministic/behavioral coverage anchors | List concrete paths like `tests/...`, `features/...` |
| `migration_action` | Minimal next step | `label-only`, `extract port`, `move pure logic`, `split adapter`, `thin entrypoint` |
| `owner` | Responsible team/person | Use real owner alias |
| `issue_link` | Tracking issue | `ISSUE-XXXX` |

---

## 2) **Executed census pass** (current modules)

> Note: "depends_on" summarizes significant internal dependencies, not every single import.

| component | current_role | target_module | depends_on | dep_direction_ok | external_systems | test_tier | coupling | blast | test_cost | score | boundary_risk | current_test_locations | migration_action |
| --- | --- | --- | --- | --- | --- | --- | ---:| ---:| ---:| ---:| --- | --- | --- |
| `sat_chatbot_memory_v2.py` | monolithic runtime entrypoint + orchestration + infra wiring | `entrypoints` (+ composition root) | ~32 internal modules across pipeline/policy/storage/rendering | **no** | home_assistant (`ha_ask`), llm/runtime libs, filesystem/runtime | smoke/service | 3 | 3 | 3 | **9** | orchestration bloat + infra leakage | `features/` runtime scenarios; `tests/` entrypoint/orchestration regressions | split into thin entrypoint + app service wiring |
| `pipeline_state.py` | canonical turn state and cross-stage data contract | `domain` | currently imports `memory_cards` | **no** | filesystem/json helpers | unit | 2 | 3 | 2 | **7** | domain depending on memory infra shape | `tests/` state/parity checks; `features/steps/` turn-state assertions | extract pure state model from memory adapter concerns |
| `stabilization.py` | pre-route stabilization and candidate/durable fact handling | `logic` | `candidate_encoding`, `pipeline_state`, `memory_cards`, `vector_store` | **no** | vector/memory infra via `vector_store` | unit/service | 3 | 2 | 2 | **7** | logic layer coupled to adapter/storage | `tests/` stabilization and runtime-path checks | split pure stabilizer from store-backed lookup |
| `evidence_retrieval.py` | retrieval-stage evidence assembly for pipeline | `logic` + `ports` | `pipeline_state`, `stabilization` (+ `langchain_core`) | **no** | embedding/document infra (`langchain_core`) | service | 3 | 2 | 2 | **7** | retrieval policy mixed with provider types | `tests/` retrieval and runtime-parity checks | add retrieval port + adapter DTO mapper |
| `answer_commit.py` | answer commit orchestration and provenance write-through | `application` | `answer_assembly`, `answer_rendering`, `answer_validation`, `pipeline_state` | **no** | persistence/runtime side effects | service | 2 | 2 | 3 | **7** | commit orchestration mixed with rendering/validation pipeline | `tests/` answer pipeline regressions; `features/steps/` provenance steps | separate commit service from answer formatting/validation |
| `policy_decision.py` | action-class decisioning from intent/evidence | `policies` | `intent_router`, `retrieval_routing`, `evidence_retrieval` | **partial/no** | none direct | unit | 2 | 2 | 2 | 6 | policy coupled to retrieval structures | `tests/` policy/intent decision coverage | move policy inputs to normalized domain DTO |
| `source_ingest.py` | source ingestion workflow and store writes | `application` + `adapters` | `source_connectors`, `vector_store` | **no** | connectors + vector persistence | integration/service | 2 | 1 | 3 | 6 | use-case orchestration fused with adapter calls | `tests/` ingest/integration coverage | introduce ingest service + connector/store ports |
| `vector_store.py` | concrete vector + memory backend access | `adapters` | none internal | **yes** | `elasticsearch`, `langchain_core` | integration | 1 | 2 | 3 | 6 | backend-specific data contracts leaking upward | `tests/` vector backend integration coverage | keep adapter, expose protocol in `ports/` |
| `source_connectors.py` | concrete source connector loading/normalization | `adapters` | none internal | **yes** | dynamic loading/filesystem/importlib | integration | 2 | 1 | 2 | 5 | dynamic connector behavior hard to contract-test | `tests/` connector adapter coverage | define connector contract tests per connector type |
| `intent_router.py` | intent enums/routes and route tokens | `domain` or `policies` | none internal | **yes** | none | unit | 1 | 3 | 1 | 5 | wide fan-in contract; accidental constants drift | `tests/` route token/intent mapping checks | freeze as stable contract module |
| `answer_validation.py` | semantic/provenance validation checks | `logic` | `answer_assembly`, `pipeline_state` | **partial/no** | none direct | unit | 2 | 2 | 1 | 5 | validation depends on assembly shape | `tests/` validation behavior checks | define validation input DTO and decouple assembly internals |
| `canonical_turn_orchestrator.py` | turn-stage orchestration wrapper | `application` | `pipeline_state` | **yes** | none | service | 1 | 1 | 1 | 3 | thin now; risk of future bloating | `tests/` orchestrator service checks | keep thin and enforce boundary tests |

### Executed census pass — extended scope

The following table extends the executed census beyond `src/testbot/*.py` as an explicit inventory. These rows are **not** used for P-band priority unless they are scored at file-level granularity.

| component | current_role | target_module | depends_on | dep_direction_ok | external_systems | test_tier | coupling | blast | test_cost | score | boundary_risk | current_test_locations | migration_action |
| --- | --- | --- | --- | --- | --- | --- | ---:| ---:| ---:| ---:| --- | --- | --- |
| `src/testbot/pipeline/*.py` | pipeline stage orchestration, telemetry flow, and stage contracts | `application` + `observability` + `logic` | `pipeline_state`, runtime orchestration modules, metrics emitters | **pending (not file-scored yet)** | filesystem/runtime metrics sinks | service/integration | — | — | — | **TBD** | cannot claim risk rank until per-file evidence is scored | `tests/pipeline/`, `tests/architecture/` | run file-level census for `src/testbot/pipeline/*.py`; do not include in P-bands until complete |
| `src/seem_bot/*.py` | adjacent runtime and cross-runtime integration surface | `entrypoints` + `application` + `adapters` | shared runtime conventions and integration boundaries with `testbot` | **pending (not file-scored yet)** | external runtime integrations (varies by module) | service/smoke | — | — | — | **TBD** | hidden cross-runtime coupling may exist but is not yet measured | `tests/seem_bot/`, `features/seem_bot/` | run companion file-level census and codify cross-runtime port contracts |
| `tests/architecture/` | architecture boundary enforcement and direction checks | `governance_tooling` + `tests` | import-boundary rules, package-map constraints | **yes** | none | unit/service | 1 | 3 | 1 | 5 | gaps between policy and enforceable checks | `tests/architecture/` | map each correspondence rule to deterministic test IDs |
| `tests/seem_bot/` | deterministic regression and behavior guardrails for seem_bot runtime | `tests` | seem_bot runtime modules and shared fixtures | **yes** | none | unit/service/integration | 1 | 2 | 2 | 5 | adjacent runtime changes can bypass pivot confidence signals | `tests/seem_bot/` | align test tiers and add runtime-parity markers where needed |
| `features/steps/` | BDD step implementations for stakeholder-visible behavior | `governance_tooling` + `tests` | runtime entrypoints, step helper adapters, fixtures | **partial/no** | filesystem/test harness | bdd | 2 | 3 | 2 | **7** | behavioral coverage can drift from module boundaries | `features/steps/` | add traceability from BDD scenarios to scoped pivot components |
| `scripts/` controls | readiness gate, issue/policy validators, quality control scripts | `governance_tooling` | repo metadata, test runners, issue/governance records | **yes** | filesystem/CLI/process execution | integration | 2 | 3 | 2 | **7** | controls are critical but not versioned as explicit control inventory | `scripts/all_green_gate.py`, `scripts/validate_*.py` | maintain controls register with owner, cadence, and output schema |
| `config/` | governance/runtime configuration and policy knobs | `policies` + `governance_tooling` | runtime modules, scripts, docs controls | **partial/no** | none direct | unit/integration | 2 | 2 | 2 | 6 | config drift can silently alter control behavior | `config/` | define config schema + ownership and validate in gate |
| `eval/` | evaluation fixtures and runtime parity evidence assets | `governance_tooling` + `tests` | eval harness, runtime outputs, scoring checks | **yes** | filesystem | integration | 1 | 2 | 2 | 5 | evaluation drift without explicit change controls | `eval/`, `tests/test_eval_runtime_parity.py` | add parity/eval manifest checks in canonical gate |
| `artifacts/` evidence outputs | generated gate/test/eval evidence and readiness artifacts | `governance_tooling` + `observability` | scripts/all_green_gate outputs, evaluation reports | **yes** | filesystem | integration/smoke | 1 | 3 | 1 | 5 | evidence format/version instability harms auditability | `artifacts/` | define authoritative artifact schema + retention/version rules |

### Key findings from completed pass

1. **Primary hotspot remains `sat_chatbot_memory_v2.py` (score 9).**
   - This is the clearest single-file architectural bottleneck and should be split first.
2. **Four P1 modules score 7 and are boundary-violating now:**
   - `pipeline_state.py`, `stabilization.py`, `evidence_retrieval.py`, `answer_commit.py`.
3. **Extended-scope inventory is now explicit, but `src/testbot/pipeline/*.py` is intentionally not risk-ranked yet.**
   - It is marked `score=TBD` until file-level census scoring is completed.
4. **Policy and validation are close to pure but still shape-coupled:**
   - `policy_decision.py`, `answer_validation.py` should consume stable DTOs rather than adapter/assembly shapes.
5. **Adapters exist but ports are not explicit enough:**
   - `vector_store.py` and `source_connectors.py` are identifiable adapters; they need corresponding formal ports.

---

## 3) Prioritized migration order (derived from census scores)

### P0 (score 8–9)

1. **Split `sat_chatbot_memory_v2.py` into:**
   - `entrypoints/chatbot_runtime.py` (argparse / runtime boot only),
   - `application/services/turn_service.py` (orchestration),
   - explicit adapter wiring module.
2. **`src/testbot/pipeline/*.py` (deferred P-band assignment):**
   - explicitly deferred until file-level coupling/blast/test_cost rows are produced; current surface-group inventory is not sufficient to prioritize as P0/P1.

### P1 (score 7)

2. **Extract pure domain from `pipeline_state.py`**
   - remove direct memory-implementation coupling.
3. **Split `stabilization.py`**
   - pure stabilizer logic vs storage-backed lookup helpers.
4. **Split `evidence_retrieval.py`**
   - retrieval decision logic vs provider-specific mapping.
5. **Refactor `answer_commit.py`**
   - keep commit persistence orchestration separate from rendering/validation assembly pipeline.

### P2 (score 5–6)

6. **Introduce typed policy input DTO** for `policy_decision.py` and `answer_validation.py`.
7. **Formalize ports** for ingest/retrieval/memory so adapter modules remain replaceable.

### P3 (<=4)

8. Keep low-risk thin orchestrators as-is, enforce with import-boundary checks.

---

## 4) Target package map (unchanged direction, now backed by findings)

```text
src/testbot/
  domain/
  logic/
    answer/
  policies/
  application/
    orchestrators/
    services/
  ports/
  adapters/
    memory/
    retrieval/
    llm/
    automation/
    notifications/
    artifacts/
  entrypoints/
  observability/
  runtime/
```

### Dependency direction policy (target)

- `domain` -> depends on nothing else in `testbot`.
- `logic` -> may depend on `domain` only.
- `policies` -> may depend on `domain` + `logic`.
- `application` -> may depend on `domain` + `logic` + `policies` + `ports`.
- `ports` -> interfaces only; never import adapters.
- `adapters` -> implement ports; never import entrypoints.
- `entrypoints` -> boot + wiring only.
- `observability` -> telemetry only, no decision ownership.

---

## 5) Pytest boundary proposal (now tied to scored components)

```text
tests/
  unit/
    domain/
    logic/
    policies/
  service/
    application/
  integration/
    adapters/
    ports_contracts/
  smoke/
    entrypoints/
```

Boundary rules:

1. P0/P1 modules must gain or retain deterministic tests before moves.
2. Any module marked `dep_direction_ok=no` must have a refactor test proving decoupling before relocation.
3. Adapter tests validate concrete backend behavior; service tests run only with fakes.
4. BDD remains canonical for stakeholder-visible behavior.

---

## 6) Concrete deliverables for next PRs (non-circular)

1. **`ISSUE-0013-A`**: split `sat_chatbot_memory_v2.py` into thin entrypoint + turn service wiring.
2. **`ISSUE-0013-B`**: extract `PipelineState` pure domain model from memory coupling.
3. **`ISSUE-0013-C`**: split stabilization/retrieval into pure logic + port-backed adapters.
4. **`ISSUE-0013-D`**: add ports (`MemoryRepository`, `VectorStore`, `LanguageModel`, `SourceConnector`) and contract tests.
5. **`ISSUE-0013-E`**: add import-boundary checks enforcing dependency direction.

### Pivot deliverables checklist

- [ ] **`ISSUE-0013-E` complete**: dependency contracts are CI-enforced with owners, failure semantics, and readiness-blocking behavior documented.

## 6.D) Port extraction done criteria (`ISSUE-0013-D`)

This section defines the completion criteria for each boundary extracted under **`ISSUE-0013-D`**.

### Required port characteristics (`src/testbot/ports/`)

Each new port must be represented as a `typing.Protocol` interface with stable DTO contracts at the boundary:

- `MemoryRepository`
- `VectorStore`
- `LanguageModel`
- `SourceConnector`

Required properties per port:

1. **Protocol-first interface**
   - Declare behavior using `typing.Protocol` in `src/testbot/ports/`.
   - Keep protocols behavioral and dependency-light (no adapter imports).
2. **Stable DTO inputs/outputs**
   - Use explicit typed DTOs for method inputs/outputs.
   - Avoid leaking backend/provider-native objects across the port boundary.
3. **Deterministic contract shape**
   - Method signatures are versioned by intent and remain stable across adapter swaps.
   - Breaking DTO/signature changes require issue-linked migration notes and matching test updates.

### Boundary public API declaration rules

Boundary-facing modules must declare explicit public surfaces:

- Include `__all__` in each boundary-facing module/package.
- Export only intentionally supported symbols (protocols, DTOs, boundary errors, factory entrypoints as applicable).
- Avoid implicit wildcard exports and private symbol leakage as accidental API.

### Typed-package policy (`py.typed`)

For cross-module strict typing guarantees:

- Treat the package as typed and include/retain `py.typed` per PEP 561 policy.
- New boundary DTO/protocol modules must type-check under strict settings used by readiness checks.
- Port consumers/adapters must not degrade to untyped fallback at module boundaries.

### Port migration checklist template (per component)

Use this checklist for each migrated component touching a boundary contract:

- [ ] imports obey direction
- [ ] port protocol exists
- [ ] adapter implements protocol
- [ ] contract tests added under `tests/architecture` or `tests/*_contracts`

### Current P1/P2 hotspot cross-links

Apply this done-criteria section to the currently ranked hotspot modules during migration planning and review:

- `src/testbot/pipeline_state.py`
- `src/testbot/stabilization.py`
- `src/testbot/evidence_retrieval.py`
- `src/testbot/answer_commit.py`

This converts the pivot from abstract scaffolding into a scored, TestBot-specific reorganization backlog.

---

## 6.1) Dependency contracts (CI-enforced)

This section defines implementation-level dependency contracts and their explicit CI ownership as part of **`ISSUE-0013-E`**.

### Contract catalog

| Contract ID | Rule text | Source module(s) | Forbidden / allowed module(s) | CI job owner |
| --- | --- | --- | --- | --- |
| `CR-001` | `domain` must remain pure and cannot import orchestration or infrastructure layers. | `src/testbot/domain/**` | **Forbidden:** `application`, `adapters`, `entrypoints`, `observability`, `runtime`. **Allowed:** standard library + intra-`domain` only. | Architecture Owners (`ci-architecture-boundaries`) |
| `CR-002` | `logic` may depend on `domain` only (plus stdlib); cross-layer imports are prohibited. | `src/testbot/logic/**` | **Forbidden:** `application`, `adapters`, `entrypoints`, `observability`, `runtime`, `policies` (unless explicitly promoted). **Allowed:** `domain` + intra-`logic`. | Runtime Platform (`ci-architecture-boundaries`) |
| `CR-003` | `scripts` may import only documented public package entrypoints and governance helpers. | `scripts/**` | **Forbidden:** internal deep imports such as `src/testbot/**` private modules. **Allowed:** public package entrypoints (`testbot.entrypoints.*`, CLI-facing APIs), `scripts/*` helpers, stdlib/approved tooling libs. | DevEx / Release Engineering (`ci-readiness-gate`) |

### Explicit contract examples

1. **Domain isolation contract**  
   `domain` is forbidden from depending on both `adapters` and `application` (enforced by `CR-001`).
2. **Logic narrowing contract**  
   `logic` only depends on `domain` (and stdlib), with all other module dependencies rejected (`CR-002`).
3. **Scripts public-surface contract**  
   `scripts` are restricted to public package entrypoints rather than private/internal module paths (`CR-003`).

### Intended CI enforcement points

- **Import graph contracts (`import-linter`)**  
  Define and version the contracts in either:
  - repository root `.importlinter`, or
  - `pyproject.toml` `[tool.importlinter]` section.
- **Lint/type boundary checks**
  - `ruff` import rules to forbid illegal cross-layer imports (including scripts deep-import violations).
  - `mypy` strict boundary checks to ensure typed interfaces align with allowed dependency directions.
- **Readiness gate integration**
  - wire contract checks into `python scripts/all_green_gate.py` so boundary validation is part of canonical readiness evidence.

### Failure semantics

- Any dependency contract violation is classified as a **defect**, not advisory debt.
- A violation **fails CI** for the owning boundary job and **blocks readiness/merge** until resolved or formally re-baselined via approved issue workflow.
- Contract waivers, if ever granted, must be time-boxed and tracked under **`ISSUE-0013-E`** with explicit owner and expiry.

---

## 6.2) `scripts/` boundary rules and allowed import surfaces

This subsection operationalizes `CR-003` as an explicit scripts boundary contract.

### Scripts import-surface policy table

| Script path pattern | Allowed package surface | Forbidden internal modules | Rationale |
| --- | --- | --- | --- |
| `scripts/all_green_gate.py` | `scripts.*` helper modules, `testbot.entrypoints.*` public CLI/runtime entrypoints, stdlib, approved dev tooling libs | `testbot.adapters.*`, `testbot.logic.*`, `testbot.application.*`, `testbot.pipeline.*`, direct imports from `src/testbot/**` implementation files | Canonical gate must validate behavior through public boundaries and remain stable when internals are reorganized. |
| `scripts/validate_*.py` | `scripts.*` shared validators, `testbot.entrypoints.*` (if needed), stdlib, approved tooling libs (`json`, `pathlib`, `subprocess`, etc.) | `testbot.adapters.*`, `testbot.runtime.*`, `testbot.observability.*`, any deep internal module not declared public API | Governance validators should not couple to runtime implementation details or storage adapters. |
| `scripts/eval_*.py` | Public evaluation-facing APIs (promoted package exports), `testbot.entrypoints.*`, stdlib, approved eval dependencies | `testbot.adapters.*`, `testbot.pipeline.*`, private utility modules imported only by file path conventions | Eval tooling must exercise supported public surfaces to preserve runtime/eval parity under refactors. |
| `scripts/*.py` (default catch-all) | `python -m`-resolvable package entrypoints, `scripts.*` helpers, stdlib, approved third-party CLI libs | Any deep import below allowed surfaces; all `testbot.adapters.*` imports unless explicit whitelist is documented under `CR-003` waiver metadata | Keeps scripts as thin orchestration/control-plane code, not alternate runtime entrypoints. |

### Allowed execution model (normative)

1. **Prefer module execution via package entrypoints:** use `python -m testbot.<entrypoint>` when invoking runtime behavior from scripts.
2. **Prohibit `sys.path` manipulation for internal imports:** scripts must not mutate `sys.path` to reach internal modules.
3. **Prefer explicit public API imports:** if direct imports are needed, import from documented public package surfaces only.

### Deep-import contract rule (`CR-003-S1`)

- `scripts/*` **must not import deep internal modules**, including `testbot.adapters.*`, `testbot.application.*`, `testbot.logic.*`, and `testbot.pipeline.*`.
- Exception path: only explicitly whitelisted modules are allowed, and each whitelist entry must include:
  - an issue reference,
  - an owner,
  - an expiry date,
  - and a migration removal plan.
- Any unapproved deep import is treated as a contract violation and is readiness-blocking under the canonical gate.

### Planned verification hooks in canonical gate

`python scripts/all_green_gate.py` should include scripted boundary verification checks, initially as optional/staged checks and then promoted to mandatory readiness blockers.

Planned hook sequence:

1. **`scripts_surface_check` (optional mode initially):** detect deep imports from `scripts/*.py` into disallowed `testbot.*` internals.
2. **`scripts_sys_path_check` (optional mode initially):** detect `sys.path` mutation patterns used for internal import reach-through.
3. **`scripts_entrypoint_execution_check` (optional mode initially):** verify runtime invocation patterns prefer `python -m testbot.<entrypoint>`.

Promotion policy:

- Stage 1: report-only in optional mode (`--continue-on-failure` and/or JSON summary output).
- Stage 2: warning-class failures in default mode.
- Stage 3: hard-fail readiness blockers in default mode once migration notes below are closed.

### Migration notes for existing scripts (current known violations)

1. **`sys.path` manipulation currently present and must be removed**
   - `scripts/all_green_gate.py`
   - `scripts/validate_issue_links.py`
   - `scripts/validate_issues.py`
   - Migration target: package the shared helper surface so these scripts can import without `sys.path.insert(...)`.
2. **Deep runtime module imports currently present and should be promoted or wrapped**
   - `scripts/aggregate_turn_analytics.py` imports `testbot.turn_analytics_diagnostics`.
   - `scripts/eval_recall.py` imports `testbot.eval_fixtures`, `testbot.rerank`, and `testbot.time_parse`.
   - Migration target: promote stable evaluation/analytics entrypoints (or a narrow public API module) and switch scripts to those surfaces.
3. **Temporary compatibility path**
   - Existing violating scripts may run behind staged checks while migration PRs land.
   - Each temporary allowance must be explicitly tracked under `ISSUE-0013-E` sub-items with owner + expiry.

## 7) Scope gap analysis: what is currently out of scope of this pivot

The executed census in Section 2 now includes the primary runtime/governance-critical surfaces. Remaining scope gaps are implementation-depth gaps (traceability, control formalization), not directory omissions. Current scope is effectively:

- selected flat modules in `src/testbot/*.py` (primarily turn pipeline runtime hotspots),
- extended architecture/governance surfaces (`src/testbot/pipeline`, `src/seem_bot`, `tests/architecture`, `tests/seem_bot`, `features/steps`, `scripts`, `config`, `eval`, `artifacts`),
- migration direction for package targets,
- boundary-test proposal tied to those hotspots.

### Scope coverage summary (authoritative)

| Granularity class | Count | Interpretation |
| --- | ---:| --- |
| Individually file-scored components | 12 | These rows have explicit coupling/blast/test_cost evidence and can be ranked into P0/P1/P2/P3. |
| Surface-group inventory rows | 9 | These rows establish scope inclusion only; they are not equivalent to file-level risk evidence. |
| Surface groups with deferred score (`TBD`) | 2 | `src/testbot/pipeline/*.py`, `src/seem_bot/*.py` require file-level census before priority ranking. |
| **Total entries in Section 2 census** | **21** | Mixed granularity by design; only file-scored rows drive migration priority. |

The table above is the fixed review anchor for future deltas. Keep the title string exact (`Scope coverage summary (authoritative)`) so diffs remain searchable across revisions.

The following repository areas are in scope but still need deeper control-definition detail for the pivot to be complete and auditable.

Scope-decision application note: each surface-group inventory row above is in scope because it satisfies at least one rule in the Section 7 decision criteria (runtime coupling, readiness controls, governance records, or evaluation/evidence role).

| In-scope path needing deeper definition | Why scope inclusion is now explicit | Why additional depth is still needed | Next hardening action |
| --- | --- | --- | --- |
| `src/testbot/pipeline/` | Included as an extended-scope census surface. | Stage-level module granularity still needs per-file rows. | Add per-module rows and explicit dependency-direction checks by file. |
| `src/seem_bot/` | Included as cross-runtime census surface. | Cross-runtime contract boundaries are still implicit. | Define explicit ports/contracts and ownership at package boundary. |
| `tests/architecture/` and `tests/seem_bot/` | Included as scored evidence surfaces. | Tier mapping and gap inventory are not yet complete. | Publish tier map and missing-test backlog tied to scored risks. |
| `features/steps/` | Included as stakeholder-behavior evidence surface. | Scenario→component traceability is not yet explicit. | Add traceability matrix from scenarios/steps to pivot components. |
| `scripts/` controls | Included as governance-control surface. | Control catalog and output schema are not yet formalized. | Create controls register (owner/cadence/input/output/failure mode). |
| `config/` | Included as governance/runtime control surface. | Schema and ownership controls remain underspecified. | Add schema validation + ownership metadata checks in gate. |
| `eval/` and `artifacts/` | Included as quality/evidence surfaces. | Artifact schema, versioning, and retention controls are still partial. | Define authoritative evidence schema and retention policy checks. |

### Scope decision rule for next pass

A directory must be in pivot scope if **any** of the following are true:

1. It contains runtime code with coupling into turn execution.
2. It provides gate/check logic used as readiness evidence.
3. It contains policy, invariants, or issue/governance records that justify controls.
4. It stores evaluation fixtures or generated evidence used to assert quality/trustworthiness.

---

## 8) Mandatory controls assessment against applicable standards

This section extends the pivot from module decomposition to control completeness. Status values:

- **Implemented**: control exists and has an obvious enforcing artifact.
- **Partial**: control exists but lacks full scope, structure, or auditable output.
- **Missing**: no explicit control artifact found in current pivot/governance flow.

| Standard | Mandatory control theme | Current status | Evidence anchor (current repo) | Gap to close in pivot |
| --- | --- | --- | --- | --- |
| ISO/IEC 25010:2023 | Quality scoring must trace to maintainability/testability characteristics. | **Partial** | Current census scoring in this document, Sections 0–3. | Add explicit per-component mapping fields: `modularity`, `modifiability`, `analyzability`, `testability` and keep score derivation reproducible. |
| ISO/IEC/IEEE 42010:2022 | Architecture correspondence rules with verifiable constraints and stakeholder concerns. | **Partial** | Dependency direction policy in Section 4; CI enforcement intent in Section 6E. | Add stakeholder/concern/viewpoint table and correspondence-rule IDs tied to concrete import-boundary tests. |
| NIST AI RMF 1.0 | MAP/MEASURE/MANAGE controls for AI context, trustworthiness, and monitoring. | **Partial** | Existing invariants/directives and gate scripts are present but not RMF-tagged. | Add AI system context profile (inputs, model behavior, failure modes) and map invariants/gates to RMF functions with owners and cadence. |
| ISO/IEC 42001:2023 | AIMS lifecycle: policy, risk assessment, operational controls, monitoring, continual improvement, supplier oversight. | **Partial** | Governance docs and issue workflow exist; separation direction exists in this pivot. | Publish an AIMS crosswalk linking current docs to 42001 clauses, identify missing artifacts (formal risk register, supplier oversight checklist, management review log). |
| ISO/IEC/IEEE 29119 | Test process + auditable test completion evidence/reporting. | **Partial** | Canonical gate script and testing docs define checks and pass/fail operation. | Emit structured completion report artifact (objectives, deviations, recommendation, pass/fail rationale) per gate run. |

### P0/P1 baseline: current test locations (from executed census)

| Component | Priority band | current_test_locations |
| --- | --- | --- |
| `sat_chatbot_memory_v2.py` | P0 | `features/` runtime scenarios; `tests/` entrypoint/orchestration regressions |
| `pipeline_state.py` | P1 | `tests/` state/parity checks; `features/steps/` turn-state assertions |
| `stabilization.py` | P1 | `tests/` stabilization and runtime-path checks |
| `evidence_retrieval.py` | P1 | `tests/` retrieval and runtime-parity checks |
| `answer_commit.py` | P1 | `tests/` answer pipeline regressions; `features/steps/` provenance steps |

### Additional mandatory controls to add to pivot backlog

1. **Architecture correspondence control set (42010):**
   - Define rule IDs (e.g., `CR-001 domain_no_internal_deps`) and map each to specific automated checks.
2. **AI system context and trustworthiness profile (NIST AI RMF MAP):**
   - Document TestBot boundaries, data categories, model providers, and high-priority trustworthiness characteristics.
3. **AIMS crosswalk package (42001):**
   - Build policy→risk→control→monitoring→improvement matrix, with named owners and review cadence.
4. **Test completion evidence schema (29119-3):**
   - Extend gate output to include objective coverage, deviations, blocker summary, and release recommendation.
5. **Supplier oversight controls (42001 + RMF MANAGE):**
   - Add explicit dependency risk controls for Ollama, Elasticsearch, and Home Assistant adapters/ports.

### Recommended issue slicing to bring out-of-scope assets into scope

- **`ISSUE-0013-F`**: full repository scope census (`src/testbot/pipeline`, `src/seem_bot`, tests/features alignment).
- **`ISSUE-0013-G`**: architecture correspondence rule catalog + import-boundary enforcement mapping.
- **`ISSUE-0013-H`**: AI RMF/42001 governance crosswalk and supplier oversight controls.
- **`ISSUE-0013-I`**: 29119-compatible gate completion report artifact and artifact-retention policy.

These additions keep the current pivot direction intact while making scope, controls, and audit evidence explicit.

## 9) Readiness evidence contract

This section defines the mandatory evidence artifact contract for every canonical readiness gate execution (`python scripts/all_green_gate.py`). The contract is normative for implementers and reviewers and is intended to remove ambiguity in audit trails and issue closure decisions.

### 9.1 Mandatory artifact fields for each gate run

Every gate run must emit one machine-readable JSON artifact containing, at minimum, the following top-level fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `schema_version` | string | yes | Artifact schema version (for compatibility and migration). |
| `artifact_type` | string | yes | Must be `readiness_evidence`. |
| `gate_profile` | string | yes | Gate mode/profile executed (for example `default`, `continue_on_failure`, or other named profile). |
| `generated_at_utc` | string (ISO 8601) | yes | UTC generation timestamp. |
| `repository` | object | yes | Repository identity and revision context (see nested fields). |
| `checks` | array | yes | Ordered list of checks executed in the run. |
| `summary` | object | yes | Aggregate pass/fail counts and final recommendation. |
| `blocked_by_rule_ids` | array[string] | yes | Unique rule/control IDs currently blocking readiness (empty array if none). |
| `issue_links` | array[string] | yes | Issue IDs or canonical issue URIs associated with this run/release decision. |
| `traceability` | object | yes | Mapping to release/closure context and evidence lineage. |

Required nested fields:

- `repository.commit_sha` (full Git commit SHA evaluated by the gate),
- `repository.branch` (branch name at run time),
- `checks[*].check_id` (stable ID),
- `checks[*].description`,
- `checks[*].status` (`pass` / `fail` / `skip` / `blocked`),
- `checks[*].duration_ms`,
- `checks[*].evidence_refs` (paths/URIs to detailed outputs where applicable),
- `summary.final_status` (`pass` or `fail`),
- `summary.total_checks`, `summary.passed`, `summary.failed`, `summary.skipped`, `summary.blocked`,
- `traceability.related_issue_ids`,
- `traceability.closure_decision` (`ready`, `not_ready`, or `conditional`),
- `traceability.supersedes_artifact_ids` (if replacing prior evidence).

### 9.2 Storage location, naming, and versioning under `artifacts/`

Evidence artifacts are stored under the repository-local evidence tree:

- Root: `artifacts/readiness/`
- Per-run path pattern: `artifacts/readiness/YYYY/MM/DD/<gate_profile>/<timestamp>_<short_sha>.json`
- Optional stable pointer for latest run by profile: `artifacts/readiness/latest_<gate_profile>.json` (copy, not move)

Versioning requirements:

1. `schema_version` follows semantic versioning (`MAJOR.MINOR.PATCH`).
2. Backward-incompatible changes require MAJOR bump and migration note in the linked issue record.
3. New additive fields require MINOR bump.
4. Editorial/non-structural clarifications require PATCH bump.
5. Gate implementations must reject unknown major versions unless an explicit compatibility adapter exists.

### 9.3 Retention and traceability requirements

Retention minimums:

1. Keep all readiness evidence artifacts for **at least 18 months** from `generated_at_utc`.
2. Keep all artifacts linked to open issues or red-tag incidents until issue closure + 18 months, whichever is later.
3. Do not delete artifacts referenced by release notes, post-incident reports, or governance review records.

Traceability rules:

1. Each issue closure record must reference at least one evidence artifact ID/path proving the closure decision.
2. Each evidence artifact must include `traceability.related_issue_ids` for issues it supports.
3. If a new run supersedes a prior failure/conditional run, record prior IDs in `traceability.supersedes_artifact_ids`.
4. Release/readiness decisions must be reconstructable from (`commit_sha`, `issue_links`, `blocked_by_rule_ids`, `summary.final_status`).

### 9.4 Standards-claim mapping for artifact fields

The following mapping connects required fields to standards claims already listed in Section 8:

| Artifact field(s) | Standards claim supported | Rationale |
| --- | --- | --- |
| `checks[*]`, `summary.*`, `blocked_by_rule_ids` | ISO/IEC/IEEE 29119 | Provides auditable test/gate completion evidence and explicit pass/fail/block rationale. |
| `gate_profile`, `checks[*].check_id`, `blocked_by_rule_ids` | ISO/IEC/IEEE 42010 | Supports correspondence-rule traceability and verifiable architecture/control constraint enforcement. |
| `summary.*`, `checks[*].status`, `traceability.closure_decision` | ISO/IEC 25010 | Preserves quality-characteristic evidence needed for maintainability/testability readiness judgments. |
| `issue_links`, `traceability.related_issue_ids`, `traceability.supersedes_artifact_ids` | ISO/IEC 42001 | Enables lifecycle governance, operational control tracking, and continual-improvement history. |
| `generated_at_utc`, `repository.commit_sha`, `checks[*].evidence_refs`, `blocked_by_rule_ids` | NIST AI RMF 1.0 | Supports MEASURE/MANAGE monitoring provenance and accountable decision records over time. |

### 9.5 Example minimal JSON schema (implementation baseline)

```json
{
  "schema_version": "1.0.0",
  "artifact_type": "readiness_evidence",
  "artifact_id": "readiness-2026-03-18T12:34:56Z-a1b2c3d",
  "gate_profile": "default",
  "generated_at_utc": "2026-03-18T12:34:56Z",
  "repository": {
    "name": "TestBot",
    "branch": "feature/example",
    "commit_sha": "a1b2c3d4e5f678901234567890abcdef12345678"
  },
  "checks": [
    {
      "check_id": "gate.behave",
      "description": "BDD behavioral suite",
      "status": "pass",
      "duration_ms": 12450,
      "evidence_refs": [
        "artifacts/test/behave-2026-03-18.log"
      ]
    }
  ],
  "summary": {
    "total_checks": 1,
    "passed": 1,
    "failed": 0,
    "skipped": 0,
    "blocked": 0,
    "final_status": "pass"
  },
  "blocked_by_rule_ids": [],
  "issue_links": [
    "ISSUE-0013-I"
  ],
  "traceability": {
    "related_issue_ids": [
      "ISSUE-0013-I"
    ],
    "closure_decision": "ready",
    "supersedes_artifact_ids": []
  }
}
```
