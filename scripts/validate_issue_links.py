#!/usr/bin/env python3
"""Deterministic governance checks for issue linkage and issue record consistency."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ISSUES_DIR = REPO_ROOT / "docs" / "issues"
ISSUES_POLICY = REPO_ROOT / "docs" / "issues.md"
RED_TAG_FILE = ISSUES_DIR / "RED_TAG.md"

ISSUE_ID_PATTERN = re.compile(r"\bISSUE-\d{4}\b")
FIELD_LINE_PATTERN = re.compile(r"^-\s+\*\*(.+?):\*\*\s*(.*)$")
SECTION_NUMBER_LINE = re.compile(r"^\s*\d+\.\s+`([^`]+)`")
RED_TAG_ITEM_PATTERN = re.compile(r"\b(ISSUE-\d{4})\b")

STATUS_OPENISH = {"open", "in_progress", "blocked"}
STATUS_CLOSEDISH = {"resolved", "closed"}
PLACEHOLDER_VALUES = {"", "tbd", "none", "unassigned", "n/a", "na", "-"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pr-body-file",
        type=Path,
        help="Path to a file containing pull request description/body metadata.",
    )
    parser.add_argument(
        "--base-ref",
        default="HEAD~1",
        help="Git base ref used to inspect commit metadata (default: HEAD~1).",
    )
    parser.add_argument(
        "--all-issue-files",
        action="store_true",
        help="Validate every issue file under docs/issues instead of only newly added files.",
    )
    return parser.parse_args()


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "git command failed"
        raise RuntimeError(stderr)
    return result.stdout


def load_canonical_sections() -> list[str]:
    text = ISSUES_POLICY.read_text(encoding="utf-8")
    sections: list[str] = []
    capture = False
    for line in text.splitlines():
        if line.strip().lower().startswith("every issue file must include"):
            capture = True
            continue
        if capture:
            if not line.strip():
                if sections:
                    break
                continue
            match = SECTION_NUMBER_LINE.match(line)
            if match:
                sections.append(match.group(1).strip())
            elif sections:
                break

    if not sections:
        raise RuntimeError("Could not parse canonical sections from docs/issues.md")
    return sections


def list_all_issue_files() -> list[Path]:
    return sorted(path for path in ISSUES_DIR.glob("ISSUE-*.md") if path.is_file())


def list_new_issue_files(base_ref: str) -> list[Path]:
    stdout = run_git(["diff", "--name-only", "--diff-filter=A", f"{base_ref}...HEAD", "--", "docs/issues/*.md"])
    files: list[Path] = []
    for line in stdout.splitlines():
        rel = Path(line.strip())
        if not line.strip() or rel.name == "RED_TAG.md":
            continue
        files.append(REPO_ROOT / rel)
    return sorted(files)


def is_non_trivial(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    lowered = stripped.lower()
    if "#trivial" in lowered or "[trivial]" in lowered:
        return False
    words = re.findall(r"[A-Za-z0-9_-]+", stripped)
    return len(words) >= 12


def parse_issue_fields(issue_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in issue_text.splitlines():
        match = FIELD_LINE_PATTERN.match(line.strip())
        if not match:
            continue
        key = match.group(1).strip()
        value = match.group(2).strip()
        fields[key] = value
    return fields


def contains_schema_section(issue_text: str, section_name: str) -> bool:
    label = re.compile(rf"^[-*]\s+\*\*{re.escape(section_name)}:\*\*\s*.+$", re.IGNORECASE | re.MULTILINE)
    heading = re.compile(rf"^##\s+{re.escape(section_name)}\s*$", re.IGNORECASE | re.MULTILINE)
    return bool(label.search(issue_text) or heading.search(issue_text))


def is_placeholder(value: str) -> bool:
    return value.strip().lower() in PLACEHOLDER_VALUES


def validate_pr_and_commit_metadata(pr_body_file: Path | None, base_ref: str, failures: list[str]) -> None:
    if pr_body_file:
        body_path = pr_body_file if pr_body_file.is_absolute() else REPO_ROOT / pr_body_file
        if not body_path.exists():
            failures.append(f"PR body file does not exist: {pr_body_file}")
        else:
            body = body_path.read_text(encoding="utf-8")
            if is_non_trivial(body) and not ISSUE_ID_PATTERN.search(body):
                failures.append("Non-trivial PR metadata must include at least one issue ID (ISSUE-XXXX).")

    try:
        rev_lines = [line.strip() for line in run_git(["rev-list", "--parents", f"{base_ref}...HEAD"]).splitlines() if line.strip()]
    except RuntimeError as exc:
        failures.append(f"Could not inspect commits for issue links: {exc}")
        return

    commit_ids: list[str] = []
    for line in rev_lines:
        parts = line.split()
        commit_id = parts[0]
        parent_count = len(parts) - 1
        if parent_count > 1:
            continue
        commit_ids.append(commit_id)

    for commit_id in commit_ids:
        message = run_git(["show", "-s", "--format=%B", commit_id]).strip()
        if is_non_trivial(message) and not ISSUE_ID_PATTERN.search(message):
            short = run_git(["show", "-s", "--format=%s", commit_id]).strip()
            failures.append(
                f"Commit {commit_id[:10]} has non-trivial metadata but no ISSUE-XXXX reference: {short!r}"
            )


def validate_issue_schema(issue_files: list[Path], canonical_sections: list[str], failures: list[str]) -> dict[str, dict[str, str]]:
    parsed: dict[str, dict[str, str]] = {}
    for issue_file in issue_files:
        rel = issue_file.relative_to(REPO_ROOT)
        text = issue_file.read_text(encoding="utf-8")
        fields = parse_issue_fields(text)
        parsed[issue_file.name] = fields

        missing_sections = [s for s in canonical_sections if not contains_schema_section(text, s)]
        if missing_sections:
            failures.append(f"{rel}: missing canonical schema fields/sections: {', '.join(missing_sections)}")

        if fields.get("ID"):
            expected_id = issue_file.name.split("-", maxsplit=2)
            expected_issue = "-".join(expected_id[:2]) if len(expected_id) >= 2 else ""
            if fields["ID"] != expected_issue:
                failures.append(f"{rel}: ID field '{fields['ID']}' does not match filename issue id '{expected_issue}'.")
    return parsed


def parse_red_tag_index() -> tuple[set[str], set[str]]:
    text = RED_TAG_FILE.read_text(encoding="utf-8")
    current_section = ""
    active: set[str] = set()
    resolved: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.lower().startswith("## "):
            current_section = line[3:].strip().lower()
            continue
        match = RED_TAG_ITEM_PATTERN.search(line)
        if not match:
            continue
        issue_id = match.group(1)
        if current_section == "active":
            active.add(issue_id)
        elif current_section == "resolved":
            resolved.add(issue_id)

    return active, resolved


def validate_red_severity_consistency(all_issue_files: list[Path], failures: list[str]) -> None:
    active_ids, resolved_ids = parse_red_tag_index()
    overlap = active_ids & resolved_ids
    if overlap:
        failures.append(f"docs/issues/RED_TAG.md: issue(s) appear in both Active and Resolved: {', '.join(sorted(overlap))}")

    for issue_file in all_issue_files:
        rel = issue_file.relative_to(REPO_ROOT)
        text = issue_file.read_text(encoding="utf-8")
        fields = parse_issue_fields(text)

        issue_id = fields.get("ID", "")
        severity = fields.get("Severity", "").strip().lower()
        status = fields.get("Status", "").strip().lower()
        owner = fields.get("Owner", "")
        target_sprint = fields.get("Target Sprint", "")

        if severity != "red":
            continue

        if not issue_id:
            failures.append(f"{rel}: red-severity issue must include non-empty ID field.")
            continue

        if is_placeholder(owner):
            failures.append(f"{rel}: red-severity issue must include a concrete Owner (not placeholder).")
        if is_placeholder(target_sprint):
            failures.append(f"{rel}: red-severity issue must include a concrete Target Sprint (not placeholder).")

        in_active = issue_id in active_ids
        in_resolved = issue_id in resolved_ids
        if not in_active and not in_resolved:
            failures.append(f"{rel}: red-severity issue must be listed in docs/issues/RED_TAG.md.")

        if status in STATUS_OPENISH and not in_active:
            failures.append(f"{rel}: status '{status}' requires membership in RED_TAG Active section.")
        if status in STATUS_CLOSEDISH and not in_resolved:
            failures.append(f"{rel}: status '{status}' requires membership in RED_TAG Resolved section.")
        if status in STATUS_OPENISH and in_resolved:
            failures.append(f"{rel}: status '{status}' is inconsistent with RED_TAG Resolved section.")
        if status in STATUS_CLOSEDISH and in_active:
            failures.append(f"{rel}: status '{status}' is inconsistent with RED_TAG Active section.")


def main() -> int:
    args = parse_args()
    failures: list[str] = []

    validate_pr_and_commit_metadata(args.pr_body_file, args.base_ref, failures)

    canonical_sections = load_canonical_sections()

    if args.all_issue_files:
        issue_files = list_all_issue_files()
    else:
        try:
            issue_files = list_new_issue_files(args.base_ref)
        except RuntimeError as exc:
            print(f"[WARN] Could not detect newly added issue files ({exc}); validating all issue files.")
            issue_files = list_all_issue_files()

    if issue_files:
        validate_issue_schema(issue_files, canonical_sections, failures)
    else:
        print("[INFO] No new issue files detected under docs/issues/.")

    # Red-tag governance must be checked against the full dataset for deterministic consistency.
    validate_red_severity_consistency(list_all_issue_files(), failures)

    if failures:
        print("Governance validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Governance validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
