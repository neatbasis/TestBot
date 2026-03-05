from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_VALIDATE_ISSUES_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_issue_links.py"
_spec = importlib.util.spec_from_file_location("validate_issue_links", _VALIDATE_ISSUES_PATH)
assert _spec and _spec.loader
validate_issue_links = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = validate_issue_links
_spec.loader.exec_module(validate_issue_links)

CANONICAL_SECTIONS = [
    "ID",
    "Title",
    "Status",
    "Severity",
    "Owner",
    "Created",
    "Target Sprint",
    "Principle Alignment",
    "Problem Statement",
    "Evidence",
    "Impact",
    "Acceptance Criteria",
    "Work Plan",
    "Verification",
    "Closure Notes",
]


def test_validate_pr_and_commit_metadata_requires_issue_reference(monkeypatch: pytest.MonkeyPatch) -> None:
    failures: list[validate_issue_links.ValidationFailure] = []

    responses = {
        ("rev-list", "--parents", "origin/main...HEAD"): "abc123 parent\n",
        (
            "show",
            "-s",
            "--format=%B",
            "abc123",
        ): "Add deterministic governance validator coverage for merge readiness policy enforcement update across contributor workflows now",
        ("show", "-s", "--format=%s", "abc123"): "Add governance validator coverage",
    }

    def fake_run_git(args: list[str]) -> str:
        return responses[tuple(args)]

    monkeypatch.setattr(validate_issue_links, "run_git", fake_run_git)

    validate_issue_links.validate_pr_and_commit_metadata(None, "origin/main", failures)

    assert any(f.category == "ISSUE_LINK" and "no ISSUE-XXXX" in f.message for f in failures)


def test_validate_issue_schema_fails_incomplete_canonical_fields(tmp_path: Path) -> None:
    issue_file = tmp_path / "ISSUE-0011-example.md"
    issue_file.write_text(
        """# ISSUE-0011: Example

- **ID:** ISSUE-0011
- **Title:** Example
- **Status:** maybe
- **Severity:** red
- **Owner:** TBD
- **Created:** 2026-03-05
- **Target Sprint:** TBD
- **Principle Alignment:** traceable

## Problem Statement

Need better governance checks.

## Evidence

- Sample evidence.

## Impact

Important.

## Acceptance Criteria

1. Done.

## Work Plan

- Implement checks.

## Verification

python -m pytest tests/test_validate_issue_links.py

## Closure Notes

TBD
""",
        encoding="utf-8",
    )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(validate_issue_links, "REPO_ROOT", tmp_path)
    failures: list[validate_issue_links.ValidationFailure] = []
    validate_issue_links.validate_issue_schema([issue_file], CANONICAL_SECTIONS, failures)
    monkeypatch.undo()

    messages = "\n".join(f.message for f in failures)
    assert "required canonical field 'Owner'" in messages
    assert "required canonical field 'Target Sprint'" in messages
    assert "field 'Status' has invalid value 'maybe'" in messages
    assert "section 'Closure Notes' is empty or placeholder" in messages


def test_validate_red_severity_consistency_catches_owner_and_sprint_placeholders(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    issues_dir = tmp_path / "docs" / "issues"
    issues_dir.mkdir(parents=True)
    red_tag = issues_dir / "RED_TAG.md"
    red_tag.write_text("# Red-Tag\n\n## Active\n- ISSUE-0020\n\n## Resolved\n", encoding="utf-8")

    issue_file = issues_dir / "ISSUE-0020-example.md"
    issue_file.write_text(
        """# ISSUE-0020: Example

- **ID:** ISSUE-0020
- **Title:** Example
- **Status:** open
- **Severity:** red
- **Owner:** none
- **Created:** 2026-03-05
- **Target Sprint:** n/a
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(validate_issue_links, "RED_TAG_FILE", red_tag)
    monkeypatch.setattr(validate_issue_links, "REPO_ROOT", tmp_path)

    failures: list[validate_issue_links.ValidationFailure] = []
    validate_issue_links.validate_red_severity_consistency([issue_file], failures)

    assert any("concrete Owner" in f.message for f in failures)
    assert any("concrete Target Sprint" in f.message for f in failures)
