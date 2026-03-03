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
