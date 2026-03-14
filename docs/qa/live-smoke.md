# Live Smoke Runner Configuration

The live smoke runner and runtime startup (`testbot --mode ...`) read required HA/Ollama values directly from the process environment.

## Canonical bug-elimination sequencing (ISSUE-0013)

Use live-smoke evidence to close the learning loop for canonical-turn-pipeline defects: every failed smoke run should create or update a linked evidence note and route sequencing updates through
[`ISSUE-0013`](../issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md). Keep ISSUE-0012 references as historical planning context only.

Checklist for each smoke execution:

- Record artifact paths (`smoke-summary.json`, `smoke-details.jsonl`, optional `smoke-report.md`).
- Classify failure against canonical pipeline slices (foundation, decisioning, commit/audit).
- Update ISSUE-0013 `Work Plan`/`Closure Notes` with defect-elimination sequencing and next validation command.
- Cross-link any dependent capability issue IDs only after ISSUE-0013 routing is recorded.

## Required variables (TestBot production profile)

Set these keys in the shell/session before running smoke checks:

- `HA_API_URL` (full `http://` or `https://` URL)
- `HA_API_SECRET` (non-empty Home Assistant bearer token)
- `HA_SATELLITE_ENTITY_ID` (target satellite entity ID used by runtime/control tests)
- `OLLAMA_BASE_URL` (full `http://` or `https://` URL)
- `OLLAMA_MODEL` (chat/generation model name, for example `llama3.1:latest`)
- `OLLAMA_EMBEDDING_MODEL` (embedding model name, for example `nomic-embed-text`)
- `X_OLLAMA_KEY` (non-empty Ollama API key sent as `X-Ollama-Key` for readiness and execution auth)
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
X_OLLAMA_KEY=replace-with-ollama-api-key
SMOKE_CONNECT_TIMEOUT_S=3
SMOKE_REQUEST_TIMEOUT_S=10
```

## Check-to-capability mapping

The default `scripts/smoke/checks.example.json` is designed to validate these stakeholder/runtime objectives:

- `ha-api-health` → **HA control plane reachability**: proves TestBot can reach Home Assistant at all.
- `ha-api-readiness` → **HA context readiness**: proves runtime state/config endpoints are available for grounded behavior.
- `ollama-api-ready` → **Ollama model runtime readiness**: proves model-serving infrastructure is reachable for response generation.
- `ollama-embedding-ready` → **Ollama embedding runtime readiness**: proves retrieval/grounding embedding infrastructure is online.

### Readiness checks vs execution checks

Live smoke now separates two classes of Ollama validation:

- **Readiness checks** (fast):
  - `GET ${OLLAMA_BASE_URL}/api/tags` probes (`ollama-api-ready`, `ollama-embedding-ready`) with `X-Ollama-Key: ${X_OLLAMA_KEY}`
  - Goal: determine endpoint/service reachability quickly.
  - Failure category in artifact rows: `endpoint_unreachable`.
- **Execution checks** (explicit runtime calls):
  - `ChatOllama.invoke(...)` and `OllamaEmbeddings.embed_query(...)` in `ollama-runtime-execution`
  - Goal: prove model + embedding execution works, not just endpoint readiness.
  - Failure categories in artifact rows:
    - `model_missing`
    - `inference_execution_failure`
    - `embedding_execution_failure`

Enable execution checks for live environments with:

```bash
SMOKE_INCLUDE_OLLAMA_EXECUTION_CHECKS=1 scripts/smoke/run_live_smoke.sh
```

Or directly:

```bash
python scripts/smoke/run_live_smoke.py --include-ollama-execution-checks
```

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

- Never commit secret-bearing environment exports, scripts, or shell history snippets to git.
- Rotate secrets/tokens regularly and immediately after suspected exposure.
- Use secure secret injection for your shell/session (for example, password managers, direnv with local-only files, or CI secret stores).
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
SMOKE_INCLUDE_OLLAMA_EXECUTION_CHECKS=1 \
SMOKE_WRITE_MARKDOWN=1 \
scripts/smoke/run_live_smoke.sh
```
