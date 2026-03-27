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

from testbot import sat_chatbot_memory_v2 as _legacy_runtime
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


def parse_args(argv: list[str] | None = None):
    _warn_legacy_runtime_bridge()
    return _legacy_runtime.parse_args(argv)


def read_runtime_env() -> dict[str, object]:
    _warn_legacy_runtime_bridge()
    return _legacy_runtime.read_runtime_env()


def build_capability_snapshot(*, requested_mode: str, daemon_mode: bool, runtime: dict[str, object]):
    _warn_legacy_runtime_bridge()
    return _legacy_runtime.build_capability_snapshot(
        requested_mode=requested_mode,
        daemon_mode=daemon_mode,
        runtime=runtime,
    )


def build_runtime_memory_store(*, runtime: dict[str, object], embeddings: Embeddings) -> MemoryStorePort:
    _warn_legacy_runtime_bridge()
    return _legacy_runtime.build_runtime_memory_store(runtime=runtime, embeddings=embeddings)


def run_source_ingestion(*, runtime: dict[str, object], store: MemoryStorePort) -> None:
    _warn_legacy_runtime_bridge()
    _legacy_runtime.run_source_ingestion(runtime=runtime, store=store)


def print_startup_status(*, snapshot: object) -> None:
    _warn_legacy_runtime_bridge()
    _legacy_runtime.print_startup_status(snapshot=snapshot)


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
    _legacy_runtime.run_chat_loop(
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
    _legacy_runtime.sat_say(client, entity_id, text)


__all__ = [
    "build_capability_snapshot",
    "build_runtime_memory_store",
    "parse_args",
    "print_startup_status",
    "read_runtime_env",
    "run_chat_loop",
    "run_source_ingestion",
    "sat_say",
]
