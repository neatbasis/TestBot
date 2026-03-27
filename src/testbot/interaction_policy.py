from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from testbot.interaction_standards import InteractionRequirements

InteractionIntent = Literal["collect_turn_input"]
ChannelContext = Literal["satellite", "cli"]
TaskFlowContext = Literal["memory_chat_loop", "general"]

COLLECT_TURN_INPUT_INTENT: InteractionIntent = "collect_turn_input"


@dataclass(frozen=True, slots=True)
class InteractionPolicyRequest:
    """Canonical planner/runtime request passed to AskGateway.

    Deferred scope (intentionally not solved in this contract):
    - channel auto-resolution
    - person-to-channel routing
    - output-channel unification
    - mobile/Discord runtime expansion
    """

    intent: InteractionIntent
    channel_context: ChannelContext
    task_flow_context: TaskFlowContext
    interaction_requirements: InteractionRequirements
    policy_id: str


__all__ = [
    "COLLECT_TURN_INPUT_INTENT",
    "ChannelContext",
    "InteractionIntent",
    "InteractionPolicyRequest",
    "TaskFlowContext",
]
