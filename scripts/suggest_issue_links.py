#!/usr/bin/env python3
"""Suggest likely capability->issue_id links for feature-status contract maintenance."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import importlib.util
import sys

_REPORT_FEATURE_STATUS_PATH = Path(__file__).resolve().parent / "report_feature_status.py"
_spec = importlib.util.spec_from_file_location("report_feature_status", _REPORT_FEATURE_STATUS_PATH)
assert _spec and _spec.loader
report_feature_status = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = report_feature_status
_spec.loader.exec_module(report_feature_status)

REPO_ROOT = report_feature_status.REPO_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=Path("docs/qa/feature-status.yaml"))
    parser.add_argument("--gate-summary", type=Path, default=Path("artifacts/all-green-gate-summary.json"))
    parser.add_argument("--issues-dir", type=Path, default=Path("docs/issues"))
    parser.add_argument("--json-output", type=Path, help="Optional path to write JSON suggestions.")
    return parser.parse_args()


def _tokens(value: str) -> set[str]:
    parts = re.split(r"[^a-z0-9]+", value.lower())
    return {part for part in parts if len(part) >= 3 and part != "issue"}


def score_issue(capability_id: str, failed_checks: list[str], issue: report_feature_status.OpenIssue) -> int:
    score = 0
    haystack = f"{issue.issue_id} {issue.title} {issue.path.stem}".lower()
    cap_tokens = _tokens(capability_id)
    check_tokens = {tok for check in failed_checks for tok in _tokens(check)}

    for token in cap_tokens:
        if token in haystack:
            score += 3
    for token in check_tokens:
        if token in haystack:
            score += 1

    if issue.status.lower() in {"open", "in_progress"}:
        score += 1
    return score


def main() -> int:
    args = parse_args()
    contract_path = args.contract if args.contract.is_absolute() else REPO_ROOT / args.contract
    gate_path = args.gate_summary if args.gate_summary.is_absolute() else REPO_ROOT / args.gate_summary
    issues_dir = args.issues_dir if args.issues_dir.is_absolute() else REPO_ROOT / args.issues_dir

    contract = report_feature_status.load_yaml(contract_path)
    gate_results = report_feature_status.load_gate_results(report_feature_status.load_gate_payload(gate_path))
    open_issues = report_feature_status.collect_open_issues(issues_dir)

    suggestions: list[dict[str, Any]] = []
    for capability in contract.get("capabilities", []):
        capability_id = str(capability.get("capability_id", "")).strip()
        if not capability_id:
            continue

        if capability.get("issue_ids") or capability.get("open_issues"):
            continue

        failed_checks = [
            check_name
            for check_name in capability.get("gate_checks", [])
            if gate_results.get(check_name) == "failed"
        ]

        ranked = sorted(
            (
                {
                    "issue_id": issue.issue_id,
                    "title": issue.title,
                    "path": issue.path.relative_to(REPO_ROOT).as_posix(),
                    "score": score_issue(capability_id, failed_checks, issue),
                }
                for issue in open_issues
            ),
            key=lambda it: (-it["score"], it["issue_id"]),
        )
        top = [item for item in ranked if item["score"] > 0][:3]
        suggestions.append(
            {
                "capability_id": capability_id,
                "failed_gate_checks": failed_checks,
                "suggested_issue_ids": [item["issue_id"] for item in top],
                "candidates": top,
            }
        )

    payload = {
        "contract_path": contract_path.relative_to(REPO_ROOT).as_posix(),
        "gate_summary_path": gate_path.relative_to(REPO_ROOT).as_posix(),
        "issues_dir": issues_dir.relative_to(REPO_ROOT).as_posix(),
        "suggestions": suggestions,
    }

    print(json.dumps(payload, indent=2))

    if args.json_output:
        out = args.json_output if args.json_output.is_absolute() else REPO_ROOT / args.json_output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
