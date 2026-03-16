from __future__ import annotations

from typing import Any, Literal

from langchain_core.messages import AIMessage, HumanMessage

from .state_types import PassageRecord, State
from .utils import make_id, message_id, message_text, now_utc


def next_passage_index(state: State) -> int:
    return len(state.get("passages", []))


def latest_passage_of_kind(state: State, kind: str) -> PassageRecord | None:
    for passage in reversed(state.get("passages", [])):
        if passage["kind"] == kind:
            return passage
    return None


def make_passage(
    *,
    state: State,
    msg: HumanMessage | AIMessage,
    kind: Literal["observation", "response"],
    role_prefix: str,
    metadata: dict[str, Any] | None = None,
) -> PassageRecord:
    idx = next_passage_index(state)
    return {
        "passage_id": make_id("passage"),
        "kind": kind,
        "observed_at": now_utc(),
        "sequence_index": idx,
        "source_message_ids": [message_id(msg, idx)],
        "canonical_text": f"{role_prefix}: {message_text(msg)}",
        "metadata": metadata or {},
    }


def stabilize_observation(state: State) -> dict[str, Any]:
    messages = state.get("messages", [])
    if not messages or not isinstance(messages[-1], HumanMessage):
        return {}

    passage = make_passage(
        state=state,
        msg=messages[-1],
        kind="observation",
        role_prefix="human",
    )
    return {
        "passages": state.get("passages", []) + [passage],
        "iteration": state.get("iteration", 0) + 1,
    }


def stabilize_response(state: State) -> dict[str, Any]:
    messages = state.get("messages", [])
    if not messages or not isinstance(messages[-1], AIMessage):
        return {}

    passage = make_passage(
        state=state,
        msg=messages[-1],
        kind="response",
        role_prefix="ai",
        metadata={
            "validation_passed": state.get("validation", {}).get("passed", True),
            "source": "render_reply",
        },
    )
    return {"passages": state.get("passages", []) + [passage]}
