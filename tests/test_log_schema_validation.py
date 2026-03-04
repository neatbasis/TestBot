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
