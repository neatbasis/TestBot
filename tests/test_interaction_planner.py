from __future__ import annotations

from testbot.interaction_planner import COLLECT_TURN_INPUT_INTENT, select_interaction_policy_request
from testbot.interaction_standards import InteractionRequirements


def test_select_interaction_policy_request_satellite_memory_loop_rule() -> None:
    plan = select_interaction_policy_request(
        interaction_intent=COLLECT_TURN_INPUT_INTENT,
        channel_context="satellite",
        task_flow_context="memory_chat_loop",
    )

    assert plan.interaction_requirements == InteractionRequirements()
    assert plan.rule_id == "satellite.memory_chat_loop.turn_input.v1"
    assert plan.request.policy_id == plan.rule_id
    assert plan.rationale is not None


def test_select_interaction_policy_request_cli_memory_loop_rule() -> None:
    plan = select_interaction_policy_request(
        interaction_intent=COLLECT_TURN_INPUT_INTENT,
        channel_context="cli",
        task_flow_context="general",
    )

    assert plan.interaction_requirements == InteractionRequirements(
        stable_id_required=False,
        deterministic_field_collection_required=False,
        open_text_preferred=True,
        sentence_style_fit="plain_sentence",
        machine_actionable=False,
    )
    assert plan.rule_id == "cli.turn_input.free_text.v1"


def test_select_interaction_policy_request_keeps_semantic_shape_consistent_across_channels() -> None:
    satellite = select_interaction_policy_request(
        interaction_intent=COLLECT_TURN_INPUT_INTENT,
        channel_context="satellite",
        task_flow_context="memory_chat_loop",
    ).request
    cli = select_interaction_policy_request(
        interaction_intent=COLLECT_TURN_INPUT_INTENT,
        channel_context="cli",
        task_flow_context="memory_chat_loop",
    ).request

    assert satellite.intent == cli.intent == "collect_turn_input"
    assert satellite.task_flow_context == cli.task_flow_context == "memory_chat_loop"
    assert satellite.channel_context != cli.channel_context
