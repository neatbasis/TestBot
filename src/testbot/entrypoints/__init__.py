"""Runtime entrypoints for TestBot."""

from __future__ import annotations


def main(argv: list[str] | None = None) -> None:
    """Lazy convenience wrapper for the canonical runtime CLI entrypoint.

    Keep sat_cli import deferred so ``python -m testbot.entrypoints.sat_cli``
    is not preloaded through package import side effects.
    """

    from .sat_cli import main as sat_cli_main

    sat_cli_main(argv)

__all__ = ["main"]
