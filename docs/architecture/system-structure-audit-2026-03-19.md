# System Structure Audit — 2026-03-19 (Amended)

## Executive summary

The prior audit correctly identified `sat_chatbot_memory_v2.py` as a major authority concentration point, but it understated the breadth and exact collapse mechanics.

This amended audit makes the authority census explicit, identifies concrete API-risk symbols, and defines a receiver-first extraction protocol to avoid parallel implementations.

- **Primary collapse point (historical framing + current state):** `sat_chatbot_memory_v2.py` has historically concentrated runtime authority; canonical stage execution now routes through `src/testbot/application/services/turn_service.py` using receiver-bound handlers (`_TurnPipelineStageHandlers`) rather than inline closures.
- **Secondary collapse points (historical framing):** `answer_assemble()` and the monolith-owned alignment symbol surface were historical collapse contributors; `evaluate_alignment_decision()` now remains in the monolith as a compatibility shim symbol.
- **Hidden coupling:** dict-shaped contracts (`confidence_decision`, `commit_receipt`, `candidate_facts`) are written/read across multiple domains without a typed interface.

## Scope and evidence basis

- Runtime code under `src/testbot/`.
- Existing enforcement tests/scripts under `tests/` and `scripts/`.
- **Historical snapshot (date-stamped 2026-03-19, pre-extraction baseline):** symbol census previously anchored to `src/testbot/sat_chatbot_memory_v2.py` at **4613** lines.
- **Current state (as of latest changelog in `docs/pivot.md`):** `src/testbot/sat_chatbot_memory_v2.py` is now **3806** lines, and package/CLI startup authority routes through `src/testbot/entrypoints/sat_cli.py::main(...)` with `sat_chatbot_memory_v2.main(...)` retained as a compatibility delegator.

---

## 1) Authority census for `sat_chatbot_memory_v2.py`

### 1.1 Historical snapshot (date-stamped, non-authoritative for current structure)

> **Historical snapshot date:** 2026-03-19 baseline captured at **4613 lines**.  
> **Status:** historical-only reference; the line ranges below are **not authoritative** for current file shape.

| Domain | Historical approx lines (4613-line file) | Historical ownership readout |
|---|---:|---|
| A. Boot / entrypoint | 4521–4613 | `main()`, arg/env parsing, mode dispatch |
| B. Infrastructure probing | 719–816 | HA/Ollama reachability and mode-effective checks |
| C. Capability snapshot | 487–515, 4478–4519 | `RuntimeCapabilityStatus`, `CapabilitySnapshot`, `build_capability_snapshot()` |
| D. Source ingestion lifecycle | 255–422 | execute/start/poll/process ingestion + obligation/dead-letter transitions |
| E. Canonical turn pipeline | 3571–4156 | `_run_canonical_turn_pipeline()` compatibility façade delegating to application turn service |
| F. Decision / alignment logic | ~1500–3568 | ambiguity/blocker reasoning, answer assembly/validation helpers, alignment scoring |
| G. Chat loop / I/O | 4158–4396 | chat loop and CLI/satellite runtime loops |

### 1.2 Current state (as of latest changelog)

> **Current reference date:** 2026-03-19 (latest changelog notes in `docs/pivot.md`).  
> **Current file shape:** `sat_chatbot_memory_v2.py` = **3806 lines**.

| Domain | Current anchor lines (3806-line file) | Current ownership readout |
|---|---:|---|
| A. Boot / compatibility entrypoint | 3799–3806 | `main(...)` is a compatibility delegator that forwards to `testbot.entrypoints.sat_cli:main` |
| B. Startup wiring helpers (compatibility surface) | 763–973 | `_parse_args`, `_read_runtime_env`, `_resolve_mode`, `_print_startup_status` exported for compatibility and consumed by `entrypoints/sat_cli.py` |
| C. Capability snapshot | 590–605, 3649–3698 | `RuntimeCapabilityStatus`, `CapabilitySnapshot`, `build_capability_snapshot(...)` |
| D. Source ingestion lifecycle | 961–972, 3704–3767 | `_run_source_ingestion(...)` and `run_source_ingestion(...)` |
| E. Canonical turn pipeline compatibility façade | 3272–3327 | `_run_canonical_turn_pipeline(...)` delegates to application canonical turn runtime/service |
| F. Decision / answer compatibility surface | 2434–3243 | `answer_assemble(...)`, canonical/deprecated answer-stage entrypoints, and alignment compatibility shim |
| G. Chat loop / I/O runtime loop wrappers | 3329–3647, 3770–3797 | `_run_chat_loop`, `_run_cli_mode`, `_run_satellite_mode`, `run_chat_loop(...)` |

Additionally, the module still owns cross-cutting compatibility symbols (for example `append_session_log`, `doc_to_candidate_hit`, and `resolve_turn_intent`), so authority remains concentrated even after extracted service ownership.

---

## 2) Real collapse point (specific)

### 2.1 Current state (as of latest changelog): `_run_canonical_turn_pipeline()` remains an authority surface, but closure capture was reduced

`_run_canonical_turn_pipeline()` is still the monolith-owned compatibility entry, but canonical stage assembly/execution now lives in the application service (`run_canonical_turn_pipeline_service(...)`) with `_TurnPipelineStageHandlers(runtime=stage_runtime)` bound methods.

This removes the prior inline lambda/closure-capture pattern for canonical stage wiring while preserving a single runtime dependency receiver object.

Practical impact:

1. Composition authority is still split because runtime dependency construction remains monolith-owned, even though orchestration moved to the service layer.
2. Stage replacement is now easier in service-layer tests, but monolith behavior ownership remains substantial across retrieval/assembly/validation helpers.
3. Boot/runtime composition authority still lives in entrypoint runtime code instead of a dedicated thin composition root.

### 2.2 Historical snapshot + current state: `answer_assemble()` remains a secondary collapse

`answer_assemble()` is public and test-visible, while also blending routing/result formatting/LLM orchestration concerns that ideally belong to separated services.

### 2.3 Current state (as of latest changelog): `evaluate_alignment_decision()` lifecycle state (compatibility shim)

`evaluate_alignment_decision()` in `sat_chatbot_memory_v2.py` is currently a **compatibility shim** that delegates to `testbot.logic.alignment.evaluate_alignment_decision`.

The collapse characterization for this symbol is therefore primarily **historical** (when scoring ownership lived directly in the monolith), while current risk is compatibility-surface drift until alias retirement is complete.

---

## 3) Caller-facing implicit API surface (high-risk symbols)

The module acts as a de-facto API surface. Moving symbols without compatibility shims is high risk.

| Symbol | Role | Move risk |
|---|---|---|
| `append_session_log` | Telemetry sink | **High** |
| `run_canonical_answer_stage_flow` | Public turn runner | **High** |
| `run_answer_stage_flow` | Deprecated alias delegating to canonical runner | **Medium** |
| `answer_assemble` | Orchestration-heavy public helper | **High** |
| `build_capability_snapshot` | startup capability resolver | Medium |
| `resolve_turn_intent` | diagnostics/parity helper | Medium |
| `evaluate_alignment_decision` | scoring logic | Medium |
| `doc_to_candidate_hit` | DTO conversion | Low |

**Most dangerous symbol to move carelessly:** `append_session_log` because it is called across most runtime domains and is likely imported by tests/integration utilities.

---

## 4) Hidden coupling through dict-shaped semantic contracts

### 4.1 `confidence_decision`

The state field is represented by artifact-compatible mapping wrappers, but in runtime usage many keys are still dynamically extended and consumed by string key conventions across stages and diagnostics.

### 4.2 `commit_receipt`

Its semantic shape is authored in `answer_commit.py` but consumed by key lookups in runtime loop/context continuity paths without a dedicated typed receipt contract for readers.

### 4.3 `candidate_facts`

Population and reads cross multiple boundaries with convention-based keys (`facts`, `segment_id`, `turn_id`, constraints, etc.), rather than a single typed domain interface for all stage consumers.

---

## 5) Parallel-implementation trap (current evidence)

As of **2026-03-19**, canonical answer-stage execution authority is intentionally singular:

- `run_canonical_answer_stage_flow()`
- `run_answer_stage_flow()`

`run_answer_stage_flow()` currently emits a `DeprecationWarning` and directly delegates to `run_canonical_answer_stage_flow()`, so functional execution is centralized through the canonical symbol.

**As-of date + code evidence note (auditability):**
- `run_canonical_answer_stage_flow` is defined in `src/testbot/sat_chatbot_memory_v2.py` and routes seeded artifacts through `_run_canonical_turn_pipeline(...)` (which delegates into the canonical turn service).
- `run_answer_stage_flow` emits a deprecation warning and calls `run_canonical_answer_stage_flow(...)`.
- `_run_full_canonical_turn_from_seeded_artifacts(...)` has been removed to eliminate seeded-artifact runner overlap from runtime code.

Residual risk now comes primarily from import-surface drift (callers continuing to import deprecated compatibility aliases) and delayed alias retirement, rather than from duplicate active logic.

### 5.1 Compatibility entry-surface inventory + lifecycle state (as of 2026-03-19)

| Symbol surface (`sat_chatbot_memory_v2.py`) | Category | Lifecycle state | Removal target | Removal-ready criteria |
|---|---|---|---|---|
| `run_canonical_answer_stage_flow` | Canonical entrypoint | still present (authoritative) | n/a | n/a |
| `run_answer_stage_flow` | Deprecated compatibility alias (in `__all__`) | still present | 2026-04-01 | no internal callers + no non-compatibility-test imports remain |
| `evaluate_alignment_decision` | Deprecated alignment compatibility shim export (in `__all__`) | still present (delegates to canonical logic owner) | 2026-04-01 | all callers import canonical owner `testbot.logic.alignment.evaluate_alignment_decision`; shim passthrough tests only |
| `_answer_routing_from_decision_object` | Deprecated stage helper bridge (not in `__all__`) | still present | TBD (post decision-helper migration completion) | no in-repo callers outside shim tests |
| `_run_full_canonical_turn_from_seeded_artifacts` | Deprecated seeded helper | removed | removed 2026-03-19 | n/a |

### 5.2 Import drift enforcement added

Architecture boundary enforcement now includes a static AST check that fails when deprecated aliases (`run_answer_stage_flow`, `evaluate_alignment_decision`) are imported from `testbot.sat_chatbot_memory_v2` outside approved compatibility tests.

---

## 6) Receiver-first protocol required before deleting/moving logic

### Step 1 — Freeze API surface

Add explicit `__all__` in `sat_chatbot_memory_v2.py` (or successor module) to define stable exports and expose accidental internal imports.

#### Finalized export contract (implemented 2026-03-19)

`src/testbot/sat_chatbot_memory_v2.py` now declares an explicit stable export set via `__all__`.

- **Core runtime contracts:** `append_session_log`, `run_canonical_answer_stage_flow`, `run_answer_stage_flow`, `answer_assemble`, `build_capability_snapshot`, `resolve_turn_intent`.
- **Compatibility constants/types:** `RuntimeCapabilityStatus`, `CapabilitySnapshot`, `AnswerAssembleResult`, `AnswerValidateResult`, `FALLBACK_ANSWER`, `CLARIFY_ANSWER`, `DENY_ANSWER`, `ROUTE_TO_ASK_ANSWER`, `ASSIST_ALTERNATIVES_ANSWER`, `NON_KNOWLEDGE_UNCERTAINTY_ANSWER`.
- **Diagnostic/policy helpers intentionally stabilized as façades:** `parse_args`, `read_runtime_env`, `resolve_mode`, `print_startup_status`, `run_source_ingestion`, `run_chat_loop`, `resolve_answer_routing_from_decision_object`, `decision_object_from_assembled`, `build_debug_turn_payload`, `format_debug_turn_trace`, `format_debug_turn_trace_payload`, `ambiguity_score`, `user_followup_signal_proxy`, `derive_response_blocker_reason`, `intent_label`.
- **Additional existing public helpers preserved:** `stage_rewrite_query`, `stage_rerank`, `build_provenance_metadata`, `collect_used_source_evidence_refs`, `has_sufficient_context_confidence`, `has_required_memory_citation`, `raw_claim_like_text_detected`, `response_contains_claims`, `validate_answer_contract`, `generate_reflection_yaml`, `render_context`, `evaluate_alignment_decision`.

Tests that previously imported underscored helpers now consume these stable façade symbols.

### Step 2 — Complete alias removal timeline and import migration

`run_answer_stage_flow` is already a deprecated delegating alias to `run_canonical_answer_stage_flow`. The next step is to:

1. publish a removal target release/date for `run_answer_stage_flow`,
2. migrate all internal imports/callers to `run_canonical_answer_stage_flow`,
3. keep a temporary compatibility shim only until migration completion criteria are met.

Also remove duplicate definitional-query helper implementation by selecting one canonical owner.

### Step 3 — Type high-coupling contracts before extraction

Define typed contracts (`dataclass`/`TypedDict`) for:

- confidence decision payload
- commit receipt payload (reader-safe interface)
- candidate facts payload

Moving code before these receiver interfaces exist is the most likely way to recreate parallel implementations.

### Step 4 — Extract leaf-first in dependency order

Recommended order:

1. telemetry sink (`append_session_log`) to observability module + re-export shim
2. alignment scoring logic + constants to logic/policy module
3. stage closures to dedicated turn stage service module
4. `_run_canonical_turn_pipeline` to application turn service wrapper
5. source ingestion lifecycle to ingestion service with typed runtime state
6. startup probes to adapter module
7. capability snapshot builder/types to application module
8. keep entrypoint runtime thin (boot/wire/run)

---

## 7) Target shape after extraction

After extraction, the runtime entrypoint should be thin (~150–200 lines):

- parse args/env
- construct runtime dependencies
- resolve capability snapshot
- wire services (turn + ingestion)
- run loop

No alignment formulas, no stage closure definitions, and no decision policy internals should remain in entrypoint code.

---

## 8) CI contracts to add alongside extraction

Refactor safety should be enforced in CI as extraction occurs:

| Rule | Enforcement suggestion | Failure behavior |
|---|---|---|
| Layer import direction (`entrypoints`, `application`, `logic`, `adapters`) | import-linter | hard fail |
| Single canonical `append_session_log` owner | linter forbidden-import rule | hard fail |
| Stage functions independently unit-testable | pytest/unit gates | hard fail |
| Duplicate helper definitions forbidden | AST/static check | hard fail |

---

## 9) Distilled answer to the meta-question

> **Where does structure collapse into narrative?**

Primary collapse is now the **authority concentration** in `sat_chatbot_memory_v2.py` (boot wiring + substantial behavior helpers + compatibility surface), amplified by dict-convention semantic contracts and incomplete boundary enforcement.

In short: the system has strong canonical-order and validation enforcement, but architectural authority and semantic typing are still too centralized in one runtime module.

---

## 2026-03-19 update (current state as of latest changelog: entrypoint + service ownership hardening)

### Symbol moves
- Canonical stage-order authority is now explicitly declared in `src/testbot/application/services/turn_service.py` as `CANONICAL_STAGE_SEQUENCE` and consumed by handler wiring.
- Decision helper ownership moved from `src/testbot/sat_chatbot_memory_v2.py` to `src/testbot/logic/decision_helpers.py` for:
  - `selected_decision_from_confidence(...)`
  - `resolve_answer_routing_from_decision_object(...)`
  - `resolve_answer_routing_for_stage(...)`
  - fallback-action mapping used by `decision_object_from_assembled(...)`
- Canonical turn runner composition now delegates through `src/testbot/application/services/canonical_turn_runtime.py` (`run_canonical_turn_pipeline(...)`), leaving `_run_canonical_turn_pipeline(...)` in the monolith as a compatibility façade.
- Startup authority now uses **active path** `src/testbot/entrypoints/sat_cli.py::main(...)`; `sat_chatbot_memory_v2.main(...)` remains a compatibility delegator.

### Verified non-changes
- Canonical stage names/order contract remains `observe.turn -> ... -> answer.commit`.
- Public compatibility exports in `sat_chatbot_memory_v2.py` remain available; caller migration is incremental, not breaking.
- Session log schema version and commit receipt wire shape were not intentionally changed in this extraction step.
