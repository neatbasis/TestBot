# Smoke evidence schema and output contract

This contract defines deterministic CI artifacts emitted by `scripts/smoke/run_live_smoke.sh`.

Canonical turn-pipeline sequencing note: evidence in this contract must be triaged through
[`ISSUE-0013`](../issues/ISSUE-0013-canonical-turn-pipeline-primary-bug-elimination-program.md) for bug elimination and delivery-status updates; use ISSUE-0012 only as historical planning context.

## Entrypoint

```bash
scripts/smoke/run_live_smoke.sh
```

Environment variables:

- `SMOKE_OUTPUT_DIR` (default `artifacts/smoke`)
- `SMOKE_ENVIRONMENT` (default `local`)
- `SMOKE_ACTOR` (default `GITHUB_ACTOR` or `local`)
- `SMOKE_CHECKS_FILE` (default `scripts/smoke/checks.example.json`)
- `SMOKE_TIMESTAMP` (optional explicit ISO-8601 UTC timestamp for deterministic reruns)
- `SMOKE_WRITE_MARKDOWN=1` to also write `smoke-report.md`

## Capability catalog

`docs/qa/capability-map.yaml` is the production capability catalog. It records each critical capability and the smoke check(s) that own proving it.

## Input check schema

The checks file is JSON and accepts either a top-level array or `{ "checks": [...] }`.

Each check object must include:

- `name` (string)
- `target` (string URL)
- `capability_id` (string)
- `capability_name` (string)
- `business_impact` (string)
- `severity_if_broken` (string)

Optional fields:

- `method` (defaults to `GET`)
- `expected_status` (defaults to `200`)
- `timeout_s` (defaults to `10`)
- `headers` (object of HTTP headers, values support `${ENV_VAR}` expansion)

## Output artifacts

When artifacts indicate failures or regressions, attach artifact references to ISSUE-0013 and note the affected canonical pipeline slice before opening follow-on issue threads.

### `smoke-summary.json`

```json
{
  "metadata": {
    "timestamp": "2026-03-05T12:34:56Z",
    "commit_sha": "<git sha>",
    "branch": "<git branch>",
    "environment": "staging",
    "actor": "ci-bot"
  },
  "counts": {
    "total": 3,
    "passed": 2,
    "failed": 1
  },
  "gate_status": "fail",
  "validated_capabilities": [
    {
      "capability_id": "cap-auth-service-availability",
      "capability_name": "Authentication service availability",
      "business_impact": "Users cannot sign in if authentication health fails.",
      "severity_if_broken": "critical",
      "validated_by_check": "healthz"
    }
  ]
}
```

### `smoke-details.jsonl`

One JSON object per check, sorted by `check_name`.

```json
{
  "check_name": "healthz",
  "request_target": "http://127.0.0.1:8000/healthz",
  "http_method": "GET",
  "status_code": 200,
  "expected_status": 200,
  "latency_ms": 11,
  "passed": true,
  "error_snippet": "",
  "capability_id": "cap-auth-service-availability",
  "capability_name": "Authentication service availability",
  "business_impact": "Users cannot sign in if authentication health fails.",
  "severity_if_broken": "critical"
}
```

### Optional `smoke-report.md`

A human-readable tabular report with the same pass/fail data as JSON artifacts plus a **Validated Capabilities** section listing production capabilities proven by successful checks in the run.

## Determinism and CI suitability

- JSON keys are sorted and written with stable formatting.
- Check execution order is deterministic (`name` sort).
- Validated capabilities are deduplicated by `capability_id` and sorted.
- All output paths are inside one directory for straightforward CI artifact upload.
- `SMOKE_TIMESTAMP` allows deterministic reruns for evidence regeneration.
