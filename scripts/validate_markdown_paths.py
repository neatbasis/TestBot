#!/usr/bin/env python3
"""Validate local file/path references used in markdown files."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_FEATURE_STATUS_PATH = REPO_ROOT / "docs" / "qa" / "feature-status.yaml"
LEGACY_FEATURE_STATUS_PATH = REPO_ROOT / "docs" / "qa" / "feature-status.yml"

# Matches markdown links like [text](path/to/file.md)
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def iter_markdown_files() -> list[Path]:
    return sorted(REPO_ROOT.rglob("*.md"))


def normalize_target(raw_target: str) -> str:
    target = raw_target.strip()

    # Strip optional title from markdown link target: (path "title")
    if ' "' in target:
        target = target.split(' "', 1)[0].strip()

    # Drop anchors and query strings.
    target = target.split("#", 1)[0].split("?", 1)[0].strip()
    return target


def is_local_path(target: str) -> bool:
    if not target:
        return False

    lowered = target.lower()
    disallowed_prefixes = ("http://", "https://", "mailto:", "tel:")
    if lowered.startswith(disallowed_prefixes):
        return False

    return True


def validate_links() -> int:
    failures: list[str] = []

    if CANONICAL_FEATURE_STATUS_PATH.exists() and LEGACY_FEATURE_STATUS_PATH.exists():
        failures.append(
            "Canonical/legacy feature status files must not coexist: "
            "docs/qa/feature-status.yaml and docs/qa/feature-status.yml"
        )

    for md_file in iter_markdown_files():
        text = md_file.read_text(encoding="utf-8")
        for match in LINK_PATTERN.finditer(text):
            target = normalize_target(match.group(1))
            if not is_local_path(target):
                continue

            target_path = Path(target)
            resolved = (REPO_ROOT / target_path).resolve() if target_path.is_absolute() else (md_file.parent / target_path).resolve()

            try:
                resolved.relative_to(REPO_ROOT)
            except ValueError:
                failures.append(f"{md_file.relative_to(REPO_ROOT)}: path escapes repo: {target}")
                continue

            if not resolved.exists():
                failures.append(f"{md_file.relative_to(REPO_ROOT)}: missing path: {target}")

    if failures:
        print("Found markdown path validation errors:")
        for issue in failures:
            print(f"- {issue}")
        return 1

    print("All markdown local file/path references look valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate_links())
