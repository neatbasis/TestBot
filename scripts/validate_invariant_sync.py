#!/usr/bin/env python3
"""Validate that invariant docs stay synchronized."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    completed = subprocess.run(
        [sys.executable, "scripts/sync_invariants_mirror.py", "--check"],
        check=False,
    )
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
