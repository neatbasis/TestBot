#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

python scripts/smoke/run_live_smoke.py \
  --output-dir "${SMOKE_OUTPUT_DIR:-artifacts/smoke}" \
  --environment "${SMOKE_ENVIRONMENT:-local}" \
  --actor "${SMOKE_ACTOR:-${GITHUB_ACTOR:-local}}" \
  --checks-file "${SMOKE_CHECKS_FILE:-scripts/smoke/checks.example.json}" \
  ${SMOKE_TIMESTAMP:+--timestamp "$SMOKE_TIMESTAMP"} \
  ${SMOKE_WRITE_MARKDOWN:+--report-md}
