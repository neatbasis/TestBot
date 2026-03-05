#!/usr/bin/env python3
"""Run deterministic live smoke checks and emit CI-friendly evidence artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


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
        target = str(entry.get("target", "")).strip()
        if not name or not target:
            raise ValueError("every check requires non-empty 'name' and 'target'")
        capabilities = entry.get("capabilities", [])
        if not isinstance(capabilities, list) or any(not isinstance(cap, str) for cap in capabilities):
            raise ValueError("capabilities must be a list of strings")
        normalized.append(
            {
                "name": name,
                "target": target,
                "method": str(entry.get("method", "GET")).upper(),
                "expected_status": int(entry.get("expected_status", 200)),
                "capabilities": sorted({cap.strip() for cap in capabilities if cap.strip()}),
                "timeout_s": float(entry.get("timeout_s", 10)),
            }
        )
    return sorted(normalized, key=lambda item: item["name"])


def _run_check(check: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(url=check["target"], method=check["method"])
    started = time.perf_counter()
    status_code: int | None = None
    error_snippet = ""
    passed = False

    try:
        with urllib.request.urlopen(request, timeout=check["timeout_s"]) as response:
            status_code = int(response.status)
            response.read(512)
    except urllib.error.HTTPError as exc:
        status_code = int(exc.code)
        body = exc.read(512)
        error_snippet = body.decode("utf-8", errors="replace").strip().replace("\n", " ")[:200]
    except Exception as exc:  # noqa: BLE001
        error_snippet = str(exc).strip().replace("\n", " ")[:200]

    latency_ms = int((time.perf_counter() - started) * 1000)
    if status_code is not None and status_code == check["expected_status"]:
        passed = True

    return {
        "check_name": check["name"],
        "request_target": check["target"],
        "http_method": check["method"],
        "status_code": status_code,
        "expected_status": check["expected_status"],
        "latency_ms": latency_ms,
        "passed": passed,
        "error_snippet": error_snippet,
        "capability_tags": check["capabilities"],
    }


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
        "| Check | Status | HTTP | Latency (ms) | Capabilities |",
        "|---|---|---:|---:|---|",
    ]
    for row in details:
        status = "PASS" if row["passed"] else "FAIL"
        capabilities = ", ".join(row["capability_tags"])
        lines.append(
            f"| {row['check_name']} | {status} | {row['status_code']} | {row['latency_ms']} | {capabilities} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    checks = _load_checks(args.checks_file)

    metadata = {
        "timestamp": _now_iso8601(args.timestamp),
        "commit_sha": _git_value("rev-parse", "HEAD"),
        "branch": _git_value("rev-parse", "--abbrev-ref", "HEAD"),
        "environment": args.environment,
        "actor": args.actor,
    }

    details = [_run_check(check) for check in checks]
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
