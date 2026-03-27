from __future__ import annotations

from testbot.interaction_planner import select_interaction_requirements
from testbot.interaction_standards import InteractionRequirements


def test_select_interaction_requirements_satellite_memory_loop_rule() -> None:
    plan = select_interaction_requirements(
        need_profile="ask_turn_input",
        channel_context="satellite",
        task_flow_context="memory_chat_loop",
    )

    assert plan.interaction_requirements == InteractionRequirements()
    assert plan.rule_id == "satellite.memory_chat_loop.turn_input.v1"
    assert plan.rationale is not None


def test_select_interaction_requirements_fallback_rule() -> None:
    plan = select_interaction_requirements(
        need_profile="ask_turn_input",
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
