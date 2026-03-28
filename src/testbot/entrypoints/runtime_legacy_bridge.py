"""Temporary compatibility bridge for legacy runtime exports.

Why this module exists:
- Preserve the extracted entrypoint seam where planner/profile selection stays in
  ``entrypoints`` + ``interaction_planner``.
- Make remaining monolith coupling explicit and reviewable.

What this module is not:
- It is not the final runtime authority boundary.
- It does not complete monolith breakup.

Removal target:
- Retire after runtime bootstrap/chat-loop wiring is extracted into stable modules.
"""

from __future__ import annotations

import warnings
from collections import deque

from homeassistant_api import Client
from langchain_core.embeddings import Embeddings
from langchain_ollama import ChatOllama

from testbot.entrypoints import runtime_bootstrap as _runtime_bootstrap
from testbot.entrypoints import runtime_loop as _runtime_loop
from testbot.domain import Clock
from testbot.ports import MemoryStorePort

ChatMsg = dict[str, str]


_LEGACY_RUNTIME_WARNING_EMITTED = False

_LEGACY_RUNTIME_WARNING = (
    "entrypoints.runtime_legacy_bridge depends on testbot.sat_chatbot_memory_v2 compatibility exports; "
    "migrate callers to extracted services/entrypoints ownership before removing this bridge."
)


def _warn_legacy_runtime_bridge() -> None:
    """Emit a one-time deprecation warning for bridge-backed runtime calls."""
    global _LEGACY_RUNTIME_WARNING_EMITTED
    if _LEGACY_RUNTIME_WARNING_EMITTED:
        return
    warnings.warn(_LEGACY_RUNTIME_WARNING, DeprecationWarning, stacklevel=2)
    _LEGACY_RUNTIME_WARNING_EMITTED = True


def read_runtime_env() -> dict[str, object]:
    _warn_legacy_runtime_bridge()
    return _runtime_bootstrap.read_runtime_env()


def build_runtime_memory_store(*, runtime: dict[str, object], embeddings: Embeddings) -> MemoryStorePort:
    _warn_legacy_runtime_bridge()
    return _runtime_bootstrap.build_runtime_memory_store(runtime=runtime, embeddings=embeddings)


def run_chat_loop(
    *,
    runtime: dict[str, object],
    llm: ChatOllama,
    store: MemoryStorePort,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    io_channel: str,
    capability_status: str,
    capability_snapshot: object,
    read_user_utterance,
    send_assistant_text,
    clock: Clock,
) -> None:
    _warn_legacy_runtime_bridge()
    _runtime_loop.run_chat_loop(
        runtime=runtime,
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=near_tie_delta,
        io_channel=io_channel,
        capability_status=capability_status,
        capability_snapshot=capability_snapshot,
        read_user_utterance=read_user_utterance,
        send_assistant_text=send_assistant_text,
        clock=clock,
    )


def sat_say(client: Client, entity_id: str, text: str) -> None:
    _warn_legacy_runtime_bridge()
    _runtime_loop.sat_say(client, entity_id, text)


__all__ = [
    "build_runtime_memory_store",
    "read_runtime_env",
    "run_chat_loop",
    "sat_say",
]
