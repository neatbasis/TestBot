#!/usr/bin/env python3
"""CI checks for issue governance and pull request metadata."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ISSUES_DIR = REPO_ROOT / "docs" / "issues"
ISSUES_POLICY = REPO_ROOT / "docs" / "issues.md"
ISSUE_REF_PATTERN = re.compile(r"\bIssue:\s*ISSUE-\d{4}\b", re.IGNORECASE)
SECTION_NUMBER_LINE = re.compile(r"^\s*\d+\.\s+`([^`]+)`")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pr-body-file",
        type=Path,
        help="Path to a file containing pull request description/body.",
    )
    parser.add_argument(
        "--base-ref",
        default="HEAD~1",
        help="Git base ref used to detect newly added issue files.",
    )
    parser.add_argument(
        "--all-issue-files",
        action="store_true",
        help="Validate every issue file under docs/issues instead of only newly added files.",
    )
    return parser.parse_args()


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


def run_git_diff_for_added_files(base_ref: str) -> list[Path]:
    cmd = ["git", "diff", "--name-only", "--diff-filter=A", f"{base_ref}...HEAD", "--", "docs/issues/*.md"]
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff failed")

    paths: list[Path] = []
    for raw in result.stdout.splitlines():
        path = raw.strip()
        if not path:
            continue
        rel = Path(path)
        if rel.name == "RED_TAG.md":
            continue
        paths.append(REPO_ROOT / rel)
    return sorted(paths)


def list_all_issue_files() -> list[Path]:
    return sorted(path for path in ISSUES_DIR.glob("ISSUE-*.md") if path.is_file())


def is_non_trivial_pr(pr_body: str) -> bool:
    stripped = pr_body.strip()
    if not stripped:
        return False
    if "#trivial" in stripped.lower():
        return False
    words = re.findall(r"[A-Za-z0-9_-]+", stripped)
    return len(words) >= 15


def has_issue_reference(pr_body: str) -> bool:
    return bool(ISSUE_REF_PATTERN.search(pr_body))


def contains_section(text: str, section_name: str) -> bool:
    heading = re.compile(rf"^##\s+{re.escape(section_name)}\s*$", re.IGNORECASE | re.MULTILINE)
    label = re.compile(rf"\*\*{re.escape(section_name)}:\*\*", re.IGNORECASE)
    return bool(heading.search(text) or label.search(text))


def field_value(text: str, field_name: str) -> str:
    pattern = re.compile(rf"\*\*{re.escape(field_name)}:\*\*\s*(.+)")
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(1).strip()


def validate_pr_body(pr_body_file: Path | None, failures: list[str]) -> None:
    if not pr_body_file:
        print("[INFO] No --pr-body-file provided; skipping PR description validation.")
        return

    body_path = pr_body_file if pr_body_file.is_absolute() else REPO_ROOT / pr_body_file
    if not body_path.exists():
        failures.append(f"PR body file does not exist: {pr_body_file}")
        return

    body = body_path.read_text(encoding="utf-8")
    if is_non_trivial_pr(body) and not has_issue_reference(body):
        failures.append("Non-trivial PR description must include 'Issue: ISSUE-XXXX'.")


def validate_issue_files(issue_files: list[Path], canonical_sections: list[str], failures: list[str]) -> None:
    for issue_file in issue_files:
        text = issue_file.read_text(encoding="utf-8")
        rel = issue_file.relative_to(REPO_ROOT)

        missing = [section for section in canonical_sections if not contains_section(text, section)]
        if missing:
            failures.append(f"{rel}: missing canonical sections: {', '.join(missing)}")

        severity = field_value(text, "Severity").lower()
        if severity == "red":
            owner = field_value(text, "Owner")
            sprint = field_value(text, "Target Sprint")
            if not owner:
                failures.append(f"{rel}: red-tag issue must include a non-empty Owner.")
            if not sprint:
                failures.append(f"{rel}: red-tag issue must include a non-empty Target Sprint.")


def main() -> int:
    args = parse_args()
    failures: list[str] = []

    validate_pr_body(args.pr_body_file, failures)

    canonical_sections = load_canonical_sections()
    if args.all_issue_files:
        issue_files = list_all_issue_files()
    else:
        try:
            issue_files = run_git_diff_for_added_files(args.base_ref)
        except RuntimeError as exc:
            print(f"[WARN] Could not detect newly added issue files ({exc}); validating all issue files.")
            issue_files = list_all_issue_files()

    if issue_files:
        validate_issue_files(issue_files, canonical_sections, failures)
    else:
        print("[INFO] No new issue files detected under docs/issues/.")

    if failures:
        print("Issue validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Issue validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
