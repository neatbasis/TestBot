#!/usr/bin/env python3
"""Authoritative verification-manifest contract shared by producer and consumer code.

Contract statement:
- Producer (`scripts/all_green_gate.py`) MUST emit this manifest shape and MUST source
  `required_checks` from `REQUIRED_VERIFICATION_CHECKS` in this module.
- Consumer (`scripts/validate_issue_links.py`) MUST validate referenced manifest path/run-id,
  treat `run_id` and `required_checks` as authoritative fields, and fail closed when
  `required_checks` is missing, malformed, or missing any canonical check name.
"""

from __future__ import annotations

from typing import Mapping, Sequence

VERIFICATION_MANIFEST_SCHEMA_VERSION = "1.0"
REQUIRED_VERIFICATION_CHECKS: tuple[str, ...] = (
    "product_behave",
    "product_eval_recall_topk4",
    "safety_validate_log_schema",
    "safety_validate_pipeline_stage_conformance",
    "qa_pytest_not_live_smoke",
)


def build_verification_manifest_payload(
    *,
    run_id: str,
    generated_at_utc: str,
    manifest_path: str,
    base_ref_requested: str,
    base_ref_effective: str | None,
    continue_on_failure: bool,
    profile: str,
    kpi_guardrail_mode: str,
    summary: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": VERIFICATION_MANIFEST_SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at_utc": generated_at_utc,
        "manifest_path": manifest_path,
        "required_checks": list(REQUIRED_VERIFICATION_CHECKS),
        "gate": {
            "base_ref_requested": base_ref_requested,
            "base_ref_effective": base_ref_effective,
            "continue_on_failure": continue_on_failure,
            "profile": profile,
            "kpi_guardrail_mode": kpi_guardrail_mode,
        },
        "summary": dict(summary),
        "checks": summary.get("checks", []),
    }


def missing_required_checks(payload: Mapping[str, object]) -> list[str] | None:
    required_checks = payload.get("required_checks")
    if not isinstance(required_checks, Sequence) or isinstance(required_checks, (str, bytes)):
        return None
    check_names = {value for value in required_checks if isinstance(value, str)}
    return sorted(set(REQUIRED_VERIFICATION_CHECKS) - check_names)
