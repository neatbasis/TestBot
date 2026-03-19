from __future__ import annotations

from dataclasses import replace
from typing import Mapping

from testbot.answer_policy import AnswerPolicyInput, AnswerRoutingDecision, resolve_answer_routing
from testbot.intent_router import IntentType, classify_intent
from testbot.pipeline_state import PipelineState
from testbot.policy_decision import DecisionClass, DecisionObject, DecisionReasoning
from testbot.reflection_policy import CapabilityStatus, decide_fallback_action


def selected_decision_from_confidence(confidence_decision: Mapping[str, object]) -> DecisionObject | None:
    raw = confidence_decision.get("selected_decision_object")
    if not isinstance(raw, dict):
        return None
    decision_class_value = str(raw.get("decision_class") or "").strip()
    retrieval_branch = str(raw.get("retrieval_branch") or "").strip()
    if not decision_class_value or not retrieval_branch:
        return None
    try:
        decision_class = DecisionClass(decision_class_value)
    except ValueError:
        return None
    reasoning = raw.get("reasoning")
    if not isinstance(reasoning, Mapping):
        reasoning = {}
    return DecisionObject(
        decision_class=decision_class,
        retrieval_branch=retrieval_branch,
        rationale=str(raw.get("rationale") or "selected_decision_override"),
        reasoning=DecisionReasoning.from_mapping({str(key): value for key, value in reasoning.items()}).to_dict(),
    )


def resolve_answer_routing_from_decision_object(
    decision: DecisionObject,
    *,
    capability_status: CapabilityStatus,
) -> AnswerRoutingDecision:
    decision_routing_map: dict[DecisionClass, tuple[str, str, bool]] = {
        DecisionClass.ANSWER_FROM_MEMORY: ("ANSWER_FROM_MEMORY", "LLM_DRAFT", False),
        DecisionClass.ASK_FOR_CLARIFICATION: ("ASK_CLARIFYING_QUESTION", "PARTIAL_MEMORY_CLARIFIER", True),
        DecisionClass.CONTINUE_REPAIR_RECONSTRUCTION: ("ASK_CLARIFYING_QUESTION", "PARTIAL_MEMORY_CLARIFIER", True),
        DecisionClass.PENDING_LOOKUP_BACKGROUND_INGESTION: (
            "ANSWER_UNKNOWN",
            "NON_KNOWLEDGE_UNCERTAINTY_ANSWER",
            False,
        ),
        DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED: ("ANSWER_GENERAL_KNOWLEDGE", "LLM_DRAFT", False),
    }
    routing_tuple = decision_routing_map.get(decision.decision_class)
    if routing_tuple is None:
        raise ValueError(f"Unsupported DecisionClass for answer routing bridge: {decision.decision_class!r}")
    fallback_action, token, clarification_allowed = routing_tuple
    return AnswerRoutingDecision(
        fallback_action=fallback_action,
        canonical_response_token=token,
        route_to_ask_expected=False,
        clarification_allowed=clarification_allowed,
        rationale={
            "authority": "decision_object",
            "decision_class": decision.decision_class.value,
            "decision_rationale": decision.rationale,
            "decision_reasoning": dict(decision.reasoning),
            "capability_status": capability_status,
            "fallback_reason": "decision_object_mapping",
            "considered_alternatives": [
                {
                    "action": fallback_action,
                    "status": "selected",
                    "reason": "selected by canonical decision_object authority",
                }
            ],
        },
    )


def resolve_answer_routing_for_stage(
    state: PipelineState,
    *,
    capability_status: CapabilityStatus,
    selected_decision: DecisionObject | None,
    intent_class_for_policy,
) -> tuple[PipelineState, AnswerRoutingDecision]:
    resolved_intent = IntentType(state.resolved_intent or classify_intent(state.user_input).value)
    if not state.resolved_intent:
        state = replace(state, resolved_intent=resolved_intent.value)

    if selected_decision is not None:
        answer_routing = resolve_answer_routing_from_decision_object(
            selected_decision,
            capability_status=capability_status,
        )
    else:
        answer_routing = resolve_answer_routing(
            AnswerPolicyInput(
                intent=intent_class_for_policy(resolved_intent),
                confidence_decision=state.confidence_decision,
                capability_status=capability_status,
                source_confidence=(
                    float(state.confidence_decision["source_confidence"])
                    if "source_confidence" in state.confidence_decision
                    else None
                ),
            ),
            fallback_decider=decide_fallback_action,
        )
    return state, answer_routing


def decision_object_from_assembled(fallback_action: str) -> DecisionObject:
    lookup = {
        "ANSWER_FROM_MEMORY": DecisionClass.ANSWER_FROM_MEMORY,
        "ASK_CLARIFYING_QUESTION": DecisionClass.ASK_FOR_CLARIFICATION,
        "ANSWER_UNKNOWN": DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED,
        "ANSWER_GENERAL_KNOWLEDGE": DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED,
    }
    decision_class = lookup.get(fallback_action.strip().upper(), DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED)
    return DecisionObject(
        decision_class=decision_class,
        retrieval_branch=("memory_retrieval" if decision_class is DecisionClass.ANSWER_FROM_MEMORY else "direct_answer"),
        rationale="derived_from_answer_policy_rationale",
    )
