from __future__ import annotations

import operator
import os
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph


class PassageRecord(TypedDict):
    passage_id: str
    observed_at: str
    sequence_index: int
    source_message_ids: list[str]
    canonical_text: str
    metadata: dict[str, Any]


class State(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    passages: Annotated[list[PassageRecord], operator.add]
    iteration: int


ITERATION_LIMIT = 5

load_dotenv()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", os.getenv("SEEM_BOT_MODEL", "llama3.2:3b"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
X_OLLAMA_KEY = os.getenv("X_OLLAMA_KEY", "").strip()


def _ollama_client_kwargs() -> dict[str, object]:
    if X_OLLAMA_KEY:
        return {"client_kwargs": {"headers": {"X-Ollama-Key": X_OLLAMA_KEY}}}
    return {}


model = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0,
    **_ollama_client_kwargs(),
)


def _message_id(msg: AnyMessage, index_hint: int) -> str:
    existing = getattr(msg, "id", None)
    return str(existing) if existing else f"msg-{index_hint}-{uuid4().hex[:12]}"


def read_input(state: State) -> dict[str, Any]:
    try:
        user_query = input("query: ").strip()
    except EOFError:
        return {"iteration": ITERATION_LIMIT}
    if not user_query:
        return {"iteration": ITERATION_LIMIT}
    return {"messages": [HumanMessage(content=user_query)]}


def stabilize_passage(state: State) -> dict[str, Any]:
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_msg = messages[-1]
    if not isinstance(last_msg, HumanMessage):
        return {}

    sequence_index = len(state.get("passages", []))
    msg_text = last_msg.content if isinstance(last_msg.content, str) else str(last_msg.content)

    passage: PassageRecord = {
        "passage_id": f"passage-{uuid4().hex}",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "sequence_index": sequence_index,
        "source_message_ids": [_message_id(last_msg, sequence_index)],
        "canonical_text": f"human: {msg_text.strip()}",
        "metadata": {},
    }
    return {"passages": [passage]}


def answer_from_state(state: State) -> dict[str, Any]:
    if state.get("iteration", 0) >= ITERATION_LIMIT:
        return {}

    messages = state.get("messages", [])
    if not messages:
        return {}

    try:
        answer: AIMessage = model.invoke(messages)
    except Exception as exc:
        answer = AIMessage(content=f"[offline fallback] Could not reach Ollama: {exc}")

    print("answer:", answer.content)
    return {
        "messages": [answer],
        "iteration": state.get("iteration", 0) + 1,
    }


def should_continue(state: State) -> str:
    if state.get("iteration", 0) >= ITERATION_LIMIT:
        return END
    return "read_input"


graph = StateGraph(State)

graph.add_node("read_input", read_input)
graph.add_node("stabilize_passage", stabilize_passage)
graph.add_node("answer_from_state", answer_from_state)

graph.add_edge(START, "read_input")
graph.add_edge("read_input", "stabilize_passage")
graph.add_edge("stabilize_passage", "answer_from_state")
graph.add_conditional_edges(
    "answer_from_state",
    should_continue,
    {
        "read_input": "read_input",
        END: END,
    },
)

workflow = graph.compile()
workflow.invoke({"iteration": 0})
