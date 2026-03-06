from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_ALL_GREEN_GATE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "all_green_gate.py"
_all_green_gate_spec = importlib.util.spec_from_file_location("all_green_gate", _ALL_GREEN_GATE_PATH)
assert _all_green_gate_spec and _all_green_gate_spec.loader
all_green_gate = importlib.util.module_from_spec(_all_green_gate_spec)
sys.modules[_all_green_gate_spec.name] = all_green_gate
_all_green_gate_spec.loader.exec_module(all_green_gate)


def test_main_fails_fast_when_behave_dependency_missing(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(all_green_gate, "parse_args", lambda: all_green_gate.argparse.Namespace(
        continue_on_failure=False,
        base_ref="origin/main",
        json_output=None,
        kpi_guardrail_mode="optional",
    ))
    monkeypatch.setattr(all_green_gate.importlib.util, "find_spec", lambda _name: None)

    run_gate_called = False

    def fake_run_gate(*_args: object, **_kwargs: object) -> tuple[list[all_green_gate.CheckResult], int]:
        nonlocal run_gate_called
        run_gate_called = True
        return [], 0

    monkeypatch.setattr(all_green_gate, "run_gate", fake_run_gate)

    exit_code = all_green_gate.main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert run_gate_called is False
    assert all_green_gate.BEHAVE_PREFLIGHT_CHECK_NAME in output
    assert "python -m pip install -e .[dev]" in output

    summary = json.loads(output.split("\n\n", maxsplit=1)[0])
    assert summary["status"] == "failed"
    assert summary["checks"][0]["name"] == all_green_gate.BEHAVE_PREFLIGHT_CHECK_NAME



def test_resolve_base_ref_falls_back_when_origin_main_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(all_green_gate, "git_ref_exists", lambda ref: ref == "HEAD~1")

    resolved, notes = all_green_gate.resolve_base_ref("origin/main")

    assert resolved == "HEAD~1"
    assert any("using fallback 'HEAD~1'" in note for note in notes)


def test_main_propagates_effective_base_ref_to_governance_checks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        all_green_gate,
        "parse_args",
        lambda: all_green_gate.argparse.Namespace(
            continue_on_failure=False,
            base_ref="origin/main",
            json_output=None,
            kpi_guardrail_mode="optional",
        ),
    )
    monkeypatch.setattr(all_green_gate.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(all_green_gate, "resolve_base_ref", lambda _ref: ("HEAD~1", []))

    captured_checks: list[all_green_gate.GateCheck] = []

    def fake_run_gate(*, checks: list[all_green_gate.GateCheck], continue_on_failure: bool) -> tuple[list[all_green_gate.CheckResult], int]:
        del continue_on_failure
        captured_checks.extend(checks)
        return [], 0

    monkeypatch.setattr(all_green_gate, "run_gate", fake_run_gate)

    exit_code = all_green_gate.main()

    assert exit_code == 0
    issue_link_cmd = next(c.command for c in captured_checks if c.name == "qa_validate_issue_links")
    issue_cmd = next(c.command for c in captured_checks if c.name == "qa_validate_issues")
    assert issue_link_cmd[-1] == "HEAD~1"
    assert issue_cmd[-1] == "HEAD~1"


def test_build_checks_disables_turn_analytics_when_mode_off() -> None:
    checks = all_green_gate.build_checks(base_ref="origin/main", kpi_guardrail_mode="off")

    check_names = [check.name for check in checks]
    assert "qa_aggregate_turn_analytics" not in check_names
    assert "qa_validate_kpi_guardrails" not in check_names


def test_build_checks_adds_optional_turn_analytics_checks() -> None:
    checks = all_green_gate.build_checks(base_ref="origin/main", kpi_guardrail_mode="optional")

    aggregate_check = next(check for check in checks if check.name == "qa_aggregate_turn_analytics")
    kpi_check = next(check for check in checks if check.name == "qa_validate_kpi_guardrails")

    assert aggregate_check.command[1:] == [
        "scripts/aggregate_turn_analytics.py",
        "--input",
        "logs/session.jsonl",
        "--output",
        "logs/turn_analytics.jsonl",
        "--summary-output",
        "logs/turn_analytics_summary.json",
    ]
    assert kpi_check.command[1:] == [
        "scripts/validate_kpi_guardrails.py",
        "--summary",
        "logs/turn_analytics_summary.json",
        "--config",
        "config/kpi_guardrails.json",
    ]
    assert aggregate_check.blocking is False
    assert kpi_check.blocking is False


def test_run_gate_marks_optional_failure_as_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    checks = [all_green_gate.GateCheck(name="optional", command=["optional"], blocking=False)]

    def fake_run_check(_check: all_green_gate.GateCheck) -> all_green_gate.CheckResult:
        return all_green_gate.CheckResult(
            name="optional",
            command="optional",
            status="failed",
            exit_code=2,
            duration_s=0.01,
        )

    monkeypatch.setattr(all_green_gate, "run_check", fake_run_check)

    results, exit_code = all_green_gate.run_gate(checks=checks, continue_on_failure=False)

    assert results[0].status == "warning"
    assert exit_code == 0


def test_run_gate_enforces_blocking_turn_analytics_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    checks = [
        all_green_gate.GateCheck(name="qa_aggregate_turn_analytics", command=["aggregate"], blocking=True),
        all_green_gate.GateCheck(name="later_blocking", command=["later"], blocking=True),
    ]

    def fake_run_check(_check: all_green_gate.GateCheck) -> all_green_gate.CheckResult:
        return all_green_gate.CheckResult(
            name="qa_aggregate_turn_analytics",
            command="aggregate",
            status="failed",
            exit_code=1,
            duration_s=0.01,
        )

    monkeypatch.setattr(all_green_gate, "run_check", fake_run_check)

    results, exit_code = all_green_gate.run_gate(checks=checks, continue_on_failure=False)

    assert [result.status for result in results] == ["failed", "not_run"]
    assert exit_code == 1
