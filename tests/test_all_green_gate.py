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


def _result(
    *,
    name: str,
    command: str,
    status: str,
    exit_code: int | None,
    duration_s: float,
    artifact_path: str | None = None,
    diagnostic_reason: str | None = None,
) -> all_green_gate.CheckResult:
    return all_green_gate.CheckResult(
        name=name,
        stage=all_green_gate.stage_name_for_check(name),
        command=command,
        status=status,
        exit_code=exit_code,
        duration_s=duration_s,
        artifact_path=artifact_path,
        diagnostic_reason=diagnostic_reason,
    )


def test_main_fails_fast_when_behave_dependency_missing(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(all_green_gate, "parse_args", lambda: all_green_gate.argparse.Namespace(
        continue_on_failure=False,
        base_ref="origin/main",
        json_output=None,
        profile="triage",
        kpi_guardrail_mode="optional",
        force_full_governance=False,
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
    assert summary["remediation"] == [all_green_gate.BEHAVE_REMEDIATION_MESSAGE]





def test_main_writes_behave_remediation_to_json_summary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    summary_path = tmp_path / "all-green-summary.json"
    monkeypatch.setattr(
        all_green_gate,
        "parse_args",
        lambda: all_green_gate.argparse.Namespace(
            continue_on_failure=False,
            base_ref="origin/main",
            json_output=summary_path,
            profile="readiness",
            kpi_guardrail_mode="optional",
            force_full_governance=False,
        ),
    )
    monkeypatch.setattr(all_green_gate.importlib.util, "find_spec", lambda _name: None)

    exit_code = all_green_gate.main()

    assert exit_code == 1
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["checks"][0]["name"] == all_green_gate.BEHAVE_PREFLIGHT_CHECK_NAME
    assert payload["remediation"] == [all_green_gate.BEHAVE_REMEDIATION_MESSAGE]


def test_resolve_base_ref_falls_back_when_origin_main_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(all_green_gate, "git_ref_exists", lambda ref: ref == "HEAD~1")

    resolved, notes = all_green_gate.resolve_base_ref("origin/main")

    assert resolved == "HEAD~1"
    assert any("falling back to 'HEAD~1'" in note for note in notes)
    assert any("This is expected in Codex task containers or shallow CI clones." in note for note in notes)


def test_main_propagates_effective_base_ref_to_governance_checks_in_readiness_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        all_green_gate,
        "parse_args",
        lambda: all_green_gate.argparse.Namespace(
            continue_on_failure=False,
            base_ref="origin/main",
            json_output=None,
            profile="readiness",
            kpi_guardrail_mode="optional",
            force_full_governance=False,
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
    checks = all_green_gate.build_checks(base_ref="origin/main", kpi_guardrail_mode="off", profile="readiness")

    check_names = [check.name for check in checks]
    assert "qa_aggregate_turn_analytics" not in check_names
    assert "qa_validate_kpi_guardrails" not in check_names


def test_build_checks_adds_optional_turn_analytics_checks() -> None:
    checks = all_green_gate.build_checks(base_ref="origin/main", kpi_guardrail_mode="optional", profile="readiness")

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
        return _result(name="optional", command="optional", status="failed", exit_code=2, duration_s=0.01)

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
        return _result(
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


def test_build_checks_includes_pipeline_stage_conformance_validator() -> None:
    checks = all_green_gate.build_checks(base_ref="origin/main", kpi_guardrail_mode="optional", profile="readiness")

    check = next(check for check in checks if check.name == "safety_validate_pipeline_stage_conformance")
    assert check.command[1:] == ["scripts/validate_pipeline_stage_conformance.py"]

def test_build_checks_readiness_profile_has_expected_check_names() -> None:
    checks = all_green_gate.build_checks(base_ref="origin/main", kpi_guardrail_mode="optional", profile="readiness")

    assert [check.name for check in checks] == [
        "product_behave",
        "product_eval_recall_topk4",
        "safety_validate_log_schema",
        "safety_validate_pipeline_stage_conformance",
        "qa_pytest_not_live_smoke",
        "qa_validate_issue_links",
        "qa_validate_issues",
        "qa_validate_invariant_sync",
        "qa_validate_markdown_paths",
        "qa_aggregate_turn_analytics",
        "qa_validate_kpi_guardrails",
    ]


def test_build_checks_triage_profile_excludes_governance_checks() -> None:
    checks = all_green_gate.build_checks(base_ref="origin/main", kpi_guardrail_mode="optional", profile="triage")

    check_names = [check.name for check in checks]
    assert "qa_validate_issue_links" not in check_names
    assert "qa_validate_issues" not in check_names
    assert "qa_aggregate_turn_analytics" not in check_names


def test_build_checks_readiness_profile_has_no_duplicate_pytest_file_payloads() -> None:
    checks = all_green_gate.build_checks(base_ref="origin/main", kpi_guardrail_mode="optional", profile="readiness")

    test_file_counts: dict[str, int] = {}
    for check in checks:
        if check.command[:3] != [all_green_gate.sys.executable, "-m", "pytest"]:
            continue
        for arg in check.command[3:]:
            if arg.startswith("tests/") and arg.endswith(".py"):
                test_file_counts[arg] = test_file_counts.get(arg, 0) + 1

    assert all(count == 1 for count in test_file_counts.values())


def test_summarize_includes_stable_stage_rollups() -> None:
    summary = all_green_gate.summarize(
        results=[
            _result(name="product_behave", command="behave", status="passed", exit_code=0, duration_s=0.2),
            _result(
                name="product_eval_recall_topk4",
                command="eval",
                status="failed",
                exit_code=5,
                duration_s=0.3,
                artifact_path="artifacts/eval.json",
            ),
            _result(name="qa_validate_issues", command="issues", status="not_run", exit_code=None, duration_s=0.0),
        ],
        continue_on_failure=False,
    )

    assert summary["stages"] == [
        {
            "stage": "product",
            "duration_s": 0.5,
            "exit_code": 5,
            "first_failing_command": "eval",
            "artifact_path": "artifacts/eval.json",
            "warning_reasons": [],
        },
        {
            "stage": "qa",
            "duration_s": 0.0,
            "exit_code": 0,
            "first_failing_command": None,
            "artifact_path": None,
            "warning_reasons": [],
        },
    ]


def test_parse_args_supports_default_json_output_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["all_green_gate.py", "--json-output"])

    args = all_green_gate.parse_args()

    assert args.json_output == Path("artifacts/all-green-gate-summary.json")


def test_extract_kpi_reason_classification_reads_structured_reason() -> None:
    reason = all_green_gate.extract_kpi_reason_classification(
        '{"status":"failed","reason_classification":"missing_input"}'
    )

    assert reason == "missing_input"


def test_summarize_includes_warning_reason_diagnostics() -> None:
    summary = all_green_gate.summarize(
        results=[
            _result(
                name="qa_validate_kpi_guardrails",
                command="kpi",
                status="warning",
                exit_code=1,
                duration_s=0.1,
                diagnostic_reason="threshold_violation",
            )
        ],
        continue_on_failure=False,
    )

    assert summary["warning_diagnostics"] == [
        {"check": "qa_validate_kpi_guardrails", "reason_classification": "threshold_violation"}
    ]
    assert summary["stages"][0]["warning_reasons"] == ["threshold_violation"]


def test_resolve_profile_defaults_to_triage_without_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("BUILD_BUILDID", raising=False)
    monkeypatch.delenv("TESTBOT_RELEASE_VALIDATION", raising=False)

    assert all_green_gate.resolve_profile(None) == "triage"


def test_resolve_profile_defaults_to_readiness_in_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "true")

    assert all_green_gate.resolve_profile(None) == "readiness"


def test_summarize_groups_product_and_governance_failures() -> None:
    summary = all_green_gate.summarize(
        results=[
            _result(name="product_eval_recall_topk4", command="eval", status="failed", exit_code=2, duration_s=0.2),
            _result(name="qa_validate_issues", command="issues", status="failed", exit_code=3, duration_s=0.1),
        ],
        continue_on_failure=False,
    )

    assert [failure["name"] for failure in summary["product_failures"]] == ["product_eval_recall_topk4"]
    assert [failure["name"] for failure in summary["governance_failures"]] == ["qa_validate_issues"]


def test_apply_governance_skip_policy_skips_issue_and_invariant_checks_when_irrelevant_changes() -> None:
    checks = all_green_gate.build_checks(base_ref="origin/main", kpi_guardrail_mode="optional", profile="readiness")

    updated_checks, notes = all_green_gate.apply_governance_skip_policy(
        checks,
        changed_paths={"src/testbot/runtime.py"},
        force_full_governance=False,
    )

    skipped = {check.name: check.skip_reason for check in updated_checks if check.skip_reason}
    assert "qa_validate_issue_links" in skipped
    assert "qa_validate_issues" in skipped
    assert "qa_validate_invariant_sync" in skipped
    assert any("Skipping qa_validate_issue_links" in note for note in notes)


def test_apply_governance_skip_policy_respects_force_full_governance() -> None:
    checks = all_green_gate.build_checks(base_ref="origin/main", kpi_guardrail_mode="optional", profile="readiness")

    updated_checks, notes = all_green_gate.apply_governance_skip_policy(
        checks,
        changed_paths={"src/testbot/runtime.py"},
        force_full_governance=True,
    )

    assert all(check.skip_reason is None for check in updated_checks)
    assert notes == ["--force-full-governance enabled: running all governance checks."]


def test_run_gate_marks_skipped_checks_with_reason() -> None:
    checks = [
        all_green_gate.GateCheck(
            name="qa_validate_issues",
            command=["validate"],
            skip_reason="No governance files changed.",
        )
    ]

    results, exit_code = all_green_gate.run_gate(checks=checks, continue_on_failure=False)

    assert exit_code == 0
    assert results[0].status == "skipped"
    assert results[0].diagnostic_reason == "No governance files changed."


def test_summarize_includes_skipped_check_reasons() -> None:
    summary = all_green_gate.summarize(
        results=[
            _result(
                name="qa_validate_issues",
                command="issues",
                status="skipped",
                exit_code=None,
                duration_s=0.0,
                diagnostic_reason="No governance files changed.",
            )
        ],
        continue_on_failure=False,
    )

    assert summary["skipped_checks"] == [
        {"check": "qa_validate_issues", "reason": "No governance files changed."}
    ]


def test_parse_args_supports_force_full_governance_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["all_green_gate.py", "--force-full-governance"])

    args = all_green_gate.parse_args()

    assert args.force_full_governance is True
