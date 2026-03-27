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
    parser.add_argument(
        "--source-ingestion",
        choices=("env", "menu", "reference", "freeform", "off", "fixture", "local_markdown", "wikipedia", "arxiv"),
        default="env",
        help=(
            "User-facing source-ingestion selection. "
            "'menu' shows an Ask-demo-style entry menu; "
            "'reference' applies a known-good reference example; "
            "'freeform' accepts <connector>:<value>; "
            "'env' keeps deployment SOURCE_* settings; "
            "'off' disables ingestion; direct connector choices force that connector."
        ),
    )
    parser.add_argument(
        "--source-reference",
        choices=("wikipedia_hilbert", "local_alignment_docs", "arxiv_category_theory"),
        default="wikipedia_hilbert",
        help="Reference example key used when --source-ingestion reference is selected.",
    )
    parser.add_argument(
        "--source-freeform",
        default="",
        help="Freeform ingestion request in '<connector>:<value>' format used by --source-ingestion freeform.",
    )
    return parser.parse_args(argv)


__all__ = ["parse_args"]
