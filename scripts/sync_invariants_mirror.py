#!/usr/bin/env python3
"""Sync the directive invariants mirror from canonical answer-policy invariants."""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

CANONICAL_PATH = Path("docs/invariants/answer-policy.md")
MIRROR_PATH = Path("docs/directives/invariants.md")
SYNC_BEGIN = "<!-- BEGIN_SYNCED_INVARIANTS_TABLE_AND_SCENARIO_MAP -->"
SYNC_END = "<!-- END_SYNCED_INVARIANTS_TABLE_AND_SCENARIO_MAP -->"


class SyncError(RuntimeError):
    """Raised when invariant sync markers are missing or malformed."""


def _extract_synced_block(text: str, *, path: Path) -> str:
    if SYNC_BEGIN not in text or SYNC_END not in text:
        raise SyncError(f"Missing sync markers in {path}")

    start = text.index(SYNC_BEGIN) + len(SYNC_BEGIN)
    end = text.index(SYNC_END)
    if end <= start:
        raise SyncError(f"Malformed sync marker ordering in {path}")

    block = text[start:end].strip("\n")
    if not block:
        raise SyncError(f"Synced block is empty in {path}")

    return block


def _render_mirror(mirror_text: str, synced_block: str, *, path: Path) -> str:
    if SYNC_BEGIN not in mirror_text or SYNC_END not in mirror_text:
        raise SyncError(f"Missing sync markers in {path}")

    prefix, remainder = mirror_text.split(SYNC_BEGIN, 1)
    _, suffix = remainder.split(SYNC_END, 1)
    return f"{prefix}{SYNC_BEGIN}\n\n{synced_block}\n\n{SYNC_END}{suffix}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate mirror content without writing changes.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    canonical_text = CANONICAL_PATH.read_text(encoding="utf-8")
    mirror_text = MIRROR_PATH.read_text(encoding="utf-8")
    synced_block = _extract_synced_block(canonical_text, path=CANONICAL_PATH)
    expected_mirror = _render_mirror(mirror_text, synced_block, path=MIRROR_PATH)

    if mirror_text == expected_mirror:
        print("Invariant mirror is synchronized.")
        return 0

    if args.check:
        print("Invariant mirror is out of sync.")
        diff = difflib.unified_diff(
            mirror_text.splitlines(),
            expected_mirror.splitlines(),
            fromfile=str(MIRROR_PATH),
            tofile=f"{MIRROR_PATH} (expected)",
            lineterm="",
        )
        for line in diff:
            print(line)
        return 1

    MIRROR_PATH.write_text(expected_mirror, encoding="utf-8")
    print(f"Updated {MIRROR_PATH} from canonical answer-policy source {CANONICAL_PATH}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SyncError as exc:
        print(f"Invariant mirror sync error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
