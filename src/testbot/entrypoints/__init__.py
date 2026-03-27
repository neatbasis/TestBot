"""Runtime entrypoints for TestBot."""

from __future__ import annotations


def main(argv: list[str] | None = None) -> None:
    """Lazy convenience wrapper for the canonical runtime CLI entrypoint.

    Keep cli import deferred so ``python -m testbot.entrypoints.cli``
    is not preloaded through package import side effects.
    """

    from .cli import main as cli_main

    cli_main(argv)


__all__ = ["main"]
