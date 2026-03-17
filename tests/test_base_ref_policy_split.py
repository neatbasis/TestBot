from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


all_green_gate = _load_module("all_green_gate", _SCRIPTS_DIR / "all_green_gate.py")
validate_issue_links = _load_module("validate_issue_links", _SCRIPTS_DIR / "validate_issue_links.py")


def test_base_ref_policy_split_between_diff_checks_and_commit_traceability() -> None:
    """Diff-oriented checks accept fallback refs while commit traceability fails closed."""
    readiness_checks = all_green_gate.build_checks(base_ref="HEAD~1", profile="readiness")
    issue_link_check = next(check for check in readiness_checks if check.name == "qa_validate_issue_links")

    assert issue_link_check.command[-1] == "HEAD~1"

    failures: list[validate_issue_links.ValidationFailure] = []
    allowed = validate_issue_links.commit_traceability_requires_exact_base_ref(
        requested_base_ref="origin/main",
        effective_base_ref="HEAD~1",
        allow_degraded_commit_traceability=False,
        failures=failures,
    )

    assert allowed is False
    assert failures
    assert "fail closed" in failures[0].message
