from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from .assistant_acts import declare_assistant_act, update_focus_from_declared_act
from .focus_state import expire_focus
from .passage_log import stabilize_observation, stabilize_response
from .referent_resolution import resolve_referent
from .render_context import select_supporting_passages
from .reply_renderer import render_reply
from .reply_validation import validate_reply
from .response_planner import plan_response_node
from .state_types import State
from .user_act_classifier import classify_user_act


def build_workflow():
    graph = StateGraph(State)

    graph.add_node("stabilize_observation", stabilize_observation)
    graph.add_node("expire_focus", expire_focus)
    graph.add_node("classify_user_act", classify_user_act)
    graph.add_node("resolve_referent", resolve_referent)
    graph.add_node("plan_response", plan_response_node)
    graph.add_node("select_supporting_passages", select_supporting_passages)
    graph.add_node("render_reply", render_reply)
    graph.add_node("validate_reply", validate_reply)
    graph.add_node("stabilize_response", stabilize_response)
    graph.add_node("declare_assistant_act", declare_assistant_act)
    graph.add_node("update_focus_from_declared_act", update_focus_from_declared_act)

    graph.add_edge(START, "stabilize_observation")
    graph.add_edge("stabilize_observation", "expire_focus")
    graph.add_edge("expire_focus", "classify_user_act")
    graph.add_edge("classify_user_act", "resolve_referent")
    graph.add_edge("resolve_referent", "plan_response")
    graph.add_edge("plan_response", "select_supporting_passages")
    graph.add_edge("select_supporting_passages", "render_reply")
    graph.add_edge("render_reply", "validate_reply")
    graph.add_edge("validate_reply", "stabilize_response")
    graph.add_edge("stabilize_response", "declare_assistant_act")
    graph.add_edge("declare_assistant_act", "update_focus_from_declared_act")
    graph.add_edge("update_focus_from_declared_act", END)

    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)
