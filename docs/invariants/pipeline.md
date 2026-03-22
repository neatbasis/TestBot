# Pipeline Semantics Invariants

This registry defines canonical cross-stage semantic invariants for the canonical turn pipeline. Stage-local boundary details remain owned by `docs/architecture/canonical-turn-pipeline.md` and `docs/directives/traceability-matrix.md`; this file owns stable invariant classes that span stage families.

## Pipeline invariant ID scheme

Pipeline invariants use the dedicated `PINV-*` namespace to avoid ambiguity with response-policy invariants (`INV-*`).

| Pipeline Invariant ID | Invariant statement | Scope |
|---|---|---|
| PINV-001 | **Canonical stage ordering is fixed**: the runtime pipeline preserves the exact stage order `observe.turn → encode.candidates → stabilize.pre_route → context.resolve → intent.resolve → retrieve.evidence → policy.decide → answer.assemble → answer.validate → answer.render → answer.commit`. | Stage-ordering semantics across all canonical turns. |
| PINV-002 | **Observe before infer**: raw user content and turn metadata are durably observed before any downstream abstraction may discard or overwrite them. | `U → O` preservation and trace-backed observation integrity. |
| PINV-003 | **Candidate multiplicity before authority**: multiple plausible interpretations may coexist through `encode.candidates`; authoritative routing/intent collapse must not occur before stabilization + context-sensitive resolution. | Pre-route anti-collapse semantics (`O → C → S`). |
| PINV-004 | **Stabilize before route**: durable extractable user facts, provenance links, and memory-ready representations must exist in stabilized pre-route state before routing authority is assigned. | `C → S` durability and routing preconditions. |
| PINV-005 | **Context enrichment before intent authority**: pending repair state, unresolved obligations, prior assistant-offer anchors, and active focus/anaphora anchors are explicit before authoritative intent resolution. | `S → context.resolve → intent.resolve` continuity semantics. |
| PINV-006 | **Intent authority derives from enriched state**: `resolved_intent` is the sole authoritative downstream intent; it must be derived from enriched stabilized/context state (not raw text alone), and telemetry `intent` must mirror `resolved_intent` without divergence. | Intent authority + anti-projection + telemetry coherence. |
| PINV-007 | **Evidence posture is semantically typed**: retrieval output preserves distinct evidence postures (including valid evidence, no-candidate empty evidence, and scored-empty candidate sets); these postures are not interchangeable. | Retrieval evidence-state semantics and downstream policy safety. |
| PINV-008 | **Retrieval-policy coherence**: retrieval branch selection and downstream policy posture remain coherent with resolved intent and discourse context; valid memory-oriented evidence cannot be silently relabeled as generic non-memory handling. | `retrieve.evidence` ↔ `policy.decide` coherence. |
| PINV-009 | **Decision-answer class alignment**: decision object class, assembled answer class, validation posture, and rendered response class must agree semantically; no free-form path bypasses selected decision class authority. | `policy.decide → answer.assemble → answer.validate/render` alignment. |
| PINV-010 | **Validation gates semantic rendering**: semantic answer text renders as normal output only from validated state; failed validation may transition only to explicit degraded fallback artifacts. | `answer.validate → answer.render` safety boundary. |
| PINV-011 | **Commit preserves continuity-critical state**: commit persists assistant utterance memory card, provenance, pending repair state, resolved/remaining obligations, and confirmed user facts required for next-turn continuity. | `answer.commit` continuity and replayability semantics. |
| PINV-012 | **Boundary claims remain trace-backed**: pipeline-produced provenance/confidence/memory-grounding/self-report claims must be supportable by canonical trace-backed state, evidence links, or committed artifacts. | Claim-legitimacy and traceability semantics across decision/render/commit boundaries. |

## Conformance enforcement

Canonical stage-transition conformance is validated by `scripts/validate_pipeline_stage_conformance.py` and requires pipeline-semantics rows in canonical docs to include `PINV-*` linkage. Runtime guard/evidence hooks continue to emit stage-boundary evidence (`stage_transition_validation`, `pipeline_state_snapshot`, and related event keys) while semantic interpretation of that evidence is governed by this registry.

## Stage transition contracts

| Stage | Preconditions | Postconditions | Invariant linkage |
|---|---|---|---|
| `observe.turn` | `user_input` is present and non-empty before processing begins. | Observation artifact preserves raw user utterance and turn metadata without interpretation loss. | `PINV-001`, `PINV-002`, `PINV-012`. |
| `encode.candidates` | `turn_observation` artifact is present. | Candidate encodings preserve multiplicity (speech-act/fact/repair/query candidates) without assigning route authority. | `PINV-001`, `PINV-003`. |
| `stabilize.pre_route` | `encoded_candidates` artifact is present. | Stable pre-routing artifacts (utterance card + candidate facts with provenance) are persisted before intent routing. | `PINV-001`, `PINV-004`, `PINV-012`. |
| `context.resolve` | `stabilized_turn_state` artifact is present. | Context state includes pending repair/obligation anchors used by downstream intent resolution. | `PINV-001`, `PINV-005`, `PINV-011`. |
| `intent.resolve` | `turn_observation`, `encoded_candidates`, and `stabilized_turn_state` artifacts are present. | Intent/state classification is derived from enriched artifacts; forbidden early projection `U → I` (raw utterance directly to interpreted intent) is not allowed; telemetry intent mirrors authoritative resolved intent. | `PINV-001`, `PINV-005`, `PINV-006`. |
| `retrieve.evidence` | `resolved_intent` and stabilized state are present. | Evidence bundle selection is coherent with resolved intent and preserves provenance references and empty-evidence distinctions. | `PINV-001`, `PINV-007`, `PINV-008`, `PINV-012`. |
| `policy.decide` | Retrieval result plus stabilized/context artifacts are present. | Decision object class is explicit (`answer_from_memory`, `ask_for_clarification`, repair continuation, etc.) and remains coherent with evidence posture and resolved intent. | `PINV-001`, `PINV-008`, `PINV-009`. |
| `answer.assemble` | Decision object and evidence bundle are present. | Draft answer is bound to explicit evidence/provenance payloads and selected response class. | `PINV-001`, `PINV-009`, `PINV-012`. |
| `answer.validate` | Draft answer and decision metadata are present. | Validation result is explicit and records grounding/provenance/alignment outcomes before render eligibility. | `PINV-001`, `PINV-009`, `PINV-010`, `PINV-012`. |
| `answer.render` | Validated answer state is present. | Render either a normal validated answer (when validation passes) or an explicit degraded fallback artifact (when validation fails); never render unvalidated semantic answer text. | `PINV-001`, `PINV-009`, `PINV-010`, `PINV-012`. |
| `answer.commit` | Validated/rendered answer plus stabilized state are present. | Commit only passing validated answers or explicit degraded fallback artifacts; persist continuity-critical next-turn state. | `PINV-001`, `PINV-010`, `PINV-011`, `PINV-012`. |
