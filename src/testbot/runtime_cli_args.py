"""Runtime CLI argument parsing owner.

This module is the canonical owner for runtime CLI argument schema used by
entrypoint composition. Keeping it separate from compatibility bridges allows
incremental removal of bridge imports without changing argument behavior.
"""

from __future__ import annotations

from argparse import ArgumentParser, BooleanOptionalAction, Namespace


def parse_args(argv: list[str] | None = None) -> Namespace:
    parser = ArgumentParser(description="Run TestBot with satellite or CLI chat interfaces.")
    parser.add_argument(
        "--mode",
        choices=("auto", "satellite", "cli"),
        default="auto",
        help="Input/output mode. auto prefers satellite and falls back to CLI.",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Do not fall back to CLI if satellite mode is unavailable; exit instead.",
    )
    parser.add_argument(
        "--debug-verbose",
        action=BooleanOptionalAction,
        default=None,
        help=(
            "Enable verbose debug trace payloads when TESTBOT_DEBUG=1. "
            "Defaults to TESTBOT_DEBUG_VERBOSE environment setting."
        ),
    )
    return parser.parse_args(argv)


__all__ = ["parse_args"]
