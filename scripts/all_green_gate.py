#!/usr/bin/env python3
"""Run every blocking stakeholder obligation check for all-systems-green readiness."""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from governance_rules import (
    git_ref_exists as governance_git_ref_exists,
    resolve_base_ref as governance_resolve_base_ref,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_MANIFEST_DIR = REPO_ROOT / "artifacts" / "verification"
VERIFICATION_MANIFEST_SCHEMA_VERSION = "1.0"
REQUIRED_VERIFICATION_CHECKS = [
    "product_behave",
    "product_eval_recall_topk4",
    "safety_validate_log_schema",
    "safety_validate_pipeline_stage_conformance",
    "qa_pytest_not_live_smoke",
]
BEHAVE_PREFLIGHT_CHECK_NAME = "preflight_bdd_dependencies"
BEHAVE_REMEDIATION_MESSAGE = (
    "Missing required BDD dependency 'behave'. Install development dependencies before running "
    "the canonical gate: python -m pip install -e .[dev]"
)


@dataclass
class GateCheck:
    name: str
    command: list[str]
    blocking: bool = True
    skip_reason: str | None = None


@dataclass
class CheckResult:
    name: str
    stage: str
    command: str
    status: str
    exit_code: int | None
    duration_s: float
    artifact_path: str | None
    diagnostic_reason: str | None = None


def with_remediation(summary: dict[str, object], *messages: str) -> dict[str, object]:
    remediation = [message for message in messages if message]
    if remediation:
        summary["remediation"] = remediation
    return summary


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
        help=(
            "Git base ref passed to governance validators (default: origin/main). "
            "If origin/main is unavailable in shallow/detached environments, "
            "the gate falls back to HEAD~1, then HEAD. Override with --base-ref."
        ),
    )
    parser.add_argument(
        "--json-output",
        nargs="?",
        const=Path("artifacts/all-green-gate-summary.json"),
        type=Path,
        help=(
            "Optional path to write the machine-readable JSON summary. "
            "When provided without a value, defaults to artifacts/all-green-gate-summary.json."
        ),
    )
    parser.add_argument(
        "--post-triage-router",
        action="store_true",
        help=(
            "Optionally run scripts/triage_router.py after writing --json-output summary. "
            "Requires --json-output."
        ),
    )
    parser.add_argument(
        "--triage-routing-config",
        type=Path,
        default=Path("docs/qa/triage-routing.yaml"),
        help="Routing config path used by --post-triage-router.",
    )
    parser.add_argument(
        "--triage-output",
        type=Path,
        default=Path("artifacts/all-green-gate-triage.json"),
        help="JSON output path for triage router recommendations.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help=(
            "Optional verification run identifier used in artifacts/verification/<run-id>.json. "
            "When omitted, a deterministic timestamp+suffix id is generated."
        ),
    )
    parser.add_argument(
        "--profile",
        choices=("triage", "readiness"),
        default=None,
        help=(
            "Gate execution profile. 'triage' runs runtime/schema/core deterministic checks; "
            "'readiness' runs the full merge/release gate. Defaults to triage locally and readiness in CI/release environments."
        ),
    )
    parser.add_argument(
        "--force-full-governance",
        action="store_true",
        help=(
            "Always run all governance checks in readiness profile, even when changed-path "
            "detection would otherwise skip a subset."
        ),
    )
    parser.add_argument(
        "--kpi-guardrail-mode",
        choices=("off", "optional", "blocking"),
        default="optional",
        help=(
            "Rollout mode for turn analytics + KPI guardrail checks (default: optional). "
            "Policy and promotion criteria: docs/testing.md#kpi-guardrail-mode-policy-authoritative."
        ),
    )
    return parser.parse_args()


def generate_run_id() -> str:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


def write_verification_manifest(
    *,
    run_id: str,
    args: argparse.Namespace,
    effective_base_ref: str | None,
    profile: str,
    summary: dict[str, object],
) -> Path:
    VERIFICATION_MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = VERIFICATION_MANIFEST_DIR / f"{run_id}.json"
    payload = {
        "schema_version": VERIFICATION_MANIFEST_SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "manifest_path": str(manifest_path.relative_to(REPO_ROOT)),
        "required_checks": REQUIRED_VERIFICATION_CHECKS,
        "gate": {
            "base_ref_requested": args.base_ref,
            "base_ref_effective": effective_base_ref,
            "continue_on_failure": args.continue_on_failure,
            "profile": profile,
            "kpi_guardrail_mode": args.kpi_guardrail_mode,
        },
        "summary": summary,
        "checks": summary.get("checks", []),
    }
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def stage_name_for_check(check_name: str) -> str:
    return check_name.split("_", maxsplit=1)[0]


def extract_artifact_path(command: Sequence[str]) -> str | None:
    path_flags = {"--json-output", "--summary-output", "--output"}
    for idx, token in enumerate(command[:-1]):
        if token in path_flags:
            candidate = command[idx + 1]
            if not candidate.startswith("-"):
                return candidate
    return None


def extract_kpi_reason_classification(stdout: str) -> str | None:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    reason = payload.get("reason_classification")
    return reason if isinstance(reason, str) else None


def git_ref_exists(ref: str) -> bool:
    return governance_git_ref_exists(ref, repo_root=REPO_ROOT)


def resolve_base_ref(base_ref: str) -> tuple[str | None, list[str]]:
    return governance_resolve_base_ref(base_ref, ref_exists=git_ref_exists)


def default_profile_for_environment() -> str:
    if any(
        os.getenv(flag)
        for flag in (
            "CI",
            "GITHUB_ACTIONS",
            "BUILD_BUILDID",
            "TESTBOT_RELEASE_VALIDATION",
        )
    ):
        return "readiness"
    return "triage"


def resolve_profile(explicit_profile: str | None) -> str:
    return explicit_profile or default_profile_for_environment()


ISSUE_VALIDATOR_CHECKS = {"qa_validate_issue_links", "qa_validate_issues"}
INVARIANT_SYNC_CHECKS = {"qa_validate_invariant_sync"}

ISSUE_VALIDATOR_PATH_PREFIXES = (
    "docs/issues/",
    "docs/governance/",
    "docs/releases/",
    "docs/qa/",
)
ISSUE_VALIDATOR_EXACT_PATHS = {
    "docs/issues.md",
}

INVARIANT_PATH_PREFIXES = (
    "docs/directives/",
    "docs/invariants/",
)
INVARIANT_EXACT_PATHS = {
    "docs/invariants.md",
}


def detect_changed_paths(base_ref: str) -> tuple[set[str] | None, list[str]]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        reason = completed.stderr.strip() or completed.stdout.strip() or "unknown git diff failure"
        return None, [
            (
                f"Changed-path detection failed for base ref '{base_ref}'. "
                f"Running full governance checks for safety. Details: {reason}"
            )
        ]
    changed_paths = {
        line.strip() for line in completed.stdout.splitlines() if line.strip()
    }
    return changed_paths, []


def _matches_path_scopes(path: str, *, exact_paths: set[str], prefixes: tuple[str, ...]) -> bool:
    return path in exact_paths or any(path.startswith(prefix) for prefix in prefixes)


def apply_governance_skip_policy(
    checks: Sequence[GateCheck],
    *,
    changed_paths: set[str] | None,
    force_full_governance: bool,
) -> tuple[list[GateCheck], list[str]]:
    if force_full_governance:
        return list(checks), ["--force-full-governance enabled: running all governance checks."]
    if changed_paths is None:
        return list(checks), []

    run_issue_validators = any(
        _matches_path_scopes(
            path,
            exact_paths=ISSUE_VALIDATOR_EXACT_PATHS,
            prefixes=ISSUE_VALIDATOR_PATH_PREFIXES,
        )
        for path in changed_paths
    )
    run_invariant_sync = any(
        _matches_path_scopes(
            path,
            exact_paths=INVARIANT_EXACT_PATHS,
            prefixes=INVARIANT_PATH_PREFIXES,
        )
        for path in changed_paths
    )

    updated_checks: list[GateCheck] = []
    skip_notes: list[str] = []
    for check in checks:
        skip_reason: str | None = None
        if check.name in ISSUE_VALIDATOR_CHECKS and not run_issue_validators:
            skip_reason = (
                "No docs/issues, release metadata, or governance docs changed "
                f"against base ref; detected {len(changed_paths)} changed paths."
            )
        if check.name in INVARIANT_SYNC_CHECKS and not run_invariant_sync:
            skip_reason = (
                "No invariant/directive files changed against base ref; "
                f"detected {len(changed_paths)} changed paths."
            )
        updated_checks.append(
            GateCheck(
                name=check.name,
                command=check.command,
                blocking=check.blocking,
                skip_reason=skip_reason,
            )
        )
        if skip_reason:
            skip_notes.append(f"Skipping {check.name}: {skip_reason}")
    return updated_checks, skip_notes

def build_checks(
    *,
    base_ref: str | None,
    kpi_guardrail_mode: str = "optional",
    profile: str = "triage",
) -> list[GateCheck]:
    checks = [
        GateCheck(name="product_behave", command=[sys.executable, "-m", "behave"]),
        GateCheck(
            name="product_eval_recall_topk4",
            command=[sys.executable, "scripts/eval_recall.py", "--top-k", "4"],
        ),
        GateCheck(
            name="safety_validate_log_schema",
            command=[sys.executable, "scripts/validate_log_schema.py"],
        ),
        GateCheck(
            name="safety_validate_pipeline_stage_conformance",
            command=[sys.executable, "scripts/validate_pipeline_stage_conformance.py"],
        ),
        GateCheck(
            name="qa_pytest_not_live_smoke",
            command=[sys.executable, "-m", "pytest", "-m", "not live_smoke"],
        ),
    ]

    if profile == "readiness":
        checks.extend(
            [
                GateCheck(
                    name="qa_validate_issue_links",
                    command=[
                        sys.executable,
                        "scripts/validate_issue_links.py",
                        "--all-issue-files",
                        "--base-ref",
                        base_ref or "HEAD",
                    ],
                ),
                GateCheck(
                    name="qa_validate_issues",
                    command=[
                        sys.executable,
                        "scripts/validate_issues.py",
                        "--all-issue-files",
                        "--base-ref",
                        base_ref or "HEAD",
                    ],
                ),
                GateCheck(
                    name="qa_validate_invariant_sync",
                    command=[sys.executable, "scripts/sync_invariants_mirror.py", "--check"],
                ),
                GateCheck(
                    name="qa_validate_markdown_paths",
                    command=[sys.executable, "scripts/validate_markdown_paths.py"],
                ),
            ]
        )

    if profile == "readiness" and kpi_guardrail_mode != "off":
        kpi_blocking = kpi_guardrail_mode == "blocking"
        checks.extend(
            [
                GateCheck(
                    name="qa_aggregate_turn_analytics",
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
                    blocking=kpi_blocking,
                ),
                GateCheck(
                    name="qa_validate_kpi_guardrails",
                    command=[
                        sys.executable,
                        "scripts/validate_kpi_guardrails.py",
                        "--summary",
                        "logs/turn_analytics_summary.json",
                        "--config",
                        "config/kpi_guardrails.json",
                    ],
                    blocking=kpi_blocking,
                ),
            ]
        )

    return checks


def run_check(check: GateCheck) -> CheckResult:
    started = time.monotonic()
    command_text = shlex.join(check.command)
    diagnostic_reason: str | None = None
    try:
        completed = subprocess.run(check.command, cwd=REPO_ROOT, capture_output=True, text=True)
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end="")
        code = int(completed.returncode)
        status = "passed" if code == 0 else "failed"
        if check.name == "qa_validate_kpi_guardrails":
            diagnostic_reason = extract_kpi_reason_classification(completed.stdout)
    except FileNotFoundError:
        code = 127
        status = "failed"
    duration_s = round(time.monotonic() - started, 3)
    return CheckResult(
        name=check.name,
        stage=stage_name_for_check(check.name),
        command=command_text,
        status=status,
        exit_code=code,
        duration_s=duration_s,
        artifact_path=extract_artifact_path(check.command),
        diagnostic_reason=diagnostic_reason,
    )


def run_gate(checks: Sequence[GateCheck], continue_on_failure: bool) -> tuple[list[CheckResult], int]:
    results: list[CheckResult] = []
    for idx, check in enumerate(checks):
        if check.skip_reason:
            print(f"[SKIP] {check.name}: {check.skip_reason}")
            results.append(
                CheckResult(
                    name=check.name,
                    stage=stage_name_for_check(check.name),
                    command=shlex.join(check.command),
                    status="skipped",
                    exit_code=None,
                    duration_s=0.0,
                    artifact_path=extract_artifact_path(check.command),
                    diagnostic_reason=check.skip_reason,
                )
            )
            continue
        result = run_check(check)
        if result.status == "failed" and not check.blocking:
            result.status = "warning"
        results.append(result)
        if result.status == "failed" and check.blocking and not continue_on_failure:
            for remaining in checks[idx + 1 :]:
                results.append(
                    CheckResult(
                        name=remaining.name,
                        stage=stage_name_for_check(remaining.name),
                        command=shlex.join(remaining.command),
                        status="not_run",
                        exit_code=None,
                        duration_s=0.0,
                        artifact_path=extract_artifact_path(remaining.command),
                        diagnostic_reason=None,
                    )
                )
            break
    exit_code = 1 if any(result.status == "failed" for result in results) else 0
    return results, exit_code


def preflight_bdd_dependencies() -> CheckResult | None:
    started = time.monotonic()
    behave_available = importlib.util.find_spec("behave") is not None
    duration_s = round(time.monotonic() - started, 3)
    if behave_available:
        return None
    return CheckResult(
        name=BEHAVE_PREFLIGHT_CHECK_NAME,
        stage=stage_name_for_check(BEHAVE_PREFLIGHT_CHECK_NAME),
        command=f"{sys.executable} -c 'import behave'",
        status="failed",
        exit_code=1,
        duration_s=duration_s,
        artifact_path=None,
        diagnostic_reason=None,
    )


def summarize_stages(results: Sequence[CheckResult]) -> list[dict[str, object]]:
    stage_summaries: list[dict[str, object]] = []
    for result in results:
        if not stage_summaries or stage_summaries[-1]["stage"] != result.stage:
            stage_summaries.append(
                {
                    "stage": result.stage,
                    "duration_s": 0.0,
                    "exit_code": 0,
                    "first_failing_command": None,
                    "artifact_path": None,
                    "warning_reasons": [],
                }
            )

        summary = stage_summaries[-1]
        summary["duration_s"] = round(float(summary["duration_s"]) + result.duration_s, 3)

        if result.artifact_path and summary["artifact_path"] is None:
            summary["artifact_path"] = result.artifact_path

        if result.status in {"failed", "warning"} and summary["first_failing_command"] is None:
            summary["first_failing_command"] = result.command

        if result.status == "warning" and result.diagnostic_reason:
            warning_reasons = summary["warning_reasons"]
            if result.diagnostic_reason not in warning_reasons:
                warning_reasons.append(result.diagnostic_reason)

        if result.exit_code not in {None, 0} and summary["exit_code"] == 0:
            summary["exit_code"] = result.exit_code

    return stage_summaries


def print_stage_summary(stage_summaries: Sequence[dict[str, object]]) -> None:
    print("Stage summary:")
    for stage_summary in stage_summaries:
        stage = stage_summary["stage"]
        duration_s = stage_summary["duration_s"]
        exit_code = stage_summary["exit_code"]
        first_failing_command = stage_summary["first_failing_command"] or "-"
        artifact_path = stage_summary["artifact_path"] or "-"
        warning_reasons = ",".join(stage_summary["warning_reasons"]) or "-"
        print(
            f"- {stage}: duration_s={duration_s:.3f}, exit_code={exit_code}, "
            f"first_failing_command={first_failing_command}, artifact_path={artifact_path}, "
            f"warning_reasons={warning_reasons}"
        )


def summarize(results: Sequence[CheckResult], continue_on_failure: bool) -> dict[str, object]:
    has_failure = any(result.status == "failed" for result in results)
    warning_count = sum(1 for result in results if result.status == "warning")
    stage_summaries = summarize_stages(results)
    warning_diagnostics = [
        {"check": result.name, "reason_classification": result.diagnostic_reason}
        for result in results
        if result.status == "warning"
    ]
    product_failures = [
        asdict(result)
        for result in results
        if result.status == "failed" and result.stage in {"product", "safety", "ops"}
    ]
    governance_failures = [
        asdict(result)
        for result in results
        if result.status == "failed" and result.stage == "qa"
    ]
    skipped_checks = [
        {"check": result.name, "reason": result.diagnostic_reason}
        for result in results
        if result.status == "skipped"
    ]
    return {
        "status": "failed" if has_failure else "passed",
        "exit_code": 1 if has_failure else 0,
        "continue_on_failure": continue_on_failure,
        "warning_count": warning_count,
        "warning_diagnostics": warning_diagnostics,
        "product_failures": product_failures,
        "governance_failures": governance_failures,
        "skipped_checks": skipped_checks,
        "stages": stage_summaries,
        "checks": [asdict(result) for result in results],
    }


def maybe_run_triage_router(
    *,
    enabled: bool,
    summary_path: Path | None,
    routing_config: Path,
    triage_output: Path,
    base_ref: str,
) -> None:
    if not enabled:
        return
    if summary_path is None:
        print("[WARN] --post-triage-router requires --json-output; skipping triage routing.")
        return

    router_cmd = [
        sys.executable,
        "scripts/triage_router.py",
        "--summary",
        str(summary_path),
        "--routing-config",
        str(routing_config),
        "--base-ref",
        base_ref,
        "--output",
        str(triage_output),
    ]
    print(f"[INFO] Running triage router: {shlex.join(router_cmd)}")
    completed = subprocess.run(
        router_cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if completed.stdout.strip():
        print(completed.stdout.rstrip())
    if completed.returncode != 0:
        print(f"[WARN] triage router failed with exit code {completed.returncode}")
        if completed.stderr.strip():
            print(completed.stderr.rstrip())
        return
    print(f"[INFO] Triage recommendations written: {triage_output}")


def main() -> int:
    args = parse_args()
    run_id = args.run_id or generate_run_id()
    preflight_result = preflight_bdd_dependencies()
    if preflight_result is not None:
        summary = with_remediation(
            summarize(results=[preflight_result], continue_on_failure=args.continue_on_failure),
            BEHAVE_REMEDIATION_MESSAGE,
        )
        summary_json = json.dumps(summary, indent=2)
        print(summary_json)
        print(f"\n{BEHAVE_REMEDIATION_MESSAGE}")
        if args.json_output:
            out_path = args.json_output if args.json_output.is_absolute() else REPO_ROOT / args.json_output
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(summary_json + "\n", encoding="utf-8")
        manifest_path = write_verification_manifest(
            run_id=run_id,
            args=args,
            effective_base_ref=None,
            profile=resolve_profile(args.profile),
            summary=summary,
        )
        print(f"[INFO] Verification manifest written: {manifest_path.relative_to(REPO_ROOT)}")
        return 1

    effective_base_ref, base_ref_notes = resolve_base_ref(args.base_ref)
    for note in base_ref_notes:
        print(f"[WARN] {note}")
    if args.base_ref == "origin/main" and effective_base_ref in {"HEAD~1", "HEAD"}:
        print(
            f"[INFO] Base-ref fallback is active by canonical policy: "
            f"origin/main -> HEAD~1 -> HEAD (using {effective_base_ref!r})."
        )

    profile = resolve_profile(args.profile)
    print(f"[INFO] Running all-green profile: {profile}")

    checks = build_checks(
        base_ref=effective_base_ref,
        kpi_guardrail_mode=args.kpi_guardrail_mode,
        profile=profile,
    )
    governance_skip_notes: list[str] = []
    if profile == "readiness":
        changed_paths: set[str] | None = None
        if effective_base_ref is None:
            print("[WARN] Base ref unavailable; running full governance checks to preserve safety.")
        else:
            changed_paths, changed_path_notes = detect_changed_paths(effective_base_ref)
            for note in changed_path_notes:
                print(f"[WARN] {note}")
            if changed_paths is not None:
                print(
                    f"[INFO] Changed-path detection against '{effective_base_ref}' found "
                    f"{len(changed_paths)} changed paths."
                )

        checks, governance_skip_notes = apply_governance_skip_policy(
            checks,
            changed_paths=changed_paths,
            force_full_governance=args.force_full_governance,
        )
        for note in governance_skip_notes:
            print(f"[INFO] {note}")

    results, exit_code = run_gate(checks=checks, continue_on_failure=args.continue_on_failure)
    summary = summarize(results=results, continue_on_failure=args.continue_on_failure)
    if governance_skip_notes:
        summary["governance_skip_notes"] = governance_skip_notes

    print_stage_summary(summary["stages"])
    print()
    summary_json = json.dumps(summary, indent=2)
    print(summary_json)

    if any(r.status == "failed" and r.exit_code in {1, 127} for r in results):
        print(
            "\nIf checks failed because test tooling is missing, install development dependencies first: "
            "python -m pip install -e .[dev]"
        )

    if args.kpi_guardrail_mode == "optional":
        print(
            "\nTurn analytics and KPI guardrail checks are running in optional mode. "
            "Promote with --kpi-guardrail-mode blocking once the criteria in docs/testing.md#kpi-guardrail-mode-policy-authoritative are met."
        )

    summary_output_path: Path | None = None
    if args.json_output:
        out_path = args.json_output if args.json_output.is_absolute() else REPO_ROOT / args.json_output
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(summary_json + "\n", encoding="utf-8")
        summary_output_path = out_path

    triage_output = (
        args.triage_output if args.triage_output.is_absolute() else REPO_ROOT / args.triage_output
    )
    triage_routing_config = (
        args.triage_routing_config
        if args.triage_routing_config.is_absolute()
        else REPO_ROOT / args.triage_routing_config
    )
    maybe_run_triage_router(
        enabled=args.post_triage_router,
        summary_path=summary_output_path,
        routing_config=triage_routing_config,
        triage_output=triage_output,
        base_ref=effective_base_ref or args.base_ref,
    )

    manifest_path = write_verification_manifest(
        run_id=run_id,
        args=args,
        effective_base_ref=effective_base_ref,
        profile=profile,
        summary=summary,
    )
    print(f"[INFO] Verification manifest written: {manifest_path.relative_to(REPO_ROOT)}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
