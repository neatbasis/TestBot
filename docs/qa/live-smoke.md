# Live Smoke Runner Configuration

The live smoke runner requires a local environment file at:

- `~/.testbot/.env`

`scripts/smoke/run_live_smoke.py` loads this file before executing checks and exits early with a clear config error if the file is missing or invalid.

## Required variables (TestBot production profile)

Add these keys to `~/.testbot/.env`:

- `HA_API_URL` (full `http://` or `https://` URL)
- `HA_API_SECRET` (non-empty Home Assistant bearer token)
- `HA_SATELLITE_ENTITY_ID` (target satellite entity ID used by runtime/control tests)
- `OLLAMA_BASE_URL` (full `http://` or `https://` URL)
- `OLLAMA_MODEL` (chat/generation model name, for example `llama3.1:latest`)
- `OLLAMA_EMBEDDING_MODEL` (embedding model name, for example `nomic-embed-text`)
- `SMOKE_CONNECT_TIMEOUT_S` (numeric, greater than `0`)
- `SMOKE_REQUEST_TIMEOUT_S` (numeric, greater than `0`)

Example:

```dotenv
HA_API_URL=http://homeassistant.local:8123
HA_API_SECRET=replace-with-long-ha-token
HA_SATELLITE_ENTITY_ID=assist_satellite.kitchen
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
SMOKE_CONNECT_TIMEOUT_S=3
SMOKE_REQUEST_TIMEOUT_S=10
```

## Check-to-capability mapping

The default `scripts/smoke/checks.example.json` is designed to validate these stakeholder/runtime objectives:

- `ha-api-health` → **HA control plane reachability**: proves TestBot can reach Home Assistant at all.
- `ha-api-readiness` → **HA context readiness**: proves runtime state/config endpoints are available for grounded behavior.
- `ollama-api-ready` → **Ollama model runtime readiness**: proves model-serving infrastructure is reachable for response generation.
- `ollama-embedding-ready` → **Ollama embedding runtime readiness**: proves retrieval/grounding embedding infrastructure is online.

## Optional TestBot app health endpoint

If your deployment also exposes an app-level health route, create a supplemental checks file (or replace the default checks file) and add a check such as:

```json
{
  "name": "testbot-app-health",
  "target": "${TESTBOT_APP_HEALTH_URL}",
  "method": "GET",
  "expected_status": 200,
  "capability_id": "cap-testbot-service-availability",
  "capability_name": "TestBot service availability",
  "business_impact": "User requests fail if the TestBot service process is unhealthy.",
  "severity_if_broken": "critical"
}
```

Then point the runner to your profile via `--checks-file` (or `SMOKE_CHECKS_FILE`).

## Secure handling guidance

- Never commit `~/.testbot/.env` or any secret-bearing copy of it to git.
- Rotate secrets/tokens regularly and immediately after suspected exposure.
- Restrict local permissions so only your user can read it (for example `chmod 600 ~/.testbot/.env`).
- Prefer short-lived tokens where possible.

## Quick start

Run the smoke checks directly:

```bash
python scripts/smoke/run_live_smoke.py \
  --checks-file scripts/smoke/checks.example.json \
  --output-dir artifacts/smoke \
  --report-md
```

Or use the shell wrapper:

```bash
scripts/smoke/run_live_smoke.sh
```

To override metadata fields:

```bash
SMOKE_ENVIRONMENT=staging \
SMOKE_ACTOR="$(whoami)" \
SMOKE_WRITE_MARKDOWN=1 \
scripts/smoke/run_live_smoke.sh
```
