# SEEM (arXiv:2601.06411) fit analysis for TestBot

## Paper snapshot
- **Title**: Structured Episodic Event Memory.
- **Core claim**: replacing flat/static memory retrieval with a hybrid of relational graph memory + dynamic episodic memory improves long-horizon coherence and logical consistency.
- **Main mechanisms**:
  1. Episodic Event Frames (EEFs) with provenance.
  2. Agentic associative fusion over fragmented evidence.
  3. Reverse Provenance Expansion (RPE) to reconstruct narrative context.

## Why this maps well to TestBot
TestBot already has a turn pipeline, explicit memory cards, vector retrieval, continuity write-through (`answer.commit`), and evidence/provenance-oriented policies. This creates a natural insertion point for SEEM-style structure without replacing the whole architecture.

## Concrete value SEEM could add in this architecture

1. **Higher narrative continuity across turns**
   - Current memory can be expanded from flat cards into event frames (who, what, when, causal link, confidence, source).
   - This reduces "fact shards" and makes multi-turn obligations easier to carry.

2. **Stronger conflict handling in knowing vs unknowing mode**
   - A graph layer can encode contradictions and trust tiers explicitly.
   - Decision policy can route contradictions to unknowing/clarifier behavior with clearer rationale.

3. **More faithful provenance**
   - EEFs can keep pointer-level lineage to source snippets + memory commits.
   - This directly supports TestBot's evidence-backed answer contract.

4. **Better long-context retrieval efficiency**
   - Associative expansion from an anchor event can pull only relevant neighboring events.
   - This can reduce context bloat versus broad semantic top-k retrieval.

5. **Improved repair and obligation tracking**
   - Reverse provenance expansion can replay why a prior answer/commit happened.
   - This improves user-facing corrections and auditability.

## Suggested integration points in TestBot

1. **Encode stage**
   - Build EEF objects per turn from observed user/assistant actions.
   - Include fields: actors, temporal markers, intent, claims, commitments, evidence refs.

2. **Memory storage**
   - Keep existing vector store for lexical/semantic recall.
   - Add graph persistence keyed by event/frame IDs and typed edges (`causes`, `updates`, `contradicts`, `fulfills`, `supersedes`).

3. **Context resolution**
   - Retrieval becomes two-step:
     1. semantic anchor selection,
     2. graph/episodic neighborhood expansion (RPE-like traversal).

4. **Inference & policy layer**
   - Provide conflict sets and lineage chains as explicit model inputs.
   - Use decision policy to select: grounded answer, clarification, or safe fallback.

5. **Commit stage**
   - Persist both durable facts and event-frame transitions.
   - Emit commit receipts that include frame IDs and edge updates for downstream traceability.

## Expected impact areas (if implemented well)
- Better consistency on long-running dialogs.
- Reduced hallucinated bridging between unrelated memories.
- More explainable "why I answered this way" metadata.
- Higher robustness on benchmarks/tasks that require temporal and causal reconstruction.

## Risks and mitigations
- **Complexity risk**: graph + episodic layer increases operational overhead.
  - Mitigate with phased rollout (shadow writes first, read path later).
- **Latency risk**: neighborhood expansion can grow quickly.
  - Mitigate with hop limits, trust-weighted pruning, and deterministic caps.
- **Data quality risk**: poor event extraction creates noisy graphs.
  - Mitigate with schema validation + deterministic post-processing.

## Practical rollout plan (incremental)
1. Define EEF schema and add write-only extraction in encode/commit stages.
2. Introduce graph persistence and receipt metadata, keep current retrieval as primary.
3. Add optional RPE-like expansion behind a feature flag.
4. Add BDD + deterministic tests for contradiction handling, continuity, and provenance.
5. Switch policy to prefer structured retrieval when confidence/coverage thresholds are met.

## Bottom line
In TestBot's current architecture, this paper most likely offers a **memory-structure upgrade**: better long-horizon coherence, explicit causal/temporal traceability, and cleaner knowing-vs-unknowing decisions via structured event-centric retrieval and provenance reconstruction.
