from __future__ import annotations

from pathlib import Path


INVENTORY_PATH = Path("docs/architecture/runtime-entrypoint-legacy-inventory-2026-03-27.md")
REQUIRES_MIGRATION_FIELDS = {"transitional_warn", "temporary_keep", "extract_later"}
REQUIRED_COLUMNS = {
    "Current owner",
    "Canonical replacement",
    "Removal condition",
    "Blocker",
    "Recommended next PR scope",
}


def _parse_markdown_table_rows(markdown: str) -> tuple[list[str], list[list[str]]]:
    lines = markdown.splitlines()
    header_index = next(i for i, line in enumerate(lines) if line.startswith("| Surface |"))
    header = [cell.strip() for cell in lines[header_index].strip().strip("|").split("|")]
    rows: list[list[str]] = []
    for line in lines[header_index + 2 :]:
        if not line.startswith("|"):
            break
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return header, rows


def test_runtime_inventory_has_required_migration_fields_for_remaining_items() -> None:
    header, rows = _parse_markdown_table_rows(INVENTORY_PATH.read_text())
    index_by_column = {name: idx for idx, name in enumerate(header)}

    for required in REQUIRED_COLUMNS | {"Classification"}:
        assert required in index_by_column

    for row in rows:
        classification = row[index_by_column["Classification"]].strip("`")
        if classification not in REQUIRES_MIGRATION_FIELDS:
            continue

        for column in REQUIRED_COLUMNS:
            value = row[index_by_column[column]]
            assert value, f"Missing '{column}' for classification '{classification}'"
            assert value not in {"TBD", "N/A", "none", "None"}
