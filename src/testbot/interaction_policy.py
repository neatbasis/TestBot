from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from testbot.interaction_standards import InteractionRequirements

InteractionIntent = Literal["collect_turn_input"]
ChannelContext = Literal["satellite", "cli"]
TaskFlowContext = Literal["memory_chat_loop", "general"]
ResolutionSource = Literal[
    "explicit_policy_channel",
    "explicit_override",
    "recent_successful_ask_channel",
    "named_fallback",
]

COLLECT_TURN_INPUT_INTENT: InteractionIntent = "collect_turn_input"
DEFAULT_CHANNEL_RESOLUTION_RULE_ID = "explicit_policy_then_override_then_recent_success_then_named_fallback.v1"


@dataclass(frozen=True, slots=True)
class InteractionPolicyRequest:
    """Canonical planner/runtime request passed to AskGateway.

    Deferred scope (intentionally not solved in this contract):
    - person-to-channel routing
    - output-channel unification
    - mobile/Discord runtime expansion
    """

    intent: InteractionIntent
    channel_context: ChannelContext
    task_flow_context: TaskFlowContext
    interaction_requirements: InteractionRequirements
    policy_id: str
    channel_resolution_rule_id: str = DEFAULT_CHANNEL_RESOLUTION_RULE_ID
    named_fallback_channel_context: ChannelContext = "cli"


@dataclass(frozen=True, slots=True)
class ChannelResolutionOutcome:
    resolved_channel_context: ChannelContext
    resolution_source: ResolutionSource
    fallback_used: bool
    fallback_reason: str | None


def resolve_channel_context(
    *,
    interaction_policy: InteractionPolicyRequest,
    allowed_channels: frozenset[ChannelContext],
    explicit_override_channel_context: ChannelContext | None = None,
    recent_successful_channel_context: ChannelContext | None = None,
) -> ChannelResolutionOutcome:
    """Resolve Ask channel context from explicit policy + inspectable fallbacks.

    Precedence is explicit and fail-closed:
    1) policy channel_context
    2) explicit override
    3) recent successful ask channel
    4) named fallback channel_context
    """

    if not allowed_channels:
        raise ValueError("No allowed channels were provided for interaction-policy channel resolution")

    if interaction_policy.channel_context in allowed_channels:
        return ChannelResolutionOutcome(
            resolved_channel_context=interaction_policy.channel_context,
            resolution_source="explicit_policy_channel",
            fallback_used=False,
            fallback_reason=None,
        )

    if explicit_override_channel_context is not None and explicit_override_channel_context in allowed_channels:
        return ChannelResolutionOutcome(
            resolved_channel_context=explicit_override_channel_context,
            resolution_source="explicit_override",
            fallback_used=True,
            fallback_reason="policy_channel_unavailable",
        )

    if recent_successful_channel_context is not None and recent_successful_channel_context in allowed_channels:
        return ChannelResolutionOutcome(
            resolved_channel_context=recent_successful_channel_context,
            resolution_source="recent_successful_ask_channel",
            fallback_used=True,
            fallback_reason="policy_and_override_unavailable",
        )

    if interaction_policy.named_fallback_channel_context in allowed_channels:
        return ChannelResolutionOutcome(
            resolved_channel_context=interaction_policy.named_fallback_channel_context,
            resolution_source="named_fallback",
            fallback_used=True,
            fallback_reason="policy_override_recent_unavailable",
        )

    raise ValueError(
        "Channel resolution failed: policy, override, recent-success, and named fallback channels are unavailable"
    )


__all__ = [
    "COLLECT_TURN_INPUT_INTENT",
    "ChannelContext",
    "ChannelResolutionOutcome",
    "DEFAULT_CHANNEL_RESOLUTION_RULE_ID",
    "InteractionIntent",
    "InteractionPolicyRequest",
    "ResolutionSource",
    "TaskFlowContext",
    "resolve_channel_context",
]
