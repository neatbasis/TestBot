from __future__ import annotations

from collections import deque
from collections.abc import Callable

from homeassistant_api import Client
from langchain_ollama import ChatOllama

from testbot.adapters.ask_gateway import AskGateway, STOP_DECISION_ID
from testbot.domain import Clock
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
    capability_snapshot: CapabilitySnapshot,
    clock: Clock,
    ask_gateway: AskGateway,
    run_chat_loop: Callable[..., None],
    satellite_say: Callable[[Client, str, str], None],
) -> None:
    with Client(ask_gateway.normalized_ha_rest_url(), ask_gateway.ha_api_token) as client:
        entity_id = ask_gateway.satellite_entity_id
        satellite_say(client, entity_id, "v0 memory loop online. Say 'stop' to exit.")

        def _read() -> str | None:
            ask_result = ask_gateway.request_satellite_turn_input(
                question="Ask one memory-grounded question.",
                timeout_s=60.0,
            )
            if ask_result.error:
                satellite_say(client, entity_id, f"I didn't get that. Error: {ask_result.error}")
                return ""
            if ask_result.decision_id == STOP_DECISION_ID:
                return "stop"
            return ask_result.sentence

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
