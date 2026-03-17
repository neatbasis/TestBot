"""Authoritative verification manifest contract used by producer and consumers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

VERIFICATION_MANIFEST_SCHEMA_VERSION = "1.0"
REQUIRED_VERIFICATION_CHECKS = [
    "product_behave",
    "product_eval_recall_topk4",
    "safety_validate_log_schema",
    "safety_validate_pipeline_stage_conformance",
    "qa_pytest_not_live_smoke",
]


@dataclass(frozen=True)
class ManifestContractValidation:
    run_id_matches: bool
    required_checks_valid: bool
    checks_valid: bool
    missing_required_checks: list[str]


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
    summary: dict[str, object],
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
        "summary": summary,
        "checks": summary.get("checks", []),
    }


def validate_manifest_payload_contract(payload: Any, *, declared_run_id: str) -> ManifestContractValidation:
    if not isinstance(payload, dict):
        return ManifestContractValidation(False, False, False, list(REQUIRED_VERIFICATION_CHECKS))

    manifest_run_id = payload.get("run_id")
    run_id_matches = isinstance(manifest_run_id, str) and manifest_run_id == declared_run_id

    required_checks = payload.get("required_checks")
    required_checks_valid = (
        isinstance(required_checks, list)
        and all(isinstance(check_name, str) for check_name in required_checks)
        and required_checks == REQUIRED_VERIFICATION_CHECKS
    )

    checks = payload.get("checks")
    checks_valid = isinstance(checks, list)
    check_names = {
        row.get("name")
        for row in checks
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    } if checks_valid else set()

    missing_required_checks = [
        check_name for check_name in REQUIRED_VERIFICATION_CHECKS if check_name not in check_names
    ]

    return ManifestContractValidation(
        run_id_matches=run_id_matches,
        required_checks_valid=required_checks_valid,
        checks_valid=checks_valid,
        missing_required_checks=missing_required_checks,
    )
