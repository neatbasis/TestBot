#!/usr/bin/env python3
"""Validate KPI summary against configured guardrails."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path("config/kpi_guardrails.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=Path("logs/turn_analytics_summary.json"), help="KPI summary JSON path.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Guardrail config JSON path.")
    return parser.parse_args()


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object payload in {path}")
    return payload


def _as_float(name: str, value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    raise ValueError(f"kpi '{name}' must be numeric, got {type(value).__name__}")


def evaluate_thresholds(summary: dict[str, Any], config: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    kpis = config.get("kpis")
    if not isinstance(kpis, dict):
        raise ValueError("config.kpis must be an object")

    for metric, bounds in sorted(kpis.items()):
        if not isinstance(bounds, dict):
            raise ValueError(f"config for metric '{metric}' must be an object")
        if metric not in summary:
            violations.append(f"missing metric '{metric}' in summary")
            continue

        value = _as_float(metric, summary[metric])
        min_value = bounds.get("min")
        max_value = bounds.get("max")

        if min_value is not None:
            min_num = _as_float(f"{metric}.min", min_value)
            if value < min_num:
                violations.append(f"{metric}={value:.4f} below minimum {min_num:.4f}")
        if max_value is not None:
            max_num = _as_float(f"{metric}.max", max_value)
            if value > max_num:
                violations.append(f"{metric}={value:.4f} above maximum {max_num:.4f}")

    return violations


def classify_failure(summary_path: Path, violations: list[str], error: Exception | None) -> str | None:
    if isinstance(error, FileNotFoundError):
        if str(summary_path) in str(error):
            return "missing_input"
        return "schema_error"
    if isinstance(error, (ValueError, json.JSONDecodeError, TypeError)):
        return "schema_error"
    if violations:
        return "threshold_violation"
    return None


def main() -> int:
    args = parse_args()
    summary_path = _resolve(args.summary)
    config_path = _resolve(args.config)

    violations: list[str] = []
    error: Exception | None = None

    try:
        config = _read_json(config_path)
        summary = _read_json(summary_path)
        violations = evaluate_thresholds(summary=summary, config=config)
    except Exception as exc:  # surfaced as structured diagnostics below
        error = exc

    payload = {
        "status": "failed" if error or violations else "passed",
        "summary_path": str(summary_path),
        "config_path": str(config_path),
        "reason_classification": classify_failure(summary_path, violations, error),
        "violations": violations,
    }
    if error is not None:
        payload["error"] = str(error)

    print(json.dumps(payload, indent=2))
    return 1 if error or violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
