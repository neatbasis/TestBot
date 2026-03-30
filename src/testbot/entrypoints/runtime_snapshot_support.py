"""Canonical runtime snapshot-time support helpers.

Ownership:
- This module is the canonical owner for runtime-loop snapshot timestamp
  provider construction.
- Compatibility façades may delegate here while legacy helpers are retired.
"""

from __future__ import annotations

from dataclasses import dataclass

from testbot.domain import Clock


@dataclass(frozen=True)
class RuntimeClockBackedSnapshotTimeProvider:
    """Clock-backed snapshot provider for pipeline snapshot emission."""

    clock: Clock

    def now_iso(self) -> str:
        return self.clock.now().isoformat()


def runtime_clock_snapshot_time_provider(*, clock: Clock) -> RuntimeClockBackedSnapshotTimeProvider:
    return RuntimeClockBackedSnapshotTimeProvider(clock=clock)


__all__ = ["RuntimeClockBackedSnapshotTimeProvider", "runtime_clock_snapshot_time_provider"]
