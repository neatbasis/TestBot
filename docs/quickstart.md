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

2. Install project dependencies.

   ```bash
   pip install -e .
   ```

   Optional development extras:

   ```bash
   pip install -e .[dev]
   ```

3. Start Ollama and pull required models.

   ```bash
   ollama serve
   ollama pull llama3.1
   ollama pull nomic-embed-text
   ```

4. Configure environment variables.

   ```bash
   cp .env.example .env
   ```

   Minimum expected values:

   ```env
   HA_API_URL=http://homeassistant.local:8123
   HA_API_SECRET=YOUR_LONG_LIVED_TOKEN
   HA_SATELLITE_ENTITY_ID=assist_satellite.your_satellite_entity

   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.1:latest
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

Alternative direct module run:

```bash
python src/testbot/sat_chatbot_memory_v2.py
```

Say `stop` to end the loop.

## Quick acceptance checklist

- [ ] Bot process starts without import/config errors.
- [ ] Satellite utterances are ingested.
- [ ] Memory-grounded responses include `doc_id` and `ts` citations when memory exists.
- [ ] Fallback is exactly `I don't know from memory.` when memory is insufficient.
