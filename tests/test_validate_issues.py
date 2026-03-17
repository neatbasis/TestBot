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


def test_resolve_base_ref_uses_canonical_missing_origin_note(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_issues, "governance_git_ref_exists", lambda _ref, *, repo_root: False)

    resolved, notes = validate_issues.resolve_safe_changed_path_base_ref("origin/main")

    assert resolved is None
    assert notes == [
        "Could not resolve base ref 'origin/main' or fallbacks (HEAD~1, HEAD). Governance diff checks will run against a reduced baseline and all issue files may be validated."
    ]


def _write_issue(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_validate_issue_files_accepts_triage_intake_minimal_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    issue = _write_issue(
        tmp_path,
        "ISSUE-9998-triage-intake.md",
        """
**ID:** ISSUE-9998
**Title:** Intake only
**Issue State:** triage_intake
**Status:** open
**Problem:** Initial report
**Owner:** Team
**Severity:** amber
**Next Action:** Reproduce and scope
""",
    )

    monkeypatch.setattr(validate_issues, "REPO_ROOT", tmp_path)

    failures: list[str] = []
    validate_issues.validate_issue_files([issue], ["ID", "Title", "Status", "Issue State", "Severity", "Owner"], failures, ruleset=validate_issues.RULESET_STRICT)

    assert failures == []


def test_validate_issue_files_accepts_governed_execution_full_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    issue = _write_issue(
        tmp_path,
        "ISSUE-9999-governed.md",
        """
**ID:** ISSUE-9999
**Title:** Full issue
**Status:** in_progress
**Issue State:** governed_execution
**Severity:** green
**Owner:** Team
**Created:** 2026-01-01
**Target Sprint:** S1
**Principle Alignment:** deterministic
**Problem Statement:** Defined problem
**Evidence:** Logs
**Impact:** Delivery
**Acceptance Criteria:** Tests pass
**Work Plan:** Implement
**Verification:** Run pytest
**Closure Notes:** Pending
""",
    )

    monkeypatch.setattr(validate_issues, "REPO_ROOT", tmp_path)

    failures: list[str] = []
    canonical = [
        "ID",
        "Title",
        "Status",
        "Issue State",
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
    validate_issues.validate_issue_files([issue], canonical, failures, ruleset=validate_issues.RULESET_STRICT)

    assert failures == []


def test_validate_issue_files_rejects_triage_intake_in_progress_transition(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    issue = _write_issue(
        tmp_path,
        "ISSUE-7777-invalid-transition.md",
        """
**ID:** ISSUE-7777
**Title:** Invalid transition
**Issue State:** triage_intake
**Status:** in_progress
**Problem:** Initial report
**Owner:** Team
**Severity:** green
**Next Action:** Promote schema
""",
    )

    monkeypatch.setattr(validate_issues, "REPO_ROOT", tmp_path)

    failures: list[str] = []
    validate_issues.validate_issue_files([issue], ["ID", "Title", "Status", "Issue State"], failures, ruleset=validate_issues.RULESET_STRICT)

    assert any("triage_intake issues must remain Status 'open'" in failure for failure in failures)


def test_validate_pr_body_uses_shared_metadata_issue_reference_primitive(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    body = tmp_path / "pr.md"
    body.write_text("non trivial body", encoding="utf-8")
    monkeypatch.setattr(validate_issues, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(validate_issues, "metadata_missing_issue_reference", lambda _text: True)

    failures: list[str] = []
    validate_issues.validate_pr_body(Path("pr.md"), failures)

    assert failures == ["Non-trivial PR description must include at least one ISSUE-XXXX reference."]


def test_validate_issue_files_uses_shared_missing_canonical_sections_primitive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    issue = _write_issue(
        tmp_path,
        "ISSUE-1000-minimal.md",
        """
**Issue State:** governed_execution
**Status:** open
""",
    )
    monkeypatch.setattr(validate_issues, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(validate_issues, "missing_canonical_sections", lambda _text, _sections: ["Title"])

    failures: list[str] = []
    validate_issues.validate_issue_files([issue], ["ID", "Title"], failures, ruleset=validate_issues.RULESET_STRICT)

    assert any("missing canonical sections: Title" in failure for failure in failures)
