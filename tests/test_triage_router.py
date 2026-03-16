from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_TRIAGE_ROUTER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "triage_router.py"
_triage_router_spec = importlib.util.spec_from_file_location("triage_router", _TRIAGE_ROUTER_PATH)
assert _triage_router_spec and _triage_router_spec.loader
triage_router = importlib.util.module_from_spec(_triage_router_spec)
sys.modules[_triage_router_spec.name] = triage_router
_triage_router_spec.loader.exec_module(triage_router)


def test_route_failures_prefers_directory_route() -> None:
    summary = {
        "status": "failed",
        "checks": [
            {
                "name": "qa_pytest_not_live_smoke",
                "stage": "qa",
                "status": "failed",
                "command": "python -m pytest",
            }
        ],
    }
    routing = {
        "defaults": {"owner_role": "qa_governance_owner", "severity": "amber"},
        "check_routes": {
            "qa_pytest_not_live_smoke": {"owner_role": "qa_automation_owner", "severity": "amber"}
        },
        "directory_routes": [
            {"path_prefix": "src/testbot/", "owner_role": "runtime_pipeline_owner", "severity": "red"}
        ],
    }

    payload = triage_router.route_failures(summary=summary, routing=routing, changed_dirs=["src/testbot/"])

    recommendation = payload["recommendations"][0]
    assert recommendation["owner_role"] == "runtime_pipeline_owner"
    assert recommendation["severity_suggestion"] == "red"
    assert payload["overall_severity_suggestion"] == "red"


def test_main_writes_output_file(tmp_path: Path, monkeypatch) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "status": "failed",
                "checks": [
                    {
                        "name": "product_behave",
                        "stage": "product",
                        "status": "failed",
                        "command": "python -m behave",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    routing_path = tmp_path / "routing.yaml"
    routing_path.write_text(
        """
defaults:
  owner_role: qa_governance_owner
  severity: amber
check_routes:
  product_behave:
    owner_role: runtime_pipeline_owner
    severity: amber
directory_routes: []
""".strip()
        + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "triage.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "triage_router.py",
            "--summary",
            str(summary_path),
            "--routing-config",
            str(routing_path),
            "--changed-dir",
            "scripts/",
            "--output",
            str(output_path),
        ],
    )

    exit_code = triage_router.main()

    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["recommendations"][0]["owner_role"] == "runtime_pipeline_owner"
