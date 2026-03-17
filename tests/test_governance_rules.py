from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


governance_rules = _load_module("governance_rules_for_tests", _SCRIPTS_DIR / "governance_rules.py")


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


def test_contains_canonical_section_accepts_list_item_field_format() -> None:
    issue_text = "- **Problem Statement:** some content"

    assert governance_rules.contains_canonical_section(issue_text, "Problem Statement") is True


def test_has_issue_reference_accepts_issue_id_without_issue_prefix() -> None:
    body = "Summary: closes governance drift for ISSUE-0015 with deterministic checks"

    assert governance_rules.has_issue_reference(body) is True
