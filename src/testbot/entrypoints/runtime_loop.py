"""Canonical runtime loop entrypoint helpers.

Ownership:
- This module is the canonical owner for runtime loop invocation and
  satellite output helpers used by the CLI runtime entrypoint.
- During retirement, implementation delegates to the compatibility façade
  while this module remains the stable import surface for runtime callers.
"""

from __future__ import annotations

from collections import deque

from homeassistant_api import Client
from langchain_ollama import ChatOllama

from testbot import sat_chatbot_memory_v2 as _legacy_runtime
from testbot.domain import Clock
from testbot.ports import MemoryStorePort

ChatMsg = dict[str, str]


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
    _legacy_runtime.sat_say(client, entity_id, text)


__all__ = ["run_chat_loop", "sat_say"]
