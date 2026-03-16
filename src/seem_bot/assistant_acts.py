from __future__ import annotations

from typing import Any

from .passage_log import latest_passage_of_kind
from .state_types import ActiveFocus, AssistantAct, State
from .utils import make_id, now_utc


def declare_assistant_act(state: State) -> dict[str, Any]:
    plan = state.get("response_plan", {})
    resolution = state.get("referent_resolution", {})

    mode = plan.get("mode")

    act: AssistantAct | None = None

    if mode == "clarify_missing_referent":
        act = {
            "act_type": "question",
            "subject": "missing referent clarification",
            "expires_after_turns": 2,
        }
    elif mode in {"answer", "respond", "casual_reply", "structured_help", "generate", "summarize_user_queries"}:
        act = {
            "act_type": "statement",
            "subject": resolution.get("referent_subject", "") or mode,
            "expires_after_turns": 0,
        }
    elif mode == "advance_current_topic":
        act = {
            "act_type": "statement",
            "subject": resolution.get("referent_subject", "") or "current topic",
            "expires_after_turns": 0,
        }
    elif mode == "repair_direction":
        act = {
            "act_type": "question",
            "subject": resolution.get("referent_subject", "") or "direction repair",
            "expires_after_turns": 2,
        }

    if not act:
        return {}

    return {"assistant_act": act}


def update_focus_from_declared_act(state: State) -> dict[str, Any]:
    assistant_act = state.get("assistant_act")
    if not assistant_act:
        return {}

    latest_response = latest_passage_of_kind(state, "response")
    source_passage_id = latest_response["passage_id"] if latest_response else ""

    act_type = assistant_act.get("act_type")

    if act_type == "question":
        focus: ActiveFocus = {
            "focus_id": make_id("focus"),
            "kind": "assistant_question",
            "subject": assistant_act.get("subject", ""),
            "source_passage_id": source_passage_id,
            "created_at": now_utc(),
            "created_turn": state.get("iteration", 0),
            "expires_after_turns": assistant_act.get("expires_after_turns", 2),
            "status": "active",
        }
        return {"active_focus": focus}

    if act_type == "task_open":
        focus = {
            "focus_id": make_id("focus"),
            "kind": "task",
            "subject": assistant_act.get("subject", ""),
            "source_passage_id": source_passage_id,
            "created_at": now_utc(),
            "created_turn": state.get("iteration", 0),
            "expires_after_turns": assistant_act.get("expires_after_turns", 6),
            "status": "active",
        }
        return {"active_focus": focus}

    if act_type == "task_close":
        current = state.get("active_focus")
        if current:
            return {"active_focus": {**current, "status": "resolved"}}
        return {}

    return {}
