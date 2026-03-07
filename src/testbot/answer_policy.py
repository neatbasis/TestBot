"""Pure answer-stage routing policy primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Mapping, Any

from testbot.reflection_policy import CapabilityStatus, FallbackAction, IntentClass, decide_fallback_action

CanonicalResponseToken = Literal[
    "ROUTE_TO_ASK_ANSWER",
    "PARTIAL_MEMORY_CLARIFIER",
    "ASSIST_ALTERNATIVES_ANSWER",
    "NON_KNOWLEDGE_UNCERTAINTY_ANSWER",
    "TIME_ANSWER",
    "LLM_DRAFT",
    "DENY_ANSWER",
    "FALLBACK_ANSWER",
]

AnswerMode = Literal["deny", "clarify", "dont-know", "assist", "memory-grounded"]


@dataclass(frozen=True)
class AnswerPolicyInput:
    intent: IntentClass
    confidence_decision: Mapping[str, Any]
    capability_status: CapabilityStatus
    source_confidence: float | None = None


@dataclass(frozen=True)
class AnswerRoutingDecision:
    fallback_action: FallbackAction
    canonical_response_token: CanonicalResponseToken
    route_to_ask_expected: bool
    clarification_allowed: bool
    rationale: dict[str, object]


@dataclass(frozen=True)
class AnswerModeDecision:
    answer_mode: AnswerMode
    rationale: dict[str, object]


def resolve_answer_routing(
    policy_input: AnswerPolicyInput,
    *,
    fallback_decider: Callable[..., FallbackAction] = decide_fallback_action,
) -> AnswerRoutingDecision:
    """Resolve answer-stage routing with deterministic metadata."""

    confidence_decision = policy_input.confidence_decision
    memory_hit = bool(confidence_decision.get("context_confident", False))
    ambiguity = bool(confidence_decision.get("ambiguity_detected", False))
    memory_hit_count = int(confidence_decision.get("memory_hit_count", 0) or 0)

    fallback_action = fallback_decider(
        intent=policy_input.intent,
        memory_hit=memory_hit,
        ambiguity=ambiguity,
        capability_status=policy_input.capability_status,
        source_confidence=policy_input.source_confidence,
    )

    route_to_ask_expected = fallback_action == "ROUTE_TO_ASK"
    clarification_allowed = (
        (policy_input.intent == "memory_recall" or route_to_ask_expected)
        and (ambiguity or (policy_input.intent == "memory_recall" and memory_hit_count == 0))
        and (not route_to_ask_expected or policy_input.capability_status == "ask_available")
    )

    if fallback_action == "ROUTE_TO_ASK":
        token: CanonicalResponseToken = "ROUTE_TO_ASK_ANSWER"
    elif fallback_action == "ASK_CLARIFYING_QUESTION" and clarification_allowed:
        token = "PARTIAL_MEMORY_CLARIFIER"
    elif fallback_action == "ASK_CLARIFYING_QUESTION":
        token = "ASSIST_ALTERNATIVES_ANSWER"
    elif fallback_action == "ANSWER_UNKNOWN":
        token = "NON_KNOWLEDGE_UNCERTAINTY_ANSWER"
    elif fallback_action == "ANSWER_TIME":
        token = "TIME_ANSWER"
    elif fallback_action == "OFFER_CAPABILITY_ALTERNATIVES":
        token = "ASSIST_ALTERNATIVES_ANSWER"
    else:
        token = "LLM_DRAFT"

    rationale = {
        "intent": policy_input.intent,
        "memory_hit": memory_hit,
        "ambiguity": ambiguity,
        "memory_hit_count": memory_hit_count,
        "capability_status": policy_input.capability_status,
        "source_confidence": policy_input.source_confidence,
    }
    return AnswerRoutingDecision(
        fallback_action=fallback_action,
        canonical_response_token=token,
        route_to_ask_expected=route_to_ask_expected,
        clarification_allowed=clarification_allowed,
        rationale=rationale,
    )


def resolve_answer_mode(
    *,
    final_answer: str,
    fallback_action: FallbackAction,
    social_or_non_knowledge_intent: bool,
    is_clarification_answer: bool,
    is_deny_answer: bool,
    is_assist_alternatives_answer: bool,
    is_fallback_answer: bool,
    is_non_knowledge_uncertainty_answer: bool,
) -> AnswerModeDecision:
    """Derive answer mode and rationale metadata from final outputs."""

    if is_deny_answer:
        return AnswerModeDecision(
            answer_mode="deny",
            rationale={"reason": "deny_answer", "fallback_action": fallback_action},
        )

    if is_clarification_answer:
        return AnswerModeDecision(
            answer_mode="clarify",
            rationale={"reason": "clarification_answer", "fallback_action": fallback_action},
        )

    if fallback_action == "ANSWER_UNKNOWN" or is_fallback_answer or is_non_knowledge_uncertainty_answer:
        return AnswerModeDecision(
            answer_mode="dont-know",
            rationale={"reason": "unknown_fallback", "fallback_action": fallback_action},
        )

    if is_assist_alternatives_answer or social_or_non_knowledge_intent:
        return AnswerModeDecision(
            answer_mode="assist",
            rationale={"reason": "assist_or_social", "fallback_action": fallback_action},
        )

    return AnswerModeDecision(
        answer_mode="memory-grounded",
        rationale={"reason": "grounded_answer", "fallback_action": fallback_action},
    )
