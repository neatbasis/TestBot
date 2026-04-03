# Quickstart

## Who
Operators responsible for running TestBot in a local or lab Home Assistant environment.

## What
Set up dependencies, configure environment variables, and start the v0 memory-grounded bot loop.

## When
Run this before first launch, after dependency upgrades, or when provisioning a new machine.

## Where
From the repository root (`/workspace/TestBot`) with access to:
- Home Assistant REST API
- an Assist Satellite entity
- an Ollama endpoint

## Why
A consistent startup path reduces configuration drift and prevents runtime failures caused by missing models, missing environment variables, or incorrect entry commands.

Canonical turn-pipeline triage note: track pipeline defect elimination and delivery status in
[`docs/issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md`](issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md).
Use ISSUE-0012 only as linked historical delivery-planning context.

## Prerequisites

- Python 3.11+
- Home Assistant reachable via REST API
- Working Assist Satellite entity
- Ollama running locally or on your network

## Setup

1. Create and activate a virtual environment.

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -U pip
   ```

2. Install project dependencies by persona.

   Operator/runtime-only install:

   ```bash
   pip install -e .
   ```

   Contributor/QA install (includes runtime dependencies and validation tooling):

   ```bash
   pip install -e .[dev]
   ```

   If `behave` is missing, your setup is incomplete—follow the canonical note in [docs/testing.md](testing.md#bdd-tooling-health-check-canonical).

3. Start Ollama and pull required models.

   ```bash
   ollama serve
   ollama pull llama3.1
   ollama pull nomic-embed-text
   ```

4. Configure environment variables in your shell/session (shared by runtime startup and live smoke checks).

   Example:

   ```env
   HA_BASE_URL=http://homeassistant.local:8123
   HA_API_TOKEN=YOUR_LONG_LIVED_TOKEN
   HA_SATELLITE_ENTITY_ID=assist_satellite.your_satellite_entity

   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.1:latest
   OLLAMA_EMBEDDING_MODEL=nomic-embed-text
   ```

## Run

Start with automatic mode (prefers Home Assistant satellite, falls back to CLI chat if unavailable):

```bash
testbot --mode auto
```

Force satellite mode:

```bash
testbot --mode satellite
```

Force local CLI chat mode:

```bash
testbot --mode cli
```

Daemon behavior (no CLI fallback when Home Assistant is unavailable):

```bash
testbot --mode satellite --daemon
```

Alternative module run (same canonical entrypoint):

```bash
python -m testbot.entrypoints.cli
```

Say `stop` to end the loop.

Operational note for CLI mode:
- Runtime turn acquisition is Ask-backed and requires at least one usable Ask channel (`terminal`, `satellite`, or both).
- In CLI mode that Ask channel is typically `terminal`; satellite Ask remains optional/channel-specific.
- Assistant output remains direct CLI printing for now (intentional temporary split).

## Quick acceptance checklist

- [ ] Bot process starts without import/config errors.
- [ ] Satellite utterances are ingested.
- [ ] Memory-grounded responses include `doc_id` and `ts` citations when memory exists.
- [ ] Memory-insufficient responses use progressive fallback (targeted clarifier or at least two capability-based alternatives), with exact `I don't know from memory.` reserved for explicit deny/safety-only cases.

## Optional: source ingestion connectors

Primary user-facing control surface: `--source-ingestion`.
The flow follows Ask's terminal demo pattern (`python -m ask.demo_terminal_scenarios`):
menu selection, reference examples, and freeform entry.
Canonical control-surface/ownership contract: [docs/architecture/source-ingestion-control-surface.md](architecture/source-ingestion-control-surface.md).

### Client entry modes (primary UX)

- `--source-ingestion menu` → interactive menu in client (`reference`, `freeform`, `direct connector`, `off`)
- `--source-ingestion reference --source-reference wikipedia_hilbert` → apply known-good reference example
- `--source-ingestion freeform --source-freeform 'wikipedia:Hilbert space'` → start from freeform request
- `--source-ingestion wikipedia|arxiv|local_markdown|fixture` → explicit direct connector mode
- `--source-ingestion off` → explicit disable

`SOURCE_*` environment variables remain deployment/runtime configuration inputs
for connector-specific parameters (paths/topics/limits), not the primary
capability enable toggle.

Prefer connector inputs that encode the system's intended reasoning basis:

- local operator canon (invariants, trust policy, provenance doctrine),
- stable public ontology references,
- frontier research signals with explicit preprint trust semantics.

### Recommended onboarding flow (canonical)

Start with interactive menu:

```bash
testbot --mode cli --source-ingestion menu
```

Apply a known-good reference example:

```bash
testbot --mode cli --source-ingestion reference --source-reference wikipedia_hilbert
```

Start from freeform request:

```bash
testbot --mode cli --source-ingestion freeform --source-freeform 'arxiv:all:"category theory" AND cat:cs.LG'
```

### Deployment/runtime parameterized connector runs

Local markdown file/directory ingestion:

```bash
SOURCE_MARKDOWN_PATH=./docs/alignment-canon \
SOURCE_INGEST_LIMIT=20 \
testbot --mode cli --source-ingestion local_markdown
```

Wikipedia summary retrieval:

```bash
SOURCE_WIKIPEDIA_TOPIC="Hilbert space" \
SOURCE_WIKIPEDIA_LANGUAGE=en \
SOURCE_INGEST_LIMIT=1 \
testbot --mode cli --source-ingestion wikipedia
```

Alternative ontology topics: `Category theory`, `Transformer`, `Kernel method`.

arXiv metadata/content extraction:

```bash
SOURCE_ARXIV_QUERY='all:"category theory" AND cat:cs.LG' \
SOURCE_INGEST_LIMIT=5 \
testbot --mode cli --source-ingestion arxiv
```

Alternative query:

```bash
SOURCE_ARXIV_QUERY='all:"reproducing kernel Hilbert space"'
```

Dry-run validation (deterministic tests):

```bash
python -m pytest tests/test_source_connectors.py tests/test_source_ingest.py tests/test_runtime_modes.py -k source
```
