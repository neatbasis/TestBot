from __future__ import annotations

import importlib.util
from pathlib import Path

FIXTURE_DIR = Path("tests/fixtures/log_schema")
VALIDATOR_PATH = Path("scripts/validate_log_schema.py")

spec = importlib.util.spec_from_file_location("validate_log_schema", VALIDATOR_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

validate_file = module.validate_file
validate_row = module.validate_row


def test_validate_log_schema_accepts_previous_and_current_fixture_artifacts() -> None:
    fixture_paths = [
        FIXTURE_DIR / "previous_schema_v1.jsonl",
        FIXTURE_DIR / "current_schema_v2.jsonl",
        FIXTURE_DIR / "current_schema_v3.jsonl",
    ]

    for fixture_path in fixture_paths:
        assert validate_file(fixture_path) == []


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
        "schema_version": 3,
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
        "schema_version": 3,
        "trace": "[debug] compact",
    }

    errors = validate_row(row, row_label="test-row")

    assert "test-row: missing required key 'payload'" in errors


def test_validate_log_schema_accepts_debug_turn_trace_without_legacy_trace() -> None:
    row = {
        "ts": "2026-03-03T00:00:00Z",
        "event": "debug_turn_trace",
        "schema_version": 3,
        "payload": {"debug.policy": {"reject_code": "CONTEXT_CONF_BELOW_THRESHOLD"}},
    }

    assert validate_row(row, row_label="test-row") == []
