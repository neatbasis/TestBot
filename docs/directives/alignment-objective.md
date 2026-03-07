# Alignment Objective Specification

- **Spec ID:** ALIGN-OBJECTIVE
- **Version:** `2026-03-05.v3`
- **Scope:** per-turn answer emission in `sat_chatbot_memory_v2`.

## Objective Dimensions

Each turn must produce all five dimension scores in `[0.0, 1.0]` and a final decision.

1. **factual-grounding reliability**
   - Raw inputs:
     - `raw_claim_like_text_detected ∈ {0,1}`
     - `has_required_memory_citation ∈ {0,1}`
     - confidence margin (`top_final_score - second_final_score`) and `min_margin_to_second`
   - Normalization:
     - `citation_validity = 1.0` when response is contract-exempt, no raw claim-like text is detected, or required citation is present; else `0.0`.
     - `confidence_margin_normalized = clamp01(confidence_margin / min_margin_to_second)`.
   - Score:
     - `factual_grounding_reliability = clamp01(0.65 * citation_validity + 0.35 * confidence_margin_normalized)`.

2. **safety/compliance strictness**
   - `1.0` when request is safe, or unsafe request is denied.
   - `0.0` when unsafe request is not denied.

3. **response utility**
   - Raw inputs:
     - fallback mode class from `final_answer`
     - `context_confident` as intent-fulfillment proxy.
   - Normalization:
     - `fallback_mode_score`: deny=`0.0`, fallback=`0.25`, clarify/assist=`0.7`, grounded answer=`1.0`.
     - `intent_fulfillment_proxy`: grounded confident answer=`1.0`, contract-exempt clarify/assist=`0.75`, otherwise=`0.45`.
   - Score:
     - `response_utility = clamp01(0.5 * fallback_mode_score + 0.5 * intent_fulfillment_proxy)`.

4. **cost/latency budget**
   - Raw inputs:
     - `turn_latency_ms` and `latency_budget_ms` (default budget `3500ms`)
     - `token_budget_ratio` (used/allowed tokens; optional).
   - Normalization:
     - `latency_score = 1.0` when latency signal is missing, else `clamp01(1 - turn_latency_ms / latency_budget_ms)`.
     - `token_budget_score = 1.0` when token signal is missing, else `clamp01(1 - token_budget_ratio)`.
   - Score:
     - `cost_latency_budget = min(latency_score, token_budget_score)`.

5. **provenance transparency**
   - Required completeness checks for non-trivial answers:
     - `claims` non-empty,
     - `provenance_types` non-empty,
     - `basis_statement` non-empty.
   - Score:
     - trivial outputs (`deny`, fallback, clarify/assist) => `1.0`.
     - non-trivial outputs => `passed_checks / 3`.

## Decision Policy

- **deny** when `safety/compliance strictness < 1.0`.
- **fallback** when any of:
  - `factual_grounding_reliability < 0.6`
  - `response_utility < 0.5`
  - `provenance_transparency < 0.75`
  - `cost_latency_budget < 0.35`
- **allow** otherwise.

## Trace Record Contract

`PipelineState.alignment_decision` stores:

- `objective_version`
- `dimensions` object with all five required keys in `[0.0, 1.0]`
- `dimension_inputs.raw` (raw per-dimension inputs)
- `dimension_inputs.normalized` (normalized component values)
- `final_alignment_decision` in `{allow, fallback, deny}`

Session logs must include `alignment_decision_evaluated` rows carrying both raw inputs and normalized components for post-hoc audits.
