#!/usr/bin/env python3
"""Run every blocking stakeholder obligation check for all-systems-green readiness."""

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
        "--base-ref",
        default="origin/main",
        help="Git base ref passed to issue-link validation (default: origin/main).",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path to write the JSON summary.",
    )
    return parser.parse_args()


def build_checks(*, base_ref: str) -> list[GateCheck]:
    return [
        GateCheck(name="product_behave", command=[sys.executable, "-m", "behave"]),
        GateCheck(
            name="product_eval_runtime_parity",
            command=[sys.executable, "-m", "pytest", "tests/test_eval_runtime_parity.py"],
        ),
        GateCheck(
            name="product_eval_recall_topk4",
            command=[sys.executable, "scripts/eval_recall.py", "--top-k", "4"],
        ),
        GateCheck(
            name="safety_behave_answer_contract_and_memory",
            command=[
                sys.executable,
                "-m",
                "behave",
                "features/answer_contract.feature",
                "features/memory_recall.feature",
            ],
        ),
        GateCheck(
            name="safety_reflection_and_runtime_logging_pytests",
            command=[
                sys.executable,
                "-m",
                "pytest",
                "tests/test_reflection_policy.py",
                "tests/test_runtime_logging_events.py",
            ],
        ),
        GateCheck(
            name="safety_validate_log_schema",
            command=[sys.executable, "scripts/validate_log_schema.py"],
        ),
        GateCheck(
            name="ops_runtime_modes_and_startup_status",
            command=[
                sys.executable,
                "-m",
                "pytest",
                "tests/test_runtime_modes.py",
                "tests/test_startup_status.py",
            ],
        ),
        GateCheck(
            name="qa_pytest_not_live_smoke",
            command=[sys.executable, "-m", "pytest", "-m", "not live_smoke"],
        ),
        GateCheck(
            name="qa_eval_fixtures_and_runtime_parity",
            command=[
                sys.executable,
                "-m",
                "pytest",
                "tests/test_eval_fixtures.py",
                "tests/test_eval_runtime_parity.py",
            ],
        ),
        GateCheck(
            name="qa_validate_issue_links",
            command=[
                sys.executable,
                "scripts/validate_issue_links.py",
                "--all-issue-files",
                "--base-ref",
                base_ref,
            ],
        ),
        GateCheck(
            name="qa_validate_invariant_sync",
            command=[sys.executable, "scripts/validate_invariant_sync.py"],
        ),
        GateCheck(
            name="qa_validate_markdown_paths",
            command=[sys.executable, "scripts/validate_markdown_paths.py"],
        ),
    ]


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
        results.append(result)
        if result.status == "failed" and not continue_on_failure:
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
    return {
        "status": "failed" if has_failure else "passed",
        "exit_code": 1 if has_failure else 0,
        "continue_on_failure": continue_on_failure,
        "checks": [asdict(result) for result in results],
    }


def main() -> int:
    args = parse_args()
    checks = build_checks(base_ref=args.base_ref)
    results, exit_code = run_gate(checks=checks, continue_on_failure=args.continue_on_failure)
    summary = summarize(results=results, continue_on_failure=args.continue_on_failure)

    summary_json = json.dumps(summary, indent=2)
    print(summary_json)

    if any(r.status == "failed" and r.exit_code in {1, 127} for r in results):
        print(
            "\nIf checks failed because test tooling is missing, install development dependencies first: "
            "python -m pip install -e .[dev]"
        )

    if args.json_output:
        out_path = args.json_output if args.json_output.is_absolute() else REPO_ROOT / args.json_output
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(summary_json + "\n", encoding="utf-8")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
