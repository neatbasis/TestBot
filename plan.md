## Authoritative artifacts for current status (pivot)

In order of authority for **current status** during the pivot:

0. `docs/pivot.md`
1. `plan.md`
2. `docs/architecture/system-structure-audit-2026-03-19.md`
3. `docs/architecture/plan-execution-checklist.md`
4. `docs/qa/architecture-boundaries.json`
5. `artifacts/architecture-boundary-report.current.md`
6. `artifacts/architecture-boundary-report.current.json`

Additional pivot-thread and supporting artifacts in active use:

- `scripts/architecture_boundary_report.py`
- PR #587 remediation/report artifacts (second-pass remediation report)
- PR #588 remediation/report artifacts (`MemoryStorePort` boundary fix)
- PR #589 remediation/report artifacts (attempted shared contract ownership move)
- Compact/revised module census and target package map report
- Architecture Drift Register
- Canonical Turn Pipeline documentation
- `CHANGELOG.md` lifecycle/removal criteria entries for compatibility paths

To turn the concept into reality, you need to do four kinds of work in parallel:

1. **Make the pipeline real in code**
2. **Make the boundaries enforceable**
3. **Make the behavior testable and migration-safe**
4. **Make the governance/audit layer produce evidence, not just intention**

What you have now is already strong as a **target architecture and contract document**. The remaining work is mostly about converting each sentence from “should” into one of these forms:

* a typed data structure
* a function or stage boundary
* a deterministic test
* a CI-enforced rule
* a persisted artifact

## 1. The biggest shift: from implicit runtime behavior to explicit staged state

Right now, the document is saying the system must stop behaving like this:

```text
raw utterance → guess intent → do stuff
```

and start behaving like this:

```text
raw utterance → preserve observation → preserve alternatives → enrich with context → resolve intent → retrieve evidence → decide → assemble → validate → render → commit
```

That means the first real implementation burden is not “better classification.” It is **state architecture**.

You need a canonical `PipelineState` or equivalent staged state object that can carry:

* the raw utterance unchanged
* candidate encodings
* stabilized fact candidates
* context anchors
* pending repair obligations
* both classifier-only and resolved intent
* evidence with provenance
* policy decision object
* answer candidate
* validation results
* render artifact
* commit metadata

So the first concrete reality step is:

### A. Define the stage DTOs and invariants in code

You will need explicit types for at least:

* `TurnObservation`
* `CandidateEncodingSet`
* `PreRouteState`
* `ContextResolvedState`
* `IntentResolution`
* `EvidenceSet`
* `PolicyDecision`
* `AnswerCandidate`
* `ValidationResult`
* `RenderedResponse`
* `CommittedTurnState`

And these types need to preserve the distinctions your document relies on, especially:

* raw observation vs interpretation
* candidates vs resolved choice
* empty evidence vs zero-scored candidates
* validated answer vs degraded fallback
* rendered repair offer vs committed pending repair state

Without those type distinctions, the architecture will collapse back into informal dict-passing and ad hoc flags.

## 2. You need to split the current monolith by responsibility, not just by filename

Your census already identified this correctly. The hard part is not moving files into prettier folders. The hard part is **extracting authority**.

For example:

* `sat_chatbot_memory_v2.py` currently appears to own too much orchestration and wiring.
* `pipeline_state.py` is not pure enough.
* `stabilization.py` mixes logic with storage concerns.
* `evidence_retrieval.py` mixes retrieval policy with provider shapes.
* `answer_commit.py` mixes persistence flow with answer pipeline concerns.

So the actual work is to move from **mixed authority modules** to **single-purpose modules**.

### B. Refactor by ownership boundaries

That means creating a real package structure like:

* `domain/` for pure state objects, enums, DTOs, invariant-level concepts
* `logic/` for pure transformations
* `policies/` for decision rules
* `application/` for orchestration services
* `ports/` for protocol interfaces
* `adapters/` for Elasticsearch, Ollama, Home Assistant, filesystem, etc.
* `entrypoints/` for CLI/runtime boot
* `observability/` for telemetry only

The key is that each stage in the canonical pipeline must have a **clear implementation owner**.

For example:

* `observe.turn` should live in application/orchestration but emit a domain DTO
* `encode.candidates` should be pure logic if possible
* `stabilize.pre_route` should be split into pure extraction logic plus optional repository writes through a port
* `context.resolve` should read from committed state and pending obligations, not from adapter-specific storage shapes
* `intent.resolve` should consume only canonical state, not raw connector payloads
* `retrieve.evidence` should call a retrieval port and receive stable DTOs back
* `policy.decide` should operate on normalized inputs only
* `answer.validate` should never need to know Elasticsearch or LangChain types
* `answer.commit` should write via ports and persist the canonical next-turn state

That is a substantial refactor, because it is not cosmetic. It changes who is allowed to know what.

## 3. The intent system needs a two-layer model, not one classifier output

Your document already implies this with:

* `classified_intent`
* `resolved_intent`
* `intent` alias mirroring `resolved_intent`

This is important. To make it real, you need to separate:

### C. Intent signals from intent authority

That means implementing at least two stages of interpretation:

#### 1) Candidate / signal extraction

This is where you collect evidence like:

* looks like a command
* looks like self-identification
* looks like clarification response
* looks like memory recall
* looks like time query

These are not yet authoritative.

#### 2) Context-aware intent resolution

This is where you decide:

* given pending clarification, “Display name.” is a clarification response
* given pending repair offer, “What do you need?” is repair followup
* given prior stored user fact, “What’s my name?” is memory recall
* given no discourse anchor, a similar phrase might instead be meta-conversation or knowledge question

So the real work here is:

* build deterministic precedence rules
* implement facet validation
* reject invalid combinations
* persist both lower-precedence alternatives and final resolved intent
* ensure every downstream consumer reads from the same resolved state object

This is one of the most important anti-drift changes in the whole plan.

## 4. Pre-route stabilization is a real subsystem, not a helper function

This document is telling you that memory-worthy facts and discourse structure must be extracted **before** routing throws information away.

That means `stabilize.pre_route` is not just “save some stuff.” It is a **canonical preservation barrier**.

### D. Build stabilization as a first-class stage

It needs to do at least four things:

* create a memory-ready utterance record
* preserve fact candidates with provenance
* assign durable IDs
* retain alternative candidate interpretations without collapsing them

To achieve that, you likely need:

* a memory-card DTO or equivalent
* provenance references back to utterance span / turn ID / timestamp
* durable IDs for candidate facts and candidate discourse objects
* explicit distinction between “candidate fact” and “confirmed committed fact”

This stage is also where your current architecture is probably most tempted to cheat by directly calling vector-store-ish code. That is exactly what should be separated.

Pure stabilization logic should decide **what** should be preserved.
A port-backed repository adapter should decide **how** it is stored.

## 5. Context resolution requires a discourse-state model, not just chat history

A lot of systems say they use “context,” but really mean “previous messages.” Your document is asking for something stronger.

You want:

* pending repair mode
* unresolved obligations
* prior assistant-offer anchors
* active focus/anaphora anchors

That means you need an explicit **dialogue state / obligation state** model.

### E. Model unresolved conversational commitments

Examples:

* the assistant asked a clarification question and is waiting for a slot value
* the assistant offered a repair path and the user is now following up
* the assistant made an offer that established expected next-step semantics
* a pronoun or short reply attaches to an active focus object

To make that real, you need committed state representations for:

* `PendingClarification`
* `PendingRepair`
* `AssistantOfferAnchor`
* `FocusAnchor`
* `UnresolvedObligation`

And then `context.resolve` becomes a deterministic operation over canonical state rather than a fuzzy re-interpretation of chat history.

This is a major difference between a chatbot and a turn pipeline with discourse integrity.

## 6. Evidence retrieval must become contract-driven, not provider-driven

Your document says retrieval must be coherent with resolved intent and discourse context. That means retrieval can no longer be a generic “hit the store and get top-k.”

### F. Normalize retrieval around evidence classes

You need evidence DTOs that can represent at least:

* structured facts
* episodic utterances
* assistant offers
* reflections/anchors
* maybe external knowledge evidence

And retrieval must preserve the distinction between:

* no evidence source available
* evidence source available but no candidates
* candidates retrieved but below threshold
* sufficient evidence

That distinction matters because your validation and fallback logic depend on it.

You will likely need:

* retrieval query DTOs derived from resolved intent
* retrieval result DTOs independent of LangChain / Elasticsearch shapes
* explicit empty-state semantics
* provenance references from evidence back to committed state or sources

This is where ports matter most. The retrieval stage should not be contaminated by backend-native objects.

## 7. Policy and answer generation must be bound together by decision class

One of the strongest parts of your document is the insistence on **decision-answer alignment**.

This means you need a proper `PolicyDecision` object, not just a string label and some incidental behavior.

### G. Introduce a typed decision contract

A decision object should likely include:

* decision class
* rationale / triggering rule
* expected answer mode
* evidence sufficiency status
* fallback status
* repair/clarification continuation metadata
* maybe allowed rendering modes

Because then:

* `answer.assemble` can only construct within the decision class
* `answer.validate` can check alignment
* `answer.render` knows whether it is rendering a normal answer or degraded fallback
* `answer.commit` knows whether a pending repair state must be established

This is how you prevent “policy said clarify, renderer emitted confident answer” type bugs.

## 8. Validation is where the doctrine becomes enforceable

Without real validation, the pipeline is just elegant prose.

### H. Implement `answer.validate` as a gate, not a logger

It needs to reject or downgrade when:

* evidence is insufficient
* citations/provenance are missing where required
* decision class and answer class diverge
* discourse-state obligations are violated
* answer content claims exceed evidence

So you need:

* a `ValidationResult` type with explicit pass/fail/degraded semantics
* deterministic validation reason codes
* explicit degraded fallback artifact generation
* a hard rule that unvalidated semantic answer text is neither rendered nor committed

This is one of the most important practical controls in the whole system.

## 9. Commit semantics are as important as answer semantics

Many systems treat “save conversation state” as an afterthought. Your document correctly does not.

### I. Build `answer.commit` as authoritative state transition logic

It must persist:

* assistant utterance memory card
* provenance links
* pending repair state
* resolved/remaining obligations
* confirmed user facts

So commit is not just “append to memory.” It is the **state transition from S to S'**.

That means you need explicit commit rules for:

* when candidate facts become confirmed facts
* when repair mode becomes active
* when obligations are resolved vs carried forward
* when degraded fallback is committed as a fallback artifact only
* when failed semantic content must be discarded

This is a core architectural pillar, not an output side effect.

## 10. The work needs to be delivered in a migration order that reduces risk

Your priority ordering already points in the right direction. In practice, the safest sequence is:

### Phase 1: Create the canonical contracts without changing too much behavior

**Status (2026-03-19): Substantially started.** Typed DTOs were introduced, stage interfaces are partially defined, and compatibility shims exist. Remaining work is to complete the five semantic distinction types and type the remaining dict blobs.

* introduce typed DTOs and enums
* define canonical stage interfaces
* add `PolicyDecision`, `ValidationResult`, evidence DTOs
* add canonical `PipelineState` split from adapter concerns
* keep old orchestration working through shims if necessary

### Phase 2: Split orchestration and authority

**Status (2026-03-19): In progress.** `turn_service.py` and `canonical_turn_runtime.py` now carry canonical turn execution, and boot/wiring extraction has started through `src/testbot/entrypoints/sat_cli.py`. Remaining work is to shrink residual monolith authority in `sat_chatbot_memory_v2.py`, retire compatibility delegators on schedule, and complete typed replacement of dict-heavy contracts at stage boundaries.

* thin out `sat_chatbot_memory_v2.py`
* create `turn_service` or equivalent application orchestrator
* move boot/wiring to entrypoints
* make stages explicit and ordered

### Phase 3: Separate pure logic from ports/adapters

**Status (2026-03-19): Partially started.** Port protocols exist, but `Document` leakage remains in `evidence_retrieval.py`, and direct timestamp calls remain in runtime/connectors. Remaining work is to seal the `evidence_retrieval` boundary and audit all remaining direct backend imports between `intent.resolve` and `answer.commit`.

* extract memory, retrieval, model, connector protocols
* move Elasticsearch/LangChain/Home Assistant logic into adapters
* remove backend-native object leakage from logic/policy layers

### Phase 4: Enforce validation and commit semantics

**Status (2026-03-19): Partially started.** Hard validation gating exists in the canonical service path, but legacy paths remain unresolved. Remaining work is to eliminate or gate legacy paths and complete `answer_commit.py` decomposition with a tracked issue.

* add answer validation gate
* enforce degraded fallback only on failed validation
* implement pending repair and clarification commit behavior
* ensure failed semantic answers are not rendered/committed

### Phase 5: Enforce dependency direction and script boundaries

**Status (2026-03-19): Not started.** Import-linter configuration is not yet present.

* add import-linter / boundary tests
* remove deep imports and `sys.path` hacks
* promote public package surfaces for scripts and eval tooling

### Phase 6: Complete governance evidence

**Status (2026-03-19): In progress.** Verification manifest schema versioning is implemented (`VERIFICATION_MANIFEST_SCHEMA_VERSION = "1.0"`), but readiness-evidence closure is still incomplete at rule-ID/blocking, traceability metadata, and retention/versioning policy levels.

* readiness artifacts (full-field completeness)
* check/rule IDs and blocking semantics
* traceability to issue IDs/owners/check links
* retention/version policy completeness
* standards crosswalk as enforceable evidence (not prose-only intent)

That order minimizes the chance of reorganizing files before the contracts are strong enough.

## 11. The testing burden is large, but it is also what makes the architecture real

To make this real, the tests must stop checking just outputs and start checking **stage semantics**.

### J. You need three categories of tests

#### 1) Deterministic unit tests

For:

* candidate extraction
* precedence resolution
* facet legality
* evidence empty-state distinctions
* decision-answer alignment rules
* validation reason codes
* commit state transitions

#### 2) Service tests

For:

* canonical turn pipeline over fake ports
* repair followup continuation
* clarification slot resolution
* memory recall routing
* degraded fallback behavior
* provenance preservation

#### 3) BDD / stakeholder-visible tests

For the exact example traces A–G:

* self-identification
* memory recall
* repair offer followup
* clarification response
* general knowledge question
* control
* meta-conversation

Those example traces should become executable behavior contracts, not just documentation.

And you also need architecture tests for:

* import boundaries
* scripts deep-import prohibition
* public API surface declarations
* port contract compliance

## 12. The port work is broader than just adding `Protocol`s

Your document correctly asks for `typing.Protocol`, DTOs, `__all__`, `py.typed`, contract tests. That is good, but the real work is **semantic normalization**.

### K. Each port needs stable intent-shaped methods

For example, don’t expose backend-ish operations like:

* `similarity_search_with_score(...)`
* `langchain Document`
* raw Elasticsearch hits

Instead expose methods like:

* `fetch_user_fact_candidates(query: FactQuery) -> list[FactEvidence]`
* `fetch_episodic_turns(anchor: DialogueAnchorQuery) -> list[EpisodicEvidence]`
* `store_turn_observation(card: UtteranceCard) -> StoredReference`
* `store_confirmed_user_fact(fact: ConfirmedFact) -> StoredReference`

That is what prevents backend leakage upward.

So the real port work is partly interface design, partly ontology design.

## 13. The scripts/governance work is not optional overhead

Your document includes strong readiness evidence and standards alignment sections. To make those real, you need to treat governance artifacts as production outputs.

### L. Build the gate output as a real evidence product

That means `all_green_gate.py` or its replacement must emit structured artifacts with:

* schema version
* check IDs
* status
* durations
* evidence refs
* blocking rule IDs
* issue links
* traceability metadata

And the checks inside that gate need to include:

* dependency contract checks
* script boundary checks
* tests and BDD execution results
* maybe config schema validation
* maybe artifact schema validation

This is what turns the pivot into something auditable and reviewable rather than “the architecture is in our heads.”

## 14. The standards mapping work is mostly crosswalk and control inventory work

The standards sections do not require magic. They require disciplined mapping.

### M. For each standards claim, create a repo artifact that answers:

* what control exists
* where it is implemented
* who owns it
* how it is measured
* what evidence proves it ran
* how failures block readiness

For example:

* ISO 42010 → correspondence rules + architecture tests
* ISO 25010 → scoring dimensions + quality evidence
* ISO 29119 → structured gate completion artifacts
* NIST AI RMF → trustworthiness profile, monitoring, failure modes
* ISO 42001 → policy/risk/control/monitoring/improvement crosswalk, supplier oversight

This is mostly documentation plus evidence schema plus ownership mapping, but it matters because your system is explicitly trying to be accountable.

## 15. The hardest practical risks

There are a few places where this can fail even if the design is sound.

### Risk 1: Fake modularization

Files move, but authority and data leakage remain unchanged.

### Risk 2: DTO explosion without semantic clarity

You create many types, but they do not encode the distinctions the invariants require.

### Risk 3: Old runtime bypasses canonical stages

Some path still goes raw utterance → intent → answer.

### Risk 4: Validation becomes advisory

Failures are logged but invalid answers still render or commit.

### Risk 5: Port boundaries leak provider-native objects

Then the adapters are still infecting the logic layer.

### Risk 6: BDD and architecture diverge

Behavior tests say one thing; imports and runtime control surfaces say another.

### Risk 7: Changelog describes intent, not evidence

Entries record planned or partial work without clearly distinguishing “interface was defined” from “extraction complete and all callers updated.”  
**Guard:** every changelog entry must state the current patch/import target for each moved symbol, verified by grep rather than inspection of the new file alone.

Your own document is already aware of these risks. The implementation work must keep them front and center.

## 16. The minimum concrete backlog to make this real

If I compress the whole thing into the smallest serious implementation program, it looks like this:

### Workstream A — Canonical types and stage interfaces

**Current status (2026-03-19): Partial.** All eleven named stage DTO classes are present and key artifact boundaries are typed. Remaining obligations are concentrated in dict-heavy residual contracts (`reasoning` payloads and non-critical artifact maps), where monolith-era string-key semantics still carry authority that should move into canonical typed contracts.

Create all state/DTO types and stage contracts.

### Workstream B — Thin orchestration path

**Current status (2026-03-19): Partial.** `turn_service.py` now owns canonical sequence declaration (`CANONICAL_STAGE_SEQUENCE`) and stage binding via `_TurnPipelineStageHandlers(runtime=stage_runtime)`. Boot/wiring extraction has started through `src/testbot/entrypoints/sat_cli.py` (including package-script authority), while `sat_chatbot_memory_v2.main(...)` remains a compatibility delegator. Remaining obligations are concentrated in reducing residual monolith runtime authority, retiring compatibility delegators on schedule (including `run_answer_stage_flow`), and finishing extraction of dict-heavy stage contracts that still blur boundary ownership.

Replace monolithic entrypoint behavior with a `turn_service` that executes the canonical sequence.

### Workstream C — Stabilization and discourse state

**Current status (2026-03-19): Minimal.** Stabilization logic/persistence split exists, but candidate facts still collapse without durable per-candidate IDs. Residual risk is now concentrated in closing dict-heavy contract surfaces and tightening obligation lifecycle semantics (creation, carry-forward, and resolution transitions) across turns.

Implement candidate preservation, fact candidate persistence, pending repair/clarification modeling.

### Workstream D — Intent resolution and retrieval contracts

**Current status (2026-03-19): Partial.** Two-stage intent modeling exists (`classified_intent` + `resolved_intent`), and `EvidencePosture` explicit states exist. `langchain_core` `Document` still crosses `evidence_retrieval.py` boundaries. `PolicyDecision` exists but still lacks typed `expected_answer_mode`, `evidence_sufficiency`, and `fallback_continuation` fields.

Add classifier vs resolved intent split, normalized evidence DTOs, retrieval empty-state semantics.

### Workstream E — Decision/validation/commit chain

**Current status (2026-03-19): Partial.** Validation is hard-gated in the canonical service path. Legacy paths can still proceed through contract objects without the same gate semantics. `answer_commit.py` full decomposition remains incomplete and is currently documented as partial.

Implement `PolicyDecision`, validation gating, degraded fallback, committed next-turn state.

### Workstream F — Ports and adapters

**Current status (2026-03-19): Partial.** All four named protocols exist and integration contract tests exist. `SnapshotTimeProvider` exists for pipeline snapshots, but direct `arrow.utcnow()` timestamp calls remain in runtime/connectors.

Introduce `MemoryRepository`, `VectorStore`, `LanguageModel`, `SourceConnector` with contract tests.

### Workstream G — Boundary enforcement

**Current status (2026-03-19): Partial.** Boundary enforcement is already active in two forms: (1) blocking static import-boundary tests (`tests/architecture/test_import_boundaries.py`) and (2) readiness-gate integration of `qa_architecture_boundary_report` as a non-blocking warning-mode check with machine-readable artifacts. Remaining work is the warning→blocking ratchet for architecture-boundary findings, plus broader script-surface/package-policy hardening (`import-linter`, deeper public-surface declarations, and residual monolith authority reduction).

Import-linter, script surface rules, public API declarations, typed-package enforcement.

### Workstream H — Executable evidence and governance

**Current status (2026-03-19): In progress.** Verification manifest output is schema-versioned (`VERIFICATION_MANIFEST_SCHEMA_VERSION = "1.0"`), but governance closure is still open for blocking rule-ID resolution, traceability metadata completeness (issue/control/owner/check linkage), retention/versioning policy completeness, and remaining readiness-evidence fields required for machine-verifiable standards crosswalk outputs.

Readiness artifact schema, gate outputs, rule IDs, traceability, retention/versioning, standards crosswalk.

## 17. What “done” really means here

This becomes reality when a full turn can be observed in logs and tests as:

* raw utterance preserved
* multiple candidate interpretations preserved
* memory-worthy facts stabilized before routing
* context obligations materialized explicitly
* resolved intent derived from enriched state
* evidence retrieved via normalized contracts
* decision object chosen explicitly
* answer assembled only within decision class
* validation either passes or degrades
* only validated/degraded render artifacts are shown
* commit writes the next-turn discourse state correctly

At that point, the canonical turn pipeline is no longer just architecture. It is the actual execution substrate.

The short truth is: this is a **serious architecture migration**, not a light refactor. But it is also very coherent. The main thing you still need is ruthless translation from prose into typed contracts, deterministic tests, and CI-enforced boundaries.

I can turn this into a **phased implementation plan with concrete file-level deliverables per PR**
