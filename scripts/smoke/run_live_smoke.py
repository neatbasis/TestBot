#!/usr/bin/env python3
"""Run deterministic live smoke checks and emit CI-friendly evidence artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

REQUIRED_ENV_KEYS = (
    "HA_API_URL",
    "HA_API_SECRET",
    "HA_SATELLITE_ENTITY_ID",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "OLLAMA_EMBEDDING_MODEL",
    "X_OLLAMA_KEY",
    "SMOKE_CONNECT_TIMEOUT_S",
    "SMOKE_REQUEST_TIMEOUT_S",
)


def _git_value(*args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"
    return completed.stdout.strip() or "unknown"


def _load_required_env() -> dict[str, str]:
    env_values = {key: os.getenv(key, "") for key in REQUIRED_ENV_KEYS}

    missing = [key for key in REQUIRED_ENV_KEYS if not env_values.get(key, "").strip()]
    if missing:
        raise ValueError(
            "Missing required environment variables in "
            f"process environment: {', '.join(missing)}."
        )

    parsed_ha_url = urlparse(env_values["HA_API_URL"])
    if parsed_ha_url.scheme not in {"http", "https"} or not parsed_ha_url.netloc:
        raise ValueError(
            "Invalid HA_API_URL in "
            "process environment: must be a full http(s) URL."
        )

    parsed_base_url = urlparse(env_values["OLLAMA_BASE_URL"])
    if parsed_base_url.scheme not in {"http", "https"} or not parsed_base_url.netloc:
        raise ValueError(
            "Invalid OLLAMA_BASE_URL in "
            "process environment: must be a full http(s) URL."
        )
    if len(env_values["HA_API_SECRET"].strip()) < 8:
        raise ValueError(
            "Invalid HA_API_SECRET in "
            "process environment: value is too short to be a usable credential/token."
        )
    for key in ("SMOKE_CONNECT_TIMEOUT_S", "SMOKE_REQUEST_TIMEOUT_S"):
        raw_value = env_values[key]
        try:
            timeout = float(raw_value)
        except ValueError as exc:
            raise ValueError(f"Invalid {key} in process environment: '{raw_value}' is not numeric.") from exc
        if timeout <= 0:
            raise ValueError(f"Invalid {key} in process environment: must be > 0 seconds.")

    return env_values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/smoke"))
    parser.add_argument("--environment", default="local")
    parser.add_argument("--actor", default="local")
    parser.add_argument(
        "--timestamp",
        help=(
            "Optional UTC timestamp in ISO-8601 format. "
            "Defaults to current UTC time when omitted."
        ),
    )
    parser.add_argument(
        "--checks-file",
        type=Path,
        default=Path("scripts/smoke/checks.example.json"),
        help="JSON file with smoke checks.",
    )
    parser.add_argument(
        "--report-md",
        action="store_true",
        help="Write smoke-report.md in addition to JSON artifacts.",
    )
    parser.add_argument(
        "--include-ollama-execution-checks",
        action="store_true",
        help=(
            "Run explicit Ollama execution probes (ChatOllama.invoke + "
            "OllamaEmbeddings.embed_query) in addition to HTTP readiness checks."
        ),
    )
    return parser.parse_args()


def _now_iso8601(timestamp: str | None) -> str:
    if timestamp:
        return timestamp
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_checks(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    checks = raw.get("checks", []) if isinstance(raw, dict) else raw
    if not isinstance(checks, list):
        raise ValueError("checks file must contain a list or {'checks': [...]} object")
    normalized: list[dict[str, Any]] = []
    for entry in checks:
        if not isinstance(entry, dict):
            raise ValueError("every check must be an object")
        name = str(entry.get("name", "")).strip()
        target = os.path.expandvars(str(entry.get("target", "")).strip())
        if not name or not target:
            raise ValueError("every check requires non-empty 'name' and 'target'")
        capability_id = str(entry.get("capability_id", "")).strip()
        capability_name = str(entry.get("capability_name", "")).strip()
        business_impact = str(entry.get("business_impact", "")).strip()
        severity_if_broken = str(entry.get("severity_if_broken", "")).strip()
        if not all((capability_id, capability_name, business_impact, severity_if_broken)):
            raise ValueError(
                "every check requires non-empty capability_id, capability_name, "
                "business_impact, and severity_if_broken"
            )
        raw_headers = entry.get("headers", {})
        headers: dict[str, str] = {}
        if raw_headers is not None:
            if not isinstance(raw_headers, dict):
                raise ValueError("optional 'headers' must be an object of string key/value pairs")
            for raw_key, raw_value in raw_headers.items():
                key = str(raw_key).strip()
                value = os.path.expandvars(str(raw_value).strip())
                if not key or not value:
                    raise ValueError("optional 'headers' requires non-empty key/value strings")
                headers[key] = value

        normalized.append(
            {
                "name": name,
                "target": target,
                "method": str(entry.get("method", "GET")).upper(),
                "expected_status": int(entry.get("expected_status", 200)),
                "headers": headers,
                "capability_id": capability_id,
                "capability_name": capability_name,
                "business_impact": business_impact,
                "severity_if_broken": severity_if_broken,
                "timeout_s": float(entry.get("timeout_s", os.environ["SMOKE_REQUEST_TIMEOUT_S"])),
            }
        )
    return sorted(normalized, key=lambda item: item["name"])


def _run_check(check: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url=check["target"],
        method=check["method"],
        headers=check.get("headers", {}),
    )
    started = time.perf_counter()
    status_code: int | None = None
    error_snippet = ""
    failure_category = ""
    passed = False

    try:
        with urllib.request.urlopen(request, timeout=check["timeout_s"]) as response:
            status_code = int(response.status)
            response.read(512)
    except urllib.error.HTTPError as exc:
        status_code = int(exc.code)
        body = exc.read(512)
        error_snippet = body.decode("utf-8", errors="replace").strip().replace("\n", " ")[:200]
        failure_category = "endpoint_unreachable"
    except Exception as exc:  # noqa: BLE001
        error_snippet = str(exc).strip().replace("\n", " ")[:200]
        failure_category = "endpoint_unreachable"

    latency_ms = int((time.perf_counter() - started) * 1000)
    if status_code is not None and status_code == check["expected_status"]:
        passed = True
        failure_category = ""
    elif not failure_category:
        failure_category = "endpoint_unreachable"

    return {
        "check_name": check["name"],
        "request_target": check["target"],
        "http_method": check["method"],
        "status_code": status_code,
        "expected_status": check["expected_status"],
        "latency_ms": latency_ms,
        "passed": passed,
        "check_type": "readiness",
        "failure_category": failure_category,
        "error_snippet": error_snippet,
        "capability_id": check["capability_id"],
        "capability_name": check["capability_name"],
        "business_impact": check["business_impact"],
        "severity_if_broken": check["severity_if_broken"],
    }


def _run_ollama_execution_probe(env_values: dict[str, str]) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        from langchain_ollama import ChatOllama, OllamaEmbeddings
    except Exception as exc:  # noqa: BLE001
        latency_ms = int((time.perf_counter() - started) * 1000)
        return {
            "check_name": "ollama-runtime-execution",
            "request_target": env_values["OLLAMA_BASE_URL"],
            "http_method": "N/A",
            "status_code": None,
            "expected_status": None,
            "latency_ms": latency_ms,
            "passed": False,
            "check_type": "execution",
            "failure_category": "inference_execution_failure",
            "error_snippet": (
                "langchain_ollama import failed; install dev/runtime dependencies "
                f"to run execution probes ({type(exc).__name__}: {exc})"
            )[:200],
            "capability_id": "cap-ollama-runtime-execution",
            "capability_name": "Ollama runtime execution",
            "business_impact": "Model and embedding calls may still fail even when readiness endpoints are reachable.",
            "severity_if_broken": "critical",
        }

    check = {
        "check_name": "ollama-runtime-execution",
        "request_target": env_values["OLLAMA_BASE_URL"],
        "http_method": "N/A",
        "status_code": None,
        "expected_status": None,
        "capability_id": "cap-ollama-runtime-execution",
        "capability_name": "Ollama runtime execution",
        "business_impact": "Model and embedding calls may still fail even when readiness endpoints are reachable.",
        "severity_if_broken": "critical",
        "check_type": "execution",
    }

    try:
        ollama_client_kwargs = {
            "client_kwargs": {"headers": {"X-Ollama-Key": env_values["X_OLLAMA_KEY"]}}
        }

        llm = ChatOllama(
            model=env_values["OLLAMA_MODEL"],
            base_url=env_values["OLLAMA_BASE_URL"],
            **ollama_client_kwargs,
            temperature=0.0,
        )
        response = llm.invoke("Reply with exactly: ok")
        text = getattr(response, "content", str(response)).strip()
        if not text:
            raise RuntimeError("ChatOllama.invoke returned an empty response.")

        embeddings = OllamaEmbeddings(
            model=env_values["OLLAMA_EMBEDDING_MODEL"],
            base_url=env_values["OLLAMA_BASE_URL"],
            **ollama_client_kwargs,
        )
        vector = embeddings.embed_query("smoke test")
        if not vector or not any(float(value) != 0.0 for value in vector):
            raise RuntimeError("embed_query returned an empty or zero-only vector.")

        check["passed"] = True
        check["failure_category"] = ""
        check["error_snippet"] = ""
    except Exception as exc:  # noqa: BLE001
        message = str(exc).strip().replace("\n", " ")
        lowered = message.lower()
        if "not found" in lowered or "pull" in lowered or "model" in lowered:
            failure_category = "model_missing"
        elif "embed" in lowered:
            failure_category = "embedding_execution_failure"
        else:
            failure_category = "inference_execution_failure"

        check["passed"] = False
        check["failure_category"] = failure_category
        check["error_snippet"] = message[:200]

    check["latency_ms"] = int((time.perf_counter() - started) * 1000)
    return check


def _validated_capabilities(details: list[dict[str, Any]]) -> list[dict[str, str]]:
    passed_capabilities: dict[str, dict[str, str]] = {}
    for row in details:
        if not row["passed"]:
            continue
        capability_id = row["capability_id"]
        passed_capabilities[capability_id] = {
            "capability_id": capability_id,
            "capability_name": row["capability_name"],
            "business_impact": row["business_impact"],
            "severity_if_broken": row["severity_if_broken"],
            "validated_by_check": row["check_name"],
        }
    return [passed_capabilities[key] for key in sorted(passed_capabilities)]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _write_markdown(path: Path, summary: dict[str, Any], details: list[dict[str, Any]]) -> None:
    lines = [
        "# Smoke Report",
        "",
        f"- Gate status: **{summary['gate_status']}**",
        f"- Passed: {summary['counts']['passed']}",
        f"- Failed: {summary['counts']['failed']}",
        "",
        "| Check | Status | HTTP | Latency (ms) | Capability | Severity if Broken |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in details:
        status = "PASS" if row["passed"] else "FAIL"
        lines.append(
            f"| {row['check_name']} | {status} | {row['status_code']} | {row['latency_ms']} | "
            f"{row['capability_name']} ({row['capability_id']}) | {row['severity_if_broken']} |"
        )

    lines.extend(["", "## Validated Capabilities", ""])
    if summary["validated_capabilities"]:
        for capability in summary["validated_capabilities"]:
            lines.append(
                f"- **{capability['capability_name']}** ({capability['capability_id']}) via "
                f"`{capability['validated_by_check']}` — {capability['business_impact']} "
                f"(severity if broken: {capability['severity_if_broken']})"
            )
    else:
        lines.append("- No production capabilities were validated in this run.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    try:
        env_values = _load_required_env()
    except ValueError as exc:
        print(f"[smoke-config-error] {exc}")
        return 2
    checks = _load_checks(args.checks_file)

    metadata = {
        "timestamp": _now_iso8601(args.timestamp),
        "commit_sha": _git_value("rev-parse", "HEAD"),
        "branch": _git_value("rev-parse", "--abbrev-ref", "HEAD"),
        "environment": args.environment,
        "actor": args.actor,
        "env_source": "process_environment",
        "request_timeout_s": float(env_values["SMOKE_REQUEST_TIMEOUT_S"]),
    }

    details = [_run_check(check) for check in checks]
    if args.include_ollama_execution_checks:
        details.append(_run_ollama_execution_probe(env_values))
    passed_count = sum(1 for detail in details if detail["passed"])
    failed_count = len(details) - passed_count

    summary = {
        "metadata": metadata,
        "counts": {
            "total": len(details),
            "passed": passed_count,
            "failed": failed_count,
        },
        "gate_status": "pass" if failed_count == 0 else "fail",
        "validated_capabilities": _validated_capabilities(details),
    }

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "smoke-summary.json", summary)
    _write_jsonl(output_dir / "smoke-details.jsonl", details)
    if args.report_md:
        _write_markdown(output_dir / "smoke-report.md", summary, details)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["gate_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
