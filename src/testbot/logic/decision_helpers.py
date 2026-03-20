from __future__ import annotations

from dataclasses import replace
from typing import Mapping

from testbot.answer_policy import AnswerPolicyInput, AnswerRoutingDecision, resolve_answer_routing
from testbot.intent_router import IntentType, classify_intent
from testbot.pipeline_state import PipelineState
from testbot.policy_decision import DecisionClass, DecisionObject, DecisionReasoning
from testbot.reflection_policy import CapabilityStatus


_DECISION_AUTHORITY_ORDER: tuple[str, ...] = ("policy", "assemble", "validate", "commit")


def _authority_rank(stage: str) -> int:
    try:
        return _DECISION_AUTHORITY_ORDER.index(stage)
    except ValueError:
        return -1


def selected_decision_from_confidence(confidence_decision: Mapping[str, object]) -> DecisionObject | None:
    """Return a policy-stage DecisionObject only when explicit override gating is enabled.

    Authority precedence is canonical and monotonic: policy -> assemble -> validate -> commit.
    Confidence payloads are pre-policy hints and MUST NOT silently override routing once any
    authoritative stage decision exists. This helper therefore requires explicit gating:

    * `allow_selected_decision_override` must be True
    * `selected_decision_authority_stage` must be "policy"

    Without both controls, the payload is treated as non-authoritative and ignored.
    """

    allow_override = bool(confidence_decision.get("allow_selected_decision_override", False))
    authority_stage = str(confidence_decision.get("selected_decision_authority_stage") or "").strip().lower()
    if not allow_override or authority_stage != "policy":
        return None

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
    normalized_reasoning = DecisionReasoning.from_mapping({str(key): value for key, value in reasoning.items()}).to_dict()
    normalized_reasoning["authority_stage"] = "policy"
    normalized_reasoning["authority_source"] = "confidence_payload"
    return DecisionObject(
        decision_class=decision_class,
        retrieval_branch=retrieval_branch,
        rationale=str(raw.get("rationale") or "selected_decision_policy_override"),
        reasoning=normalized_reasoning,
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
    """Resolve answer routing while enforcing authority precedence.

    Canonical authority order is: policy -> assemble -> validate -> commit.
    This stage runs at assemble-time, so only policy/assemble authority is admissible.
    Any selected_decision that appears to come from confidence payload metadata after
    policy authority is established is ignored and policy routing is recomputed.
    """

    resolved_intent = IntentType(state.resolved_intent or classify_intent(state.user_input).value)
    if not state.resolved_intent:
        state = replace(state, resolved_intent=resolved_intent.value)

    selected_authority_stage = "policy"
    if selected_decision is not None:
        selected_authority_stage = str(getattr(selected_decision.reasoning, "get", lambda *_a, **_k: "")("authority_stage", "policy"))
    policy_already_authoritative = bool(state.confidence_decision.get("authoritative_decision_established", False))

    use_selected_decision = selected_decision is not None and (
        _authority_rank(selected_authority_stage) >= _authority_rank("policy")
        and (not policy_already_authoritative or selected_authority_stage != "confidence")
    )

    if use_selected_decision:
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
        )
    return state, answer_routing


def decision_object_from_assembled(fallback_action: str) -> DecisionObject:
    """Create an assemble-stage DecisionObject from canonical fallback action.

    Authority precedence is policy -> assemble -> validate -> commit. This helper creates
    only assemble-stage artifacts and never back-propagates to policy authority.

    Unknown/degraded outcomes map to `PENDING_LOOKUP_BACKGROUND_INGESTION` so action and
    label semantics remain coherent and non-fabricating (`ANSWER_UNKNOWN` routing).
    """

    lookup = {
        "ANSWER_FROM_MEMORY": DecisionClass.ANSWER_FROM_MEMORY,
        "ASK_CLARIFYING_QUESTION": DecisionClass.ASK_FOR_CLARIFICATION,
        "ANSWER_UNKNOWN": DecisionClass.PENDING_LOOKUP_BACKGROUND_INGESTION,
        "ANSWER_GENERAL_KNOWLEDGE": DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED,
    }
    normalized_action = fallback_action.strip().upper()
    decision_class = lookup.get(normalized_action, DecisionClass.ANSWER_GENERAL_KNOWLEDGE_LABELED)
    reasoning = DecisionReasoning.from_mapping({"authority_stage": "assemble", "assembled_fallback_action": normalized_action})
    return DecisionObject(
        decision_class=decision_class,
        retrieval_branch=("memory_retrieval" if decision_class is DecisionClass.ANSWER_FROM_MEMORY else "direct_answer"),
        rationale="derived_from_answer_policy_rationale",
        reasoning=reasoning.to_dict(),
    )
