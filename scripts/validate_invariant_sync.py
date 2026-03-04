#!/usr/bin/env python3
"""Validate that invariant docs stay synchronized.

Checks `docs/invariants.md` (canonical source-of-truth) against
`docs/directives/invariants.md` (directive mirror).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CANONICAL_PATH = Path("docs/invariants.md")
MIRROR_PATH = Path("docs/directives/invariants.md")

INV_ID_RE = re.compile(r"INV-\d+")
SCENARIO_RE = re.compile(
    r"-\s*`(?P<id>BDD-[A-Z]+-\d+)`\s*(?::|→)\s*`(?P<feature>[^`]+)`\s*"
    r"(?:→|->)\s*`Scenario:\s*(?P<scenario>[^`]+)`"
)


def _normalize(text: str) -> str:
    no_md = re.sub(r"[*_`]+", "", text)
    return " ".join(no_md.split()).strip()


def _split_table_row(line: str) -> list[str]:
    cols = [c.strip() for c in line.strip().strip("|").split("|")]
    return cols


def extract_invariants(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header: list[str] | None = None
    invariants: dict[str, str] = {}

    for line in lines:
        if not line.strip().startswith("|"):
            continue

        cols = _split_table_row(line)
        if not cols or len(cols) < 2:
            continue

        # Header row
        if "Invariant ID" in cols:
            header = cols
            continue

        # separator row
        if all(set(c) <= {"-", ":"} for c in cols):
            continue

        inv_id = next((c for c in cols if INV_ID_RE.fullmatch(c)), None)
        if not inv_id or header is None:
            continue

        statement_idx = None
        for i, name in enumerate(header):
            low = name.lower()
            if "statement" in low or "definition" in low:
                statement_idx = i
                break

        if statement_idx is None or statement_idx >= len(cols):
            raise ValueError(f"Could not find statement/definition column in table at {path}")

        invariants[inv_id] = _normalize(cols[statement_idx])

    if not invariants:
        raise ValueError(f"No invariants found in {path}")

    return invariants


def extract_scenarios(path: Path) -> dict[str, tuple[str, str]]:
    mappings: dict[str, tuple[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = SCENARIO_RE.match(line.strip())
        if not m:
            continue
        mappings[m.group("id")] = (m.group("feature"), f"Scenario: {m.group('scenario')}")

    if not mappings:
        raise ValueError(f"No scenario mappings found in {path}")

    return mappings


def main() -> int:
    canonical_invariants = extract_invariants(CANONICAL_PATH)
    mirror_invariants = extract_invariants(MIRROR_PATH)

    canonical_scenarios = extract_scenarios(CANONICAL_PATH)
    mirror_scenarios = extract_scenarios(MIRROR_PATH)

    errors: list[str] = []

    if set(canonical_invariants) != set(mirror_invariants):
        errors.append(
            "Invariant ID mismatch: "
            f"canonical={sorted(canonical_invariants)} mirror={sorted(mirror_invariants)}"
        )

    for inv_id in sorted(set(canonical_invariants) & set(mirror_invariants)):
        if canonical_invariants[inv_id] != mirror_invariants[inv_id]:
            errors.append(
                f"Invariant statement mismatch for {inv_id}: "
                f"canonical='{canonical_invariants[inv_id]}' mirror='{mirror_invariants[inv_id]}'"
            )

    if canonical_scenarios != mirror_scenarios:
        errors.append(
            "Scenario mapping mismatch: "
            f"canonical={canonical_scenarios} mirror={mirror_scenarios}"
        )

    if errors:
        print("Invariant documentation sync check FAILED:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Invariant documentation sync check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
