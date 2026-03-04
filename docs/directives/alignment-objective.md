# Alignment Objective Specification

- **Spec ID:** ALIGN-OBJECTIVE
- **Version:** `2026-03-01.v1`
- **Scope:** per-turn answer emission in `sat_chatbot_memory_v2`.

## Objective Dimensions

Each turn must produce all four dimension scores in `[0.0, 1.0]` and a final decision.

1. **factual-grounding reliability**
   - Measures whether factual claims are grounded in memory and citation-backed.
   - `1.0` when there are no claims, or when claims have required citations and memory context is confident.
   - `0.0` otherwise.

2. **safety/compliance strictness**
   - Measures policy-safe behavior for harmful or exploitative requests.
   - `1.0` when request is safe, or unsafe request is denied.
   - `0.0` when unsafe request is not denied.

3. **response utility**
   - Measures usefulness to user while still respecting constraints.
   - `1.0` for grounded non-fallback responses.
   - `0.4` for fallback/deny responses.

4. **cost/latency budget**
   - Measures conformance to bounded single-turn latency/cost behavior.
   - `1.0` for current one-pass deterministic path.

## Decision Policy

- **deny** when `safety/compliance strictness < 1.0`.
- **fallback** when factual-grounding reliability fails or response utility is below threshold.
- **allow** otherwise.

## Trace Record Contract

`PipelineState.alignment_decision` stores:

- `objective_version`
- `dimensions` object with all four required keys
- `final_alignment_decision` in `{allow, fallback, deny}`

Transition checks must reject answer-stage completion when the above is missing or inconsistent with emitted answer mode.
