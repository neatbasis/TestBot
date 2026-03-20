from __future__ import annotations

from testbot.answer_policy import resolve_answer_mode
from testbot.intent_router import IntentType
from testbot.logic.decision_helpers import (
    decision_object_from_assembled,
    resolve_answer_routing_for_stage,
    selected_decision_from_confidence,
)
from testbot.pipeline_state import PipelineState
from testbot.policy_decision import DecisionClass, DecisionObject


def _intent_class_for_policy(intent: IntentType) -> str:
    if intent == IntentType.MEMORY_RECALL:
        return "memory_recall"
    if intent == IntentType.TIME_QUERY:
        return "time_query"
    return "non_memory"


def test_selected_decision_from_confidence_requires_explicit_policy_override_gate() -> None:
    assert (
        selected_decision_from_confidence(
            {
                "selected_decision_object": {
                    "decision_class": DecisionClass.ANSWER_FROM_MEMORY.value,
                    "retrieval_branch": "memory_retrieval",
                }
            }
        )
        is None
    )

    selected = selected_decision_from_confidence(
        {
            "allow_selected_decision_override": True,
            "selected_decision_authority_stage": "policy",
            "selected_decision_object": {
                "decision_class": DecisionClass.ANSWER_FROM_MEMORY.value,
                "retrieval_branch": "memory_retrieval",
                "reasoning": {"evidence_posture": "scored_non_empty"},
            },
        }
    )

    assert selected is not None
    assert selected.decision_class is DecisionClass.ANSWER_FROM_MEMORY
    assert selected.reasoning.get("authority_stage") == "policy"
    assert selected.reasoning.get("authority_source") == "confidence_payload"


def test_resolve_answer_routing_for_stage_prefers_authoritative_selected_decision() -> None:
    state = PipelineState(
        user_input="what did i decide?",
        resolved_intent=IntentType.MEMORY_RECALL.value,
        confidence_decision={"context_confident": False, "ambiguity_detected": True},
    )
    selected = DecisionObject(
        decision_class=DecisionClass.ANSWER_FROM_MEMORY,
        retrieval_branch="memory_retrieval",
        rationale="authoritative policy decision",
        reasoning={"authority_stage": "policy"},
    )

    _state, routing = resolve_answer_routing_for_stage(
        state,
        capability_status="ask_unavailable",
        selected_decision=selected,
        intent_class_for_policy=_intent_class_for_policy,
    )

    assert routing.fallback_action == "ANSWER_FROM_MEMORY"
    assert routing.rationale.get("authority") == "decision_object"


def test_resolve_answer_routing_for_stage_recomputes_when_no_selected_decision() -> None:
    state = PipelineState(
        user_input="what time is it?",
        resolved_intent=IntentType.TIME_QUERY.value,
        confidence_decision={"context_confident": False, "ambiguity_detected": False},
    )

    _state, routing = resolve_answer_routing_for_stage(
        state,
        capability_status="ask_unavailable",
        selected_decision=None,
        intent_class_for_policy=_intent_class_for_policy,
    )

    assert routing.fallback_action == "ANSWER_TIME"
    assert routing.canonical_response_token == "TIME_ANSWER"


def test_decision_object_from_assembled_maps_unknown_to_pending_lookup() -> None:
    decision = decision_object_from_assembled("ANSWER_UNKNOWN")

    assert decision.decision_class is DecisionClass.PENDING_LOOKUP_BACKGROUND_INGESTION
    assert decision.reasoning.get("authority_stage") == "assemble"


def test_unknown_answer_mode_is_non_fabricating_dont_know() -> None:
    answer_mode = resolve_answer_mode(
        final_answer="I don't know.",
        fallback_action="ANSWER_UNKNOWN",
        social_or_non_knowledge_intent=False,
        is_clarification_answer=False,
        is_deny_answer=False,
        is_assist_alternatives_answer=False,
        is_fallback_answer=False,
        is_non_knowledge_uncertainty_answer=True,
    )

    assert answer_mode.answer_mode == "dont-know"
    assert answer_mode.rationale["reason"] == "unknown_fallback"
