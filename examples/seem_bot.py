from __future__ import annotations

import re
import os
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from langchain_ollama import ChatOllama


# -----------------------------------------------------------------------------
# State model
# -----------------------------------------------------------------------------

class PassageRecord(TypedDict):
    passage_id: str
    kind: str                # "observation" | "response"
    observed_at: str
    sequence_index: int
    source_message_ids: list[str]
    canonical_text: str
    metadata: dict[str, Any]


class FactRecord(TypedDict):
    fact_id: str
    passage_id: str
    fact_type: str
    key: str
    value: str


class ContextRecord(TypedDict, total=False):
    thread_id: str
    now_utc: str
    latest_user_passage_id: str
    latest_passage_text: str
    user_intent_hint: str
    conversation_turn: int


class State(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    passages: list[PassageRecord]
    facts: list[FactRecord]
    context: ContextRecord
    response_plan: dict[str, Any]
    iteration: int


# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

ITERATION_LIMIT = 50

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


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _message_id(msg: AnyMessage, index_hint: int) -> str:
    existing = getattr(msg, "id", None)
    return str(existing) if existing else f"msg-{index_hint}-{uuid4().hex[:12]}"


def _message_text(msg: AnyMessage) -> str:
    content = msg.content
    if isinstance(content, str):
        return content.strip()
    return str(content).strip()


def _next_passage_index(state: State) -> int:
    return len(state.get("passages", []))


def _latest_passage_of_kind(state: State, kind: str) -> PassageRecord | None:
    for p in reversed(state.get("passages", [])):
        if p["kind"] == kind:
            return p
    return None


def _make_passage(
    *,
    state: State,
    msg: AnyMessage,
    kind: str,
    role_prefix: str,
    metadata: dict[str, Any] | None = None,
) -> PassageRecord:
    idx = _next_passage_index(state)
    return {
        "passage_id": f"passage-{uuid4().hex}",
        "kind": kind,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "sequence_index": idx,
        "source_message_ids": [_message_id(msg, idx)],
        "canonical_text": f"{role_prefix}: {_message_text(msg)}",
        "metadata": metadata or {},
    }


def _intent_hint(text: str) -> str:
    lowered = text.lower()
    if "?" in text:
        return "question"
    if lowered.startswith(("write ", "generate ", "draft ", "create ")):
        return "generation_request"
    if lowered.startswith(("fix ", "debug ", "explain ", "review ")):
        return "analysis_request"
    return "statement"


def _extract_simple_facts(passage: PassageRecord) -> list[FactRecord]:
    """
    Lightweight heuristic extraction to demonstrate the channel.
    Replace later with a structured extractor node.
    """
    text = passage["canonical_text"]

    facts: list[FactRecord] = []

    # Mentioned model names / URLs / code-ish tokens
    for match in re.findall(r"https?://\S+|[A-Za-z_][A-Za-z0-9_\-.:/]{2,}", text):
        facts.append(
            {
                "fact_id": f"fact-{uuid4().hex}",
                "passage_id": passage["passage_id"],
                "fact_type": "token_mention",
                "key": "mention",
                "value": match,
            }
        )

    # Very rough question detection
    if "?" in text:
        facts.append(
            {
                "fact_id": f"fact-{uuid4().hex}",
                "passage_id": passage["passage_id"],
                "fact_type": "speech_act",
                "key": "kind",
                "value": "question",
            }
        )

    return facts


def _format_recent_passages(state: State, limit: int = 4) -> str:
    recent = state.get("passages", [])[-limit:]
    if not recent:
        return "(none)"
    return "\n".join(
        f"- [{p['sequence_index']}:{p['kind']}] {p['canonical_text']}"
        for p in recent
    )


def _format_recent_facts(state: State, limit: int = 8) -> str:
    recent = state.get("facts", [])[-limit:]
    if not recent:
        return "(none)"
    return "\n".join(
        f"- ({f['fact_type']}) {f['key']} = {f['value']}"
        for f in recent
    )


# -----------------------------------------------------------------------------
# Nodes
# -----------------------------------------------------------------------------

def read_input(state: State) -> dict[str, Any]:
    if state.get("iteration", 0) >= ITERATION_LIMIT:
        return {}

    try:
        user_query = input("query: ").strip()
    except EOFError:
        return {"iteration": ITERATION_LIMIT}

    if not user_query:
        return {"iteration": ITERATION_LIMIT}

    return {"messages": [HumanMessage(content=user_query)]}


def stabilize_observation(state: State) -> dict[str, Any]:
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_msg = messages[-1]
    if not isinstance(last_msg, HumanMessage):
        return {}

    passage = _make_passage(
        state=state,
        msg=last_msg,
        kind="observation",
        role_prefix="human",
    )
    return {"passages": state.get("passages", []) + [passage]}


def resolve_context(state: State, config) -> dict[str, Any]:
    latest = _latest_passage_of_kind(state, "observation")
    if not latest:
        return {}

    thread_id = config.get("configurable", {}).get("thread_id", "default-thread")
    context: ContextRecord = {
        "thread_id": thread_id,
        "now_utc": datetime.now(timezone.utc).isoformat(),
        "latest_user_passage_id": latest["passage_id"],
        "latest_passage_text": latest["canonical_text"],
        "user_intent_hint": _intent_hint(latest["canonical_text"]),
        "conversation_turn": state.get("iteration", 0) + 1,
    }
    return {"context": context}


def extract_facts(state: State) -> dict[str, Any]:
    latest = _latest_passage_of_kind(state, "observation")
    if not latest:
        return {}

    new_facts = _extract_simple_facts(latest)
    if not new_facts:
        return {}

    return {"facts": state.get("facts", []) + new_facts}


def decide_response_plan(state: State) -> dict[str, Any]:
    ctx = state.get("context", {})
    intent = ctx.get("user_intent_hint", "statement")
    latest = ctx.get("latest_passage_text", "")

    if "help me" in latest.lower() or intent == "analysis_request":
        mode = "structured_help"
    elif intent == "generation_request":
        mode = "generate"
    elif intent == "question":
        mode = "answer"
    else:
        mode = "respond"

    return {
        "response_plan": {
            "mode": mode,
            "ground_on_passages": True,
            "ground_on_context": True,
            "ground_on_facts": True,
        }
    }


def answer_from_state(state: State) -> dict[str, Any]:
    if state.get("iteration", 0) >= ITERATION_LIMIT:
        return {}

    ctx = state.get("context", {})
    plan = state.get("response_plan", {})

    system_prompt = (
        "You are a passage-grounded assistant.\n"
        "Answer from the structured state below, not from vague memory.\n"
        "Prefer the latest stabilized observation and resolved context.\n"
        "If the state is insufficient, say what is missing plainly.\n"
    )

    grounded_prompt = (
        f"THREAD CONTEXT\n"
        f"- thread_id: {ctx.get('thread_id', 'unknown')}\n"
        f"- now_utc: {ctx.get('now_utc', 'unknown')}\n"
        f"- turn: {ctx.get('conversation_turn', 'unknown')}\n"
        f"- intent_hint: {ctx.get('user_intent_hint', 'unknown')}\n\n"
        f"RESPONSE PLAN\n"
        f"{plan}\n\n"
        f"RECENT PASSAGES\n"
        f"{_format_recent_passages(state)}\n\n"
        f"RECENT FACTS\n"
        f"{_format_recent_facts(state)}\n\n"
        f"Respond to the latest user need."
    )

    prompt_messages: list[AnyMessage] = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=grounded_prompt),
    ]

    try:
        answer = model.invoke(prompt_messages)
    except Exception as exc:
        answer = AIMessage(content=f"[offline fallback] Could not reach Ollama: {exc}")

    print("answer:", answer.content)
    return {
        "messages": [answer],
        "iteration": state.get("iteration", 0) + 1,
    }


def stabilize_response(state: State) -> dict[str, Any]:
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_msg = messages[-1]
    if not isinstance(last_msg, AIMessage):
        return {}

    passage = _make_passage(
        state=state,
        msg=last_msg,
        kind="response",
        role_prefix="ai",
        metadata={"source": "answer_from_state"},
    )
    return {"passages": state.get("passages", []) + [passage]}


def should_continue(state: State) -> str:
    if state.get("iteration", 0) >= ITERATION_LIMIT:
        return END
    return "read_input"


# -----------------------------------------------------------------------------
# Graph
# -----------------------------------------------------------------------------

graph = StateGraph(State)

graph.add_node("read_input", read_input)
graph.add_node("stabilize_observation", stabilize_observation)
graph.add_node("resolve_context", resolve_context)
graph.add_node("extract_facts", extract_facts)
graph.add_node("decide_response_plan", decide_response_plan)
graph.add_node("answer_from_state", answer_from_state)
graph.add_node("stabilize_response", stabilize_response)

graph.add_edge(START, "read_input")
graph.add_edge("read_input", "stabilize_observation")
graph.add_edge("stabilize_observation", "resolve_context")
graph.add_edge("resolve_context", "extract_facts")
graph.add_edge("extract_facts", "decide_response_plan")
graph.add_edge("decide_response_plan", "answer_from_state")
graph.add_edge("answer_from_state", "stabilize_response")
graph.add_conditional_edges(
    "stabilize_response",
    should_continue,
    {
        "read_input": "read_input",
        END: END,
    },
)

checkpointer = InMemorySaver()
workflow = graph.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "demo-cli-thread"}}
workflow.invoke(
    {
        "iteration": 0,
        "passages": [],
        "facts": [],
    },
    config=config,
)
