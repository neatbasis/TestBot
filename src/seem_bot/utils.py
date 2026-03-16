from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from langchain_core.messages import AnyMessage


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def message_id(msg: AnyMessage, index_hint: int) -> str:
    existing = getattr(msg, "id", None)
    return str(existing) if existing else f"msg-{index_hint}-{uuid4().hex[:12]}"


def message_text(msg: AnyMessage) -> str:
    content = msg.content
    if isinstance(content, str):
        return content.strip()
    return str(content).strip()


def strip_role_prefix(text: str, prefix: str) -> str:
    wanted = f"{prefix}:"
    if text.lower().startswith(wanted.lower()):
        return text[len(wanted) :].strip()
    return text.strip()
