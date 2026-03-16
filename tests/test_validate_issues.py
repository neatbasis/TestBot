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


validate_issues = _load_module("validate_issues", _SCRIPTS_DIR / "validate_issues.py")
validate_issue_links = _load_module("validate_issue_links_from_issues_test", _SCRIPTS_DIR / "validate_issue_links.py")
governance_rules = _load_module("governance_rules_from_issues_test", _SCRIPTS_DIR / "governance_rules.py")


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


def test_shared_fixture_parity_across_validators() -> None:
    fixture = "[trivial] docs nits around wording and formatting only"

    assert validate_issues.is_non_trivial_pr(fixture) == validate_issue_links.is_non_trivial(fixture)
    assert validate_issues.has_issue_reference(fixture) == governance_rules.has_issue_reference(fixture)


def test_has_issue_reference_accepts_issue_id_without_issue_prefix() -> None:
    body = "Summary: closes governance drift for ISSUE-0015 with deterministic checks"

    assert validate_issues.has_issue_reference(body) is True


def test_canonical_sections_are_parsed_via_shared_rules() -> None:
    policy = """
Every issue file must include:
1. `Problem Statement`
2. `Evidence`

Other text.
"""

    assert validate_issues.parse_canonical_sections(policy) == governance_rules.parse_canonical_sections(policy)
