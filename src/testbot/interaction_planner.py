"""Interaction-profile planner.

Planner owns selection of `InteractionRequirements`; translation is handled downstream by AskGateway.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from testbot.interaction_standards import InteractionRequirements

NeedProfile = Literal["ask_turn_input"]
ChannelContext = Literal["satellite", "cli"]
TaskFlowContext = Literal["memory_chat_loop", "general"]


@dataclass(frozen=True, slots=True)
class InteractionPlan:
    """Selected interaction contract and deterministic planner trace fields."""

    interaction_requirements: InteractionRequirements
    rationale: str | None = None
    rule_id: str | None = None


def select_interaction_requirements(
    *,
    need_profile: NeedProfile,
    channel_context: ChannelContext,
    task_flow_context: TaskFlowContext,
) -> InteractionPlan:
    """Select interaction requirements for the current turn.

    Intentionally minimal v1 policy: one active satellite memory-loop rule,
    one explicit CLI free-text variant, and a deterministic fallback.
    """

    if (
        need_profile == "ask_turn_input"
        and channel_context == "satellite"
        and task_flow_context == "memory_chat_loop"
    ):
        return InteractionPlan(
            interaction_requirements=InteractionRequirements(),
            rationale="Satellite memory loop turn input requires deterministic, machine-actionable collection.",
            rule_id="satellite.memory_chat_loop.turn_input.v1",
        )

    if need_profile == "ask_turn_input" and channel_context == "cli":
        return InteractionPlan(
            interaction_requirements=InteractionRequirements(
                stable_id_required=False,
                deterministic_field_collection_required=False,
                open_text_preferred=True,
                sentence_style_fit="plain_sentence",
                machine_actionable=False,
            ),
            rationale="CLI turn input prefers free-text prompts without machine-action stop actions.",
            rule_id="cli.turn_input.free_text.v1",
        )

    return InteractionPlan(
        interaction_requirements=InteractionRequirements(),
        rationale="Fallback interaction profile.",
        rule_id="fallback.default.v1",
    )


__all__ = [
    "ChannelContext",
    "InteractionPlan",
    "NeedProfile",
    "TaskFlowContext",
    "select_interaction_requirements",
]
