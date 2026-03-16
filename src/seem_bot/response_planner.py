from __future__ import annotations

from typing import Any

from .state_types import ResponsePlan, State


def plan_response_node(state: State) -> dict[str, Any]:
    user_act = state.get("user_act")
    resolution = state.get("referent_resolution")

    if not user_act or not resolution:
        return {}

    act = user_act["act_type"]

    plan: ResponsePlan

    if act == "greeting":
        plan = {
            "mode": "casual_reply",
            "needs_clarification": False,
            "should_render": True,
        }
    elif act == "summary_request":
        plan = {
            "mode": "summarize_user_queries",
            "needs_clarification": False,
            "should_render": True,
        }
    elif act == "confirmation":
        if resolution["resolved"]:
            plan = {
                "mode": "advance_current_topic",
                "needs_clarification": False,
                "should_render": True,
            }
        else:
            plan = {
                "mode": "clarify_missing_referent",
                "needs_clarification": True,
                "should_render": True,
            }
    elif act == "rejection":
        if resolution["resolved"]:
            plan = {
                "mode": "repair_direction",
                "needs_clarification": False,
                "should_render": True,
            }
        else:
            plan = {
                "mode": "clarify_missing_referent",
                "needs_clarification": True,
                "should_render": True,
            }
    elif act == "clarification":
        if resolution["resolved"]:
            plan = {
                "mode": "answer",
                "needs_clarification": False,
                "should_render": True,
            }
        else:
            plan = {
                "mode": "clarify_missing_referent",
                "needs_clarification": True,
                "should_render": True,
            }
    elif act == "generation_request":
        plan = {
            "mode": "generate",
            "needs_clarification": False,
            "should_render": True,
        }
    elif act == "analysis_request":
        plan = {
            "mode": "structured_help",
            "needs_clarification": False,
            "should_render": True,
        }
    elif act == "question":
        plan = {
            "mode": "answer",
            "needs_clarification": False,
            "should_render": True,
        }
    else:
        plan = {
            "mode": "respond",
            "needs_clarification": False,
            "should_render": True,
        }

    return {"response_plan": plan}
