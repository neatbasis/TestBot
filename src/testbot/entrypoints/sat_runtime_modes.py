"""Runtime mode runners.

Interaction/profile selection remains planner-owned via
``testbot.interaction_planner.select_interaction_policy_request``.
This module intentionally avoids direct monolith imports.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable

from homeassistant_api import Client
from langchain_ollama import ChatOllama

from testbot.adapters.ask_gateway import AskGateway, STOP_DECISION_ID
from testbot.domain import Clock
from testbot.interaction_planner import COLLECT_TURN_INPUT_INTENT, select_interaction_policy_request
from testbot.ports import MemoryStorePort

_TERMINAL_STOP_DECISION_IDS = frozenset(
    {
        STOP_DECISION_ID,
        "cancel",
        "cancelled",
        "user_cancelled",
        "user_aborted",
        "abort",
        "aborted",
        "interrupted",
        "interrupt",
        "eof",
    }
)
_TERMINAL_STOP_SENTENCES = frozenset({"stop", "quit", "exit", "cancel", "abort"})
_RETRYABLE_ERROR_MARKERS = (
    "timeout",
    "temporar",
    "unavailable",
    "try again",
    "connection",
    "network",
    "reset",
)


def _is_terminal_stop_signal(*, decision_id: str | None, sentence: str) -> bool:
    normalized_decision = str(decision_id or "").strip().lower()
    if normalized_decision in _TERMINAL_STOP_DECISION_IDS:
        return True
    normalized_sentence = sentence.strip().lower()
    return normalized_sentence in _TERMINAL_STOP_SENTENCES


def _is_retryable_ask_error(error: str) -> bool:
    normalized_error = error.strip().lower()
    return any(marker in normalized_error for marker in _RETRYABLE_ERROR_MARKERS)


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
    # Input collection is Ask-backed in CLI mode; output remains direct print() for now.
    # This split is intentional until output-channel unification is explicitly scheduled.

    interaction_plan = select_interaction_policy_request(
        interaction_intent=COLLECT_TURN_INPUT_INTENT,
        channel_context="cli",
        task_flow_context="memory_chat_loop",
    )

    def _read() -> str | None:
        ask_result = ask_gateway.request_turn_input_for_policy(
            interaction_policy=interaction_plan.request,
            question="Ask one memory-grounded question.",
            timeout_s=60.0,
        )
        if _is_terminal_stop_signal(decision_id=ask_result.decision_id, sentence=ask_result.sentence):
            return "stop"
        if ask_result.error:
            if _is_retryable_ask_error(ask_result.error):
                print(f"bot> I didn't get that yet ({ask_result.error}). Please try again.")
                return ""
            print(f"bot> Ask input is unavailable ({ask_result.error}). Stopping.")
            return "stop"
        if not ask_result.sentence.strip():
            print("bot> I heard silence. Try again.")
            return ""
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

        interaction_plan = select_interaction_policy_request(
            interaction_intent=COLLECT_TURN_INPUT_INTENT,
            channel_context="satellite",
            task_flow_context="memory_chat_loop",
        )

        def _read() -> str | None:
            ask_result = ask_gateway.request_turn_input_for_policy(
                interaction_policy=interaction_plan.request,
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
