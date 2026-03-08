# Production debug CLI session notes (2026-03-08 21:52)

## Summary finding

The pipeline shows progress in **observe/encode/stabilize instrumentation**, but still makes the wrong decision early in decisioning, which prevents retrieval and commit semantics from becoming useful for identity continuity.

## Findings

1. **Foundation/stabilization progress is real**
   - The system ingests utterances, creates turn records, persists stabilized facts, assigns segment/retrieval constraints, and applies same-turn exclusion hygiene.
2. **Rewrite-stage semantic inversion remains critical**
   - Self-identification (`Hi! I'm sebastian`) is rewritten into assistant-focused query intent, corrupting discourse object type.
3. **Decisioning misroutes both declaration and self-reference turns**
   - Turns are classified as `knowledge_question` and routed to `direct_answer` with `evidence_posture=not_requested`.
4. **Retrieval/rerank starvation follows from early misroute**
   - Retrieval and rerank are skipped; no memory evidence enters policy for grounding.
5. **Commit/audit present but semantically ineffective**
   - Commit receipts exist, but `confirmed_user_facts` remains empty, preventing next-turn identity recall from continuity state.

## Two concrete defects

- **Defect 1: rewrite-stage semantic inversion**
  - `Hi! I'm sebastian` is transformed into an assistant-facing query and no longer treated as a user identity declaration.
- **Defect 2: self-referential follow-up not memory-routed**
  - `Who am I?` remains in generic direct-answer fallback path instead of memory/context identity recall.

## Canonical implication

The system preserves identity statements structurally, but decisioning semantics misinterpret them before retrieval and commit can promote durable user facts.
