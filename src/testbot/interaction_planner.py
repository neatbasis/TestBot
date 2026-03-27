from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from testbot.interaction_standards import InteractionRequirements

NeedProfile = Literal["satellite_turn_input"]
ChannelContext = Literal["satellite", "cli"]
TaskFlowContext = Literal["memory_chat_loop", "general"]


@dataclass(frozen=True, slots=True)
class InteractionPlan:
    interaction_requirements: InteractionRequirements
    rationale: str | None = None
    rule_id: str | None = None


def select_interaction_requirements(
    *,
    need_profile: NeedProfile,
    channel_context: ChannelContext,
    task_flow_context: TaskFlowContext,
) -> InteractionPlan:
    if (
        need_profile == "satellite_turn_input"
        and channel_context == "satellite"
        and task_flow_context == "memory_chat_loop"
    ):
        return InteractionPlan(
            interaction_requirements=InteractionRequirements(),
            rationale="Satellite memory loop turn input requires deterministic, machine-actionable collection.",
            rule_id="satellite.memory_chat_loop.turn_input.v1",
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
