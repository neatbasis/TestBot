from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from testbot.memory_cards import utc_now_iso

TRANSITION_VALIDATION_SCHEMA_VERSION = 4


class TransitionValidationResult(Protocol):
    stage: str
    boundary: str

    def to_dict(self) -> dict[str, object]: ...


def build_transition_validation_log_row(
    result: TransitionValidationResult,
    *,
    now_iso: str | None = None,
) -> dict[str, object]:
    return {
        "ts": now_iso or utc_now_iso(),
        "event": "stage_transition_validation",
        "schema_version": TRANSITION_VALIDATION_SCHEMA_VERSION,
        **result.to_dict(),
    }


def append_transition_validation_log(
    result: TransitionValidationResult,
    *,
    log_path: Path = Path("./logs/session.jsonl"),
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    row = build_transition_validation_log_row(result)
    with log_path.open("a", encoding="utf-8") as file_handle:
        file_handle.write(json.dumps(row, ensure_ascii=False) + "\n")


__all__ = [
    "TRANSITION_VALIDATION_SCHEMA_VERSION",
    "append_transition_validation_log",
    "build_transition_validation_log_row",
]
