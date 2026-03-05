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
- **v2 (current):** rows include `schema_version: 2`.

Compatibility rules for replay/analytics tooling:

1. Treat missing `schema_version` as `v1`.
2. Parse by `event` first, then apply required keys for that event schema version.
3. Ignore unknown extra keys to allow additive evolution.
4. Bump `schema_version` only for breaking changes (rename/remove/type changes).
5. Keep at least one previous schema version readable during migrations.

Current event contracts validated by `scripts/validate_log_schema.py`:

- Common required keys: `ts` (`str`), `event` (`str`)
- `pipeline_state_snapshot`: `stage` (`str`), `state` (`dict`)
- `stage_transition_validation`: `stage` (`str`), `boundary` (`str`),
  `invariant_refs` (`list`), `passed` (`bool`), `failures` (`list`)

Use fixture artifacts in `tests/fixtures/log_schema/` to keep both current and previous schema
versions valid over time.


## Grounding source ingestion (Wikipedia, arXiv, markdown)

Use `scripts/ingest_grounding_sources.py` to prepare grounding documents and load them into the configured memory store.

Dry-run example (fetch + parse only):

```bash
python scripts/ingest_grounding_sources.py   --namespace testbot   --markdown-dir ./grounding   --wikipedia-title "Leonardo da Vinci"   --arxiv-query "retrieval augmented generation"   --arxiv-max-results 3   --dry-run
```

Load into Elasticsearch-backed memory index:

```bash
python scripts/ingest_grounding_sources.py   --namespace testbot   --markdown-dir ./grounding   --wikipedia-title "Leonardo da Vinci"   --arxiv-query "retrieval augmented generation"   --memory-store-mode elasticsearch   --elasticsearch-url http://localhost:9200   --elasticsearch-index testbot_memory_cards
```

Operational notes:

- Markdown files are loaded recursively from `--markdown-dir` (`*.md`).
- Wikipedia uses the REST summary endpoint with provenance `source=wikipedia`.
- arXiv uses the official Atom API with provenance `source=arxiv`.
- Keep canonical partitioning stable with `--namespace` (for example `testbot`, `prod`, `research`).
- Use `--dry-run` in CI or validation flows that should not mutate indices.

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

## Environment notes

- `OLLAMA_BASE_URL` is the canonical Ollama endpoint variable.
- `OLLAMA_HOST` may be accepted as a legacy fallback in some setups.
- Keep runtime and test environments separate so deterministic tests stay offline.
