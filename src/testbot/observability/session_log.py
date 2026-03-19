from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path

from testbot.memory_cards import utc_now_iso

SESSION_LOG_SCHEMA_VERSION = 2


def _normalize_json_safe(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return _normalize_json_safe(value.value)
    if isinstance(value, dict):
        return {str(key): _normalize_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_normalize_json_safe(item) for item in sorted(value, key=repr)]

    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        try:
            return _normalize_json_safe(to_dict())
        except Exception:
            pass

    if is_dataclass(value):
        return _normalize_json_safe(asdict(value))

    if hasattr(value, "__dict__"):
        return _normalize_json_safe(vars(value))

    return repr(value)


def append_session_log(event: str, payload: dict, *, log_path: Path = Path("./logs/session.jsonl")) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": utc_now_iso(),
        "event": event,
        "schema_version": SESSION_LOG_SCHEMA_VERSION,
        **_normalize_json_safe(payload),
    }
    with log_path.open("a", encoding="utf-8") as file_handle:
        file_handle.write(json.dumps(row, ensure_ascii=False) + "\n")
