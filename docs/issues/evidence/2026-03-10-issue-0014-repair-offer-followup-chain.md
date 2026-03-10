# Evidence — ISSUE-0014 repair-offer followup continuity chain (2026-03-10)

## Scope
Validate the repair-offer continuity chain changes:
1. Offer-bearing answer marks commit receipt repair-offered signal.
2. Context continuity emits repair anchor on next turn.
3. Intent routing supports repair-offer followup utterance family.
4. Intent resolution promotes knowledge-question followups to `capabilities_help` when repair anchor is present.

## Commands and outcomes

- `PYTHONPATH=src python -m pytest tests/test_answer_rendering_offer_bearing.py tests/test_intent_router.py tests/test_decisioning_stages.py tests/test_answer_commit_identity_promotion.py -q`
  - Outcome: pass (`53 passed`).

- `PYTHONPATH=src python - <<'PY' ... classify_intent(...) ... PY`
  - Outcome:
    - `please look up the definition => capabilities_help`
    - `yes please look it up => knowledge_question`
    - `go ahead => capabilities_help`
    - `please do => capabilities_help`
    - `look it up => capabilities_help`
    - `find the definition => capabilities_help`

## Four-turn sequence status

A live CLI/Ollama-backed four-turn replay was not executed in this evidence pass because runtime dependency parity with the production endpoint/session is not available in this repository-only test environment.

Deterministic unit-level evidence above confirms the implemented contract chain in canonical code paths:
- offer-bearing detection in canonical `answer.assemble`
- repair-offer persistence through `answer.render` -> `answer.commit`
- continuity anchor generation in `context.resolve`
- repair-anchor consumption in `intent.resolve`
