# Operations

This document covers logs, troubleshooting, and environment notes for running TestBot.

## Logs

The v0 loop writes structured JSONL logs to:

```text
logs/session.jsonl
```

Each event includes common fields:

- `ts`: UTC ISO8601 log timestamp
- `event`: event name

Common events include:

- `user_utterance_ingest`
- `query_rewrite_output`
- `retrieval_candidates`
- `time_target_parse`
- `final_answer_mode`

### Log schema contract and evolution

`logs/session.jsonl` now carries an explicit `schema_version` per row for new emitters.

- **v1 (legacy):** rows may omit `schema_version`.
- **v2 (compatibility):** rows include `schema_version: 2`.
- **v3 (authoritative current schema):** rows include `schema_version: 3`.

Runtime emitters set this field via `append_session_log(...)` in
`src/testbot/sat_chatbot_memory_v2.py`.

Compatibility rules for replay/analytics tooling:

1. Treat missing `schema_version` as `v1`.
2. Parse by `event` first, then apply required keys for that event schema version.
3. Ignore unknown extra keys to allow additive evolution.
4. Bump `schema_version` only for breaking changes (rename/remove/type changes).
5. Keep at least one previous schema version readable during migrations.

Current event contracts are validated by `scripts/validate_log_schema.py`, with canonical
`v3` fixtures in `tests/fixtures/log_schema/current_schema_v3.jsonl`:

- Common required keys: `ts` (`str`), `event` (`str`)
- `pipeline_state_snapshot`: `stage` (`str`), `state` (`dict`)
- `stage_transition_validation`: `stage` (`str`), `boundary` (`str`),
  `invariant_refs` (`list`), `passed` (`bool`), `failures` (`list`)

Use fixture artifacts in `tests/fixtures/log_schema/` to keep both current and previous schema
versions valid over time.


## Turn analytics + KPI loop

Aggregate runtime logs into a per-turn analytics dataset:

```bash
python scripts/aggregate_turn_analytics.py   --input logs/session.jsonl   --output logs/turn_analytics.jsonl   --summary-output logs/turn_analytics_summary.json
```

Per-turn dataset fields:

- `intent`: model intent label for the turn.
- `ambiguity_score`: ambiguity signal from ranking/policy.
- `action`: fallback/policy action (`NONE` means grounded-answer path).
- `followup_proxy`: proxy for user follow-up pressure.
- `provenance_completeness`: normalized [0,1] completeness score from provenance evidence.

### KPI definitions

- **grounded-answer precision**: among turns with `action == "NONE"`, share where `provenance_completeness >= 0.66`.
- **false-knowing rate**: among turns with `action == "NONE"`, share where `provenance_completeness == 0.0`.
- **fallback appropriateness**: among fallback turns (`action != "NONE"`), share where `followup_proxy >= 0.5`.
- **citation completeness**: mean `provenance_completeness` across all turns.

These KPIs are emitted to `logs/turn_analytics_summary.json` for release-review and drift tracking.

### Analytics row validation behavior

`scripts/aggregate_turn_analytics.py` performs a lightweight normalization + validation pass before
building per-turn rows:

- `schema_version` defaults to `1` when omitted (legacy compatibility).
- Validation is applied only to analytics-driving events:
  - `user_utterance_ingest`
  - `intent_classified`
  - `fallback_action_selected`
  - `provenance_summary`
- For supported schemas (`v1`, `v2`, `v3`), required keys and basic value types are validated by event.

Invalid analytics event rows are **skipped** (not fail-fast) and accounted for in
`logs/turn_analytics_summary.json` via:

- `invalid_rows`: total invalid analytics rows encountered.
- `skipped_rows`: rows skipped from aggregation (currently equal to `invalid_rows`).
- `per_event_validation_failures`: per-event failure counters.

When invalid-row counts are non-zero:

1. Treat KPI output as potentially biased due to dropped evidence.
2. Inspect offending rows in `logs/session.jsonl` and align emitters with the event schema contract.
3. Re-run `python scripts/validate_log_schema.py` and `python scripts/aggregate_turn_analytics.py`.
4. Only use KPI outputs for release review when invalid/skipped counts return to zero (or are explicitly triaged).

### KPI guardrails (release thresholds)

Machine-readable guardrails live in `config/kpi_guardrails.json` and are validated by
`scripts/validate_kpi_guardrails.py` against `logs/turn_analytics_summary.json`.

Current acceptable ranges:

- `grounded_answer_precision`: **min 0.75**
- `false_knowing_rate`: **max 0.05**
- `fallback_appropriateness`: **min 0.70**
- `citation_completeness`: **min 0.70**

### Release-gate rollout plan for KPI validation

`python scripts/all_green_gate.py` includes KPI guardrail validation in a phased mode:

1. **Optional phase (current)**: check runs as warning-only via `--kpi-guardrail-mode optional` (default).
2. **Blocking phase (target)**: switch to `--kpi-guardrail-mode blocking` once two consecutive sprint KPI evidence reviews show zero regressions.
3. **Emergency bypass**: `--kpi-guardrail-mode off` is available for incident response and must be documented in triage notes.


## Troubleshooting

### `AttributeError: 'tuple' object has no attribute 'metadata'`

Cause: treated `similarity_search_with_score` results as `Document` objects.

Fix: unpack as `(Document, score)` tuples before metadata access.

### Home Assistant API/token issues

Checklist:

- [ ] `HA_API_URL` includes scheme and correct host/port.
- [ ] `HA_API_SECRET` is a valid long-lived token.
- [ ] `HA_SATELLITE_ENTITY_ID` exists and is available.

### Ollama connectivity issues

Checklist:

- [ ] `OLLAMA_BASE_URL` points to reachable Ollama service.
- [ ] Chat model is available (`ollama list`).
- [ ] Embedding model `nomic-embed-text` is available.

### Unexpected fallback frequency

Checklist:

- [ ] Confirm retrieval candidates are present in logs.
- [ ] Check citation contract enforcement in answer stage.
- [ ] Validate temporal parsing for time-sensitive queries.


## KPI evidence artifacts

Recurring KPI review evidence is tracked at:

- `docs/issues/evidence/sprint-<NN>-kpi-review.md`

Each red-tag triage cycle must update the latest sprint evidence file with:

- current KPI values from `logs/turn_analytics_summary.json`
- pass/fail state against `config/kpi_guardrails.json`
- mitigation owners and due dates for any failed guardrail

Link this evidence from `docs/issues/RED_TAG.md` triage updates.

## Environment notes

- `OLLAMA_BASE_URL` is the canonical Ollama endpoint variable.
- `OLLAMA_HOST` may be accepted as a legacy fallback in some setups.
- Keep runtime and test environments separate so deterministic tests stay offline.

## Source ingestion connectors

TestBot can ingest external sources before the chat loop starts when `SOURCE_INGEST_ENABLED=1`.

Use connector examples that reflect the system's reasoning ontology (invariants, composition, and provenance), not just generic topical lookup.

Recommended epistemic split:

- `local_markdown`: operator-curated canonical notes/policies (highest operator-controlled trust).
- `wikipedia`: stable background ontology references (mid-trust public scaffold).
- `arxiv`: frontier/preprint research signals (explicitly preprint trust semantics).

### Local markdown connector

```bash
SOURCE_INGEST_ENABLED=1 \
SOURCE_CONNECTOR_TYPE=local_markdown \
SOURCE_MARKDOWN_PATH=./docs/alignment-canon \
SOURCE_INGEST_LIMIT=20 \
python src/testbot/sat_chatbot_memory_v2.py --mode cli
```

### Wikipedia summary connector

```bash
SOURCE_INGEST_ENABLED=1 \
SOURCE_CONNECTOR_TYPE=wikipedia \
SOURCE_WIKIPEDIA_TOPIC="Hilbert space" \
SOURCE_WIKIPEDIA_LANGUAGE=en \
SOURCE_INGEST_LIMIT=1 \
python src/testbot/sat_chatbot_memory_v2.py --mode cli
```

Other high-signal ontology topics: `Category theory`, `Kernel method`, `Transformer`.

### arXiv connector

```bash
SOURCE_INGEST_ENABLED=1 \
SOURCE_CONNECTOR_TYPE=arxiv \
SOURCE_ARXIV_QUERY='all:"category theory" AND cat:cs.LG' \
SOURCE_INGEST_LIMIT=5 \
python src/testbot/sat_chatbot_memory_v2.py --mode cli
```

Alternative query example:

```bash
SOURCE_ARXIV_QUERY='all:"reproducing kernel Hilbert space"'
```

### Dry-run validation commands

Use deterministic test-only checks to validate connector behavior without running live operator flows:

```bash
python -m pytest tests/test_source_connectors.py tests/test_source_ingest.py tests/test_runtime_modes.py -k source
```

Canonical gate before merge:

```bash
python scripts/all_green_gate.py
```
