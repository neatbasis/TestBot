# System Structure Audit — 2026-03-19

This document records a code-first architecture audit focused on:

1. Entity relationships and authority boundaries.
2. Knowledge-sharing and provenance semantics.
3. Repair/validation/commit enforcement.
4. Cross-cutting drift, observability, and enforcement gaps.

## Scope

- Runtime modules under `src/testbot/`.
- Architecture and invariant docs under `docs/`.
- Enforcement tests/scripts under `tests/` and `scripts/`.

## 1) Entity relationships — system structure and authority

### State & pipeline integrity

- The canonical pipeline has explicit fixed stage order in `CanonicalTurnOrchestrator.STAGE_ORDER` with strict equality checks at constructor time and runtime stage-order checks (`run`).
- Runtime orchestration in `_run_canonical_turn_pipeline` wires all 11 stages through one `CanonicalTurnContext` containing a single `PipelineState` plus stage artifacts.
- There is one notable caveat: state mutation uses direct `replace(...)` assignments inside stage handlers and helper stage functions, not an immutable transition object with compile-time transition typing.
- Additional snapshots use legacy-ish stage labels (`observe`, `rewrite`, `stabilize`, `rerank`, `answer`) alongside canonical labels (`answer.validate`, `answer.render`, `answer.commit`), so observability naming is not fully normalized.

### Authority boundaries

- Stage modules (`turn_observation`, `candidate_encoding`, `stabilization`, `context_resolution`, `intent_resolution`, `evidence_retrieval`, `policy_decision`, `answer_assembly`, `answer_validation`, `answer_rendering`, `answer_commit`) are mostly domain-focused and typed.
- `sat_chatbot_memory_v2.py` still holds mixed authority: orchestration, adapter wiring, retrieval execution, policy bridge decisions, fallback behavior, logging, and runtime mode concerns.
- Retrieval conversion is partially normalized in `evidence_retrieval` (`EvidenceRecord`, `EvidenceBundle`), but adapter-native `Document` objects are still consumed in the orchestrator retrieval/rerank path before normalization.

### Dependency direction

- Import-boundary tests enforce that stage modules avoid infrastructure adapters and client SDKs.
- Full stage-order composition is allowlisted only in `canonical_turn_orchestrator.py` and `sat_chatbot_memory_v2.py`.
- Tests intentionally import some internals from `sat_chatbot_memory_v2.py`, so test dependency direction is pragmatic, not strictly API-only.
- `sat_chatbot_memory_v2.py` remains the effective hidden orchestrator (even with `CanonicalTurnOrchestrator` extracted) because stage handlers and runtime flow are still constructed there.

### Entity modeling

- Explicitly modeled as typed entities:
  - Turn: `TurnObservation`, stabilized `turn_id`, `CommittedTurnState`.
  - Evidence: `EvidenceRecord`, `EvidenceBundle`, `RetrievalResult` + `EvidencePosture`.
  - Decision: `DecisionObject`, `DecisionClass`, `RetrievalPolicyDecision`.
  - Obligation/repair: answer-assembly obligations and commit receipt/pending repair fields.
- Not yet fully explicit as first-class domain types:
  - Utterance and obligation details are still carried through string fields and dict payloads in `candidate_facts`, `commit_receipt`, and `pending_repair_state`.

### Identity & continuity

- Turn identity starts with explicit `turn_id` at observe stage and is copied into stabilized artifacts and candidate facts.
- Continuity is recovered from prior commit receipts via committed anchors (`confirmed_user_facts`, `remaining_obligations`, `pending_ingestion_request_id`, repair flags).
- Some IDs are deterministic (`turn_id` for user utterance), while reflection/dialogue-state IDs are ad hoc `uuid4` values each turn.

## 2) Knowledge sharing — evidence, memory, retrieval

### Evidence model

- Evidence posture is explicit: `NOT_REQUESTED`, `EMPTY_EVIDENCE`, `SCORED_EMPTY`, `SCORED_NON_EMPTY`.
- Decision policy uses posture distinctions directly (especially for memory recall vs knowledge question behavior).

### Retrieval semantics

- Retrieval routing is driven by resolved intent and continuity guards (`decide_retrieval_routing`, identity-continuity forced memory retrieval).
- Retrieval output is normalized into DTO-style `EvidenceBundle` and `RetrievalResult`, but orchestration still touches backend-native `Document` objects before conversion.

### Memory vs retrieval

- Memory strata and evidence channels are semantically separated (`structured_facts`, `episodic_utterances`, `repair_anchors_offers`, `reflections_hypotheses`, `source_evidence`).
- User facts, episodic memory, and retrieved source evidence are represented separately in several structures, but commit payloads still serialize many distinctions as untyped dict/list values.

### Provenance

- The pipeline maintains provenance fields on state (`claims`, `provenance_types`, `used_memory_refs`, `used_source_evidence_refs`, `source_evidence_attribution`, `basis_statement`).
- Validation + render + commit stages block unvalidated normal answers and require degraded artifacts for failed validation.
- Remaining gap: because some answer text is generated before full contract checks, unsupported claims can temporarily exist in stage-local objects until validation rejects them.

### Time-awareness

- Time-awareness exists via intent routing (`time_query`) and rerank/time scoring logic in runtime helpers.
- Retrieval result posture itself is not recency-weighted semantically; recency influence currently lives in retrieval/rerank scoring logic rather than typed evidence policy fields.

### Context resolution

- Context resolution is structured (`ResolvedContext` with continuity posture, anchors, ambiguity flags, prior intent).
- This avoids pure raw-history concatenation; it pulls continuity anchors from prior commit receipts.

## 3) Repair mechanisms — validation, fallback, recovery

### Validation gate

- Canonical path enforces `answer.validate` before render/commit.
- If `answer_validation_contract.passed` is false, runtime raises before normal render/commit path.
- Rendering module supports explicit degraded artifacts when validation fails.

### Degraded fallback representation

- Degraded outcomes are explicit structured render contracts (`degraded_response=True` with typed response contract values).
- Clarifier / alternatives / deny degraded forms are concretely represented and distinguishable.

### Obligation tracking

- Commit stage persists obligations and repair state (`resolved_obligations`, `remaining_obligations`, `pending_repair_state`, `pending_ingestion_request_id`).
- Next-turn context resolution and continuity evidence extraction consume these persisted fields.

### Failure modes

- Empty vs scored-empty retrieval is deterministic and encoded as posture.
- Ambiguity and fallback routing rely on deterministic policy and confidence metadata.
- Conflict handling is partly deterministic (clarify/fallback paths) but some branch details still depend on runtime confidence payload shape in `confidence_decision` dicts.

### Commit semantics

- Commit persists rendered text, validated provenance, obligations, pending repair state, confirmed user facts, and response contract markers.
- Commit rejects failed-validation normal answers unless the rendered artifact is explicitly degraded.

### Repair loops

- Repair loop capability exists:
  - failed/insufficient evidence can trigger clarify/repair decisions,
  - commit persists pending repair/obligation state,
  - context/intent stages read those anchors next turn.
- This is enforced functionally, though some “repair meaning” still rides on string-coded obligation names.

## 4) Cross-cutting risks

### Structural integrity (bypass risk)

- Canonical orchestrator and conformance tests strongly enforce stage order and artifact dependencies.
- A direct-answer branch still exists in `policy.decide` (`requires_retrieval=False`) but it does not bypass later `answer.validate`, `answer.render`, and `answer.commit` stages.

### Illusion vs enforcement

- Many architecture claims are code-enforced by orchestrator guards and tests.
- Some doc-level ontology claims remain only partially encoded as strict types (for example, obligation semantics and some context/evidence details remain dict-like).

### Invariant enforcement

- Invariants are enforced through a mix of runtime checks (`RuntimeError` contracts), transition validators, import-boundary tests, and conformance scripts.
- Not all invariants are type-level; substantial enforcement remains test/script-based.

### Observability

- Pipeline snapshots and session logs provide stage-by-stage visibility.
- Stage naming in snapshots is mixed canonical/legacy and can make per-turn forensics harder than necessary.

### Drift detection

- There are dedicated drift checks for stage order, import boundaries, render shortcut bans, and invariant namespace separation.
- These checks reduce architectural drift risk substantially.

## 5) Distilled answer: where structure collapses into narrative

Primary collapse points are:

1. `sat_chatbot_memory_v2.py` as a concentrated orchestration + policy + runtime adapter authority center.
2. Dict-shaped payload channels (`confidence_decision`, `candidate_facts`, `commit_receipt`, `pending_repair`) where semantics depend on conventions rather than strict types.
3. Early-stage backend object handling (`Document`) before evidence normalization, which keeps adapter-native shapes in the main runtime path longer than ideal.

Overall: TestBot now has meaningful structural enforcement for stage order, contracts, and degraded-validation safety, but authority separation and typed domain modeling are incomplete at the orchestration/runtime boundary.
