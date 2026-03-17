#!/usr/bin/env python3
"""Validate roadmap snapshot consistency against canonical generated artifacts."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROADMAP_PATH = REPO_ROOT / "docs" / "roadmap" / "current-status-and-next-5-priorities.md"
DEFAULT_GATE_SUMMARY_PATH = REPO_ROOT / "artifacts" / "all-green-gate-summary.json"
DEFAULT_FEATURE_REPORT_PATH = REPO_ROOT / "docs" / "qa" / "feature-status-report.md"

TIMESTAMP_PATTERN = re.compile(r"- Timestamp \(UTC\): `([^`]+)`")
GATE_STATUS_PATTERN = re.compile(r"- Gate status: `([^`]+)`")
ROADMAP_CAPABILITY_PATTERN = re.compile(
    r"- Capability summary line \(`docs/qa/feature-status-report\.md`\): \*\*(.+?)\*\*\."
)
FEATURE_REPORT_CAPABILITY_PATTERN = re.compile(
    r"Implemented:\s*\*\*(\d+)\*\*\s*\|\s*Partial:\s*\*\*(\d+)\*\*\s*\|\s*Missing:\s*\*\*(\d+)\*\*"
)

REFRESH_COMMANDS = [
    "python scripts/all_green_gate.py --json-output artifacts/all-green-gate-summary.json",
    "python scripts/report_feature_status.py --output docs/qa/feature-status-report.md --json-output artifacts/feature-status-summary.json",
]


@dataclass(frozen=True)
class ValidationResult:
    warnings: list[str]


def parse_utc_timestamp(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)


def require_match(pattern: re.Pattern[str], text: str, description: str) -> str:
    match = pattern.search(text)
    if not match:
        raise ValueError(f"Could not find {description} in source document.")
    return match.group(1).strip()


def normalize_capability_summary(raw: str) -> str:
    numbers = re.findall(r"\d+", raw)
    if len(numbers) != 3:
        raise ValueError("Capability summary line must include implemented/partial/missing counts.")
    implemented, partial, missing = numbers
    return f"Implemented: {implemented} | Partial: {partial} | Missing: {missing}"


def validate_consistency(
    *,
    roadmap_path: Path,
    gate_summary_path: Path,
    feature_report_path: Path,
    max_staleness_seconds: int,
) -> ValidationResult:
    warnings: list[str] = []

    roadmap_text = roadmap_path.read_text(encoding="utf-8")
    feature_report_text = feature_report_path.read_text(encoding="utf-8")

    roadmap_snapshot_timestamp = parse_utc_timestamp(require_match(TIMESTAMP_PATTERN, roadmap_text, "roadmap snapshot timestamp"))
    roadmap_gate_status = require_match(GATE_STATUS_PATTERN, roadmap_text, "roadmap gate status")

    feature_report_match = FEATURE_REPORT_CAPABILITY_PATTERN.search(feature_report_text)
    if not feature_report_match:
        raise ValueError("Could not find feature report capability summary block.")
    feature_report_capability = normalize_capability_summary(" | ".join(feature_report_match.groups()))
    roadmap_capability = normalize_capability_summary(
        require_match(ROADMAP_CAPABILITY_PATTERN, roadmap_text, "roadmap capability summary line")
    )

    gate_summary_status = json.loads(gate_summary_path.read_text(encoding="utf-8")).get("status")
    if not gate_summary_status:
        raise ValueError("Gate summary JSON is missing top-level 'status'.")

    gate_artifact_timestamp = datetime.fromtimestamp(gate_summary_path.stat().st_mtime, tz=timezone.utc)
    staleness_seconds = (gate_artifact_timestamp - roadmap_snapshot_timestamp).total_seconds()

    if staleness_seconds > max_staleness_seconds:
        warnings.append(
            "Roadmap snapshot timestamp is stale versus gate artifact mtime: "
            f"roadmap={roadmap_snapshot_timestamp.isoformat()} gate_artifact_mtime={gate_artifact_timestamp.isoformat()} "
            f"delta_s={int(staleness_seconds)} threshold_s={max_staleness_seconds}."
        )

    if roadmap_gate_status != gate_summary_status:
        warnings.append(
            f"Roadmap gate status mismatch: roadmap={roadmap_gate_status} gate_artifact={gate_summary_status}."
        )

    if roadmap_capability != feature_report_capability:
        warnings.append(
            "Roadmap capability summary mismatch: "
            f"roadmap='{roadmap_capability}' feature_report='{feature_report_capability}'."
        )

    return ValidationResult(warnings=warnings)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roadmap", type=Path, default=DEFAULT_ROADMAP_PATH)
    parser.add_argument("--gate-summary", type=Path, default=DEFAULT_GATE_SUMMARY_PATH)
    parser.add_argument("--feature-report", type=Path, default=DEFAULT_FEATURE_REPORT_PATH)
    parser.add_argument(
        "--max-staleness-seconds",
        type=int,
        default=86400,
        help="Maximum allowed lag before roadmap snapshot is considered stale versus gate artifact mtime.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_consistency(
        roadmap_path=args.roadmap,
        gate_summary_path=args.gate_summary,
        feature_report_path=args.feature_report,
        max_staleness_seconds=args.max_staleness_seconds,
    )

    if not result.warnings:
        print("Roadmap consistency check passed: snapshot timestamp, gate status, and capability summary are aligned.")
        return 0

    print("Roadmap consistency check reported stale state warnings:")
    for warning in result.warnings:
        print(f"- WARNING: {warning}")

    print("Refresh commands:")
    for command in REFRESH_COMMANDS:
        print(f"  {command}")
    print("  Update docs/roadmap/current-status-and-next-5-priorities.md with refreshed timestamp/status/capability fields.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
