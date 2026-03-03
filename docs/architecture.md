# Architecture

This document summarizes the v0 pipeline, memory-card model, and time-aware reranking strategy.

## Pipeline overview

TestBot follows a single loop designed for memory-grounded answers:

1. **Observe**
   - Receive user utterance from Home Assistant satellite.
   - Capture assistant response for history.
2. **Encode memory**
   - Persist user/assistant utterances as structured cards.
   - Generate and store reflection cards linked to source utterances.
3. **Retrieve**
   - Rewrite user input into a retrieval-oriented query.
   - Fetch top-k memory candidates from vector search.
4. **Rerank**
   - Infer target time from natural language cues.
   - Apply Gaussian time weighting centered on inferred target time.
5. **Answer**
   - Provide recent chat window + memory context to the answer stage.
   - Enforce memory-only answering and citation contract.

## Memory cards

Memory is represented as text cards with stable field labels.

### Utterance memory card

```text
type: user_utterance | assistant_utterance
ts: <UTC ISO8601>
speaker: user | assistant
channel: satellite
doc_id: <stable identifier>
text: <utterance>
```

### Reflection memory card

```text
type: reflection
ts: <UTC ISO8601>
about: <speaker>
source_doc_id: <linked utterance doc_id>
doc_id: <stable identifier>
reflection:
claims: [...]
commitments: [...]
preferences: [...]
uncertainties: [...]
followups: [...]
confidence: 0.0..1.0
```

Design rule: reflection cards are hypotheses and must stay linked to source utterances.

## Rerank overview

Time-aware reranking biases retrieval toward memories near an inferred target time.

- Parse temporal phrases (for example: `2 hours ago`, `last week`, `from now`).
- Compute `target_time` from utterance + current `now`.
- Set uncertainty `σ` as a fraction of distance between `target_time` and `now`.
- Apply Gaussian weight so near-time cards are boosted and distant cards are suppressed.

This rerank pass is combined with semantic retrieval scores to improve temporal relevance.

## Answer contract

- Responses with factual claims must include memory citation fields `doc_id` and `ts`.
- If memory context is weak or citation rules are violated, output must be exactly:
  - `I don't know from memory.`

## Architecture acceptance criteria

- [ ] Observe→encode→retrieve→rerank→answer flow remains intact.
- [ ] Reflection cards always include `source_doc_id` linkage.
- [ ] Time-aware rerank is applied when target time can be inferred.
- [ ] Citation contract is enforced before final output is returned.
