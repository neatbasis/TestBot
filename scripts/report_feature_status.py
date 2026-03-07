#!/usr/bin/env python3
"""Build a concise implemented/partial/missing feature status report.

Combines:
- feature contract metadata (docs/qa/feature-status.yaml)
- gate evidence (artifacts/all-green-gate-summary.json)
- open issue evidence (docs/issues/*.md)
- roadmap priorities (docs/roadmap/*.md)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class OpenIssue:
    issue_id: str
    title: str
    status: str
    path: Path
    content_lower: str


def issue_matches_keyword(issue: OpenIssue, keyword: str) -> bool:
    normalized = keyword.strip().lower()
    if not normalized:
        return False
    searchable_fields = (
        issue.issue_id.lower(),
        issue.title.lower(),
        issue.path.stem.lower(),
        issue.content_lower,
    )
    return any(normalized in field for field in searchable_fields)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/qa/feature-status.yaml"),
        help="Path to feature status contract YAML.",
    )
    parser.add_argument(
        "--gate-summary",
        type=Path,
        default=Path("artifacts/all-green-gate-summary.json"),
        help="Path to all-green gate JSON summary.",
    )
    parser.add_argument(
        "--issues-dir",
        type=Path,
        default=Path("docs/issues"),
        help="Directory containing issue markdown records.",
    )
    parser.add_argument(
        "--roadmap-dir",
        type=Path,
        default=Path("docs/roadmap"),
        help="Directory containing roadmap markdown docs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output markdown report path. If omitted, prints only.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional JSON summary output path.",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_gate_results(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    checks = payload.get("checks", [])
    results: dict[str, str] = {}
    for check in checks:
        name = str(check.get("name", "")).strip()
        status = str(check.get("status", "unknown")).strip() or "unknown"
        if name:
            results[name] = status
    return results


def collect_open_issues(issues_dir: Path) -> list[OpenIssue]:
    open_issues: list[OpenIssue] = []
    for issue_path in sorted(issues_dir.glob("ISSUE-*.md")):
        content = issue_path.read_text(encoding="utf-8")
        status_match = re.search(r"^- \*\*Status:\*\*\s*([^\n]+)", content, flags=re.MULTILINE)
        issue_id_match = re.search(r"^- \*\*ID:\*\*\s*([^\n]+)", content, flags=re.MULTILINE)
        title_match = re.search(r"^- \*\*Title:\*\*\s*([^\n]+)", content, flags=re.MULTILINE)

        status = status_match.group(1).strip().lower() if status_match else "unknown"
        if status not in {"open", "in_progress", "todo", "triaged"}:
            continue

        issue_id = issue_id_match.group(1).strip() if issue_id_match else issue_path.stem
        title = title_match.group(1).strip() if title_match else issue_path.stem
        open_issues.append(
            OpenIssue(
                issue_id=issue_id,
                title=title,
                status=status,
                path=issue_path,
                content_lower=content.lower(),
            )
        )
    return open_issues


def collect_roadmap_priorities(roadmap_dir: Path) -> dict[str, list[str]]:
    priorities: dict[str, list[str]] = {}
    for roadmap_path in sorted(roadmap_dir.glob("*.md")):
        for line in roadmap_path.read_text(encoding="utf-8").splitlines():
            for match in re.finditer(r"\b(P\d+)\b", line):
                priority = match.group(1)
                priorities.setdefault(priority, [])
                rel = roadmap_path.relative_to(REPO_ROOT).as_posix()
                if rel not in priorities[priority]:
                    priorities[priority].append(rel)
    return priorities


def iso_utc_from_epoch(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def file_metadata(path: Path) -> dict[str, Any]:
    stat = path.stat()
    content = path.read_bytes()
    return {
        "path": path.relative_to(REPO_ROOT).as_posix(),
        "size_bytes": stat.st_size,
        "mtime_utc": iso_utc_from_epoch(stat.st_mtime),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def latest_issue_mtime(issues: list[OpenIssue]) -> float | None:
    if not issues:
        return None
    return max(issue.path.stat().st_mtime for issue in issues)


def effective_status(base_status: str, gate_failed: bool, has_open_issues: bool) -> str:
    normalized = base_status.strip().lower()
    if normalized == "planned":
        return "missing"
    if normalized == "partial":
        return "partial"
    if gate_failed or has_open_issues:
        return "partial"
    return "implemented"


def build_report(
    contract: dict[str, Any],
    gate_results: dict[str, str],
    open_issues: list[OpenIssue],
    roadmap_priorities: dict[str, list[str]],
    generated_at_utc: str,
    input_paths: dict[str, str],
    source_file_metadata: dict[str, Any],
    gate_stale_warning: str | None,
) -> tuple[str, dict[str, Any]]:
    capabilities = contract.get("capabilities", [])

    rows: list[dict[str, Any]] = []
    counts = {"implemented": 0, "partial": 0, "missing": 0}

    for capability in capabilities:
        cap_id = capability["capability_id"]
        cap_name = capability["capability_name"]
        base_status = capability.get("current_status", "planned")

        gate_checks = capability.get("gate_checks", [])
        failed_checks = [name for name in gate_checks if gate_results.get(name) == "failed"]

        keywords = [kw.lower() for kw in capability.get("issue_keywords", [])]
        relevant_issues = []
        if keywords:
            for issue in open_issues:
                if any(issue_matches_keyword(issue, kw) for kw in keywords):
                    relevant_issues.append(issue)

        priority_refs = capability.get("roadmap_priority_refs", [])
        priority_sources: dict[str, list[str]] = {
            ref: roadmap_priorities.get(ref, []) for ref in priority_refs
        }

        status = effective_status(
            base_status=base_status,
            gate_failed=bool(failed_checks),
            has_open_issues=bool(relevant_issues),
        )
        counts[status] += 1

        rows.append(
            {
                "capability_id": cap_id,
                "capability_name": cap_name,
                "owner_module": capability.get("owner_module"),
                "effective_status": status,
                "declared_status": base_status,
                "failed_gate_checks": failed_checks,
                "relevant_open_issues": [
                    {
                        "id": issue.issue_id,
                        "title": issue.title,
                        "path": issue.path.relative_to(REPO_ROOT).as_posix(),
                    }
                    for issue in relevant_issues
                ],
                "roadmap_priority_refs": priority_refs,
                "roadmap_priority_sources": priority_sources,
                "acceptance_tests": capability.get("acceptance_tests", []),
                "runtime_dependency_flags": capability.get("runtime_dependency_flags", []),
            }
        )

    lines = [
        "# Feature Status Report",
        "",
        f"Generated at (UTC): `{generated_at_utc}`",
        (
            "Inputs: "
            f"contract=`{input_paths['contract_path']}`, "
            f"gate_summary=`{input_paths['gate_summary_path']}`, "
            f"issues_dir=`{input_paths['issues_dir']}`, "
            f"roadmap_dir=`{input_paths['roadmap_dir']}`"
        ),
        "",
        f"Implemented: **{counts['implemented']}** | Partial: **{counts['partial']}** | Missing: **{counts['missing']}**",
        "",
        "| Capability | Status | Evidence signals |",
        "| --- | --- | --- |",
    ]

    if gate_stale_warning:
        lines.extend([f"> ⚠️ {gate_stale_warning}", ""])

    for row in rows:
        evidence_bits = []
        if row["failed_gate_checks"]:
            evidence_bits.append("failed checks: " + ", ".join(row["failed_gate_checks"]))
        if row["relevant_open_issues"]:
            evidence_bits.append(
                "open issues: "
                + ", ".join(f"{it['id']}" for it in row["relevant_open_issues"])
            )
        if row["roadmap_priority_refs"]:
            evidence_bits.append("roadmap: " + ", ".join(row["roadmap_priority_refs"]))
        if not evidence_bits:
            evidence_bits.append("no blocking signals from current inputs")

        lines.append(
            f"| {row['capability_name']} | {row['effective_status']} "
            f"(declared: {row['declared_status']}) | {'; '.join(evidence_bits)} |"
        )

    lines.append("")
    lines.append(
        "Generated by `python scripts/report_feature_status.py`. "
        f"Generated at (UTC): `{generated_at_utc}`."
    )
    lines.append(
        "Inputs: "
        f"contract=`{input_paths['contract_path']}`, "
        f"gate_summary=`{input_paths['gate_summary_path']}`, "
        f"issues_dir=`{input_paths['issues_dir']}`, "
        f"roadmap_dir=`{input_paths['roadmap_dir']}`"
    )

    summary_payload = {
        "generated_at_utc": generated_at_utc,
        "inputs": input_paths,
        "source_file_metadata": source_file_metadata,
        "warnings": [gate_stale_warning] if gate_stale_warning else [],
        "summary": counts,
        "capabilities": rows,
        "open_issue_count": len(open_issues),
        "gate_checks_seen": len(gate_results),
    }

    return "\n".join(lines) + "\n", summary_payload


def main() -> int:
    args = parse_args()

    contract_path = args.contract if args.contract.is_absolute() else REPO_ROOT / args.contract
    gate_path = args.gate_summary if args.gate_summary.is_absolute() else REPO_ROOT / args.gate_summary
    issues_dir = args.issues_dir if args.issues_dir.is_absolute() else REPO_ROOT / args.issues_dir
    roadmap_dir = args.roadmap_dir if args.roadmap_dir.is_absolute() else REPO_ROOT / args.roadmap_dir

    contract = load_yaml(contract_path)
    gate_results = load_gate_results(gate_path)
    open_issues = collect_open_issues(issues_dir)
    roadmap_priorities = collect_roadmap_priorities(roadmap_dir)

    generated_at_utc = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    input_paths = {
        "contract_path": contract_path.relative_to(REPO_ROOT).as_posix(),
        "gate_summary_path": gate_path.relative_to(REPO_ROOT).as_posix(),
        "issues_dir": issues_dir.relative_to(REPO_ROOT).as_posix(),
        "roadmap_dir": roadmap_dir.relative_to(REPO_ROOT).as_posix(),
    }
    source_file_metadata: dict[str, Any] = {
        "contract": file_metadata(contract_path),
        "gate_summary": file_metadata(gate_path) if gate_path.exists() else None,
        "open_issues": [file_metadata(issue.path) for issue in open_issues],
    }

    gate_stale_warning: str | None = None
    if gate_path.exists():
        gate_mtime = gate_path.stat().st_mtime
        contract_mtime = contract_path.stat().st_mtime
        latest_issue = latest_issue_mtime(open_issues)
        stale_against_contract = gate_mtime < contract_mtime
        stale_against_issues = latest_issue is not None and gate_mtime < latest_issue
        if stale_against_contract or stale_against_issues:
            gate_stale_warning = (
                "Gate summary appears older than one or more source files "
                "(contract or open issue records); regenerate gate evidence for freshest status. "
                "Hint: run `python scripts/all_green_gate.py --continue-on-failure --json-output artifacts/all-green-gate-summary.json` "
                "to refresh `artifacts/all-green-gate-summary.json`."
            )

    report_text, summary_payload = build_report(
        contract=contract,
        gate_results=gate_results,
        open_issues=open_issues,
        roadmap_priorities=roadmap_priorities,
        generated_at_utc=generated_at_utc,
        input_paths=input_paths,
        source_file_metadata=source_file_metadata,
        gate_stale_warning=gate_stale_warning,
    )

    print(report_text)

    if args.output:
        out_path = args.output if args.output.is_absolute() else REPO_ROOT / args.output
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report_text, encoding="utf-8")

    if args.json_output:
        json_path = args.json_output if args.json_output.is_absolute() else REPO_ROOT / args.json_output
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(summary_payload, indent=2) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
