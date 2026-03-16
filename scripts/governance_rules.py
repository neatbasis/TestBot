"""Shared governance primitives for issue validators."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Final

ISSUE_ID_REGEX: Final[str] = r"\bISSUE-(\d{4})\b"
ISSUE_ID_PATTERN: Final[re.Pattern[str]] = re.compile(ISSUE_ID_REGEX, re.IGNORECASE)
SECTION_NUMBER_LINE: Final[re.Pattern[str]] = re.compile(r"^\s*\d+\.\s+`([^`]+)`")
NON_TRIVIAL_WORD_PATTERN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9_-]+")
MISSING_REQUESTED_BASE_REF_NOTE: Final[str] = (
    "Base ref '{ref}' does not exist. Provide a valid --base-ref (for example origin/main, HEAD~1, or HEAD)."
)
ORIGIN_MAIN_FALLBACK_NOTE: Final[str] = (
    "Base ref 'origin/main' is unavailable; falling back to '{fallback}'.\n"
    "       This is expected in Codex task containers or shallow CI clones.\n"
    "       Governance diff checks are running against a reduced baseline.\n"
    "       For authoritative results, run locally with 'git fetch origin main' first. "
    "(Unless you are ChatGPT/Codex!)"
)
NO_USABLE_BASE_REF_NOTE: Final[str] = (
    "Could not resolve base ref 'origin/main' or fallbacks (HEAD~1, HEAD). "
    "Governance diff checks will run against a reduced baseline and all issue files may be validated."
)

# Explicit ownership map for governance rule families used by validators.
RULE_FAMILY_OWNERSHIP: Final[dict[str, dict[str, Any]]] = {
    "canonical_section_presence": {
        "owner": "Issue Governance Maintainers",
        "description": "Issue documents must include all required canonical sections/fields.",
        "consumers": ["scripts/validate_issues.py", "scripts/validate_issue_links.py"],
    },
    "metadata_issue_reference": {
        "owner": "Issue Governance Maintainers",
        "description": "Non-trivial PR/commit metadata must include ISSUE-XXXX linkage.",
        "consumers": ["scripts/validate_issues.py", "scripts/validate_issue_links.py"],
    },
}


def is_non_trivial_change(text: str) -> bool:
    """Return True when metadata text is substantial and not explicitly marked trivial."""
    stripped = text.strip()
    if not stripped:
        return False
    lowered = stripped.lower()
    if "#trivial" in lowered or "[trivial]" in lowered:
        return False
    return len(NON_TRIVIAL_WORD_PATTERN.findall(stripped)) >= 12


def extract_issue_ids(text: str) -> set[str]:
    """Extract normalized ISSUE-XXXX identifiers from text."""
    return {f"ISSUE-{digits}" for digits in ISSUE_ID_PATTERN.findall(text)}


def has_issue_reference(text: str) -> bool:
    """Return True if text includes any ISSUE-XXXX identifier."""
    return bool(extract_issue_ids(text))


def is_valid_issue_id(issue_id: str) -> bool:
    """Return True only for exact ISSUE-XXXX tokens."""
    match = ISSUE_ID_PATTERN.fullmatch(issue_id.strip())
    return bool(match)


def parse_canonical_sections(policy_text: str) -> list[str]:
    """Parse the canonical issue section list from docs/issues.md text."""
    sections: list[str] = []
    capture = False
    for line in policy_text.splitlines():
        lowered = line.strip().lower()
        if lowered.startswith("every issue file") and "must include" in lowered:
            capture = True
            continue
        if not capture:
            continue

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


def contains_canonical_section(issue_text: str, section_name: str) -> bool:
    """Return whether an issue text includes section content via heading or schema bullet label."""
    label = re.compile(rf"\*\*{re.escape(section_name)}:\*\*\s*.+", re.IGNORECASE)
    heading = re.compile(rf"^##\s+{re.escape(section_name)}\s*$", re.IGNORECASE | re.MULTILINE)
    return bool(label.search(issue_text) or heading.search(issue_text))


def missing_canonical_sections(issue_text: str, canonical_sections: list[str]) -> list[str]:
    """Return canonical sections missing from an issue text."""
    return [section for section in canonical_sections if not contains_canonical_section(issue_text, section)]


def metadata_missing_issue_reference(text: str) -> bool:
    """Return whether metadata is non-trivial yet missing ISSUE-XXXX linkage."""
    return is_non_trivial_change(text) and not has_issue_reference(text)


def git_ref_exists(ref: str, *, repo_root: Path) -> bool:
    """Return whether a Git ref exists in the given repository root."""
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def resolve_base_ref(
    base_ref: str,
    *,
    ref_exists: Callable[[str], bool],
) -> tuple[str | None, list[str]]:
    """Resolve base ref using canonical fallback order and canonical note wording."""
    notes: list[str] = []
    if ref_exists(base_ref):
        return base_ref, notes

    if base_ref != "origin/main":
        return None, [MISSING_REQUESTED_BASE_REF_NOTE.format(ref=base_ref)]

    for fallback in ("HEAD~1", "HEAD"):
        if ref_exists(fallback):
            notes.append(ORIGIN_MAIN_FALLBACK_NOTE.format(fallback=fallback))
            return fallback, notes

    notes.append(NO_USABLE_BASE_REF_NOTE)
    return None, notes
