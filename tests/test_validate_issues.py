from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_VALIDATE_ISSUES_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_issues.py"
_spec = importlib.util.spec_from_file_location("validate_issues", _VALIDATE_ISSUES_PATH)
assert _spec and _spec.loader
validate_issues = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = validate_issues
_spec.loader.exec_module(validate_issues)


def test_resolve_base_ref_prefers_origin_main_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_issues, "git_ref_exists", lambda ref: ref == "origin/main")

    resolved, notes = validate_issues.resolve_base_ref("origin/main")

    assert resolved == "origin/main"
    assert notes == []


def test_resolve_base_ref_falls_back_when_origin_main_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_issues, "git_ref_exists", lambda ref: ref == "HEAD~1")

    resolved, notes = validate_issues.resolve_base_ref("origin/main")

    assert resolved == "HEAD~1"
    assert any("falling back to 'HEAD~1'" in note for note in notes)
    assert any("This is expected in Codex task containers or shallow CI clones." in note for note in notes)


def test_is_non_trivial_pr_treats_bracket_trivial_as_trivial() -> None:
    body = "[trivial] docs nits around wording and formatting only"

    assert validate_issues.is_non_trivial_pr(body) is False


def test_has_issue_reference_accepts_issue_id_without_issue_prefix() -> None:
    body = "Summary: closes governance drift for ISSUE-0015 with deterministic checks"

    assert validate_issues.has_issue_reference(body) is True
