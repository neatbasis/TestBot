#!/usr/bin/env python3
"""Deterministic governance checks for issue linkage and issue record consistency."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from governance_rules import (
    has_issue_reference,
    is_non_trivial_change,
    is_valid_issue_id,
    parse_canonical_sections,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ISSUES_DIR = REPO_ROOT / "docs" / "issues"
ISSUES_POLICY = REPO_ROOT / "docs" / "issues.md"
RED_TAG_FILE = ISSUES_DIR / "RED_TAG.md"

FIELD_LINE_PATTERN = re.compile(r"^-\s+\*\*(.+?):\*\*\s*(.*)$")
RED_TAG_ITEM_PATTERN = re.compile(r"\b(ISSUE-\d{4})\b")

STATUS_OPENISH = {"open", "in_progress", "blocked"}
STATUS_CLOSEDISH = {"resolved", "closed"}
PLACEHOLDER_VALUES = {"", "tbd", "none", "unassigned", "n/a", "na", "-"}
REQUIRED_ENUMS: dict[str, set[str]] = {
    "Status": {"open", "in_progress", "blocked", "resolved", "closed"},
    "Severity": {"red", "amber", "green"},
}
REQUIRED_FIELD_VALUES = [
    "ID",
    "Title",
    "Status",
    "Severity",
    "Owner",
    "Created",
    "Target Sprint",
    "Principle Alignment",
]
REQUIRED_SECTION_BODIES = [
    "Problem Statement",
    "Evidence",
    "Impact",
    "Acceptance Criteria",
    "Work Plan",
    "Verification",
    "Closure Notes",
]

RULESET_STRICT = "strict"
RULESET_TRIAGE = "triage"


class ValidationFailure(NamedTuple):
    category: str
    message: str
    hint: str


def record_failure(failures: list[ValidationFailure], category: str, message: str, hint: str) -> None:
    failures.append(ValidationFailure(category=category, message=message, hint=hint))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pr-body-file",
        type=Path,
        help="Path to a file containing pull request description/body metadata.",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help=(
            "Git base ref used to inspect commit metadata (default: origin/main). "
            "If origin/main is unavailable (for example in shallow/detached environments), "
            "the validator automatically falls back to HEAD~1, then HEAD."
        ),
    )
    parser.add_argument(
        "--all-issue-files",
        action="store_true",
        help="Validate every issue file under docs/issues instead of only newly added files.",
    )
    parser.add_argument(
        "--ruleset",
        choices=[RULESET_STRICT, RULESET_TRIAGE],
        default=RULESET_STRICT,
        help="Validation profile: strict (default) or triage (lightweight checks).",
    )
    return parser.parse_args()


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or "git command failed"
        raise RuntimeError(stderr)
    return result.stdout


def git_ref_exists(ref: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def resolve_base_ref(base_ref: str) -> tuple[str | None, list[str]]:
    notes: list[str] = []
    if git_ref_exists(base_ref):
        return base_ref, notes

    if base_ref != "origin/main":
        return None, [
            (
                f"Base ref '{base_ref}' does not exist. "
                "Provide a valid --base-ref (for example origin/main, HEAD~1, or HEAD)."
            )
        ]

    for fallback in ("HEAD~1", "HEAD"):
        if git_ref_exists(fallback):
            notes.append(
                (
                    f"Base ref 'origin/main' is unavailable; falling back to '{fallback}'.\n"
                    "       This is expected in Codex task containers or shallow CI clones.\n"
                    "       Governance diff checks are running against a reduced baseline.\n"
                    "       For authoritative results, run locally with 'git fetch origin main' first. "
                    "(Unless you are ChatGPT/Codex!)"
                )
            )
            return fallback, notes

    notes.append(
        "Could not resolve base ref 'origin/main' or fallbacks (HEAD~1, HEAD). "
        "Commit-range checks will be skipped and all issue files will be validated."
    )
    return None, notes


def load_canonical_sections() -> list[str]:
    return parse_canonical_sections(ISSUES_POLICY.read_text(encoding="utf-8"))


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
    return is_non_trivial_change(text)


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


def parse_section_bodies(issue_text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    body_lines: list[str] = []

    for line in issue_text.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            if current is not None:
                sections[current] = "\n".join(body_lines).strip()
            current = heading.group(1).strip()
            body_lines = []
            continue

        if current is not None:
            body_lines.append(line)

    if current is not None:
        sections[current] = "\n".join(body_lines).strip()
    return sections


def contains_schema_section(issue_text: str, section_name: str) -> bool:
    label = re.compile(rf"^[-*]\s+\*\*{re.escape(section_name)}:\*\*\s*.+$", re.IGNORECASE | re.MULTILINE)
    heading = re.compile(rf"^##\s+{re.escape(section_name)}\s*$", re.IGNORECASE | re.MULTILINE)
    return bool(label.search(issue_text) or heading.search(issue_text))


def is_placeholder(value: str) -> bool:
    return value.strip().lower() in PLACEHOLDER_VALUES


def validate_pr_and_commit_metadata(pr_body_file: Path | None, base_ref: str, failures: list[ValidationFailure]) -> None:
    if pr_body_file:
        body_path = pr_body_file if pr_body_file.is_absolute() else REPO_ROOT / pr_body_file
        if not body_path.exists():
            record_failure(
                failures,
                "ISSUE_LINK",
                f"PR body file does not exist: {pr_body_file}",
                "Provide a valid --pr-body-file path or omit the flag when validating locally.",
            )
        else:
            body = body_path.read_text(encoding="utf-8")
            if is_non_trivial(body) and not has_issue_reference(body):
                record_failure(
                    failures,
                    "ISSUE_LINK",
                    "Non-trivial PR metadata must include at least one issue ID (ISSUE-XXXX).",
                    "Add an ISSUE-XXXX reference to the PR description (for example in Summary or Motivation).",
                )

    try:
        rev_lines = [line.strip() for line in run_git(["rev-list", "--parents", f"{base_ref}...HEAD"]).splitlines() if line.strip()]
    except RuntimeError as exc:
        record_failure(
            failures,
            "ISSUE_LINK",
            f"Could not inspect commits for issue links: {exc}",
            "Ensure the repository has the referenced base commit and rerun with a valid --base-ref.",
        )
        return

    commit_ids: list[str] = []
    for line in rev_lines:
        parts = line.split()
        commit_id = parts[0]
        if len(parts) - 1 > 1:
            continue
        commit_ids.append(commit_id)

    for commit_id in commit_ids:
        message = run_git(["show", "-s", "--format=%B", commit_id]).strip()
        if is_non_trivial(message) and not has_issue_reference(message):
            short = run_git(["show", "-s", "--format=%s", commit_id]).strip()
            record_failure(
                failures,
                "ISSUE_LINK",
                f"Commit {commit_id[:10]} has non-trivial metadata but no ISSUE-XXXX reference: {short!r}",
                "Amend the commit message to include an ISSUE-XXXX reference.",
            )


def validate_issue_schema(
    issue_files: list[Path], canonical_sections: list[str], failures: list[ValidationFailure], ruleset: str = RULESET_STRICT
) -> dict[str, dict[str, str]]:
    parsed: dict[str, dict[str, str]] = {}
    for issue_file in issue_files:
        rel = issue_file.relative_to(REPO_ROOT)
        text = issue_file.read_text(encoding="utf-8")
        fields = parse_issue_fields(text)
        sections = parse_section_bodies(text)
        parsed[issue_file.name] = fields

        missing_sections = [s for s in canonical_sections if not contains_schema_section(text, s)]
        if missing_sections:
            record_failure(
                failures,
                "SCHEMA",
                f"{rel}: missing canonical schema fields/sections: {', '.join(missing_sections)}",
                "Update the issue document to include every required section from docs/issues.md.",
            )

        issue_id = fields.get("ID", "")
        if issue_id and not is_valid_issue_id(issue_id):
            record_failure(
                failures,
                "SCHEMA",
                f"{rel}: ID field '{issue_id}' is not in ISSUE-XXXX format.",
                "Set **ID** to an ISSUE-XXXX identifier.",
            )

        if issue_id:
            expected_id = issue_file.name.split("-", maxsplit=2)
            expected_issue = "-".join(expected_id[:2]) if len(expected_id) >= 2 else ""
            if issue_id != expected_issue:
                record_failure(
                    failures,
                    "SCHEMA",
                    f"{rel}: ID field '{issue_id}' does not match filename issue id '{expected_issue}'.",
                    "Rename the file or fix the **ID** field so both use the same ISSUE-XXXX value.",
                )

        if ruleset == RULESET_TRIAGE:
            continue

        for field_name in REQUIRED_FIELD_VALUES:
            if is_placeholder(fields.get(field_name, "")):
                record_failure(
                    failures,
                    "SCHEMA",
                    f"{rel}: required canonical field '{field_name}' is missing or placeholder.",
                    f"Set **{field_name}** to a concrete non-placeholder value.",
                )

        for enum_field, allowed_values in REQUIRED_ENUMS.items():
            raw_value = fields.get(enum_field, "")
            normalized = raw_value.strip().lower()
            if normalized and normalized not in allowed_values:
                record_failure(
                    failures,
                    "SCHEMA",
                    f"{rel}: field '{enum_field}' has invalid value '{raw_value}'.",
                    f"Use one of: {', '.join(sorted(allowed_values))}.",
                )

        for section_name in REQUIRED_SECTION_BODIES:
            if is_placeholder(sections.get(section_name, "")):
                record_failure(
                    failures,
                    "SCHEMA",
                    f"{rel}: section '{section_name}' is empty or placeholder.",
                    f"Add concrete content under ## {section_name}.",
                )
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


def validate_red_severity_consistency(all_issue_files: list[Path], failures: list[ValidationFailure]) -> None:
    active_ids, resolved_ids = parse_red_tag_index()
    overlap = active_ids & resolved_ids
    if overlap:
        record_failure(
            failures,
            "RED_TAG",
            f"docs/issues/RED_TAG.md: issue(s) appear in both Active and Resolved: {', '.join(sorted(overlap))}",
            "Keep each ISSUE-XXXX in exactly one RED_TAG section that matches its lifecycle state.",
        )

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
            record_failure(
                failures,
                "RED_TAG",
                f"{rel}: red-severity issue must include non-empty ID field.",
                "Set the **ID** field to the issue identifier in ISSUE-XXXX format.",
            )
            continue

        if is_placeholder(owner):
            record_failure(
                failures,
                "RED_TAG",
                f"{rel}: red-severity issue must include a concrete Owner (not placeholder).",
                "Replace placeholder owner values with a responsible person/team.",
            )
        if is_placeholder(target_sprint):
            record_failure(
                failures,
                "RED_TAG",
                f"{rel}: red-severity issue must include a concrete Target Sprint (not placeholder).",
                "Set **Target Sprint** to a planned sprint/milestone instead of TBD/none.",
            )

        in_active = issue_id in active_ids
        in_resolved = issue_id in resolved_ids
        if not in_active and not in_resolved:
            record_failure(
                failures,
                "RED_TAG",
                f"{rel}: red-severity issue must be listed in docs/issues/RED_TAG.md.",
                "Add the ISSUE-XXXX entry to RED_TAG Active or Resolved, based on Status.",
            )

        if status in STATUS_OPENISH and not in_active:
            record_failure(
                failures,
                "RED_TAG",
                f"{rel}: status '{status}' requires membership in RED_TAG Active section.",
                "Move/add the ISSUE-XXXX entry under the Active section in docs/issues/RED_TAG.md.",
            )
        if status in STATUS_CLOSEDISH and not in_resolved:
            record_failure(
                failures,
                "RED_TAG",
                f"{rel}: status '{status}' requires membership in RED_TAG Resolved section.",
                "Move/add the ISSUE-XXXX entry under the Resolved section in docs/issues/RED_TAG.md.",
            )
        if status in STATUS_OPENISH and in_resolved:
            record_failure(
                failures,
                "RED_TAG",
                f"{rel}: status '{status}' is inconsistent with RED_TAG Resolved section.",
                "Change Status to resolved/closed or move the entry from Resolved to Active.",
            )
        if status in STATUS_CLOSEDISH and in_active:
            record_failure(
                failures,
                "RED_TAG",
                f"{rel}: status '{status}' is inconsistent with RED_TAG Active section.",
                "Change Status to open/in_progress/blocked or move the entry from Active to Resolved.",
            )


def main() -> int:
    args = parse_args()
    failures: list[ValidationFailure] = []
    effective_base_ref, resolution_notes = resolve_base_ref(args.base_ref)
    for note in resolution_notes:
        print(f"[WARN] {note}")

    if effective_base_ref:
        validate_pr_and_commit_metadata(args.pr_body_file, effective_base_ref, failures)
    else:
        print("[INFO] Skipping commit-range metadata inspection because no base ref could be resolved.")

    canonical_sections = load_canonical_sections()

    if args.all_issue_files:
        issue_files = list_all_issue_files()
    elif not effective_base_ref:
        issue_files = list_all_issue_files()
    else:
        try:
            issue_files = list_new_issue_files(effective_base_ref)
        except RuntimeError as exc:
            print(f"[WARN] Could not detect newly added issue files ({exc}); validating all issue files.")
            issue_files = list_all_issue_files()

    if issue_files:
        validate_issue_schema(issue_files, canonical_sections, failures, ruleset=args.ruleset)
    else:
        print("[INFO] No new issue files detected under docs/issues/.")

    # Red-tag governance is strict-only; triage mode keeps checks lightweight.
    if args.ruleset == RULESET_STRICT:
        validate_red_severity_consistency(list_all_issue_files(), failures)

    if failures:
        print("Governance validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- [{failure.category}] {failure.message}\n  Remediation: {failure.hint}", file=sys.stderr)
        return 1

    print("Governance validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
