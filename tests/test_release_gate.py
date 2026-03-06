from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_RELEASE_GATE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "release_gate.py"
_release_gate_spec = importlib.util.spec_from_file_location("release_gate", _RELEASE_GATE_PATH)
assert _release_gate_spec and _release_gate_spec.loader
release_gate = importlib.util.module_from_spec(_release_gate_spec)
sys.modules[_release_gate_spec.name] = release_gate
_release_gate_spec.loader.exec_module(release_gate)


@pytest.fixture
def checks() -> list[release_gate.GateCheck]:
    return [
        release_gate.GateCheck(name="first", command=["first"]),
        release_gate.GateCheck(name="second", command=["second"]),
        release_gate.GateCheck(name="third", command=["third"]),
    ]


def test_run_gate_fail_closed_stops_after_first_failure(monkeypatch: pytest.MonkeyPatch, checks: list[release_gate.GateCheck]) -> None:
    calls: list[str] = []

    def fake_run_check(check: release_gate.GateCheck) -> release_gate.CheckResult:
        calls.append(check.name)
        if check.name == "first":
            return release_gate.CheckResult(
                name=check.name,
                command=check.command[0],
                status="failed",
                exit_code=2,
                duration_s=0.01,
            )
        return release_gate.CheckResult(
            name=check.name,
            command=check.command[0],
            status="passed",
            exit_code=0,
            duration_s=0.01,
        )

    monkeypatch.setattr(release_gate, "run_check", fake_run_check)

    results, exit_code = release_gate.run_gate(checks=checks, continue_on_failure=False)

    assert calls == ["first"]
    assert [result.status for result in results] == ["failed", "not_run", "not_run"]
    assert exit_code == 1


def test_run_gate_continue_on_failure_executes_all(monkeypatch: pytest.MonkeyPatch, checks: list[release_gate.GateCheck]) -> None:
    calls: list[str] = []

    def fake_run_check(check: release_gate.GateCheck) -> release_gate.CheckResult:
        calls.append(check.name)
        status = "failed" if check.name == "second" else "passed"
        code = 1 if status == "failed" else 0
        return release_gate.CheckResult(
            name=check.name,
            command=check.command[0],
            status=status,
            exit_code=code,
            duration_s=0.01,
        )

    monkeypatch.setattr(release_gate, "run_check", fake_run_check)

    results, exit_code = release_gate.run_gate(checks=checks, continue_on_failure=True)

    assert calls == ["first", "second", "third"]
    assert [result.status for result in results] == ["passed", "failed", "passed"]
    assert exit_code == 1


def test_run_check_treats_missing_command_as_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_subprocess_run(*_args: object, **_kwargs: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(release_gate.subprocess, "run", fake_subprocess_run)

    result = release_gate.run_check(release_gate.GateCheck(name="missing", command=["definitely_missing"]))

    assert result.status == "failed"
    assert result.exit_code == 127


def test_summarize_reports_per_check_fields(checks: list[release_gate.GateCheck]) -> None:
    results = [
        release_gate.CheckResult(name=checks[0].name, command="first", status="passed", exit_code=0, duration_s=0.1),
        release_gate.CheckResult(name=checks[1].name, command="second", status="failed", exit_code=1, duration_s=0.2),
    ]

    summary = release_gate.summarize(results=results, continue_on_failure=True)

    assert summary["status"] == "failed"
    assert summary["exit_code"] == 1
    assert summary["continue_on_failure"] is True
    assert summary["warning_count"] == 0
    assert summary["checks"] == [
        {
            "name": "first",
            "command": "first",
            "status": "passed",
            "exit_code": 0,
            "duration_s": 0.1,
        },
        {
            "name": "second",
            "command": "second",
            "status": "failed",
            "exit_code": 1,
            "duration_s": 0.2,
        },
    ]


def test_build_checks_order_and_commands() -> None:
    checks = release_gate.build_checks()

    assert [check.name for check in checks] == [
        "behave",
        "pytest_source_and_provenance_fast",
        "pytest_non_live_smoke",
        "pytest_eval_runtime_parity",
        "validate_issue_links",
        "validate_issues",
        "validate_kpi_guardrails",
    ]
    assert checks[0].command[1:] == ["-m", "behave"]
    assert checks[1].command[1:] == [
        "-m",
        "pytest",
        "tests/test_vector_store.py",
        "tests/test_source_fusion.py",
        "tests/test_log_schema_validation.py",
    ]
    assert checks[2].command[1:] == ["-m", "pytest", "-m", "not live_smoke"]
    assert checks[3].command[1:] == ["-m", "pytest", "tests/test_eval_runtime_parity.py"]
    assert checks[4].command[1:] == [
        "scripts/validate_issue_links.py",
        "--all-issue-files",
        "--base-ref",
        "origin/main",
    ]
    assert checks[5].command[1:] == [
        "scripts/validate_issues.py",
        "--all-issue-files",
        "--base-ref",
        "origin/main",
    ]
    assert checks[6].command[1:] == [
        "scripts/validate_kpi_guardrails.py",
        "--summary",
        "logs/turn_analytics_summary.json",
        "--config",
        "config/kpi_guardrails.json",
    ]
    assert checks[6].blocking is False


def test_build_checks_includes_optional_replay_report() -> None:
    checks = release_gate.build_checks(replay_report=True)

    assert checks[-1].name == "replay_report"
    assert checks[-1].blocking is False
    assert checks[-1].command[1:] == [
        "scripts/aggregate_turn_analytics.py",
        "--input",
        "logs/session.jsonl",
        "--output",
        "logs/turn_analytics.jsonl",
        "--summary-output",
        "logs/turn_analytics_summary.json",
    ]


def test_non_blocking_check_is_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    checks = [release_gate.GateCheck(name="optional", command=["optional"], blocking=False)]

    def fake_run_check(_check: release_gate.GateCheck) -> release_gate.CheckResult:
        return release_gate.CheckResult(
            name="optional",
            command="optional",
            status="failed",
            exit_code=2,
            duration_s=0.01,
        )

    monkeypatch.setattr(release_gate, "run_check", fake_run_check)

    results, exit_code = release_gate.run_gate(checks=checks, continue_on_failure=False)

    assert results[0].status == "warning"
    assert exit_code == 0




def test_main_fails_fast_when_behave_dependency_missing(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(release_gate, "parse_args", lambda: release_gate.argparse.Namespace(
        continue_on_failure=False,
        json_output=None,
        base_ref="origin/main",
        replay_report=False,
        kpi_guardrail_mode="optional",
    ))
    monkeypatch.setattr(release_gate.importlib.util, "find_spec", lambda _name: None)

    run_gate_called = False

    def fake_run_gate(*_args: object, **_kwargs: object) -> tuple[list[release_gate.CheckResult], int]:
        nonlocal run_gate_called
        run_gate_called = True
        return [], 0

    monkeypatch.setattr(release_gate, "run_gate", fake_run_gate)

    exit_code = release_gate.main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert run_gate_called is False
    assert release_gate.BEHAVE_PREFLIGHT_CHECK_NAME in output
    assert "python -m pip install -e .[dev]" in output

def test_main_prints_parity_divergence_hint(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(release_gate, "parse_args", lambda: release_gate.argparse.Namespace(
        continue_on_failure=False,
        json_output=None,
        base_ref="origin/main",
        replay_report=False,
        kpi_guardrail_mode="optional",
    ))
    monkeypatch.setattr(release_gate.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(release_gate, "build_checks", lambda **_kwargs: [])
    monkeypatch.setattr(
        release_gate,
        "run_gate",
        lambda **_kwargs: (
            [
                release_gate.CheckResult(
                    name="pytest_eval_runtime_parity",
                    command="python -m pytest tests/test_eval_runtime_parity.py",
                    status="failed",
                    exit_code=1,
                    duration_s=0.1,
                )
            ],
            1,
        ),
    )

    exit_code = release_gate.main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Parity gate failed" in output
    assert "scripts/eval_recall.py <-> testbot.rerank" in output


def test_build_checks_allows_blocking_kpi_guardrail_mode() -> None:
    checks = release_gate.build_checks(kpi_guardrail_mode="blocking")
    kpi_check = next(check for check in checks if check.name == "validate_kpi_guardrails")
    assert kpi_check.blocking is True


def test_build_checks_allows_disabling_kpi_guardrail_mode() -> None:
    checks = release_gate.build_checks(kpi_guardrail_mode="off")
    assert all(check.name != "validate_kpi_guardrails" for check in checks)
