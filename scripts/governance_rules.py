"""Shared governance primitives for issue validators."""

from __future__ import annotations

import re
from typing import Final

ISSUE_ID_REGEX: Final[str] = r"\bISSUE-(\d{4})\b"
ISSUE_ID_PATTERN: Final[re.Pattern[str]] = re.compile(ISSUE_ID_REGEX, re.IGNORECASE)
SECTION_NUMBER_LINE: Final[re.Pattern[str]] = re.compile(r"^\s*\d+\.\s+`([^`]+)`")
NON_TRIVIAL_WORD_PATTERN: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9_-]+")


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
