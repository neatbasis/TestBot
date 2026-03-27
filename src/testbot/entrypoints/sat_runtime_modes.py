"""Runtime mode runners.

Interaction/profile selection remains planner-owned via
``testbot.interaction_planner.select_interaction_requirements``.
This module intentionally avoids direct monolith imports.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable

from homeassistant_api import Client
from langchain_ollama import ChatOllama

from testbot.adapters.ask_gateway import AskGateway, STOP_DECISION_ID
from testbot.domain import Clock
from testbot.interaction_planner import select_interaction_requirements
from testbot.ports import MemoryStorePort


def run_cli_mode(
    *,
    runtime: dict[str, object],
    llm: ChatOllama,
    store: MemoryStorePort,
    chat_history: deque[dict[str, str]],
    near_tie_delta: float,
    capability_snapshot: object,
    clock: Clock,
    ask_gateway: AskGateway,
    run_chat_loop: Callable[..., None],
) -> None:
    print("CLI chat ready. Ask memory-grounded questions; type 'stop' to exit.")

    interaction_plan = select_interaction_requirements(
        need_profile="ask_turn_input",
        channel_context="cli",
        task_flow_context="memory_chat_loop",
    )

    def _read() -> str | None:
        ask_result = ask_gateway.request_turn_input(
            channel="terminal",
            question="Ask one memory-grounded question.",
            timeout_s=60.0,
            interaction_requirements=interaction_plan.interaction_requirements,
        )
        if ask_result.error:
            print(f"bot> I didn't get that. Error: {ask_result.error}")
            return ""
        if ask_result.decision_id == STOP_DECISION_ID:
            return "stop"
        return ask_result.sentence

    def _send(text: str) -> None:
        print(f"bot> {text}")

    run_chat_loop(
        runtime=runtime,
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=near_tie_delta,
        io_channel="cli",
        capability_status="ask_available",
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
    chat_history: deque[dict[str, str]],
    near_tie_delta: float,
    capability_snapshot: object,
    clock: Clock,
    ask_gateway: AskGateway,
    run_chat_loop: Callable[..., None],
    satellite_say: Callable[[Client, str, str], None],
) -> None:
    with Client(ask_gateway.normalized_ha_rest_url(), ask_gateway.ha_api_token) as client:
        entity_id = ask_gateway.satellite_entity_id
        satellite_say(client, entity_id, "v0 memory loop online. Say 'stop' to exit.")

        interaction_plan = select_interaction_requirements(
            need_profile="ask_turn_input",
            channel_context="satellite",
            task_flow_context="memory_chat_loop",
        )

        def _read() -> str | None:
            ask_result = ask_gateway.request_turn_input(
                channel="satellite",
                question="Ask one memory-grounded question.",
                timeout_s=60.0,
                interaction_requirements=interaction_plan.interaction_requirements,
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
