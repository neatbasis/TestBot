"""Transitional compatibility wrapper for legacy sat_cli imports.

Canonical runtime CLI entrypoint: ``testbot.entrypoints.cli``.
"""

from __future__ import annotations

import warnings

_SAT_CLI_TRANSITION_WARNING = (
    "testbot.entrypoints.sat_cli is transitional compatibility surface. "
    "Use testbot.entrypoints.cli.main(...) instead."
)


def main(argv: list[str] | None = None) -> None:
    """Deprecated compatibility entrypoint; delegate to ``testbot.entrypoints.cli.main``."""
    warnings.warn(_SAT_CLI_TRANSITION_WARNING, DeprecationWarning, stacklevel=2)
    from .cli import main as cli_main

    cli_main(argv)


__all__ = ["main"]
