"""Compatibility bridge for legacy runtime exports.

This module centralizes temporary dependencies on ``testbot.sat_chatbot_memory_v2``
so entrypoints can migrate without silently re-introducing broad monolith imports.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from testbot import sat_chatbot_memory_v2 as _legacy_runtime

if TYPE_CHECKING:
    from argparse import Namespace
    from collections import deque

    from homeassistant_api import Client
    from langchain_core.embeddings import Embeddings
    from langchain_ollama import ChatOllama

    from testbot.domain import Clock
    from testbot.ports import MemoryStorePort
    from testbot.sat_chatbot_memory_v2 import CapabilitySnapshot, ChatMsg


_LEGACY_RUNTIME_WARNING_EMITTED = False

_LEGACY_RUNTIME_WARNING = (
    "entrypoints.runtime_legacy_bridge depends on testbot.sat_chatbot_memory_v2 compatibility exports; "
    "migrate callers to extracted services/entrypoints ownership before removing this bridge."
)


def _warn_legacy_runtime_bridge() -> None:
    global _LEGACY_RUNTIME_WARNING_EMITTED
    if _LEGACY_RUNTIME_WARNING_EMITTED:
        return
    warnings.warn(_LEGACY_RUNTIME_WARNING, DeprecationWarning, stacklevel=2)
    _LEGACY_RUNTIME_WARNING_EMITTED = True


def parse_args(argv: list[str] | None = None) -> "Namespace":
    _warn_legacy_runtime_bridge()
    return _legacy_runtime.parse_args(argv)


def read_runtime_env() -> dict[str, object]:
    _warn_legacy_runtime_bridge()
    return _legacy_runtime.read_runtime_env()


def build_capability_snapshot(*, requested_mode: str, daemon_mode: bool, runtime: dict[str, object]) -> "CapabilitySnapshot":
    _warn_legacy_runtime_bridge()
    return _legacy_runtime.build_capability_snapshot(
        requested_mode=requested_mode,
        daemon_mode=daemon_mode,
        runtime=runtime,
    )


def build_runtime_memory_store(*, runtime: dict[str, object], embeddings: "Embeddings") -> "MemoryStorePort":
    _warn_legacy_runtime_bridge()
    return _legacy_runtime.build_runtime_memory_store(runtime=runtime, embeddings=embeddings)


def run_source_ingestion(*, runtime: dict[str, object], store: "MemoryStorePort") -> None:
    _warn_legacy_runtime_bridge()
    _legacy_runtime.run_source_ingestion(runtime=runtime, store=store)


def print_startup_status(*, snapshot: "CapabilitySnapshot") -> None:
    _warn_legacy_runtime_bridge()
    _legacy_runtime.print_startup_status(snapshot=snapshot)


def run_chat_loop(
    *,
    runtime: dict[str, object],
    llm: "ChatOllama",
    store: "MemoryStorePort",
    chat_history: "deque[ChatMsg]",
    near_tie_delta: float,
    io_channel: str,
    capability_status: str,
    capability_snapshot: "CapabilitySnapshot",
    read_user_utterance,
    send_assistant_text,
    clock: "Clock",
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


def sat_say(client: "Client", entity_id: str, text: str) -> None:
    _warn_legacy_runtime_bridge()
    _legacy_runtime.sat_say(client, entity_id, text)
