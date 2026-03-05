from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


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
                        "capabilities": ["auth", "notifications", "auth"],
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

    completed = subprocess.run(command, capture_output=True, text=True)
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

    detail = json.loads(details_path.read_text(encoding="utf-8").strip())
    assert detail["check_name"] == "localhost-unreachable"
    assert detail["request_target"] == "http://127.0.0.1:9/healthz"
    assert detail["passed"] is False
    assert detail["capability_tags"] == ["auth", "notifications"]
    assert isinstance(detail["latency_ms"], int)
    assert detail["error_snippet"]
