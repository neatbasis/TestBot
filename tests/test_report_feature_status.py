from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_REPORT_FEATURE_STATUS_PATH = Path(__file__).resolve().parents[1] / "scripts" / "report_feature_status.py"
_spec = importlib.util.spec_from_file_location("report_feature_status", _REPORT_FEATURE_STATUS_PATH)
assert _spec and _spec.loader
report_feature_status = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = report_feature_status
_spec.loader.exec_module(report_feature_status)


def test_issue_matches_keyword_checks_id_title_stem_and_content(tmp_path: Path) -> None:
    issue_path = tmp_path / "docs" / "issues" / "ISSUE-4242-governance-gap.md"
    issue_path.parent.mkdir(parents=True)
    issue_path.write_text("placeholder", encoding="utf-8")

    issue = report_feature_status.OpenIssue(
        issue_id="ISSUE-4242",
        title="Governance readiness gate traceability gap",
        status="open",
        path=issue_path,
        content_lower="mentions qa_validate_issue_links and deterministic evidence",
    )

    assert report_feature_status.issue_matches_keyword(issue, "ISSUE-4242")
    assert report_feature_status.issue_matches_keyword(issue, "traceability gap")
    assert report_feature_status.issue_matches_keyword(issue, "governance-gap")
    assert report_feature_status.issue_matches_keyword(issue, "qa_validate_issue_links")


def test_build_report_links_partial_capability_to_issue_via_id_keyword(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(report_feature_status, "REPO_ROOT", tmp_path)

    issue_path = tmp_path / "docs" / "issues" / "ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md"
    issue_path.parent.mkdir(parents=True)
    issue_path.write_text("placeholder", encoding="utf-8")

    contract = {
        "capabilities": [
            {
                "capability_id": "governance_readiness_gate",
                "capability_name": "Canonical all-green merge gate and issue governance checks",
                "current_status": "partial",
                "issue_keywords": ["ISSUE-0007", "governance_readiness_gate"],
                "roadmap_priority_refs": ["P5"],
            }
        ]
    }
    issue = report_feature_status.OpenIssue(
        issue_id="ISSUE-0007",
        title="Governance readiness gate traceability is partial for capability-linked issue enforcement",
        status="open",
        path=issue_path,
        content_lower="open issue record body",
    )

    report_markdown, summary = report_feature_status.build_report(
        contract=contract,
        gate_results={},
        open_issues=[issue],
        roadmap_priorities={"P5": ["docs/roadmap/current-status-and-next-5-priorities.md"]},
        generated_at_utc="2026-03-06T00:00:00Z",
        input_paths={
            "contract_path": "docs/qa/feature-status.yaml",
            "gate_summary_path": "artifacts/all-green-gate-summary.json",
            "issues_dir": "docs/issues",
            "roadmap_dir": "docs/roadmap",
        },
        source_file_metadata={"contract": None, "gate_summary": None, "open_issues": []},
        gate_stale_warning=None,
    )

    capability = summary["capabilities"][0]
    assert capability["effective_status"] == "partial"
    assert capability["relevant_open_issues"] == [
        {
            "id": "ISSUE-0007",
            "title": "Governance readiness gate traceability is partial for capability-linked issue enforcement",
            "path": "docs/issues/ISSUE-0007-behave-gate-not-enforced-in-pr-validation.md",
        }
    ]
    assert "open issues: ISSUE-0007" in report_markdown


def test_main_writes_json_summary_with_open_issue_linkage(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    contract_path = repo_root / "docs" / "qa" / "feature-status.yaml"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text(
        """
capabilities:
  - capability_id: governance_readiness_gate
    capability_name: Canonical all-green merge gate and issue governance checks
    current_status: partial
    roadmap_priority_refs: [P5]
    issue_keywords: [ISSUE-0007]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    gate_summary_path = repo_root / "artifacts" / "all-green-gate-summary.json"
    gate_summary_path.parent.mkdir(parents=True)
    gate_summary_path.write_text('{"checks": []}\n', encoding="utf-8")

    issue_path = repo_root / "docs" / "issues" / "ISSUE-0007-example.md"
    issue_path.parent.mkdir(parents=True)
    issue_path.write_text(
        """
# ISSUE-0007
- **ID:** ISSUE-0007
- **Title:** Governance readiness gate traceability is partial
- **Status:** open
""".strip()
        + "\n",
        encoding="utf-8",
    )

    roadmap_path = repo_root / "docs" / "roadmap" / "current.md"
    roadmap_path.parent.mkdir(parents=True)
    roadmap_path.write_text("P5 governance\n", encoding="utf-8")

    output_report = repo_root / "docs" / "qa" / "feature-status-report.md"
    output_summary = repo_root / "artifacts" / "feature-status-summary.json"

    monkeypatch.setattr(report_feature_status, "REPO_ROOT", repo_root)
    monkeypatch.setattr(
        report_feature_status,
        "parse_args",
        lambda: type(
            "Args",
            (),
            {
                "contract": Path("docs/qa/feature-status.yaml"),
                "gate_summary": Path("artifacts/all-green-gate-summary.json"),
                "issues_dir": Path("docs/issues"),
                "roadmap_dir": Path("docs/roadmap"),
                "output": Path("docs/qa/feature-status-report.md"),
                "json_output": Path("artifacts/feature-status-summary.json"),
            },
        )(),
    )

    assert report_feature_status.main() == 0

    summary_payload = json.loads(output_summary.read_text(encoding="utf-8"))
    capability = summary_payload["capabilities"][0]
    assert capability["capability_id"] == "governance_readiness_gate"
    assert capability["relevant_open_issues"][0]["id"] == "ISSUE-0007"
    assert summary_payload["open_issue_count"] == 1


def test_build_report_renders_gate_stale_warning_with_refresh_hint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(report_feature_status, "REPO_ROOT", tmp_path)

    report_markdown, summary = report_feature_status.build_report(
        contract={"capabilities": []},
        gate_results={},
        open_issues=[],
        roadmap_priorities={},
        generated_at_utc="2026-03-07T00:00:00Z",
        input_paths={
            "contract_path": "docs/qa/feature-status.yaml",
            "gate_summary_path": "artifacts/all-green-gate-summary.json",
            "issues_dir": "docs/issues",
            "roadmap_dir": "docs/roadmap",
        },
        source_file_metadata={"contract": None, "gate_summary": None, "open_issues": []},
        gate_stale_warning=(
            "Gate summary appears older than one or more source files "
            "(contract or open issue records); regenerate gate evidence for freshest status. "
            "Hint: run `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json` "
            "to refresh `artifacts/all-green-gate-summary.json`."
        ),
    )

    assert "Hint: run `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json`" in report_markdown
    assert summary["warnings"]
