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


validate_issues = _load_module("validate_issues_ruleset_matrix", _SCRIPTS_DIR / "validate_issues.py")
validate_issue_links = _load_module("validate_issue_links_ruleset_matrix", _SCRIPTS_DIR / "validate_issue_links.py")

MATRIX_CANONICAL_SECTIONS = [
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


@pytest.fixture
def governance_ruleset_issue_factory(tmp_path: Path):
    def _write(category: str) -> Path:
        issue = tmp_path / f"ISSUE-4242-{category}.md"

        if category == "passes_strict_and_triage":
            issue.write_text(
                """# ISSUE-4242: matrix baseline pass\n
- **ID:** ISSUE-4242
- **Title:** Matrix baseline pass
- **Status:** open
- **Issue State:** governed_execution
- **Severity:** amber
- **Owner:** Matrix Team
- **Created:** 2026-03-17
- **Target Sprint:** S1
- **Principle Alignment:** deterministic

## Problem Statement

A compliant issue that should pass under both strict and triage.

## Evidence

- Evidence line.

## Impact

Cross-validator contract proof.

## Acceptance Criteria

1. Matrix test proves expected behavior.

## Work Plan

- Execute validators against shared fixtures.

## Verification

python -m pytest tests/test_governance_ruleset_matrix.py

## Closure Notes

Pending.
""",
                encoding="utf-8",
            )
        elif category == "fails_strict_and_triage":
            issue.write_text(
                """# ISSUE-4242: matrix fail both\n
- **ID:** ISSUE-4242
- **Status:** open
- **Issue State:** governed_execution
- **Severity:** amber
- **Owner:** Matrix Team
- **Created:** 2026-03-17
- **Target Sprint:** S1
- **Principle Alignment:** deterministic

## Problem Statement

Missing Title should fail in both rulesets for both validators.

## Evidence

- Evidence line.

## Impact

Coverage for shared fail behavior.

## Acceptance Criteria

1. Validators fail in strict and triage.

## Work Plan

- Run matrix validation.

## Verification

python -m pytest tests/test_governance_ruleset_matrix.py

## Closure Notes

Pending.
""",
                encoding="utf-8",
            )
        elif category == "fails_strict_passes_triage":
            issue.write_text(
                """# ISSUE-4242: matrix ruleset divergence\n
- **ID:** ISSUE-4242
- **Title:** Ruleset divergence fixture
- **Status:** open
- **Issue State:** governed_execution
- **Severity:** red
- **Created:** 2026-03-17
- **Principle Alignment:** deterministic

## Owner

Heading-only owner intentionally exercises canonical section presence without a schema field value.

## Target Sprint

Heading-only target sprint intentionally exercises strict-vs-triage divergence.

## Problem Statement

This fixture should be accepted by triage but rejected by strict.

## Evidence

- Evidence line.

## Impact

Proves staged rulesets are honored.

## Acceptance Criteria

1. Strict rejects this fixture.
2. Triage accepts this fixture.

## Work Plan

- Execute shared fixture matrix.

## Verification

python -m pytest tests/test_governance_ruleset_matrix.py

## Closure Notes

Pending.
""",
                encoding="utf-8",
            )
        else:
            raise ValueError(f"Unknown matrix category: {category}")

        return issue

    return _write


def _run_validator(
    validator: str,
    issue_file: Path,
    ruleset: str,
    monkeypatch: pytest.MonkeyPatch,
) -> list[str]:
    monkeypatch.setattr(validate_issues, "REPO_ROOT", issue_file.parent)
    monkeypatch.setattr(validate_issue_links, "REPO_ROOT", issue_file.parent)

    if validator == "issues":
        failures: list[str] = []
        validate_issues.validate_issue_files([issue_file], MATRIX_CANONICAL_SECTIONS, failures, ruleset=ruleset)
        return failures

    if validator == "issue_links":
        failures: list[validate_issue_links.ValidationFailure] = []
        validate_issue_links.validate_issue_schema(
            [issue_file],
            MATRIX_CANONICAL_SECTIONS,
            failures,
            ruleset=ruleset,
        )
        return [failure.message for failure in failures]

    raise ValueError(f"Unknown validator: {validator}")


@pytest.mark.parametrize(
    ("category", "validator", "ruleset", "should_pass"),
    [
        ("passes_strict_and_triage", "issues", validate_issues.RULESET_STRICT, True),
        ("passes_strict_and_triage", "issues", validate_issues.RULESET_TRIAGE, True),
        ("passes_strict_and_triage", "issue_links", validate_issue_links.RULESET_STRICT, True),
        ("passes_strict_and_triage", "issue_links", validate_issue_links.RULESET_TRIAGE, True),
        ("fails_strict_and_triage", "issues", validate_issues.RULESET_STRICT, False),
        ("fails_strict_and_triage", "issues", validate_issues.RULESET_TRIAGE, False),
        ("fails_strict_and_triage", "issue_links", validate_issue_links.RULESET_STRICT, False),
        ("fails_strict_and_triage", "issue_links", validate_issue_links.RULESET_TRIAGE, False),
        ("fails_strict_passes_triage", "issues", validate_issues.RULESET_STRICT, False),
        ("fails_strict_passes_triage", "issues", validate_issues.RULESET_TRIAGE, True),
        ("fails_strict_passes_triage", "issue_links", validate_issue_links.RULESET_STRICT, False),
        ("fails_strict_passes_triage", "issue_links", validate_issue_links.RULESET_TRIAGE, True),
    ],
    ids=lambda case: str(case),
)
def test_shared_ruleset_matrix_across_issue_validators(
    category: str,
    validator: str,
    ruleset: str,
    should_pass: bool,
    governance_ruleset_issue_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issue_file = governance_ruleset_issue_factory(category)

    failures = _run_validator(validator, issue_file, ruleset, monkeypatch)

    if should_pass:
        assert failures == []
    else:
        assert failures


@pytest.mark.parametrize("validator", ["issues", "issue_links"])
def test_strict_rejects_but_triage_accepts_relaxed_schema_fixture(
    validator: str,
    governance_ruleset_issue_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issue_file = governance_ruleset_issue_factory("fails_strict_passes_triage")

    strict_failures = _run_validator(validator, issue_file, "strict", monkeypatch)
    triage_failures = _run_validator(validator, issue_file, "triage", monkeypatch)

    assert strict_failures, f"{validator} strict should reject heading-only Owner/Target Sprint fixture"
    assert triage_failures == [], f"{validator} triage should accept heading-only Owner/Target Sprint fixture"
