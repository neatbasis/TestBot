from __future__ import annotations

from collections import deque
from collections.abc import Callable

from homeassistant_api import Client
from langchain_ollama import ChatOllama

from testbot.adapters.ask_gateway import AskGateway, STOP_DECISION_ID
from testbot.domain import Clock
from testbot.application.services.runtime_capability_service import CapabilitySnapshot
from testbot.interaction_planner import (
    ChannelContext,
    InteractionShape,
    InteractionStandardsProfile,
    NeedProfile,
    plan_interaction,
)
from testbot.sat_chatbot_memory_v2 import ChatMsg
from testbot.ports import MemoryStorePort





def _plan_runtime_interaction(*, channel_id: str, supports_satellite_ask: bool):
    return plan_interaction(
        need_profile=NeedProfile(task_intent_requirements="memory_grounded_turn"),
        channel_context=ChannelContext(channel_id=channel_id, supports_satellite_ask=supports_satellite_ask),
        interaction_standards_profile=InteractionStandardsProfile(profile_id="runtime-mode-v1"),
    )


def _capability_status_from_shape(shape: InteractionShape) -> str:
    if shape is InteractionShape.SATELLITE_VOICE_LOOP:
        return "ask_available"
    return "ask_unavailable"

def _satellite_prompt_for_shape(shape: InteractionShape) -> str:
    if shape is InteractionShape.SATELLITE_VOICE_LOOP:
        return "Ask one memory-grounded question."
    return "Share one memory-grounded question in text form."

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

    interaction_plan = _plan_runtime_interaction(channel_id="cli", supports_satellite_ask=False)

    run_chat_loop(
        runtime=runtime,
        llm=llm,
        store=store,
        chat_history=chat_history,
        near_tie_delta=near_tie_delta,
        io_channel="cli",
        capability_status=_capability_status_from_shape(interaction_plan.recommended_shape),
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
    interaction_plan = _plan_runtime_interaction(channel_id="satellite", supports_satellite_ask=True)

    with Client(ask_gateway.normalized_ha_rest_url(), ask_gateway.ha_api_token) as client:
        entity_id = ask_gateway.satellite_entity_id
        satellite_say(client, entity_id, "v0 memory loop online. Say 'stop' to exit.")

        def _read() -> str | None:
            ask_result = ask_gateway.request_satellite_turn_input(
                question=_satellite_prompt_for_shape(interaction_plan.recommended_shape),
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
            capability_status=_capability_status_from_shape(interaction_plan.recommended_shape),
            capability_snapshot=capability_snapshot,
            read_user_utterance=_read,
            send_assistant_text=_send,
            clock=clock,
        )
