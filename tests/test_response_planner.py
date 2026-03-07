from testbot.intent_router import IntentType, planning_pathway_for_intent
from testbot.response_planner import (
    PlanningStage,
    build_response_plan,
    plan_to_dict,
    render_response_plan_block,
)


def test_planning_pathway_for_intent_is_deterministic() -> None:
    assert planning_pathway_for_intent(IntentType.MEMORY_RECALL) == "memory_recall"
    assert planning_pathway_for_intent(IntentType.TIME_QUERY) == "time_query"
    assert planning_pathway_for_intent(IntentType.KNOWLEDGE_QUESTION) == "non_memory"
    assert planning_pathway_for_intent(IntentType.META_CONVERSATION) == "non_memory"


def test_build_response_plan_contains_required_stage_sequence() -> None:
    plan = build_response_plan(pathway="memory_recall", user_input="what did I say about Friday?")

    assert [stage.name for stage in plan.stages] == [
        PlanningStage.OBSERVATION,
        PlanningStage.HYPOTHESIS_EXPANSION,
        PlanningStage.PERSPECTIVE_SWITCHING,
        PlanningStage.SCENARIO_GENERATION,
        PlanningStage.LATER_CONVERGENCE,
    ]
    assert "what did I say about Friday?" in plan.stages[0].objective


def test_render_response_plan_block_includes_named_stages() -> None:
    plan = build_response_plan(pathway="time_query", user_input="what is tomorrow?")

    rendered = render_response_plan_block(plan)

    assert "planning_pathway: time_query" in rendered
    assert "- Observation:" in rendered
    assert "- Hypothesis Expansion:" in rendered
    assert "- Perspective Switching:" in rendered
    assert "- Scenario Generation:" in rendered
    assert "- Later Convergence:" in rendered


def test_plan_to_dict_is_snapshot_stable() -> None:
    plan = build_response_plan(pathway="non_memory", user_input="hello")

    payload = plan_to_dict(plan)

    assert payload["pathway"] == "non_memory"
    assert isinstance(payload["stages"], list)
    assert len(payload["stages"]) == 5
    assert payload["stages"][0]["name"] == "Observation"
