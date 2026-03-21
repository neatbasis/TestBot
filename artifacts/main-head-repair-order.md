# Main-head recommended repair order (before boundary-hardening merges)

1. **Fix retrieval contamination in `run_canonical_answer_stage_flow` compatibility path.**
   - Ensure seeded test store honors exclusion filters and does not recycle same-turn synthetic artifacts as memory evidence.
   - Re-run failing contract suites focused on fallback/GK/time/capabilities/runtime logging.

2. **Restore compatibility export(s) in `sat_chatbot_memory_v2`.**
   - Re-export `CanonicalTurnOrchestrator` (and any required canonical symbols) expected by compatibility tests.

3. **Correct `answer.commit` confirmed fact merge semantics.**
   - Merge prior committed facts + new confirmed facts deterministically, de-duplicated.

4. **Resolve continuity anchor contract drift.**
   - Decide policy: either keep new `assistant_offer_anchor` schema and update deterministic tests/docs, or revert anchor additions.

5. **Fix DTO adapter nullability compatibility (`None` vs `{}`).**
   - Align `ValidationResult` legacy roundtrip behavior with authoritative backward-compat contract.

6. **Re-run full gate and classify residual live-smoke matrix failures.**
   - After 1–5, re-run `python -m pytest` (or canonical all-green gate) to verify whether live smoke failures persist as independent issues.

## Merge-safety guidance
- **Main is not merge-safe for architecture boundary-hardening PRs** until at least steps 1–3 are complete and major contract suites are green; current baseline has 46 failing tests spanning core pipeline compatibility and invariants.
