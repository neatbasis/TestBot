# System Structure Audit — 2026-03-19 (Amended)

## Executive summary

The prior audit correctly identified `sat_chatbot_memory_v2.py` as a major authority concentration point, but it understated the breadth and exact collapse mechanics.

This amended audit makes the authority census explicit, identifies concrete API-risk symbols, and defines a receiver-first extraction protocol to avoid parallel implementations.

- **Primary collapse point:** `_run_canonical_turn_pipeline()` is a ~585-line orchestration function with 11 inline closures that close over runtime dependencies from the enclosing scope.
- **Secondary collapse points:** `answer_assemble()` and `evaluate_alignment_decision()` combine business logic and orchestration concerns in test-visible symbols.
- **Hidden coupling:** dict-shaped contracts (`confidence_decision`, `commit_receipt`, `candidate_facts`) are written/read across multiple domains without a typed interface.

## Scope and evidence basis

- Runtime code under `src/testbot/`.
- Existing enforcement tests/scripts under `tests/` and `scripts/`.
- Symbol census anchored to `src/testbot/sat_chatbot_memory_v2.py` (current line count: **4613** lines).

---

## 1) Authority census for `sat_chatbot_memory_v2.py`

The module currently spans at least seven authority domains:

| Domain | Approx lines | What it owns |
|---|---:|---|
| A. Boot / entrypoint | 4521–4613 | `main()`, arg/env parsing, mode dispatch |
| B. Infrastructure probing | 719–816 | HA/Ollama reachability and mode-effective checks |
| C. Capability snapshot | 487–515, 4478–4519 | `RuntimeCapabilityStatus`, `CapabilitySnapshot`, `build_capability_snapshot()` |
| D. Source ingestion lifecycle | 255–422 | execute/start/poll/process ingestion + obligation/dead-letter transitions |
| E. Canonical turn pipeline | 3571–4156 | `_run_canonical_turn_pipeline()` with 11 stage closures |
| F. Decision / alignment logic | ~1500–3568 | ambiguity/blocker reasoning, answer assembly/validation helpers, alignment scoring |
| G. Chat loop / I/O | 4158–4396 | chat loop and CLI/satellite runtime loops |

Additionally, the same module owns a telemetry sink (`append_session_log`), DTO mapper (`doc_to_candidate_hit`), diagnostics-only intent helper (`resolve_turn_intent`), and multiple constants/regex sets.

---

## 2) Real collapse point (specific)

### 2.1 `_run_canonical_turn_pipeline()` is the primary collapse

`_run_canonical_turn_pipeline()` defines all canonical stages inline (`_observe_turn` … `_answer_commit`) and instantiates `CanonicalTurnOrchestrator` inside the same function.

All stage closures close over shared outer-scope runtime dependencies (`llm`, `store`, `chat_history`, `prior_pipeline_state`, `utterance`, `runtime`, `clock`, `capability_snapshot`, etc.).

Practical impact:

1. Stage isolation testing is harder because individual stage callables are not first-class module symbols.
2. Stage replacement requires editing the monolithic orchestration function.
3. Composition authority lives in entrypoint runtime code instead of a dedicated application/service assembly boundary.

### 2.2 `answer_assemble()` is a secondary collapse

`answer_assemble()` is public and test-visible, while also blending routing/result formatting/LLM orchestration concerns that ideally belong to separated services.

### 2.3 `evaluate_alignment_decision()` is a third collapse

`evaluate_alignment_decision()` is pure scoring logic but currently co-located with entrypoint runtime concerns and module-level constants it implicitly owns.

---

## 3) Caller-facing implicit API surface (high-risk symbols)

The module acts as a de-facto API surface. Moving symbols without compatibility shims is high risk.

| Symbol | Role | Move risk |
|---|---|---|
| `append_session_log` | Telemetry sink | **High** |
| `run_canonical_answer_stage_flow` | Public turn runner | **High** |
| `run_answer_stage_flow` | Parallel public runner | **High** |
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

The module has multiple near-overlapping public runner entry points:

- `run_canonical_answer_stage_flow()`
- `run_answer_stage_flow()`
- `_run_full_canonical_turn_from_seeded_artifacts()`

These create synchronization risk during extraction/refactor if behavior is updated in one path but not the others.

There is also duplicated definitional-query form logic presence (local `_is_definitional_query_form` while also importing from `retrieval_routing`), which increases semantic drift risk.

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

### Step 2 — Resolve two-runner ambiguity

Formally define whether `run_answer_stage_flow` is deprecated alias vs distinct behavior. If alias, deprecate and delegate; if distinct, document contract differences.

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

Primary collapse is the **inline stage-closure orchestration pattern** in `_run_canonical_turn_pipeline()` within `sat_chatbot_memory_v2.py`, amplified by public multi-runner overlap and dict-convention semantic contracts.

In short: the system has strong canonical-order and validation enforcement, but architectural authority and semantic typing are still too centralized in one runtime module.
