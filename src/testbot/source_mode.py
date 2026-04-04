from __future__ import annotations

from enum import StrEnum
from typing import Any


class SourceMode(StrEnum):
    DISABLED = "disabled"
    BOOTSTRAP_PRELOAD = "bootstrap_preload"
    TURN_TRIGGERED_ACQUISITION = "turn_triggered_acquisition"


def normalize_source_mode(value: Any) -> SourceMode:
    if isinstance(value, SourceMode):
        return value
    if value is None:
        return SourceMode.DISABLED
    try:
        return SourceMode(str(value))
    except ValueError:
        return SourceMode.DISABLED
