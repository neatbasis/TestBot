from __future__ import annotations

import argparse
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
all_green_gate = _load_module("all_green_gate_from_links_test", _SCRIPTS_DIR / "all_green_gate.py")

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


def test_resolve_base_ref_uses_canonical_missing_requested_note(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_issue_links, "git_ref_exists", lambda _ref: False)

    resolved, notes = validate_issue_links.resolve_base_ref("feature/base")

    assert resolved is None
    assert notes == [
        "Base ref 'feature/base' does not exist. Provide a valid --base-ref (for example origin/main, HEAD~1, or HEAD)."
    ]


def test_validate_issue_schema_accepts_verification_manifest_reference(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    manifest_dir = repo_root / "artifacts" / "verification"
    manifest_dir.mkdir(parents=True)
    run_id = "20260316T181500Z-1a2b3c4d"
    manifest_path = manifest_dir / f"{run_id}.json"
    manifest_path.write_text(
        """{
  "run_id": "20260316T181500Z-1a2b3c4d",
  "checks": [
    {"name": "product_behave"},
    {"name": "product_eval_recall_topk4"},
    {"name": "safety_validate_log_schema"},
    {"name": "safety_validate_pipeline_stage_conformance"},
    {"name": "qa_pytest_not_live_smoke"}
  ]
}
""",
        encoding="utf-8",
    )

    issue_file = repo_root / "ISSUE-0011-example.md"
    issue_file.write_text(
        f"""# ISSUE-0011: Example

- **ID:** ISSUE-0011
- **Title:** Example
- **Status:** open
- **Severity:** amber
- **Owner:** Example Owner
- **Created:** 2026-03-05
- **Target Sprint:** Sprint-1
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

- Verification manifest: `artifacts/verification/{run_id}.json`
- Run ID: `{run_id}`

## Closure Notes

ready
""",
        encoding="utf-8",
    )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(validate_issue_links, "REPO_ROOT", repo_root)
    failures: list[validate_issue_links.ValidationFailure] = []
    validate_issue_links.validate_issue_schema([issue_file], CANONICAL_SECTIONS, failures)
    monkeypatch.undo()

    assert failures == []


def test_validate_issue_schema_fails_when_verification_manifest_missing_required_checks(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    manifest_dir = repo_root / "artifacts" / "verification"
    manifest_dir.mkdir(parents=True)
    run_id = "20260316T181500Z-deadbeef"
    (manifest_dir / f"{run_id}.json").write_text(
        """{
  "run_id": "20260316T181500Z-deadbeef",
  "checks": [
    {"name": "product_behave"},
    {"name": "qa_pytest_not_live_smoke"}
  ]
}
""",
        encoding="utf-8",
    )

    issue_file = repo_root / "ISSUE-0011-example.md"
    issue_file.write_text(
        f"""# ISSUE-0011: Example

- **ID:** ISSUE-0011
- **Title:** Example
- **Status:** open
- **Severity:** amber
- **Owner:** Example Owner
- **Created:** 2026-03-05
- **Target Sprint:** Sprint-1
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

- Verification manifest: `artifacts/verification/{run_id}.json`
- Run ID: `{run_id}`

## Closure Notes

ready
""",
        encoding="utf-8",
    )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(validate_issue_links, "REPO_ROOT", repo_root)
    failures: list[validate_issue_links.ValidationFailure] = []
    validate_issue_links.validate_issue_schema([issue_file], CANONICAL_SECTIONS, failures)
    monkeypatch.undo()

    messages = "\n".join(f.message for f in failures)
    assert "missing required checks" in messages


def test_validate_issue_schema_fails_when_verification_manifest_run_id_mismatch(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    manifest_dir = repo_root / "artifacts" / "verification"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "20260316T181500Z-1a2b3c4d.json").write_text(
        """{
  "run_id": "20260316T181500Z-1a2b3c4d",
  "checks": []
}
""",
        encoding="utf-8",
    )

    issue_file = repo_root / "ISSUE-0011-example.md"
    issue_file.write_text(
        """# ISSUE-0011: Example

- **ID:** ISSUE-0011
- **Title:** Example
- **Status:** open
- **Severity:** amber
- **Owner:** Example Owner
- **Created:** 2026-03-05
- **Target Sprint:** Sprint-1
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

- Verification manifest: `artifacts/verification/20260316T181500Z-1a2b3c4d.json`
- Run ID: `20260316T181500Z-deadbeef`

## Closure Notes

ready
""",
        encoding="utf-8",
    )

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(validate_issue_links, "REPO_ROOT", repo_root)
    failures: list[validate_issue_links.ValidationFailure] = []
    validate_issue_links.validate_issue_schema([issue_file], CANONICAL_SECTIONS, failures)
    monkeypatch.undo()

    messages = "\n".join(f.message for f in failures)
    assert "does not match manifest file run ID" in messages


def test_verification_manifest_round_trip_generated_manifest_is_accepted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    run_id = "20260316T181500Z-1a2b3c4d"
    repo_root = tmp_path
    manifest_dir = repo_root / "artifacts" / "verification"

    monkeypatch.setattr(all_green_gate, "REPO_ROOT", repo_root)
    monkeypatch.setattr(all_green_gate, "VERIFICATION_MANIFEST_DIR", manifest_dir)
    monkeypatch.setattr(validate_issue_links, "REPO_ROOT", repo_root)

    args = argparse.Namespace(base_ref="origin/main", continue_on_failure=False, kpi_guardrail_mode="optional")
    summary = {
        "checks": [{"name": check_name} for check_name in all_green_gate.REQUIRED_VERIFICATION_CHECKS],
    }
    manifest_path = all_green_gate.write_verification_manifest(
        run_id=run_id,
        args=args,
        effective_base_ref="origin/main",
        profile="full",
        summary=summary,
    )

    verification_body = (
        f"- Verification manifest: `artifacts/verification/{run_id}.json`\n"
        f"- Run ID: `{run_id}`"
    )

    failures: list[validate_issue_links.ValidationFailure] = []
    validate_issue_links.validate_verification_manifest_reference(
        verification_body,
        Path("docs/issues/ISSUE-9999.md"),
        failures,
    )

    assert manifest_path.exists()
    assert failures == []


def test_verification_manifest_round_trip_fails_when_declared_run_id_mismatches_filename(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    run_id = "20260316T181500Z-1a2b3c4d"
    repo_root = tmp_path
    manifest_dir = repo_root / "artifacts" / "verification"

    monkeypatch.setattr(all_green_gate, "REPO_ROOT", repo_root)
    monkeypatch.setattr(all_green_gate, "VERIFICATION_MANIFEST_DIR", manifest_dir)
    monkeypatch.setattr(validate_issue_links, "REPO_ROOT", repo_root)

    args = argparse.Namespace(base_ref="origin/main", continue_on_failure=False, kpi_guardrail_mode="optional")
    summary = {
        "checks": [{"name": check_name} for check_name in all_green_gate.REQUIRED_VERIFICATION_CHECKS],
    }
    all_green_gate.write_verification_manifest(
        run_id=run_id,
        args=args,
        effective_base_ref="origin/main",
        profile="full",
        summary=summary,
    )

    verification_body = (
        f"- Verification manifest: `artifacts/verification/{run_id}.json`\n"
        "- Run ID: `20260316T181500Z-deadbeef`"
    )

    failures: list[validate_issue_links.ValidationFailure] = []
    validate_issue_links.validate_verification_manifest_reference(
        verification_body,
        Path("docs/issues/ISSUE-9999.md"),
        failures,
    )

    assert failures
    assert any("does not match manifest file run ID" in failure.message for failure in failures)


def test_validate_pr_and_commit_metadata_uses_shared_metadata_primitive(monkeypatch: pytest.MonkeyPatch) -> None:
    failures: list[validate_issue_links.ValidationFailure] = []

    responses = {
        ("rev-list", "--parents", "origin/main...HEAD"): "abc123 parent\n",
        ("show", "-s", "--format=%B", "abc123"): "commit body",
        ("show", "-s", "--format=%s", "abc123"): "subject",
    }

    monkeypatch.setattr(validate_issue_links, "run_git", lambda args: responses[tuple(args)])
    monkeypatch.setattr(validate_issue_links, "metadata_missing_issue_reference", lambda _text: True)

    validate_issue_links.validate_pr_and_commit_metadata(None, "origin/main", failures)

    assert any("no ISSUE-XXXX reference" in f.message for f in failures)


def test_validate_issue_schema_uses_shared_missing_sections_primitive(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    issue_file = tmp_path / "ISSUE-0011-example.md"
    issue_file.write_text("- **ID:** ISSUE-0011\n", encoding="utf-8")

    monkeypatch.setattr(validate_issue_links, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(validate_issue_links, "missing_canonical_sections", lambda _text, _sections: ["Problem Statement"])

    failures: list[validate_issue_links.ValidationFailure] = []
    validate_issue_links.validate_issue_schema([issue_file], CANONICAL_SECTIONS, failures, ruleset=validate_issue_links.RULESET_TRIAGE)

    assert any("missing canonical schema fields/sections: Problem Statement" in f.message for f in failures)
