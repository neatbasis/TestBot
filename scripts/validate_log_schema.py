from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CURRENT_SCHEMA_VERSION = 3

COMMON_FIELDS: dict[str, type] = {
    "ts": str,
    "event": str,
}

EVENT_FIELDS: dict[str, dict[str, type]] = {
    "pipeline_state_snapshot": {
        "stage": str,
        "state": dict,
    },
    "stage_transition_validation": {
        "stage": str,
        "boundary": str,
        "invariant_refs": list,
        "passed": bool,
        "failures": list,
    },
    "provenance_summary": {
        "provenance_types": list,
        "used_memory_refs": list,
        "used_source_evidence_refs": list,
        "source_evidence_attribution": list,
        "basis_statement": str,
    },
}


def _check_fields(row: dict[str, Any], expected: dict[str, type], *, row_label: str) -> list[str]:
    errors: list[str] = []
    for key, expected_type in expected.items():
        if key not in row:
            errors.append(f"{row_label}: missing required key '{key}'")
            continue
        if not isinstance(row[key], expected_type):
            errors.append(
                f"{row_label}: key '{key}' expected {expected_type.__name__}, "
                f"got {type(row[key]).__name__}"
            )
    return errors


def validate_row(row: dict[str, Any], *, row_label: str = "row") -> list[str]:
    errors = _check_fields(row, COMMON_FIELDS, row_label=row_label)

    schema_version = row.get("schema_version", 1)
    if not isinstance(schema_version, int):
        errors.append(f"{row_label}: key 'schema_version' expected int when present")
    elif schema_version not in {1, 2, CURRENT_SCHEMA_VERSION}:
        errors.append(f"{row_label}: unsupported schema_version '{schema_version}'")

    event = row.get("event")
    if isinstance(event, str) and event in EVENT_FIELDS:
        errors.extend(_check_fields(row, EVENT_FIELDS[event], row_label=row_label))

    return errors


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_no}: invalid JSON ({exc})")
                continue
            if not isinstance(row, dict):
                errors.append(f"{path}:{line_no}: row must decode to object")
                continue
            errors.extend(validate_row(row, row_label=f"{path}:{line_no}"))
    return errors


def main() -> int:
    sample_dir = Path("tests/fixtures/log_schema")
    paths = sorted(sample_dir.glob("*.jsonl"))
    if not paths:
        print(f"No sample artifacts found in {sample_dir}")
        return 1

    all_errors: list[str] = []
    for path in paths:
        all_errors.extend(validate_file(path))

    if all_errors:
        print("Log schema validation failed:")
        for err in all_errors:
            print(f"- {err}")
        return 1

    print(f"Validated {len(paths)} artifact(s) against v1/v{CURRENT_SCHEMA_VERSION} schemas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
