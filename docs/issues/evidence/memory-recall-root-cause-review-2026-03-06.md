# Memory recall feature: code review and root-cause analysis (2026-03-06)

## Scope reviewed
- Runtime recall path: retrieval, rerank, confidence gating, and answer fallback routing.
- BDD/eval harness behavior for memory recall scenarios.

## Observed behavior
1. The runtime path uses **progressive fallback** (clarify/assist/don't-know), not a single strict fallback string, when memory confidence is low.
2. Temporal weighting often collapses to the base blend for broad phrases (for example, "earlier this week"), making ranking largely semantic.
3. Ambiguity detection only fires when near-tied candidates remain identical after deterministic tie-break.
4. The BDD memory feature is intentionally deterministic and does not exercise live retrieval/rerank logic.

## Root causes

### RC-1: Policy intentionally prefers assistive fallback over strict "don't know" for low-confidence memory misses
- In fallback policy, `not memory_hit` routes to `OFFER_CAPABILITY_ALTERNATIVES`, while strict unknown is reserved for a low `source_confidence` branch. This means low-confidence memory misses usually produce the assistive message rather than exact don't-know. 
- `stage_answer` maps `OFFER_CAPABILITY_ALTERNATIVES` directly to the assistive fallback text.

Impact:
- Behavior may appear inconsistent if stakeholders expect exact fallback for every low-confidence memory miss.

### RC-2: Confidence threshold is permissive (`min_margin_to_second = 0.0`) and ambiguity override is disabled
- Confidence only requires top score >= threshold and no unresolved ambiguity.
- Because margin-to-second is zero, tiny gaps can still be "confident" if ambiguity detector does not trigger.
- Ambiguity override is disabled by config, so any unresolved ambiguity forces non-confident behavior.

Impact:
- Borderline top-vs-second separations can still pass as confident.
- Once ambiguity is detected, system always falls back to clarification/assist paths.

### RC-3: Temporal parser defaults to `now` when phrases are not explicitly recognized
- `parse_target_time` returns `now` when it cannot map explicit temporal cues.
- The reranker then computes temporal Gaussian weight against `target=now`; for distant events this can become near-zero, effectively reducing to base temporal blend.

Impact:
- Some memory recall phrasing is ranked mostly by semantic score even when user intent is temporal (for example broad/indirect time expressions).

### RC-4: Ambiguity detector is narrow by design
- Near-tie candidates are collected by score delta, but ambiguity is only marked unresolved when tie-break keys are exactly equal.
- If near-tied candidates differ slightly in timestamp/type/doc_id, ambiguity may remain false despite practical uncertainty.

Impact:
- System can be "confident" in cases humans may still consider ambiguous.

### RC-5: BDD memory feature uses a synthetic harness that bypasses runtime retrieval/rerank
- Step definitions derive answers from fixture helper logic and set `context_confident = bool(candidates)` directly.
- This bypasses runtime confidence gates and rerank ambiguity logic.

Impact:
- Acceptance scenarios validate contract shape and fallback wording, but do not detect regressions in online rerank/confidence behavior.

## Supporting evidence
- `eval_recall.py` shows one don't-know decision in current fixture set, while hit@k remains 1.0 for memory lookup cases; this indicates ranking success in fixtures with limited stress on edge ambiguity/parsing paths.
- Existing tests pass for rerank and policy branches, suggesting current behavior is intentional rather than accidental.

## Recommendations (prioritized)
1. **Clarify product contract**: decide whether low-confidence memory misses should be strict don't-know or assistive alternatives, and align directives/tests accordingly.
2. **Tighten confidence discrimination**: raise `min_margin_to_second` from 0.0 to a small positive value and evaluate precision/recall tradeoff.
3. **Expand temporal parsing coverage**: add parser patterns for broad natural phrases (for example, "earlier this week", "this morning", "recently").
4. **Broaden ambiguity criteria**: optionally treat near-ties within a configurable epsilon as ambiguous even when tie-break picks a deterministic winner.
5. **Add runtime-parity BDD path**: keep deterministic harness, but add at least one scenario that goes through real rerank + confidence functions to catch drift.
