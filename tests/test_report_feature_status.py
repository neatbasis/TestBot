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
        content="placeholder",
        content_lower="mentions qa_validate_issue_links and deterministic evidence",
    )

    assert report_feature_status.issue_matches_keyword(issue, "ISSUE-4242")
    assert report_feature_status.issue_matches_keyword(issue, "traceability gap")
    assert report_feature_status.issue_matches_keyword(issue, "governance-gap")
    assert not report_feature_status.issue_matches_keyword(issue, "qa_validate_issue_links")


def test_find_relevant_issues_prefers_explicit_open_issue_ids(tmp_path: Path) -> None:
    issue_path_9 = tmp_path / "docs" / "issues" / "ISSUE-0009-knowing-gap.md"
    issue_path_9.parent.mkdir(parents=True)
    issue_path_9.write_text("placeholder", encoding="utf-8")
    issue_path_10 = tmp_path / "docs" / "issues" / "ISSUE-0010-unknowing-gap.md"
    issue_path_10.write_text("placeholder", encoding="utf-8")

    issue_9 = report_feature_status.OpenIssue(
        issue_id="ISSUE-0009",
        title="Knowing grounded answers remain partial",
        status="open",
        path=issue_path_9,
        content="placeholder",
        content_lower="irrelevant",
    )
    issue_10 = report_feature_status.OpenIssue(
        issue_id="ISSUE-0010",
        title="Unknowing safe fallback remains partial",
        status="open",
        path=issue_path_10,
        content="placeholder",
        content_lower="irrelevant",
    )

    capability = {
        "open_issues": [" ISSUE-0010 "],
        "issue_keywords": ["ISSUE-0009", "knowing"],
    }

    relevant = report_feature_status.find_relevant_issues(capability, [issue_9, issue_10])
    assert [issue.issue_id for issue in relevant] == ["ISSUE-0010"]


def test_find_relevant_issues_falls_back_to_keywords_without_fan_in(tmp_path: Path) -> None:
    issue_path_9 = tmp_path / "docs" / "issues" / "ISSUE-0009-knowing-gap.md"
    issue_path_9.parent.mkdir(parents=True)
    issue_path_9.write_text("placeholder", encoding="utf-8")
    issue_path_13 = tmp_path / "docs" / "issues" / "ISSUE-0013-canonical-pipeline.md"
    issue_path_13.write_text("placeholder", encoding="utf-8")

    issue_9 = report_feature_status.OpenIssue(
        issue_id="ISSUE-0009",
        title="Knowing grounded answers remain partial",
        status="open",
        path=issue_path_9,
        content="placeholder",
        content_lower="mentions canonical pipeline foundation",
    )
    issue_13 = report_feature_status.OpenIssue(
        issue_id="ISSUE-0013",
        title="Implement canonical turn pipeline as the primary program",
        status="open",
        path=issue_path_13,
        content="placeholder",
        content_lower="mentions canonical pipeline and many component slices",
    )

    capability = {
        "issue_keywords": ["ISSUE-0009", "knowing_grounded_answers"],
    }

    relevant = report_feature_status.find_relevant_issues(capability, [issue_9, issue_13])
    assert [issue.issue_id for issue in relevant] == ["ISSUE-0009"]


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
        content="placeholder",
        content_lower="open issue record body",
    )

    report_markdown, summary = report_feature_status.build_report(
        contract=contract,
        gate_payload={},
        gate_results={},
        open_issues=[issue],
        roadmap_priorities={"P5": ["docs/roadmap/current-status-and-next-5-priorities.md"]},
        scenario_traces=[],
        generated_at_utc="2026-03-06T00:00:00Z",
        input_paths={
            "contract_path": "docs/qa/feature-status.yaml",
            "gate_summary_path": "artifacts/all-green-gate-summary.json",
            "issues_dir": "docs/issues",
            "roadmap_dir": "docs/roadmap",
            "features_dir": "features",
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
                "features_dir": Path("features"),
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
        gate_payload={},
        gate_results={},
        open_issues=[],
        roadmap_priorities={},
        scenario_traces=[],
        generated_at_utc="2026-03-07T00:00:00Z",
        input_paths={
            "contract_path": "docs/qa/feature-status.yaml",
            "gate_summary_path": "artifacts/all-green-gate-summary.json",
            "issues_dir": "docs/issues",
            "roadmap_dir": "docs/roadmap",
            "features_dir": "features",
        },
        source_file_metadata={"contract": None, "gate_summary": None, "open_issues": []},
        gate_stale_warning=(
            "Gate summary appears older than one or more source files "
            "(contract, open issue records, or roadmap files); regenerate gate evidence for freshest status. "
            "Hint: run `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json` "
            "to refresh `artifacts/all-green-gate-summary.json`."
        ),
    )

    assert "Hint: run `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json`" in report_markdown
    assert summary["warnings"]


def test_main_marks_gate_stale_when_roadmap_newer(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    contract_path = repo_root / "docs" / "qa" / "feature-status.yaml"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text("capabilities: []\n", encoding="utf-8")

    gate_summary_path = repo_root / "artifacts" / "all-green-gate-summary.json"
    gate_summary_path.parent.mkdir(parents=True)
    gate_summary_path.write_text('{"checks": []}\n', encoding="utf-8")

    issues_dir = repo_root / "docs" / "issues"
    issues_dir.mkdir(parents=True)

    roadmap_path = repo_root / "docs" / "roadmap" / "current.md"
    roadmap_path.parent.mkdir(parents=True)
    roadmap_path.write_text("P1 ship quickly\n", encoding="utf-8")

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
                "features_dir": Path("features"),
                "output": None,
                "json_output": Path("artifacts/feature-status-summary.json"),
            },
        )(),
    )

    old = 1_700_000_000
    new = old + 100
    import os

    os.utime(gate_summary_path, (old, old))
    os.utime(contract_path, (old, old))
    os.utime(roadmap_path, (new, new))

    assert report_feature_status.main() == 0

    summary_payload = json.loads(output_summary.read_text(encoding="utf-8"))
    assert summary_payload["warnings"]
    assert "roadmap files" in summary_payload["warnings"][0]
    assert summary_payload["source_file_metadata"]["roadmap_files"] == [
        report_feature_status.file_metadata(roadmap_path)
    ]


def test_parse_issue_acceptance_criteria_extracts_id_status_and_evidence(tmp_path: Path) -> None:
    issue_path = tmp_path / "docs" / "issues" / "ISSUE-0013.md"
    issue_path.parent.mkdir(parents=True)
    content = """
# ISSUE-0013
- **ID:** ISSUE-0013
- **Title:** Canonical pipeline
- **Status:** open

## Acceptance Criteria
- [ ] [AC-0013-01] First criterion
  - evidence: `docs/architecture/canonical-turn-pipeline.md`
- [~] [AC-0013-02] Second criterion
  - evidence: `src/testbot/stabilization.py`
- [x] [AC-0013-03] Third criterion
""".strip()
    issue_path.write_text(content + "\n", encoding="utf-8")

    issue = report_feature_status.OpenIssue(
        issue_id="ISSUE-0013",
        title="Canonical pipeline",
        status="open",
        path=issue_path,
        content=content,
        content_lower=content.lower(),
    )

    criteria = report_feature_status.parse_issue_acceptance_criteria(issue)
    assert [criterion.criterion_id for criterion in criteria] == [
        "AC-0013-01",
        "AC-0013-02",
        "AC-0013-03",
    ]
    assert [criterion.status for criterion in criteria] == ["pending", "partial", "complete"]
    assert criteria[0].evidence_refs == ["docs/architecture/canonical-turn-pipeline.md"]
    assert criteria[1].evidence_refs == ["src/testbot/stabilization.py"]
    assert criteria[2].evidence_refs == []


def test_build_report_includes_unresolved_criteria_in_markdown_and_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(report_feature_status, "REPO_ROOT", tmp_path)

    issue_path = tmp_path / "docs" / "issues" / "ISSUE-0013-canonical.md"
    issue_path.parent.mkdir(parents=True)
    issue_content = """
# ISSUE-0013
- **ID:** ISSUE-0013
- **Title:** Canonical pipeline
- **Status:** open

## Acceptance Criteria
- [x] [AC-0013-01] Complete criterion
- [~] [AC-0013-02] Partial criterion
  - evidence: `tests/test_runtime_logging_events.py`
""".strip()
    issue_path.write_text(issue_content + "\n", encoding="utf-8")

    issue = report_feature_status.OpenIssue(
        issue_id="ISSUE-0013",
        title="Canonical pipeline",
        status="open",
        path=issue_path,
        content=issue_content,
        content_lower=issue_content.lower(),
    )
    contract = {
        "capabilities": [
            {
                "capability_id": "canonical_turn_pipeline_foundation",
                "capability_name": "Canonical turn pipeline foundation",
                "current_status": "partial",
                "open_issues": ["ISSUE-0013"],
                "criterion_refs": ["AC-0013-01", "AC-0013-02", "AC-0013-03"],
            }
        ]
    }

    report_markdown, summary = report_feature_status.build_report(
        contract=contract,
        gate_payload={},
        gate_results={},
        open_issues=[issue],
        roadmap_priorities={},
        scenario_traces=[],
        generated_at_utc="2026-03-08T00:00:00Z",
        input_paths={
            "contract_path": "docs/qa/feature-status.yaml",
            "gate_summary_path": "artifacts/all-green-gate-summary.json",
            "issues_dir": "docs/issues",
            "roadmap_dir": "docs/roadmap",
            "features_dir": "features",
        },
        source_file_metadata={"contract": None, "gate_summary": None, "open_issues": []},
        gate_stale_warning=None,
    )

    assert "unresolved criteria: AC-0013-02, AC-0013-03" in report_markdown
    capability = summary["capabilities"][0]
    assert capability["unresolved_criteria"] == ["AC-0013-02", "AC-0013-03"]
    assert capability["criterion_status_breakdown"] == {
        "pending": 0,
        "partial": 1,
        "complete": 1,
        "unknown": 1,
    }


def test_build_report_handles_missing_criterion_markup_gracefully(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(report_feature_status, "REPO_ROOT", tmp_path)

    issue_path = tmp_path / "docs" / "issues" / "ISSUE-0013-canonical.md"
    issue_path.parent.mkdir(parents=True)
    issue_content = """
# ISSUE-0013
- **ID:** ISSUE-0013
- **Title:** Canonical pipeline
- **Status:** open
""".strip()
    issue_path.write_text(issue_content + "\n", encoding="utf-8")

    issue = report_feature_status.OpenIssue(
        issue_id="ISSUE-0013",
        title="Canonical pipeline",
        status="open",
        path=issue_path,
        content=issue_content,
        content_lower=issue_content.lower(),
    )
    contract = {
        "capabilities": [
            {
                "capability_id": "canonical_turn_pipeline_foundation",
                "capability_name": "Canonical turn pipeline foundation",
                "current_status": "partial",
                "open_issues": ["ISSUE-0013"],
                "criterion_refs": ["AC-0013-01"],
            }
        ]
    }

    report_markdown, summary = report_feature_status.build_report(
        contract=contract,
        gate_payload={},
        gate_results={},
        open_issues=[issue],
        roadmap_priorities={},
        scenario_traces=[],
        generated_at_utc="2026-03-08T00:00:00Z",
        input_paths={
            "contract_path": "docs/qa/feature-status.yaml",
            "gate_summary_path": "artifacts/all-green-gate-summary.json",
            "issues_dir": "docs/issues",
            "roadmap_dir": "docs/roadmap",
            "features_dir": "features",
        },
        source_file_metadata={"contract": None, "gate_summary": None, "open_issues": []},
        gate_stale_warning=None,
    )

    capability = summary["capabilities"][0]
    assert capability["criterion_obligations"] == [
        {
            "criterion_id": "AC-0013-01",
            "issue_id": None,
            "status": "unknown",
            "evidence_refs": [],
        }
    ]
    assert capability["unresolved_criteria"] == ["AC-0013-01"]
    assert "unresolved criteria: AC-0013-01" in report_markdown


def test_collect_feature_scenario_traceability_extracts_issue_and_ac_tags(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(report_feature_status, "REPO_ROOT", tmp_path)

    features_dir = tmp_path / "features"
    features_dir.mkdir(parents=True)
    feature_path = features_dir / "traceability.feature"
    feature_path.write_text(
        """
@Rule:Example
Feature: Traceability parsing

  @ISSUE-1234 @AC-1234-01
  Scenario: tagged scenario
    Given setup

  @Rule:Other
  Scenario: missing trace tags
    Given setup
""".strip()
        + "\n",
        encoding="utf-8",
    )

    traces = report_feature_status.collect_feature_scenario_traceability(features_dir)
    assert len(traces) == 2
    assert traces[0].scenario_name == "tagged scenario"
    assert traces[0].issue_tags == ["@ISSUE-1234"]
    assert traces[0].ac_tags == ["@AC-1234-01"]
    assert traces[1].scenario_name == "missing trace tags"
    assert traces[1].issue_tags == []
    assert traces[1].ac_tags == []


def test_build_report_surfaces_unmapped_scenarios_for_missing_issue_ac_tags(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(report_feature_status, "REPO_ROOT", tmp_path)

    contract = {
        "capabilities": [
            {
                "capability_id": "intent_grounding_router",
                "capability_name": "Deterministic intent grounding and route selection",
                "current_status": "implemented",
                "acceptance_tests": ["features/testbot/intent_grounding.feature"],
            }
        ]
    }

    scenario_traces = [
        report_feature_status.FeatureScenarioTrace(
            feature_path="features/testbot/intent_grounding.feature",
            scenario_name="tagged",
            issue_tags=["@ISSUE-0008"],
            ac_tags=["@AC-0008-01"],
        ),
        report_feature_status.FeatureScenarioTrace(
            feature_path="features/testbot/intent_grounding.feature",
            scenario_name="untagged",
            issue_tags=[],
            ac_tags=[],
        ),
    ]

    report_markdown, summary = report_feature_status.build_report(
        contract=contract,
        gate_payload={},
        gate_results={},
        open_issues=[],
        roadmap_priorities={},
        scenario_traces=scenario_traces,
        generated_at_utc="2026-03-08T00:00:00Z",
        input_paths={
            "contract_path": "docs/qa/feature-status.yaml",
            "gate_summary_path": "artifacts/all-green-gate-summary.json",
            "issues_dir": "docs/issues",
            "roadmap_dir": "docs/roadmap",
            "features_dir": "features",
        },
        source_file_metadata={"contract": None, "gate_summary": None, "open_issues": []},
        gate_stale_warning=None,
    )

    assert "unmapped scenarios: 1" in report_markdown
    assert summary["warnings"]
    assert len(summary["unmapped_scenarios"]) == 1
    assert summary["unmapped_scenarios"][0]["scenario_name"] == "untagged"
    capability = summary["capabilities"][0]
    assert len(capability["unmapped_scenarios"]) == 1
