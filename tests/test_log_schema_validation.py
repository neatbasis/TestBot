from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from tests.helpers.log_schema_samples import build_valid_rows_by_schema_version

VALIDATOR_PATH = Path("scripts/validate_log_schema.py")

spec = importlib.util.spec_from_file_location("validate_log_schema", VALIDATOR_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

validate_file = module.validate_file
validate_row = module.validate_row


def test_validate_log_schema_accepts_generated_rows_for_current_schema_v4(tmp_path: Path) -> None:
    rows_by_schema_version = build_valid_rows_by_schema_version()
    output_path = tmp_path / "schema_v4.jsonl"
    output_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows_by_schema_version[4]) + "\n",
        encoding="utf-8",
    )

    assert validate_file(output_path) == []


def test_validate_log_schema_rejects_obsolete_schema_versions() -> None:
    rows_by_schema_version = build_valid_rows_by_schema_version()

    for obsolete_version in (1, 2, 3):
        errors = validate_row(rows_by_schema_version[obsolete_version][0], row_label="test-row")

        assert (
            f"test-row: schema_version '{obsolete_version}' is obsolete; only schema_version '4' is accepted"
            in errors
        )


def test_validate_log_schema_rejects_invalid_schema_version_type() -> None:
    row = {
        "ts": "2026-03-01T00:00:00Z",
        "event": "user_utterance_ingest",
        "schema_version": "2",
    }

    errors = validate_row(row, row_label="test-row")

    assert "test-row: key 'schema_version' expected int when present" in errors


def test_validate_log_schema_rejects_provenance_summary_missing_source_fields() -> None:
    row = {
        "ts": "2026-03-03T00:00:00Z",
        "event": "provenance_summary",
        "schema_version": 4,
        "provenance_types": ["memory"],
        "used_memory_refs": [],
        "basis_statement": "derived from memory",
    }

    errors = validate_row(row, row_label="test-row")

    assert "test-row: missing required key 'used_source_evidence_refs'" in errors
    assert "test-row: missing required key 'source_evidence_attribution'" in errors


def test_validate_log_schema_requires_debug_turn_trace_payload() -> None:
    row = {
        "ts": "2026-03-03T00:00:00Z",
        "event": "debug_turn_trace",
        "schema_version": 4,
        "trace": "[debug] compact",
    }

    errors = validate_row(row, row_label="test-row")

    assert "test-row: missing required key 'payload'" in errors


def test_validate_log_schema_accepts_debug_turn_trace_without_legacy_trace() -> None:
    row = {
        "ts": "2026-03-03T00:00:00Z",
        "event": "debug_turn_trace",
        "schema_version": 4,
        "payload": {"debug.policy": {"reject_code": "CONTEXT_CONF_BELOW_THRESHOLD"}},
    }

    assert validate_row(row, row_label="test-row") == []
