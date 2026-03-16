from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validate_issue_links = _load_module("validate_issue_links", _SCRIPTS_DIR / "validate_issue_links.py")
validate_issues = _load_module("validate_issues_from_links_test", _SCRIPTS_DIR / "validate_issues.py")

governance_rules = _load_module("governance_rules_from_links_test", _SCRIPTS_DIR / "governance_rules.py")

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


def test_shared_rule_parity_for_non_trivial_and_issue_references() -> None:
    fixture = "Implement deterministic governance checks across pipelines for ISSUE-0042 readiness evidence"

    assert validate_issue_links.is_non_trivial(fixture) == validate_issues.is_non_trivial_pr(fixture)
    assert validate_issues.has_issue_reference(fixture) == governance_rules.has_issue_reference(fixture)


# existing coverage

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


def test_validate_red_tag_generated_content_detects_mismatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    issues_dir = tmp_path / "docs" / "issues"
    issues_dir.mkdir(parents=True)
    red_tag = issues_dir / "RED_TAG.md"
    red_tag.write_text("# stale\n", encoding="utf-8")

    monkeypatch.setattr(validate_issue_links, "RED_TAG_FILE", red_tag)
    monkeypatch.setattr(validate_issue_links, "render_red_tag", lambda rows: "# fresh\n")
    monkeypatch.setattr(validate_issue_links, "list_red_open_issues", lambda: [])

    failures: list[validate_issue_links.ValidationFailure] = []
    validate_issue_links.validate_red_tag_generated_content(failures)

    assert any("does not match generated red-tag index content" in f.message for f in failures)


def test_validate_red_tag_generated_content_accepts_match(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    issues_dir = tmp_path / "docs" / "issues"
    issues_dir.mkdir(parents=True)
    red_tag = issues_dir / "RED_TAG.md"
    red_tag.write_text("# fresh\n", encoding="utf-8")

    monkeypatch.setattr(validate_issue_links, "RED_TAG_FILE", red_tag)
    monkeypatch.setattr(validate_issue_links, "render_red_tag", lambda rows: "# fresh\n")
    monkeypatch.setattr(validate_issue_links, "list_red_open_issues", lambda: [])

    failures: list[validate_issue_links.ValidationFailure] = []
    validate_issue_links.validate_red_tag_generated_content(failures)

    assert failures == []


def test_resolve_base_ref_prefers_requested_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_issue_links, "git_ref_exists", lambda ref: ref == "origin/main")

    resolved, notes = validate_issue_links.resolve_base_ref("origin/main")

    assert resolved == "origin/main"
    assert notes == []


def test_resolve_base_ref_falls_back_when_origin_main_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_issue_links, "git_ref_exists", lambda ref: ref == "HEAD~1")

    resolved, notes = validate_issue_links.resolve_base_ref("origin/main")

    assert resolved == "HEAD~1"
    assert any("falling back to 'HEAD~1'" in note for note in notes)
    assert any("This is expected in Codex task containers or shallow CI clones." in note for note in notes)


def test_resolve_base_ref_falls_back_to_head_when_head1_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_issue_links, "git_ref_exists", lambda ref: ref == "HEAD")

    resolved, notes = validate_issue_links.resolve_base_ref("origin/main")

    assert resolved == "HEAD"
    assert any("falling back to 'HEAD'" in note for note in notes)
