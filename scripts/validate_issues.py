#!/usr/bin/env python3
"""CI checks for issue governance and pull request metadata."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from governance_rules import (
    git_ref_exists as governance_git_ref_exists,
    has_issue_reference,
    is_non_trivial_change,
    metadata_missing_issue_reference,
    missing_canonical_sections,
    parse_canonical_sections,
    resolve_base_ref as governance_resolve_base_ref,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ISSUES_DIR = REPO_ROOT / "docs" / "issues"
ISSUES_POLICY = REPO_ROOT / "docs" / "issues.md"

RULESET_STRICT = "strict"
RULESET_TRIAGE = "triage"


TRIAGE_INTAKE_SECTIONS = ["ID", "Title", "Problem", "Owner", "Severity", "Next Action"]

ISSUE_STATE_TRIAGE_INTAKE = "triage_intake"
ISSUE_STATE_GOVERNED_EXECUTION = "governed_execution"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pr-body-file",
        type=Path,
        help="Path to a file containing pull request description/body.",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help=(
            "Git base ref used to detect newly added issue files (default: origin/main). "
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


def load_canonical_sections() -> list[str]:
    text = ISSUES_POLICY.read_text(encoding="utf-8")
    return parse_canonical_sections(text)


def resolve_safe_changed_path_base_ref(base_ref: str) -> tuple[str | None, list[str]]:
    """Resolve base refs for changed-path discovery with safe full-check fallback."""
    return governance_resolve_base_ref(
        base_ref,
        ref_exists=lambda ref: governance_git_ref_exists(ref, repo_root=REPO_ROOT),
    )


def resolve_base_ref(base_ref: str) -> tuple[str | None, list[str]]:
    """Backward-compatible alias for changed-path base-ref resolution."""
    return resolve_safe_changed_path_base_ref(base_ref)


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
    return is_non_trivial_change(pr_body)


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
    if metadata_missing_issue_reference(body):
        failures.append("Non-trivial PR description must include at least one ISSUE-XXXX reference.")


def validate_issue_files(issue_files: list[Path], canonical_sections: list[str], failures: list[str], ruleset: str) -> None:
    for issue_file in issue_files:
        text = issue_file.read_text(encoding="utf-8")
        rel = issue_file.relative_to(REPO_ROOT)

        issue_state = field_value(text, "Issue State").lower()
        status = field_value(text, "Status").lower()

        if issue_state == ISSUE_STATE_TRIAGE_INTAKE:
            missing = missing_canonical_sections(text, TRIAGE_INTAKE_SECTIONS)
            if missing:
                failures.append(f"{rel}: triage_intake missing required fields: {', '.join(missing)}")

            if status and status != "open":
                failures.append(
                    f"{rel}: triage_intake issues must remain Status 'open' and be promoted to governed_execution before '{status}'."
                )
            if not status:
                failures.append(
                    f"{rel}: triage_intake issues must declare Status 'open' to enforce promotion SLA before in_progress."
                )

        else:
            missing = missing_canonical_sections(text, canonical_sections)
            if missing:
                failures.append(f"{rel}: missing canonical sections: {', '.join(missing)}")

        if ruleset == RULESET_TRIAGE:
            continue

        severity = field_value(text, "Severity").lower()
        if severity == "red":
            owner = field_value(text, "Owner")
            sprint = field_value(text, "Target Sprint")
            if not owner:
                failures.append(f"{rel}: red-tag issue must include a non-empty Owner.")
            if issue_state != ISSUE_STATE_TRIAGE_INTAKE and not sprint:
                failures.append(f"{rel}: red-tag issue must include a non-empty Target Sprint.")


def main() -> int:
    args = parse_args()
    failures: list[str] = []

    validate_pr_body(args.pr_body_file, failures)

    effective_base_ref, resolution_notes = resolve_safe_changed_path_base_ref(args.base_ref)
    for note in resolution_notes:
        print(f"[WARN] {note}")

    canonical_sections = load_canonical_sections()
    if args.all_issue_files:
        issue_files = list_all_issue_files()
    else:
        if not effective_base_ref:
            issue_files = list_all_issue_files()
        else:
            try:
                issue_files = run_git_diff_for_added_files(effective_base_ref)
            except RuntimeError as exc:
                print(f"[WARN] Could not detect newly added issue files ({exc}); validating all issue files.")
                issue_files = list_all_issue_files()

    if issue_files:
        validate_issue_files(issue_files, canonical_sections, failures, ruleset=args.ruleset)
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
