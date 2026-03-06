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

