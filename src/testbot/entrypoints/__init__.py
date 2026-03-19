"""Runtime entrypoints for TestBot."""


def main(argv: list[str] | None = None) -> None:
    from .sat_cli import main as sat_main

    sat_main(argv)


__all__ = ["main"]
