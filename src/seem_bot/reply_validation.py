from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from .state_types import State, ValidationRecord
from .utils import message_text, now_utc


FORBIDDEN_PHRASES = [
    "based on the provided context",
    "i will respond accordingly",
    "response mode",
    "resolved referent",
    "supporting passages",
    "internal state",
    "hidden context",
]


def validate_reply(state: State) -> dict[str, Any]:
    messages = state.get("messages", [])
    if not messages or not isinstance(messages[-1], AIMessage):
        return {}

    text = message_text(messages[-1]).lower()
    issues: list[str] = []

    for phrase in FORBIDDEN_PHRASES:
        if phrase in text:
            issues.append(f"meta_leak:{phrase}")

    if not text.strip():
        issues.append("empty_reply")

    validation: ValidationRecord = {
        "passed": not issues,
        "issues": issues,
        "checked_at": now_utc(),
    }
    return {"validation": validation}
