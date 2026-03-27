"""Interaction-policy planner.

Planner owns policy selection; AskGateway translates selected policy requirements to AskSpec.
"""

from __future__ import annotations

from dataclasses import dataclass

from testbot.interaction_standards import InteractionRequirements
from testbot.interaction_policy import (
    COLLECT_TURN_INPUT_INTENT,
    ChannelContext,
    InteractionIntent,
    InteractionPolicyRequest,
    TaskFlowContext,
)


@dataclass(frozen=True, slots=True)
class InteractionPlan:
    """Selected interaction-policy request and deterministic planner trace fields."""

    request: InteractionPolicyRequest
    rationale: str | None = None
    rule_id: str | None = None

    @property
    def interaction_requirements(self) -> InteractionRequirements:
        return self.request.interaction_requirements


def select_interaction_policy_request(
    *,
    interaction_intent: InteractionIntent,
    channel_context: ChannelContext,
    task_flow_context: TaskFlowContext,
) -> InteractionPlan:
    """Select interaction policy request for the current turn.

    Intentionally minimal v1 policy: one active satellite memory-loop rule,
    one explicit CLI free-text variant, and a deterministic fallback.
    """

    if (
        interaction_intent == COLLECT_TURN_INPUT_INTENT
        and channel_context == "satellite"
        and task_flow_context == "memory_chat_loop"
    ):
        return InteractionPlan(
            request=InteractionPolicyRequest(
                intent=interaction_intent,
                channel_context=channel_context,
                task_flow_context=task_flow_context,
                interaction_requirements=InteractionRequirements(),
                policy_id="satellite.memory_chat_loop.turn_input.v1",
            ),
            rationale="Satellite memory loop turn input requires deterministic, machine-actionable collection.",
            rule_id="satellite.memory_chat_loop.turn_input.v1",
        )

    if interaction_intent == COLLECT_TURN_INPUT_INTENT and channel_context == "cli":
        return InteractionPlan(
            request=InteractionPolicyRequest(
                intent=interaction_intent,
                channel_context=channel_context,
                task_flow_context=task_flow_context,
                interaction_requirements=InteractionRequirements(
                    stable_id_required=False,
                    deterministic_field_collection_required=False,
                    open_text_preferred=True,
                    sentence_style_fit="plain_sentence",
                    machine_actionable=False,
                ),
                policy_id="cli.turn_input.free_text.v1",
            ),
            rationale="CLI turn input prefers free-text prompts without machine-action stop actions.",
            rule_id="cli.turn_input.free_text.v1",
        )

    return InteractionPlan(
        request=InteractionPolicyRequest(
            intent=interaction_intent,
            channel_context=channel_context,
            task_flow_context=task_flow_context,
            interaction_requirements=InteractionRequirements(),
            policy_id="fallback.default.v1",
        ),
        rationale="Fallback interaction profile.",
        rule_id="fallback.default.v1",
    )


__all__ = [
    "COLLECT_TURN_INPUT_INTENT",
    "ChannelContext",
    "InteractionIntent",
    "InteractionPlan",
    "InteractionPolicyRequest",
    "TaskFlowContext",
    "select_interaction_policy_request",
]
