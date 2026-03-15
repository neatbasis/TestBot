from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, TypedDict
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langchain_ollama import ChatOllama


class PassageRecord(TypedDict):
    passage_id: str
    observed_at: str
    sequence_index: int
    source_message_ids: list[str]
    canonical_text: str
    metadata: dict[str, Any]


class State(TypedDict):
    messages: list[AnyMessage]
    passages: list[PassageRecord]
    iteration: int


ITERATION_LIMIT = 5
DEFAULT_MODEL = os.getenv("SEEM_BOT_MODEL", "llama3.2:3b")


def _message_id(msg: AnyMessage, index_hint: int) -> str:
    existing = getattr(msg, "id", None)
    return str(existing) if existing else f"msg-{index_hint}-{uuid4().hex[:12]}"


def read_input() -> HumanMessage | None:
    user_query = input("query: ").strip()
    if not user_query:
        return None
    return HumanMessage(content=user_query)


def stabilize_passage(state: State, user_message: HumanMessage) -> PassageRecord:
    sequence_index = len(state["passages"])
    msg_text = user_message.content if isinstance(user_message.content, str) else str(user_message.content)

    passage: PassageRecord = {
        "passage_id": f"passage-{uuid4().hex}",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "sequence_index": sequence_index,
        "source_message_ids": [_message_id(user_message, sequence_index)],
        "canonical_text": f"human: {msg_text.strip()}",
        "metadata": {},
    }
    return passage


def answer_from_state(model: ChatOllama, state: State) -> AIMessage:
    answer: AIMessage = model.invoke(state["messages"])
    return answer


def _build_model() -> ChatOllama:
    return ChatOllama(model=DEFAULT_MODEL, temperature=0)


def _offline_fallback(user_message: HumanMessage) -> AIMessage:
    content = user_message.content if isinstance(user_message.content, str) else str(user_message.content)
    return AIMessage(
        content=(
            "[offline fallback] I could not reach Ollama in this environment. "
            f"I recorded your prompt: {content}"
        )
    )


def run() -> None:
    load_dotenv()
    state: State = {"messages": [], "passages": [], "iteration": 0}
    model = _build_model()

    print(f"seem_bot started (model={DEFAULT_MODEL}, max_turns={ITERATION_LIMIT})")
    print("Submit an empty line to exit.")

    while state["iteration"] < ITERATION_LIMIT:
        user_message = read_input()
        if user_message is None:
            break

        state["messages"].append(user_message)
        state["passages"].append(stabilize_passage(state, user_message))

        try:
            answer = answer_from_state(model, state)
        except Exception:
            answer = _offline_fallback(user_message)

        state["messages"].append(answer)
        state["iteration"] += 1
        print("answer:", answer.content)

    print(f"done (iterations={state['iteration']}, passages={len(state['passages'])})")


if __name__ == "__main__":
    run()
