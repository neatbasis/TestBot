# Pipeline Semantics Invariants

This registry defines canonical cross-stage semantic invariants for the canonical turn pipeline. Stage-local boundary details remain owned by `docs/architecture/canonical-turn-pipeline.md` and `docs/directives/traceability-matrix.md`; this file owns stable invariant classes that span stage families.

## Pipeline invariant ID scheme

Pipeline invariants use the dedicated `PINV-*` namespace to avoid ambiguity with response-policy invariants (`INV-*`).

| Pipeline Invariant ID | Invariant statement | Scope |
|---|---|---|
| PINV-001 | **Canonical stage ordering is fixed**: the runtime pipeline preserves the exact stage order `observe.turn → encode.candidates → stabilize.pre_route → context.resolve → intent.resolve → retrieve.evidence → policy.decide → answer.assemble → answer.validate → answer.render → answer.commit`. | Stage-ordering semantics across all canonical turns. |
| PINV-002 | **Observe before infer**: raw user content and turn metadata are durably observed before downstream abstraction may discard, normalize, or overwrite them. | `U → O` preservation and trace-backed observation integrity. |
| PINV-003 | **Candidate multiplicity before authority**: multiple plausible interpretations may coexist through `encode.candidates`; authoritative routing/intent collapse is forbidden before stabilization and context-aware resolution. | Pre-route anti-collapse semantics (`O → C → S`). |
| PINV-004 | **Stabilize before route**: durable extractable user facts, provenance links, and memory-ready representations must exist in stabilized pre-route state before routing authority is assigned. | `C → S` durability and routing preconditions. |
| PINV-005 | **Repair/obligation materialization before intent authority**: pending repair state and unresolved obligation state must be explicit in context state before authoritative intent resolution. | `context.resolve` continuity semantics. |
| PINV-006 | **Resolved-intent authority and telemetry coherence**: downstream stages consume only `resolved_intent`; telemetry `intent` must mirror `resolved_intent` from the same post-resolution state. | `intent.resolve` authority semantics. |
| PINV-007 | **Evidence posture is semantically typed**: retrieval output preserves distinct postures (valid evidence, no-candidate empty evidence, scored-empty candidates); these states are not interchangeable. | Retrieval evidence-state semantics and policy safety. |
| PINV-008 | **Retrieval-policy coherence**: retrieval branch selection and downstream policy posture remain coherent with resolved intent and discourse context. | `retrieve.evidence` ↔ `policy.decide` coherence. |
| PINV-009 | **Decision-answer class alignment**: decision object class, assembled answer class, validation posture, and rendered response class agree semantically; no free-form answer path bypasses decision authority. | `policy.decide → answer.assemble → answer.validate/render` alignment. |
| PINV-010 | **Validation gates semantic rendering**: semantic answer text renders as normal output only from validated state; failed validation may transition only to explicit degraded fallback artifacts. | `answer.validate → answer.render` safety boundary. |
| PINV-011 | **Commit preserves continuity-critical state**: commit persists assistant utterance memory card, provenance, pending repair state, resolved/remaining obligations, and confirmed user facts required for next-turn continuity. | `answer.commit` continuity and replayability semantics. |
| PINV-012 | **Grounding/provenance claims are artifact-backed**: rendered or committed grounding/provenance/confidence claims must map to trace-backed artifacts or evidence references available in canonical pipeline state. | Claim-legitimacy semantics for render/commit outputs. |

## Conformance enforcement

Canonical stage-transition conformance is validated by `scripts/validate_pipeline_stage_conformance.py` and requires pipeline-semantics rows in canonical docs to include `PINV-*` linkage. Runtime guard/evidence hooks continue to emit stage-boundary evidence (`stage_transition_validation`, `pipeline_state_snapshot`, and related event keys) while semantic interpretation of that evidence is governed by this registry.

## Stage transition contracts

| Stage | Preconditions | Postconditions | Invariant linkage |
|---|---|---|---|
| `observe.turn` | `user_input` is present and non-empty before processing begins. | Observation artifact preserves raw user utterance and turn metadata without interpretation loss. | `PINV-001`, `PINV-002`. |
| `encode.candidates` | `turn_observation` artifact is present. | Candidate encodings preserve multiplicity (speech-act/fact/repair/query candidates) without assigning route authority. | `PINV-001`, `PINV-003`. |
| `stabilize.pre_route` | `encoded_candidates` artifact is present. | Stable pre-routing artifacts (utterance card + candidate facts with provenance) are persisted before intent routing. | `PINV-001`, `PINV-004`. |
| `context.resolve` | `stabilized_turn_state` artifact is present. | Context state materializes pending repair and unresolved obligations used by downstream intent resolution. | `PINV-001`, `PINV-005`. |
| `intent.resolve` | `turn_observation`, `encoded_candidates`, and `stabilized_turn_state` artifacts are present. | Intent is resolved from enriched state; forbidden early projection `U → I` is not allowed; downstream/telemetry intent fields stay coherent with resolved intent authority. | `PINV-001`, `PINV-006`. |
| `retrieve.evidence` | `resolved_intent` and stabilized/context state are present. | Evidence bundle selection is coherent with resolved intent and preserves typed evidence postures plus provenance references. | `PINV-001`, `PINV-007`, `PINV-008`. |
| `policy.decide` | Retrieval result plus stabilized/context artifacts are present. | Decision object class is explicit and coherent with resolved intent/evidence posture. | `PINV-001`, `PINV-008`, `PINV-009`. |
| `answer.assemble` | Decision object and evidence bundle are present. | Draft answer remains bound to selected decision class and evidence/provenance payloads. | `PINV-001`, `PINV-009`, `PINV-012`. |
| `answer.validate` | Draft answer and decision metadata are present. | Validation result is explicit and records grounding/provenance/alignment outcomes before render eligibility. | `PINV-001`, `PINV-009`, `PINV-010`, `PINV-012`. |
| `answer.render` | Validated answer state is present. | Render either a normal validated answer (when validation passes) or an explicit degraded fallback artifact (when validation fails); never render unvalidated semantic answer text. | `PINV-001`, `PINV-010`, `PINV-012`. |
| `answer.commit` | Validated/rendered answer plus stabilized state are present. | Commit only passing validated answers or explicit degraded fallback artifacts; persist continuity-critical next-turn state and artifact-backed grounding/provenance claims. | `PINV-001`, `PINV-011`, `PINV-012`. |
