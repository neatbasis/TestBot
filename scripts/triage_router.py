#!/usr/bin/env python3
"""Route failing gate checks to likely owners and issue severity suggestions."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY_PATH = Path("artifacts/all-green-gate-summary.json")
DEFAULT_ROUTING_CONFIG = Path("docs/qa/triage-routing.yaml")
SEVERITY_RANK = {"green": 0, "amber": 1, "red": 2}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_SUMMARY_PATH,
        help="Path to all-green gate JSON summary.",
    )
    parser.add_argument(
        "--routing-config",
        type=Path,
        default=DEFAULT_ROUTING_CONFIG,
        help="Path to owner/severity routing configuration YAML.",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Git base ref used for changed-directory detection.",
    )
    parser.add_argument(
        "--changed-dir",
        action="append",
        default=None,
        help="Optional changed directory override (repeatable). Bypasses git diff detection when provided.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON output path for triage recommendations.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}, got {type(payload).__name__}")
    return payload


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected YAML object at {path}, got {type(payload).__name__}")
    return payload


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def detect_changed_directories(base_ref: str) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return []

    changed_dirs: set[str] = set()
    for line in completed.stdout.splitlines():
        path = line.strip()
        if not path:
            continue
        parent = Path(path).parent.as_posix()
        changed_dirs.add("." if parent == "." else f"{parent}/")
    return sorted(changed_dirs)


def _stage_defaults(stage: str) -> tuple[str, str]:
    if stage in {"product", "safety", "ops"}:
        return ("runtime_pipeline_owner", "amber")
    return ("qa_governance_owner", "green")


def _route_for_directory(changed_dirs: list[str], directory_routes: list[dict[str, str]]) -> tuple[str | None, str | None, str | None]:
    for changed_dir in changed_dirs:
        for route in directory_routes:
            prefix = str(route.get("path_prefix", "")).strip()
            if not prefix:
                continue
            normalized_prefix = prefix if prefix.endswith("/") else f"{prefix}/"
            if changed_dir.startswith(normalized_prefix):
                return (
                    route.get("owner_role"),
                    route.get("severity"),
                    normalized_prefix,
                )
    return None, None, None


def route_failures(summary: dict[str, Any], routing: dict[str, Any], changed_dirs: list[str]) -> dict[str, Any]:
    checks = summary.get("checks", [])
    if not isinstance(checks, list):
        checks = []

    failed_checks = [
        check for check in checks if isinstance(check, dict) and check.get("status") == "failed"
    ]

    check_routes = routing.get("check_routes", {})
    directory_routes = routing.get("directory_routes", [])
    default_owner = str(routing.get("defaults", {}).get("owner_role", "qa_governance_owner"))
    default_severity = str(routing.get("defaults", {}).get("severity", "amber"))

    recommendations: list[dict[str, Any]] = []
    overall_severity = default_severity

    for failed_check in failed_checks:
        check_name = str(failed_check.get("name", "unknown_check"))
        stage = str(failed_check.get("stage", "qa"))

        check_route = check_routes.get(check_name, {}) if isinstance(check_routes, dict) else {}
        stage_owner, stage_severity = _stage_defaults(stage)
        dir_owner, dir_severity, matched_prefix = _route_for_directory(changed_dirs, directory_routes)

        owner_role = dir_owner or check_route.get("owner_role") or stage_owner or default_owner
        severity = dir_severity or check_route.get("severity") or stage_severity or default_severity
        severity = severity if severity in SEVERITY_RANK else default_severity

        if SEVERITY_RANK[severity] > SEVERITY_RANK.get(overall_severity, 0):
            overall_severity = severity

        recommendations.append(
            {
                "check_name": check_name,
                "stage": stage,
                "owner_role": owner_role,
                "severity_suggestion": severity,
                "matched_directory_prefix": matched_prefix,
                "failure_command": failed_check.get("command"),
                "draft_issue": {
                    "title": f"[{severity.upper()}] {check_name} failed in canonical all-green gate",
                    "summary": (
                        f"Canonical gate check `{check_name}` failed while validating changed directories: "
                        f"{', '.join(changed_dirs) if changed_dirs else 'unknown'}"
                    ),
                    "template": {
                        "owner_role": owner_role,
                        "severity": severity,
                        "affected_checks": [check_name],
                        "changed_directories": changed_dirs,
                        "reproduction_command": failed_check.get("command"),
                        "acceptance_criteria": [
                            f"{check_name} passes in scripts/all_green_gate.py",
                            "All updated tests/docs are deterministic and aligned with directives.",
                        ],
                    },
                },
            }
        )

    return {
        "summary_status": summary.get("status"),
        "changed_directories": changed_dirs,
        "overall_severity_suggestion": overall_severity,
        "recommendations": recommendations,
    }


def main() -> int:
    args = parse_args()
    summary_path = _resolve_path(args.summary)
    routing_path = _resolve_path(args.routing_config)

    if not summary_path.exists():
        raise SystemExit(f"Summary file not found: {summary_path}")
    if not routing_path.exists():
        raise SystemExit(f"Routing config not found: {routing_path}")

    summary = _load_json(summary_path)
    routing = _load_yaml(routing_path)

    changed_dirs = sorted(set(args.changed_dir or detect_changed_directories(args.base_ref)))
    triage_payload = route_failures(summary=summary, routing=routing, changed_dirs=changed_dirs)

    output_json = json.dumps(triage_payload, indent=2)
    print(output_json)

    if args.output:
        out_path = _resolve_path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_json + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
