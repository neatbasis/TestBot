from __future__ import annotations

from collections import deque
from collections.abc import Callable

from ha_ask import AskSpec, ask_question
from ha_ask.config import normalize_rest_api_url
from homeassistant_api import Client
from langchain_ollama import ChatOllama

from testbot.clock import Clock
from testbot.sat_chatbot_memory_v2 import CapabilitySnapshot, ChatMsg
from testbot.ports import MemoryStorePort


def run_cli_mode(
    *,
    runtime: dict[str, object],
    llm: ChatOllama,
    store: MemoryStorePort,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    capability_snapshot: CapabilitySnapshot,
    clock: Clock,
    run_chat_loop: Callable[..., None],
) -> None:
    print("CLI chat ready. Ask memory-grounded questions; type 'stop' to exit.")

    def _read() -> str | None:
        try:
            return input("you> ")
        except EOFError:
            return None

    def _send(text: str) -> None:
        print(f"bot> {text}")

    run_chat_loop(
        runtime=runtime,
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=near_tie_delta,
        io_channel="cli",
        capability_status="ask_unavailable",
        capability_snapshot=capability_snapshot,
        read_user_utterance=_read,
        send_assistant_text=_send,
        clock=clock,
    )


def run_satellite_mode(
    *,
    runtime: dict[str, object],
    llm: ChatOllama,
    store: MemoryStorePort,
    chat_history: deque[ChatMsg],
    near_tie_delta: float,
    api_url: str,
    token: str,
    entity_id: str,
    capability_snapshot: CapabilitySnapshot,
    clock: Clock,
    run_chat_loop: Callable[..., None],
    satellite_say: Callable[[Client, str, str], None],
) -> None:
    rest = normalize_rest_api_url(api_url)
    with Client(rest, token) as client:
        satellite_say(client, entity_id, "v0 memory loop online. Say 'stop' to exit.")

        def _read() -> str | None:
            res = ask_question(
                channel="satellite",
                spec=AskSpec(
                    question="Ask one memory-grounded question.",
                    answers=None,
                    timeout_s=60.0,
                ),
                api_url=api_url,
                token=token,
                satellite_entity_id=entity_id,
            )
            if res.get("error"):
                satellite_say(client, entity_id, f"I didn't get that. Error: {res['error']}")
                return ""
            return str(res.get("sentence") or "")

        def _send(text: str) -> None:
            satellite_say(client, entity_id, text)

        run_chat_loop(
            runtime=runtime,
            llm=llm,
            store=store,
            chat_history=chat_history,
            near_tie_delta=near_tie_delta,
            io_channel="satellite",
            capability_status="ask_available",
            capability_snapshot=capability_snapshot,
            read_user_utterance=_read,
            send_assistant_text=_send,
            clock=clock,
        )
