from __future__ import annotations

from testbot.answer_contract_constants import CLARIFY_ANSWER
from testbot.application.services import continuity_runtime
from testbot.pipeline_state import PipelineState


def test_apply_unresolved_intent_carryover_preserves_resolved_intent_for_clarification_answers() -> None:
    state = PipelineState(
        user_input="what happened?",
        resolved_intent="memory_recall",
        final_answer=CLARIFY_ANSWER,
    )

    updated = continuity_runtime.apply_unresolved_intent_carryover(state)

    assert updated.prior_unresolved_intent == "memory_recall"


def test_apply_unresolved_intent_carryover_preserves_resolved_intent_for_capabilities_help_intent_even_without_shape_match() -> None:
    state = PipelineState(
        user_input="help",
        resolved_intent="capabilities_help",
        final_answer="Capabilities summary unavailable in this environment.",
    )

    updated = continuity_runtime.apply_unresolved_intent_carryover(state)

    assert updated.prior_unresolved_intent == "capabilities_help"


def test_apply_unresolved_intent_carryover_uses_transitional_capabilities_shape_heuristic_when_intent_missing() -> None:
    state = PipelineState(
        user_input="help",
        resolved_intent="",
        final_answer="Runtime mode: cli\nMemory recall: available\nHome Assistant: unavailable",
    )

    assert continuity_runtime.should_preserve_unresolved_intent(state=state) is True
    updated = continuity_runtime.apply_unresolved_intent_carryover(state)

    assert updated.prior_unresolved_intent == ""


def test_apply_unresolved_intent_carryover_clears_for_non_continuity_answer() -> None:
    state = PipelineState(
        user_input="who am i",
        resolved_intent="memory_recall",
        prior_unresolved_intent="memory_recall",
        final_answer="From committed facts, your name is Sam.",
    )

    assert continuity_runtime.should_preserve_unresolved_intent(state=state) is False
    updated = continuity_runtime.apply_unresolved_intent_carryover(state)

    assert updated.prior_unresolved_intent == ""
