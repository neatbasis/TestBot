"""Pure answer-stage routing policy primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Mapping, Any

from testbot.reflection_policy import CapabilityStatus, FallbackAction, IntentClass, decide_fallback_action, fallback_reason

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


def _policy_action_universe(intent: IntentClass) -> list[FallbackAction]:
    if intent == "memory_recall":
        return [
            "ROUTE_TO_ASK",
            "ASK_CLARIFYING_QUESTION",
            "OFFER_CAPABILITY_ALTERNATIVES",
            "ANSWER_FROM_MEMORY",
            "ANSWER_GENERAL_KNOWLEDGE",
            "ANSWER_UNKNOWN",
        ]
    if intent == "time_query":
        return ["ANSWER_TIME", "ANSWER_UNKNOWN", "ANSWER_GENERAL_KNOWLEDGE"]
    return ["ANSWER_GENERAL_KNOWLEDGE", "ANSWER_UNKNOWN", "OFFER_CAPABILITY_ALTERNATIVES"]


def _policy_alternative_reason(*, action: FallbackAction, chosen: FallbackAction, memory_hit: bool, ambiguity: bool) -> str:
    if action == chosen:
        return "selected"
    if action == "ROUTE_TO_ASK":
        return "ask route rejected: ambiguity or ask capability conditions not met"
    if action == "ASK_CLARIFYING_QUESTION":
        return "clarify path rejected: policy chose route-to-ask or alternatives"
    if action == "OFFER_CAPABILITY_ALTERNATIVES":
        if memory_hit and not ambiguity:
            return "alternatives rejected: retrieval confidence supported direct handling"
        return "alternatives rejected: another fallback had higher policy priority"
    if action == "ANSWER_TIME":
        return "time answer rejected: intent was not a time query"
    if action == "ANSWER_UNKNOWN":
        return "unknown fallback rejected: policy selected a more specific action"
    if action == "ANSWER_FROM_MEMORY":
        return "memory-grounded route rejected: disambiguation or recovery policy had priority"
    return "general-knowledge route rejected: fallback policy gates did not select it"


def _policy_alternatives(*, intent: IntentClass, chosen: FallbackAction, memory_hit: bool, ambiguity: bool) -> list[dict[str, str]]:
    return [
        {
            "action": action,
            "status": "selected" if action == chosen else "rejected",
            "reason": _policy_alternative_reason(
                action=action,
                chosen=chosen,
                memory_hit=memory_hit,
                ambiguity=ambiguity,
            ),
        }
        for action in _policy_action_universe(intent)
    ]


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

    if fallback_action == "ANSWER_FROM_MEMORY":
        token: CanonicalResponseToken = "LLM_DRAFT"
    elif fallback_action == "ROUTE_TO_ASK":
        token = "ROUTE_TO_ASK_ANSWER"
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
        "fallback_reason": fallback_reason(
            intent=policy_input.intent,
            fallback_action=fallback_action,
            memory_hit=memory_hit,
            ambiguity=ambiguity,
            source_confidence=policy_input.source_confidence,
        ),
        "considered_alternatives": _policy_alternatives(
            intent=policy_input.intent,
            chosen=fallback_action,
            memory_hit=memory_hit,
            ambiguity=ambiguity,
        ),
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
    pending_lookup: bool = False,
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

    if pending_lookup:
        return AnswerModeDecision(
            answer_mode="assist",
            rationale={"reason": "pending_lookup", "fallback_action": fallback_action},
        )

    if fallback_action == "ANSWER_UNKNOWN" or is_fallback_answer or is_non_knowledge_uncertainty_answer:
        return AnswerModeDecision(
            answer_mode="dont-know",
            rationale={"reason": "unknown_fallback", "fallback_action": fallback_action},
        )

    if fallback_action == "ANSWER_TIME":
        return AnswerModeDecision(
            answer_mode="assist",
            rationale={"reason": "time_answer", "fallback_action": fallback_action},
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
