from __future__ import annotations

import operator
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict
from uuid import uuid4

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
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
model = init_chat_model("openai:gpt-4o")


def _message_id(msg: AnyMessage, index_hint: int) -> str:
    existing = getattr(msg, "id", None)
    return str(existing) if existing else f"msg-{index_hint}-{uuid4().hex[:12]}"


def read_input(state: State) -> dict[str, Any]:
    user_query = input("query: ").strip()
    if not user_query:
        return {}
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
    messages = state.get("messages", [])
    if not messages:
        return {}

    answer: AIMessage = model.invoke(messages)
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
graph.add_conditional_edges("answer_from_state", should_continue, {
    "read_input": "read_input",
    END: END,
})

workflow = graph.compile()
workflow.invoke({"iteration": 0})
