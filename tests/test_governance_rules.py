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


governance_rules = _load_module("governance_rules_for_tests", _SCRIPTS_DIR / "governance_rules.py")


def _resolve(base_ref: str, exists: set[str]) -> tuple[str | None, list[str]]:
    return governance_rules.resolve_base_ref(base_ref, ref_exists=lambda ref: ref in exists)


def test_resolve_base_ref_prefers_requested_ref_when_available() -> None:
    resolved, notes = _resolve("origin/main", {"origin/main", "HEAD~1", "HEAD"})

    assert resolved == "origin/main"
    assert notes == []


def test_resolve_base_ref_falls_back_to_head1_for_origin_main() -> None:
    resolved, notes = _resolve("origin/main", {"HEAD~1", "HEAD"})

    assert resolved == "HEAD~1"
    assert any("falling back to 'HEAD~1'" in note for note in notes)


def test_resolve_base_ref_falls_back_to_head_when_head1_missing() -> None:
    resolved, notes = _resolve("origin/main", {"HEAD"})

    assert resolved == "HEAD"
    assert any("falling back to 'HEAD'" in note for note in notes)


def test_resolve_base_ref_rejects_missing_non_origin_main() -> None:
    resolved, notes = _resolve("feature/base", set())

    assert resolved is None
    assert notes == [
        "Base ref 'feature/base' does not exist. Provide a valid --base-ref (for example origin/main, HEAD~1, or HEAD)."
    ]


def test_resolve_base_ref_returns_missing_origin_note_when_no_fallbacks() -> None:
    resolved, notes = _resolve("origin/main", set())

    assert resolved is None
    assert notes == [
        "Could not resolve base ref 'origin/main' or fallbacks (HEAD~1, HEAD). Governance diff checks will run against a reduced baseline and all issue files may be validated."
    ]


def test_git_ref_exists_uses_rev_parse_exit_code(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen: list[list[str]] = []

    class Completed:
        def __init__(self, returncode: int):
            self.returncode = returncode

    def fake_run(cmd: list[str], *, cwd: Path, capture_output: bool, text: bool) -> Completed:
        seen.append(cmd)
        assert cwd == tmp_path
        assert capture_output is True
        assert text is True
        return Completed(returncode=0)

    monkeypatch.setattr(governance_rules.subprocess, "run", fake_run)

    assert governance_rules.git_ref_exists("origin/main", repo_root=tmp_path) is True
    assert seen == [["git", "rev-parse", "--verify", "--quiet", "origin/main"]]


def test_git_ref_exists_returns_false_for_nonzero_exit_code(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class Completed:
        def __init__(self, returncode: int):
            self.returncode = returncode

    def fake_run(cmd: list[str], *, cwd: Path, capture_output: bool, text: bool) -> Completed:
        assert cmd == ["git", "rev-parse", "--verify", "--quiet", "HEAD~1"]
        assert cwd == tmp_path
        assert capture_output is True
        assert text is True
        return Completed(returncode=1)

    monkeypatch.setattr(governance_rules.subprocess, "run", fake_run)

    assert governance_rules.git_ref_exists("HEAD~1", repo_root=tmp_path) is False


def test_rule_family_ownership_map_declares_shared_validator_consumers() -> None:
    ownership = governance_rules.RULE_FAMILY_OWNERSHIP

    assert ownership["canonical_section_presence"]["consumers"] == [
        "scripts/validate_issues.py",
        "scripts/validate_issue_links.py",
    ]
    assert ownership["metadata_issue_reference"]["consumers"] == [
        "scripts/validate_issues.py",
        "scripts/validate_issue_links.py",
    ]


def test_missing_canonical_sections_detects_absent_schema_entries() -> None:
    issue_text = """
- **ID:** ISSUE-0100

## Problem Statement

Need deterministic ownership.
"""

    missing = governance_rules.missing_canonical_sections(issue_text, ["ID", "Title", "Problem Statement"])

    assert missing == ["Title"]


def test_metadata_missing_issue_reference_requires_non_trivial_metadata() -> None:
    assert governance_rules.metadata_missing_issue_reference(
        "Implement robust governance metadata checks for release readiness and branch policy enforcement across CI pipelines"
    ) is True
    assert governance_rules.metadata_missing_issue_reference("[trivial] docs touchups") is False
    assert governance_rules.metadata_missing_issue_reference("Implements ISSUE-0001 policy checks for metadata") is False
