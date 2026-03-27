"""Compatibility wrapper for legacy ``sat_cli`` imports.

Canonical runtime CLI entrypoint: ``testbot.entrypoints.cli``.

Deprecation governance contract:
- Tracking issue: ``ISSUE-0021`` (`docs/issues/ISSUE-0021-legacy-boundary-pattern-deprecation-and-migration.md`)
- Review target: 2026-06-30
- Status: compatibility-only (non-authoritative)
- Removal condition: remove once operator docs, entrypoints, and external automation references
  are migrated to ``testbot.entrypoints.cli`` and one release cycle passes without authoritative use.
- Transitional rationale: preserves legacy automation/import compatibility while canonical entrypoint
  migration completes.
"""

from __future__ import annotations

import warnings

_SAT_CLI_TRANSITION_WARNING = (
    "testbot.entrypoints.sat_cli is compatibility-only transitional surface (ISSUE-0021, review target 2026-06-30). "
    "Use testbot.entrypoints.cli.main(...) instead."
)


def main(argv: list[str] | None = None) -> None:
    """Deprecated compatibility entrypoint; delegate to ``testbot.entrypoints.cli.main``."""
    warnings.warn(_SAT_CLI_TRANSITION_WARNING, DeprecationWarning, stacklevel=2)
    from .cli import main as cli_main

    cli_main(argv)


__all__ = ["main"]
