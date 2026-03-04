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
    assert summary["continue_on_failure"] is True
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
