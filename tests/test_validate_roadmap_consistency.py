from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_roadmap_consistency.py"
_spec = importlib.util.spec_from_file_location("validate_roadmap_consistency", _VALIDATOR_PATH)
assert _spec and _spec.loader
validate_roadmap_consistency = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = validate_roadmap_consistency
_spec.loader.exec_module(validate_roadmap_consistency)


def _write_fixture_files(
    tmp_path: Path,
    *,
    roadmap_timestamp: str,
    roadmap_gate_status: str,
    roadmap_capability_summary: str,
    feature_implemented: int,
    feature_partial: int,
    feature_missing: int,
    artifact_status: str,
    artifact_mtime_epoch: int | None = None,
) -> tuple[Path, Path, Path]:
    roadmap_path = tmp_path / "current-status-and-next-5-priorities.md"
    roadmap_path.write_text(
        "\n".join(
            [
                "# Snapshot",
                "- Timestamp (UTC): `" + roadmap_timestamp + "`",
                "- Gate status: `" + roadmap_gate_status + "`",
                "- Capability summary line (`docs/qa/feature-status-report.md`): **" + roadmap_capability_summary + "**.",
            ]
        ),
        encoding="utf-8",
    )

    gate_summary_path = tmp_path / "all-green-gate-summary.json"
    gate_summary_path.write_text('{"status": "' + artifact_status + '"}', encoding="utf-8")
    if artifact_mtime_epoch is not None:
        os.utime(gate_summary_path, (artifact_mtime_epoch, artifact_mtime_epoch))

    feature_report_path = tmp_path / "feature-status-report.md"
    feature_report_path.write_text(
        f"Implemented: **{feature_implemented}** | Partial: **{feature_partial}** | Missing: **{feature_missing}**\n",
        encoding="utf-8",
    )

    return roadmap_path, gate_summary_path, feature_report_path


def test_validate_consistency_passes_for_fresh_aligned_state(tmp_path: Path) -> None:
    roadmap_path, gate_summary_path, feature_report_path = _write_fixture_files(
        tmp_path,
        roadmap_timestamp="2026-03-17T22:29:40Z",
        roadmap_gate_status="passed",
        roadmap_capability_summary="Implemented: 2 | Partial: 7 | Missing: 0",
        feature_implemented=2,
        feature_partial=7,
        feature_missing=0,
        artifact_status="passed",
        artifact_mtime_epoch=1773786590,
    )

    result = validate_roadmap_consistency.validate_consistency(
        roadmap_path=roadmap_path,
        gate_summary_path=gate_summary_path,
        feature_report_path=feature_report_path,
        max_staleness_seconds=120,
    )

    assert result.warnings == []


def test_validate_consistency_warns_for_stale_gate_snapshot(tmp_path: Path) -> None:
    roadmap_path, gate_summary_path, feature_report_path = _write_fixture_files(
        tmp_path,
        roadmap_timestamp="2026-03-10T00:00:00Z",
        roadmap_gate_status="failed",
        roadmap_capability_summary="Implemented: 2 | Partial: 7 | Missing: 0",
        feature_implemented=2,
        feature_partial=7,
        feature_missing=0,
        artifact_status="passed",
        artifact_mtime_epoch=1773786590,
    )

    result = validate_roadmap_consistency.validate_consistency(
        roadmap_path=roadmap_path,
        gate_summary_path=gate_summary_path,
        feature_report_path=feature_report_path,
        max_staleness_seconds=60,
    )

    assert any("stale" in warning for warning in result.warnings)
    assert any("gate status mismatch" in warning.lower() for warning in result.warnings)


def test_validate_consistency_warns_for_capability_summary_mismatch(tmp_path: Path) -> None:
    roadmap_path, gate_summary_path, feature_report_path = _write_fixture_files(
        tmp_path,
        roadmap_timestamp="2026-03-17T22:29:40Z",
        roadmap_gate_status="passed",
        roadmap_capability_summary="Implemented: 2 | Partial: 7 | Missing: 1",
        feature_implemented=2,
        feature_partial=7,
        feature_missing=0,
        artifact_status="passed",
        artifact_mtime_epoch=1773786590,
    )

    result = validate_roadmap_consistency.validate_consistency(
        roadmap_path=roadmap_path,
        gate_summary_path=gate_summary_path,
        feature_report_path=feature_report_path,
        max_staleness_seconds=120,
    )

    assert any("capability summary mismatch" in warning.lower() for warning in result.warnings)
