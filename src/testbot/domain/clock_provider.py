from __future__ import annotations

from testbot.clock import Clock, SystemClock


def build_system_clock() -> Clock:
    """Return the default runtime clock implementation for entrypoint wiring."""
    return SystemClock()


__all__ = ["Clock", "build_system_clock"]
