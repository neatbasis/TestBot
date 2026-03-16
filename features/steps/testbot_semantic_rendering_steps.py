from __future__ import annotations

from behave import then


def _rendered_answer_from_context(context) -> str:
    for attr in ("stage_answer_state", "answer_state", "pipeline_state"):
        state = getattr(context, attr, None)
        if state is not None and getattr(state, "final_answer", None):
            return state.final_answer
    raise AssertionError("No rendered answer found on context")


def _has_marker(answer: str, marker: str) -> bool:
    lowered = answer.lower()
    checks: dict[str, bool] = {
        "uncertainty": "don't have enough reliable" in lowered or "don't know" in lowered,
        "safe_action": "i can either" in lowered and " or " in lowered,
        "general_knowledge_label": "general definition (not from your memory):" in lowered,
        "clarification_prompt": "can you clarify" in lowered,
        "chat_history_recap": "you asked" in lowered and "chat" in lowered,
        "relevance_label": lowered.startswith("relevant summary:"),
        "possible_explanations_tag": "possible explanations:" in lowered,
        "converged_recommendation": "converged recommendation:" in lowered,
        "framework_systems": "framework: systems" in lowered,
        "framework_behavioral": "framework: behavioral" in lowered,
        "synthesis_label": "synthesis:" in lowered,
        "capability_satellite_actions_unavailable": "home assistant satellite actions:" in lowered and "unavailable" in lowered,
        "capability_cli_fallback_active": "cli fallback" in lowered,
        "capability_clarification_available": "clarification/disambiguation:" in lowered and "available" in lowered,
        "capability_satellite_ask_unavailable": "satellite ask loop:" in lowered and "unavailable" in lowered,
        "capability_debug_disabled": "debug visibility:" in lowered and "disabled" in lowered,
        "capability_satellite_actions_available": "home assistant satellite actions:" in lowered and "available" in lowered,
        "capability_satellite_ask_available": "satellite ask loop:" in lowered and "available" in lowered,
        "capability_debug_enabled": "debug visibility:" in lowered and "enabled" in lowered,
        "capability_memory_recall_available": "memory recall:" in lowered and "available" in lowered,
        "capability_grounded_explanations": "grounded explanations:" in lowered and "available" in lowered,
        "capability_runtime_mode_cli": "runtime mode:" in lowered and "effective=cli" in lowered,
        "capability_satellite_action_label": "satellite_action_request:" in lowered,
        "capability_action_alternatives": "action alternatives:" in lowered,
    }
    if marker not in checks:
        raise AssertionError(f"Unknown semantic marker: {marker}")
    return checks[marker]


@then("the rendered answer should include semantic markers")
def step_then_rendered_answer_should_include_semantic_markers(context) -> None:
    answer = _rendered_answer_from_context(context)
    for row in context.table:
        marker = row["marker"].strip()
        assert _has_marker(answer, marker), f"Expected marker '{marker}' in answer: {answer}"


@then('the rendered answer should include normative phrase "{expected_phrase}"')
def step_then_rendered_answer_should_include_normative_phrase(context, expected_phrase: str) -> None:
    answer = _rendered_answer_from_context(context)
    assert expected_phrase in answer


@then('the rendered answer should not include normative phrase "{unexpected_phrase}"')
def step_then_rendered_answer_should_not_include_normative_phrase(context, unexpected_phrase: str) -> None:
    answer = _rendered_answer_from_context(context)
    assert unexpected_phrase not in answer
