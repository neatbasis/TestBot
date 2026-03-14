from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_kpi_guardrails.py"
_spec = importlib.util.spec_from_file_location("validate_kpi_guardrails", _VALIDATOR_PATH)
assert _spec and _spec.loader
validator = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = validator
_spec.loader.exec_module(validator)


def test_evaluate_thresholds_passes_when_all_metrics_within_bounds() -> None:
    summary = {
        "grounded_answer_precision": 0.9,
        "false_knowing_rate": 0.01,
        "fallback_appropriateness": 0.8,
        "citation_completeness": 0.82,
    }
    config = {
        "kpis": {
            "grounded_answer_precision": {"min": 0.75},
            "false_knowing_rate": {"max": 0.05},
            "fallback_appropriateness": {"min": 0.7},
            "citation_completeness": {"min": 0.7},
        }
    }

    assert validator.evaluate_thresholds(summary=summary, config=config) == []


def test_evaluate_thresholds_flags_regressions_and_missing_metric() -> None:
    summary = {
        "grounded_answer_precision": 0.6,
        "false_knowing_rate": 0.2,
        "fallback_appropriateness": 0.8,
    }
    config = {
        "kpis": {
            "grounded_answer_precision": {"min": 0.75},
            "false_knowing_rate": {"max": 0.05},
            "fallback_appropriateness": {"min": 0.7},
            "citation_completeness": {"min": 0.7},
        }
    }

    violations = validator.evaluate_thresholds(summary=summary, config=config)

    assert "grounded_answer_precision=0.6000 below minimum 0.7500" in violations
    assert "false_knowing_rate=0.2000 above maximum 0.0500" in violations
    assert "missing metric 'citation_completeness' in summary" in violations


def test_evaluate_thresholds_rejects_non_numeric_metric() -> None:
    summary = {"grounded_answer_precision": "high"}
    config = {"kpis": {"grounded_answer_precision": {"min": 0.75}}}

    with pytest.raises(ValueError, match="must be numeric"):
        validator.evaluate_thresholds(summary=summary, config=config)


def test_classify_failure_identifies_missing_summary_input() -> None:
    summary_path = Path('/tmp/turn_analytics_summary.json')

    reason = validator.classify_failure(
        summary_path=summary_path,
        violations=[],
        error=FileNotFoundError(f"missing file: {summary_path}"),
    )

    assert reason == "missing_input"


def test_classify_failure_identifies_threshold_violation() -> None:
    reason = validator.classify_failure(
        summary_path=Path('/tmp/turn_analytics_summary.json'),
        violations=["false_knowing_rate=0.2000 above maximum 0.0500"],
        error=None,
    )

    assert reason == "threshold_violation"
