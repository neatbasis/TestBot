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
| `migration_action` | Minimal next step | `label-only`, `extract port`, `move pure logic`, `split adapter`, `thin entrypoint` |
| `owner` | Responsible team/person | Use real owner alias |
| `issue_link` | Tracking issue | `ISSUE-XXXX` |

---

## 2) **Executed census pass** (current modules)

> Note: "depends_on" summarizes significant internal dependencies, not every single import.

| component | current_role | target_module | depends_on | dep_direction_ok | external_systems | test_tier | coupling | blast | test_cost | score | boundary_risk | migration_action |
| --- | --- | --- | --- | --- | --- | --- | ---:| ---:| ---:| ---:| --- | --- |
| `sat_chatbot_memory_v2.py` | monolithic runtime entrypoint + orchestration + infra wiring | `entrypoints` (+ composition root) | ~32 internal modules across pipeline/policy/storage/rendering | **no** | home_assistant (`ha_ask`), llm/runtime libs, filesystem/runtime | smoke/service | 3 | 3 | 3 | **9** | orchestration bloat + infra leakage | split into thin entrypoint + app service wiring |
| `pipeline_state.py` | canonical turn state and cross-stage data contract | `domain` | currently imports `memory_cards` | **no** | filesystem/json helpers | unit | 2 | 3 | 2 | **7** | domain depending on memory infra shape | extract pure state model from memory adapter concerns |
| `stabilization.py` | pre-route stabilization and candidate/durable fact handling | `logic` | `candidate_encoding`, `pipeline_state`, `memory_cards`, `vector_store` | **no** | vector/memory infra via `vector_store` | unit/service | 3 | 2 | 2 | **7** | logic layer coupled to adapter/storage | split pure stabilizer from store-backed lookup |
| `evidence_retrieval.py` | retrieval-stage evidence assembly for pipeline | `logic` + `ports` | `pipeline_state`, `stabilization` (+ `langchain_core`) | **no** | embedding/document infra (`langchain_core`) | service | 3 | 2 | 2 | **7** | retrieval policy mixed with provider types | add retrieval port + adapter DTO mapper |
| `answer_commit.py` | answer commit orchestration and provenance write-through | `application` | `answer_assembly`, `answer_rendering`, `answer_validation`, `pipeline_state` | **no** | persistence/runtime side effects | service | 2 | 2 | 3 | **7** | commit orchestration mixed with rendering/validation pipeline | separate commit service from answer formatting/validation |
| `policy_decision.py` | action-class decisioning from intent/evidence | `policies` | `intent_router`, `retrieval_routing`, `evidence_retrieval` | **partial/no** | none direct | unit | 2 | 2 | 2 | 6 | policy coupled to retrieval structures | move policy inputs to normalized domain DTO |
| `source_ingest.py` | source ingestion workflow and store writes | `application` + `adapters` | `source_connectors`, `vector_store` | **no** | connectors + vector persistence | integration/service | 2 | 1 | 3 | 6 | use-case orchestration fused with adapter calls | introduce ingest service + connector/store ports |
| `vector_store.py` | concrete vector + memory backend access | `adapters` | none internal | **yes** | `elasticsearch`, `langchain_core` | integration | 1 | 2 | 3 | 6 | backend-specific data contracts leaking upward | keep adapter, expose protocol in `ports/` |
| `source_connectors.py` | concrete source connector loading/normalization | `adapters` | none internal | **yes** | dynamic loading/filesystem/importlib | integration | 2 | 1 | 2 | 5 | dynamic connector behavior hard to contract-test | define connector contract tests per connector type |
| `intent_router.py` | intent enums/routes and route tokens | `domain` or `policies` | none internal | **yes** | none | unit | 1 | 3 | 1 | 5 | wide fan-in contract; accidental constants drift | freeze as stable contract module |
| `answer_validation.py` | semantic/provenance validation checks | `logic` | `answer_assembly`, `pipeline_state` | **partial/no** | none direct | unit | 2 | 2 | 1 | 5 | validation depends on assembly shape | define validation input DTO and decouple assembly internals |
| `canonical_turn_orchestrator.py` | turn-stage orchestration wrapper | `application` | `pipeline_state` | **yes** | none | service | 1 | 1 | 1 | 3 | thin now; risk of future bloating | keep thin and enforce boundary tests |

### Key findings from completed pass

1. **Primary hotspot is `sat_chatbot_memory_v2.py` (score 9).**
   - This is the clearest single-file architectural bottleneck and should be split first.
2. **Four P1 modules score 7 and are boundary-violating now:**
   - `pipeline_state.py`, `stabilization.py`, `evidence_retrieval.py`, `answer_commit.py`.
3. **Policy and validation are close to pure but still shape-coupled:**
   - `policy_decision.py`, `answer_validation.py` should consume stable DTOs rather than adapter/assembly shapes.
4. **Adapters exist but ports are not explicit enough:**
   - `vector_store.py` and `source_connectors.py` are identifiable adapters; they need corresponding formal ports.

---

## 3) Prioritized migration order (derived from census scores)

### P0 (score 8–9)

1. **Split `sat_chatbot_memory_v2.py` into:**
   - `entrypoints/chatbot_runtime.py` (argparse / runtime boot only),
   - `application/services/turn_service.py` (orchestration),
   - explicit adapter wiring module.

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

This converts the pivot from abstract scaffolding into a scored, TestBot-specific reorganization backlog.
