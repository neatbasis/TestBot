from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import arrow


class Clock(Protocol):
    def now(self) -> arrow.Arrow:
        """Return the current timestamp."""


@dataclass(frozen=True)
class SystemClock:
    def now(self) -> arrow.Arrow:
        return arrow.utcnow()
