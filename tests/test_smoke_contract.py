from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class _OkHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


@contextmanager
def _local_ok_server() -> str:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _OkHandler)
    host, port = server.server_address
    import threading

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{host}:{port}/healthz"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _smoke_env() -> dict[str, str]:
    return {
        "HA_API_URL": "http://127.0.0.1:8123",
        "HA_API_SECRET": "ha-test-supersecret-token",
        "HA_SATELLITE_ENTITY_ID": "assist_satellite.test",
        "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
        "OLLAMA_MODEL": "llama3.1:latest",
        "OLLAMA_EMBEDDING_MODEL": "nomic-embed-text",
        "SMOKE_CONNECT_TIMEOUT_S": "2",
        "SMOKE_REQUEST_TIMEOUT_S": "3",
    }


def test_live_smoke_runner_writes_contract_artifacts(tmp_path: Path) -> None:
    checks_file = tmp_path / "checks.json"
    checks_file.write_text(
        json.dumps(
            {
                "checks": [
                    {
                        "name": "localhost-unreachable",
                        "target": "http://127.0.0.1:9/healthz",
                        "expected_status": 200,
                        "capability_id": "cap-auth-service-availability",
                        "capability_name": "Authentication service availability",
                        "business_impact": "Users cannot sign in if authentication health fails.",
                        "severity_if_broken": "critical",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    output_dir = tmp_path / "out"
    command = [
        sys.executable,
        "scripts/smoke/run_live_smoke.py",
        "--checks-file",
        str(checks_file),
        "--output-dir",
        str(output_dir),
        "--environment",
        "ci",
        "--actor",
        "test-runner",
        "--timestamp",
        "2026-03-05T00:00:00Z",
        "--report-md",
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env={**_smoke_env(), "PATH": os.environ.get("PATH", "")},
    )
    assert completed.returncode == 1

    summary_path = output_dir / "smoke-summary.json"
    details_path = output_dir / "smoke-details.jsonl"
    report_path = output_dir / "smoke-report.md"

    assert summary_path.exists()
    assert details_path.exists()
    assert report_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["metadata"]["timestamp"] == "2026-03-05T00:00:00Z"
    assert summary["metadata"]["environment"] == "ci"
    assert summary["metadata"]["actor"] == "test-runner"
    assert summary["counts"] == {"total": 1, "passed": 0, "failed": 1}
    assert summary["gate_status"] == "fail"
    assert summary["validated_capabilities"] == []

    detail = json.loads(details_path.read_text(encoding="utf-8").strip())
    assert detail["check_name"] == "localhost-unreachable"
    assert detail["request_target"] == "http://127.0.0.1:9/healthz"
    assert detail["passed"] is False
    assert detail["capability_id"] == "cap-auth-service-availability"
    assert detail["capability_name"] == "Authentication service availability"
    assert detail["business_impact"] == "Users cannot sign in if authentication health fails."
    assert detail["severity_if_broken"] == "critical"
    assert isinstance(detail["latency_ms"], int)
    assert detail["error_snippet"]


def test_live_smoke_report_lists_validated_capabilities(tmp_path: Path) -> None:
    with _local_ok_server() as target:
        checks_file = tmp_path / "checks.json"
        checks_file.write_text(
            json.dumps(
                {
                    "checks": [
                        {
                            "name": "healthz",
                            "target": target,
                            "expected_status": 200,
                            "capability_id": "cap-auth-service-availability",
                            "capability_name": "Authentication service availability",
                            "business_impact": "Users cannot sign in if authentication health fails.",
                            "severity_if_broken": "critical",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        output_dir = tmp_path / "out"
        command = [
            sys.executable,
            "scripts/smoke/run_live_smoke.py",
            "--checks-file",
            str(checks_file),
            "--output-dir",
            str(output_dir),
            "--report-md",
        ]

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            env={**_smoke_env(), "PATH": os.environ.get("PATH", "")},
        )
        assert completed.returncode == 0

    summary = json.loads((output_dir / "smoke-summary.json").read_text(encoding="utf-8"))
    assert summary["validated_capabilities"] == [
        {
            "capability_id": "cap-auth-service-availability",
            "capability_name": "Authentication service availability",
            "business_impact": "Users cannot sign in if authentication health fails.",
            "severity_if_broken": "critical",
            "validated_by_check": "healthz",
        }
    ]

    report = (output_dir / "smoke-report.md").read_text(encoding="utf-8")
    assert "## Validated Capabilities" in report
    assert "Authentication service availability" in report


def test_live_smoke_runner_fails_with_clear_env_error(tmp_path: Path) -> None:
    checks_file = tmp_path / "checks.json"
    checks_file.write_text(
        json.dumps(
            {
                "checks": [
                    {
                        "name": "healthz",
                        "target": "http://127.0.0.1:9/healthz",
                        "expected_status": 200,
                        "capability_id": "cap-auth-service-availability",
                        "capability_name": "Authentication service availability",
                        "business_impact": "Users cannot sign in if authentication health fails.",
                        "severity_if_broken": "critical",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    command = [
        sys.executable,
        "scripts/smoke/run_live_smoke.py",
        "--checks-file",
        str(checks_file),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env={"PATH": os.environ.get("PATH", "")},
    )
    assert completed.returncode == 2
    assert "Missing required environment variables in process environment" in completed.stdout
