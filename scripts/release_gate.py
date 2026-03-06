#!/usr/bin/env python3
"""Single entrypoint for deterministic merge/release readiness checks.

Parity coverage in ``tests/test_eval_runtime_parity.py`` is an explicit blocking check
to prevent eval/runtime drift in ordering, fallback class, confidence boundaries,
and ambiguity outcomes before release.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class GateCheck:
    name: str
    command: list[str]
    blocking: bool = True


@dataclass
class CheckResult:
    name: str
    command: str
    status: str
    exit_code: int | None
    duration_s: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Run all checks even after failures and return non-zero if any failed.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path to write the JSON summary.",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Git base ref passed to governance validators (default: origin/main).",
    )
    parser.add_argument(
        "--replay-report",
        action="store_true",
        help="Include the optional replay KPI drift report command.",
    )
    parser.add_argument(
        "--kpi-guardrail-mode",
        choices=("off", "optional", "blocking"),
        default="optional",
        help="Rollout mode for KPI guardrail validation (default: optional).",
    )
    return parser.parse_args()


def build_checks(*, replay_report: bool = False, base_ref: str = "origin/main", kpi_guardrail_mode: str = "optional") -> list[GateCheck]:
    checks = [
        GateCheck(name="behave", command=[sys.executable, "-m", "behave"]),
        GateCheck(
            name="pytest_source_and_provenance_fast",
            command=[
                sys.executable,
                "-m",
                "pytest",
                "tests/test_vector_store.py",
                "tests/test_source_fusion.py",
                "tests/test_log_schema_validation.py",
            ],
        ),
        GateCheck(name="pytest_non_live_smoke", command=[sys.executable, "-m", "pytest", "-m", "not live_smoke"]),
        GateCheck(
            name="pytest_eval_runtime_parity",
            command=[sys.executable, "-m", "pytest", "tests/test_eval_runtime_parity.py"],
            blocking=True,
        ),
        GateCheck(
            name="validate_issue_links",
            command=[
                sys.executable,
                "scripts/validate_issue_links.py",
                "--all-issue-files",
                "--base-ref",
                base_ref,
            ],
        ),
        GateCheck(
            name="validate_issues",
            command=[
                sys.executable,
                "scripts/validate_issues.py",
                "--all-issue-files",
                "--base-ref",
                base_ref,
            ],
        ),
    ]

    if kpi_guardrail_mode != "off":
        checks.append(
            GateCheck(
                name="validate_kpi_guardrails",
                command=[
                    sys.executable,
                    "scripts/validate_kpi_guardrails.py",
                    "--summary",
                    "logs/turn_analytics_summary.json",
                    "--config",
                    "config/kpi_guardrails.json",
                ],
                blocking=kpi_guardrail_mode == "blocking",
            )
        )

    if replay_report:
        checks.append(
            GateCheck(
                name="replay_report",
                command=[
                    sys.executable,
                    "scripts/aggregate_turn_analytics.py",
                    "--input",
                    "logs/session.jsonl",
                    "--output",
                    "logs/turn_analytics.jsonl",
                    "--summary-output",
                    "logs/turn_analytics_summary.json",
                ],
                blocking=False,
            )
        )
    return checks


def run_check(check: GateCheck) -> CheckResult:
    started = time.monotonic()
    command_text = shlex.join(check.command)
    try:
        completed = subprocess.run(check.command, cwd=REPO_ROOT)
        code = int(completed.returncode)
        status = "passed" if code == 0 else "failed"
    except FileNotFoundError:
        code = 127
        status = "failed"
    duration_s = round(time.monotonic() - started, 3)
    return CheckResult(
        name=check.name,
        command=command_text,
        status=status,
        exit_code=code,
        duration_s=duration_s,
    )


def run_gate(checks: Sequence[GateCheck], continue_on_failure: bool) -> tuple[list[CheckResult], int]:
    results: list[CheckResult] = []

    for idx, check in enumerate(checks):
        result = run_check(check)
        if result.status == "failed" and not check.blocking:
            result.status = "warning"
        results.append(result)

        if result.status == "failed" and check.blocking and not continue_on_failure:
            for remaining in checks[idx + 1 :]:
                results.append(
                    CheckResult(
                        name=remaining.name,
                        command=shlex.join(remaining.command),
                        status="not_run",
                        exit_code=None,
                        duration_s=0.0,
                    )
                )
            break

    exit_code = 1 if any(result.status == "failed" for result in results) else 0
    return results, exit_code


def summarize(results: Sequence[CheckResult], continue_on_failure: bool) -> dict[str, object]:
    has_failure = any(result.status == "failed" for result in results)
    warning_count = sum(1 for result in results if result.status == "warning")
    return {
        "status": "failed" if has_failure else "passed",
        "exit_code": 1 if has_failure else 0,
        "continue_on_failure": continue_on_failure,
        "warning_count": warning_count,
        "checks": [asdict(result) for result in results],
    }


def main() -> int:
    args = parse_args()
    checks = build_checks(
        replay_report=args.replay_report,
        base_ref=args.base_ref,
        kpi_guardrail_mode=args.kpi_guardrail_mode,
    )
    results, exit_code = run_gate(checks=checks, continue_on_failure=args.continue_on_failure)
    summary = summarize(results=results, continue_on_failure=args.continue_on_failure)

    summary_json = json.dumps(summary, indent=2)
    print(summary_json)

    if any(r.status == "failed" and r.exit_code in {1, 127} for r in results):
        print(
            "\nIf checks failed because test tooling is missing, install development dependencies first: "
            "python -m pip install -e .[dev]"
        )

    parity_failed = any(r.name == "pytest_eval_runtime_parity" and r.status == "failed" for r in results)
    if parity_failed:
        print(
            "\nParity gate failed (blocking release gate): runtime/eval behavior drift likely in ordering, "
            "fallback class, confidence boundaries, or ambiguity outcomes."
        )
        print(
            "Inspect intermediate signals first: scored_candidates, near_tie_candidates, "
            "ambiguity_detected (tests/test_eval_runtime_parity.py and features/steps/memory_steps.py)."
        )
        print(
            "Likely boundaries: scripts/eval_recall.py <-> testbot.rerank and "
            "testbot.sat_chatbot_memory_v2 confidence handling."
        )
    if args.kpi_guardrail_mode == "optional":
        print("\nKPI guardrail check is running in optional mode. Promote with --kpi-guardrail-mode blocking once rollout criteria are met.")

    if args.json_output:
        out_path = args.json_output if args.json_output.is_absolute() else REPO_ROOT / args.json_output
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(summary_json + "\n", encoding="utf-8")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
