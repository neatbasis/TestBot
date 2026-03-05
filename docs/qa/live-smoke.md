# Live Smoke Runner Configuration

The live smoke runner requires a local environment file at:

- `~/.testbot/.env`

`scripts/smoke/run_live_smoke.py` loads this file before executing checks and exits early with a clear config error if the file is missing or invalid.

## Required variables

Add these keys to `~/.testbot/.env`:

- `OPENAI_BASE_URL` (must be a full `http://` or `https://` URL)
- `OPENAI_API_KEY` (non-empty credential/token)
- `SMOKE_CONNECT_TIMEOUT_S` (numeric, greater than `0`)
- `SMOKE_REQUEST_TIMEOUT_S` (numeric, greater than `0`)

These names align with the existing `.env.example` conventions in this repo (`OPENAI_*`) and smoke-specific timeout controls (`SMOKE_*`).

Example:

```dotenv
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-replace-with-long-random-token
SMOKE_CONNECT_TIMEOUT_S=3
SMOKE_REQUEST_TIMEOUT_S=10
```

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
