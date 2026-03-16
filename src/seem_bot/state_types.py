from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


class PassageRecord(TypedDict):
    passage_id: str
    kind: Literal["observation", "response"]
    observed_at: str
    sequence_index: int
    source_message_ids: list[str]
    canonical_text: str
    metadata: dict[str, Any]


class ActiveFocus(TypedDict, total=False):
    focus_id: str
    kind: Literal["assistant_question", "topic", "task"]
    subject: str
    source_passage_id: str
    created_at: str
    created_turn: int
    expires_after_turns: int
    status: Literal["active", "resolved", "expired"]


class UserAct(TypedDict):
    act_type: Literal[
        "greeting",
        "question",
        "confirmation",
        "rejection",
        "clarification",
        "generation_request",
        "analysis_request",
        "summary_request",
        "statement",
    ]
    confidence: float


class ReferentResolution(TypedDict):
    resolved: bool
    referent_kind: Literal["assistant_question", "topic", "task", "none"]
    referent_subject: str
    source_focus_id: str
    reason: str


class ResponsePlan(TypedDict):
    mode: Literal[
        "casual_reply",
        "answer",
        "structured_help",
        "generate",
        "summarize_user_queries",
        "clarify_missing_referent",
        "advance_current_topic",
        "repair_direction",
        "respond",
    ]
    needs_clarification: bool
    should_render: bool


class AssistantAct(TypedDict, total=False):
    act_type: Literal["question", "statement", "task_open", "task_close"]
    subject: str
    expires_after_turns: int


class ValidationRecord(TypedDict, total=False):
    passed: bool
    issues: list[str]
    checked_at: str


class RenderContext(TypedDict, total=False):
    latest_user_text: str
    response_mode: str
    referent_kind: str
    referent_subject: str
    supporting_passages: list[str]


class State(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    passages: list[PassageRecord]
    active_focus: ActiveFocus
    user_act: UserAct
    referent_resolution: ReferentResolution
    response_plan: ResponsePlan
    assistant_act: AssistantAct
    render_context: RenderContext
    validation: ValidationRecord
    iteration: int
